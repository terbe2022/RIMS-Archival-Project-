"""
mail.py — read .eml messages and classify the machine traffic. No GPU, no model.

The ACC-2026-022 intake form lists exactly what should come out of a mail
accession: automated bounce and delivery failure notification, out of office
and auto-replies, unsolicited commercial mail, and mailing list administrative
traffic as distinct from the list discussion itself.

Every one of those is identifiable from RFC822 headers. `Auto-Submitted`,
`X-Autoreply`, `Precedence: bulk`, null return paths and the standard DSN
content types are how mail systems have marked their own machine traffic for
thirty years. This needs no language model and no inference — it reads what the
sending system already declared.

That matters for two reasons beyond speed. It gives the appraisal rules a
message BODY to read instead of a filename, which is the difference between
`pp.sensitive.personal_finance` matching a subject line and matching actual
financial content. And it produces a real exclusion figure on mail, which is
the measurement issue #15 exists to obtain.

Nothing is deleted. Classification is written to the manifest as a Layer 0
decision that a person can inspect and reverse.
"""
from __future__ import annotations

import re
from email import message_from_bytes, policy
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path

MAIL_VERSION = "mail-0.1.0"
MAX_BODY = 200_000

# Header evidence, strongest first. Each entry is (reason, test).
# These are declarations by the sending system, not guesses about content.
_AUTO_HEADERS = (
    ("delivery_failure", lambda h: (h.get("content-type") or "").lower().startswith(
        ("multipart/report", "message/delivery-status"))),
    ("delivery_failure", lambda h: "failure" in (h.get("auto-submitted") or "").lower()),
    ("auto_reply", lambda h: bool(h.get("x-autoreply") or h.get("x-autorespond"))),
    ("auto_reply", lambda h: (h.get("auto-submitted") or "").lower().startswith(
        ("auto-replied", "auto-generated", "auto-notified"))),
    # NOT here: Precedence: bulk. Every mailing list sets it, on discussion
    # messages as much as on administrivia. The 022 form is explicit that the
    # list discussion IS part of the record and only the administrative traffic
    # is not. Treating the header as an exclusion would have removed most of
    # the gutvol-d corpus and produced a large, confident, wrong number.
    # Bulk is recorded as context below and never decides anything on its own.
)

_DSN_FROM = re.compile(
    r"^(mailer-daemon|postmaster|bounce|no-?reply|do-?not-?reply|listserv|"
    r"majordomo|owner-|.*-request|.*-owner|.*-bounces|.*-admin)", re.IGNORECASE)

_DSN_SUBJECT = re.compile(
    r"^\s*(re:\s*)?(returned mail|undeliverable|delivery (status notification|"
    r"failure|has failed)|mail delivery (failed|system)|failure notice|"
    r"warning: could not send|message not delivered|undelivered mail)",
    re.IGNORECASE)

_AUTOREPLY_SUBJECT = re.compile(
    r"\b(out of (the )?office|auto(matic)?[- ]?repl(y|ies)|autoreply|"
    r"away from (my|the) (desk|office)|on (vacation|holiday|leave)|"
    r"i am currently (away|out))\b", re.IGNORECASE)

# List ADMINISTRATION, as distinct from list discussion. The form is explicit
# that the discussion itself is part of the record and the admin traffic is not.
_LIST_ADMIN_SUBJECT = re.compile(
    r"^\s*(re:\s*)?(subscribe|unsubscribe|confirm(ation)?\b|welcome to|"
    r"your subscription|digest\b|.*\bdigest,? vol|command (confirmation|results)|"
    r"you have been (added|removed)|password reminder)", re.IGNORECASE)

_COMMERCIAL_SUBJECT = re.compile(
    r"\b(viagra|cialis|refinance now|lowest rate|mortgage quote|free quote|"
    r"work from home|make money fast|click here to (buy|order)|"
    r"limited time offer|act now|risk[- ]free|100% (free|guaranteed)|"
    r"enlarge|pharmacy online|cheap meds)\b", re.IGNORECASE)


def _headers(msg) -> dict:
    """
    Raw header strings, defensively.

    compat32 is deliberate. policy.default parses headers lazily and validates
    them on access, so a malformed Message-ID raises from inside .items() —
    after the parse call this module wraps, which is why a 1993 BSMTP message
    took the whole run down. CPython 3.9 has an outright IndexError in
    get_obs_local_part for obsolete address forms, and archival mail is full of
    obsolete address forms; that is what makes it archival.
    #
    Everything here is string matching, so structured header objects buy
    nothing and cost robustness.
    """
    out = {}
    for k, v in msg.raw_items() if hasattr(msg, "raw_items") else msg.items():
        try:
            out[str(k).lower()] = str(v)
        except Exception:
            continue
    return out


def _body_text(msg) -> tuple[str, bool]:
    """Plain text body. Returns (text, had_attachments)."""
    parts, attach = [], False
    if msg.is_multipart():
        for part in msg.walk():
            disp = (part.get_content_disposition() or "")
            if disp == "attachment":
                attach = True
                continue
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                try:
                    parts.append(payload.decode(charset, errors="replace"))
                except (LookupError, UnicodeDecodeError):
                    parts.append(payload.decode("cp1252", errors="replace"))
    else:
        payload = msg.get_payload(decode=True) or b""
        charset = msg.get_content_charset() or "utf-8"
        try:
            parts.append(payload.decode(charset, errors="replace"))
        except (LookupError, UnicodeDecodeError):
            parts.append(payload.decode("cp1252", errors="replace"))
    return "\n".join(p for p in parts if p), attach


def _strip_quoted(text: str) -> str:
    """
    Drop quoted reply chains. The creator's own words are what carry appraisal
    value; forty lines of quoted thread inflate every similarity score with
    text that belongs to a different message.
    """
    out = []
    for line in text.split("\n"):
        s = line.lstrip()
        if s.startswith(">"):
            continue
        if re.match(r"^-+\s*(original message|forwarded message)\s*-+$", s, re.I):
            break
        out.append(line)
    return "\n".join(out).strip()


def _spam_verdict(h: dict) -> bool:
    """
    SpamAssassin already judged this mail, at the time it arrived.

    The Hart corpus carries X-Spam-Status headers written by mail.pglaf.org in
    2010. That is a contemporaneous determination made with the full message,
    the sender's reputation and a trained Bayesian filter — strictly better
    evidence than a subject-line regex applied sixteen years later, and free.
    """
    status = (h.get("x-spam-status") or "").strip().lower()
    if status.startswith("yes"):
        return True
    if (h.get("x-spam-flag") or "").strip().upper().startswith("YES"):
        return True
    return False


def classify(headers: dict, subject: str, body: str) -> tuple[str | None, str]:
    """
    Return (exclusion_reason, evidence). None means the message is not
    identifiable machine traffic, which is not the same as "substantive" — it
    means nothing declared otherwise.
    """
    if _spam_verdict(headers):
        return "unsolicited_commercial", "SpamAssassin verdict at time of receipt"

    for reason, test in _AUTO_HEADERS:
        try:
            if test(headers):
                return reason, "header declaration"
        except Exception:
            pass

    ret = (headers.get("return-path") or "").strip()
    if ret in ("<>", "<>;", ""):
        if ret == "<>":
            return "delivery_failure", "null return-path"

    froms = [a for _, a in getaddresses([headers.get("from") or ""])]
    if froms and _DSN_FROM.match(froms[0].split("@")[0]):
        if _DSN_SUBJECT.search(subject):
            return "delivery_failure", "daemon sender and failure subject"
        if _LIST_ADMIN_SUBJECT.search(subject):
            return "list_administrative", "list manager sender"

    if _DSN_SUBJECT.search(subject):
        return "delivery_failure", "subject"
    if _AUTOREPLY_SUBJECT.search(subject):
        return "auto_reply", "subject"
    if _LIST_ADMIN_SUBJECT.search(subject):
        return "list_administrative", "subject"
    if _COMMERCIAL_SUBJECT.search(subject):
        return "unsolicited_commercial", "subject"
    if _COMMERCIAL_SUBJECT.search(body[:2000]):
        return "unsolicited_commercial", "body"

    # Bulk plus an administrative subject is list machinery. Bulk alone is a
    # discussion message on a list, which the form asks us to keep.
    if (h_bulk := (headers.get("precedence") or "").lower()) in ("bulk", "list"):
        if _LIST_ADMIN_SUBJECT.search(subject):
            return "list_administrative", f"precedence {h_bulk} and admin subject"
    return None, ""


def read(path: str | Path) -> dict:
    """Parse one .eml and return manifest columns plus an exclusion verdict."""
    try:
        raw = Path(path).read_bytes()
        msg = BytesParser(policy=policy.compat32).parsebytes(raw)
    except Exception as exc:
        return {"s03_status": "failed", "s03_error": f"{type(exc).__name__}: {exc}",
                "s03_extractor": f"{MAIL_VERSION}:parse"}

    try:
        h = _headers(msg)
    except Exception as exc:
        return {"s03_status": "failed", "s03_extractor": f"{MAIL_VERSION}:headers",
                "s03_error": f"unreadable headers: {type(exc).__name__}: {exc}"}
    subject = str(h.get("subject") or "")
    try:
        body, attach = _body_text(msg)
    except Exception as exc:
        body, attach = "", False
        h.setdefault("_body_error", f"{type(exc).__name__}: {exc}")
    body = _strip_quoted(body)[:MAX_BODY].encode("utf-8", "replace").decode("utf-8")

    sent = None
    try:
        if h.get("date"):
            sent = parsedate_to_datetime(h["date"])
    except Exception:
        pass

    reason, evidence = classify(h, subject, body)

    # The list a message was posted to, and the folder it was filed in, both
    # carry the creator's own judgement. Keep them as text the scorer can see.
    context = " ".join(x for x in (
        subject, h.get("list-id") or "", h.get("x-mailing-list") or "") if x)
    on_list = bool(h.get("list-id") or h.get("x-mailing-list")
                   or h.get("x-beenthere"))

    return {
        "s03_extractor": f"{MAIL_VERSION}:rfc822",
        "s03_status": "ok",
        "s03_text_len": len(body),
        "s03_text_sample": re.sub(
            r"\s+", " ",
            f"{context}\n{body}"[:1500].encode("utf-8", "replace").decode("utf-8")
        ).strip(),
        "s03_needs_ocr": False,
        "mail_subject": subject,
        "mail_date": sent,
        "mail_has_attachment": attach,
        "mail_exclusion": reason,
        "mail_evidence": evidence,
        # Recorded, never an exclusion on its own: the form asks us to keep the
        # list DISCUSSION and drop only the list machinery.
        "mail_on_list": on_list,
        "_text": body,
    }
