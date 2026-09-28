"""
stage05.py — descriptive metadata, and the flag an archivist acts on.

Two jobs that belong together because they answer the same question from
different ends: what is this item, and does it warrant attention.

    dc_*            Dublin Core. Half derived, half generated.
    s05_decision    priority | retained
    s05_rationale   why, in words, quoting the form clause that decided it

Derived versus generated
------------------------
`dc_format`, `dc_identifier`, `dc_date`, `dc_language` and `dc_source` come from
facts the pipeline established: a PRONOM identification, a file hash, a mail
Date header, an accession record. Those are not opinions and are not recorded as
generated.

`dc_title`, `dc_subject` and `dc_description` are inferred. Every one is listed
in `s05_generated_fields` and stamped with `s05_generated_by`,
`s05_generated_at` and `s05_human_reviewed = False`. Answer 5.3 was a flat yes
to marking machine-generated description, and an archivist reading a finding aid
in ten years needs to know what wrote a field, when, and whether anyone checked.

Dates
-----
`dc_date` never falls back to file mtime for this corpus. The Hanratty transfer
overwrote every original timestamp with the date of the copy, so mtime records
when someone ran a copy command in 2017 and asserting it as the date of creation
would be worse than leaving the field empty. Dates come from inside the content
— a mail header, a date in the text — or not at all.

The flag
--------
`priority` means a person should look at this sooner. It is set by:

  - a sensitivity outcome, always, whatever the score
  - a high relevance band against the accession's own retention criteria
  - a rule match that the ruleset marks as priority-worthy

It is never set by a model's opinion alone, and `retained` is not a rejection —
it means "kept, in the ordinary queue".
"""
from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone

from .schema import manifest as M

STAGE_VERSION = "s05-0.1.0"

GENERATED = ("dc_title", "dc_subject", "dc_description")

_STOP = set("""the a an and or of in on at to for from by with without into over under is are
was were be been being it its as such not no nor any all some each which who whom whose what
when where why how there here we our us they them their this that these those will would can
could may might must shall should do does did have has had having more most other others same
own very just also about against between during before after above below only too if then than
you your i me my he she his her but so because while dear regards sincerely thanks thank please
""".split())

_DATE_IN_TEXT = re.compile(
    r"\b(?:(?:19|20)\d{2})[-/](?:0?[1-9]|1[0-2])[-/](?:0?[1-9]|[12]\d|3[01])\b"
    r"|\b(?:0?[1-9]|[12]\d|3[01])\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(?:19|20)\d{2}\b"
    r"|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(?:0?[1-9]|[12]\d|3[01]),?\s+(?:19|20)\d{2}\b")

_LANE_TYPE = {
    "document": "Text", "email": "Text", "tabular": "Dataset",
    "image": "Image", "av": "MovingImage", "code": "Software",
    "archive": "Collection", "scientific": "Dataset",
}


def _title_from_text(text: str, filename: str) -> tuple[str | None, bool]:
    """
    A title, and whether it was inferred.

    Prefers the first substantial line of the document, which for
    correspondence and reports is usually a subject line or a heading. Falls
    back to the filename with its extension and separators cleaned up — which
    is derived rather than generated, and is marked as such.
    """
    for line in (text or "").split("\n"):
        s = line.strip()
        if 12 <= len(s) <= 120 and not s.endswith((",", ";")) and " " in s:
            return s.rstrip(". "), True
    stem = re.sub(r"\.[A-Za-z0-9]{1,5}$", "", filename or "")
    stem = re.sub(r"[_\-]+", " ", stem).strip()
    stem = re.sub(r"\s{2,}", " ", stem)
    return (stem or None), False


def _subjects(text: str, k: int = 6) -> list[str]:
    """Frequent content words. Crude, deterministic, and honest about it."""
    words = re.findall(r"[A-Za-z][A-Za-z\-']{3,}", (text or "").lower())
    counts = Counter(w for w in words if w not in _STOP)
    return [w for w, n in counts.most_common(k) if n > 1]


def _date_from_content(row: dict, text: str) -> str | None:
    sent = row.get("mail_date")
    if sent:
        try:
            return sent.date().isoformat()
        except AttributeError:
            return str(sent)[:10]
    m = _DATE_IN_TEXT.search(text or "")
    if not m:
        return None
    # Dublin Core expects ISO 8601. A date lifted from prose reads "12 March
    # 2003"; leaving it in that form means dc_date cannot be sorted or ranged,
    # which is most of what a date field is for.
    raw = m.group(0)
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d %B %Y", "%d %b %Y",
                "%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y"):
        try:
            return datetime.strptime(raw.replace(".", ""), fmt).date().isoformat()
        except ValueError:
            continue
    return raw


def describe(row: dict, accession: dict) -> dict:
    """Dublin Core for one item."""
    text = row.get("_text") or row.get("s03_text_sample") or ""
    generated: list[str] = []
    out: dict = {}

    # ---- derived: facts the pipeline established -------------------------
    out["dc_format"] = row.get("s01_format_name") or row.get("extension") or None
    out["dc_identifier"] = row.get("file_uid")
    out["dc_source"] = accession.get("source_label") or accession.get("accession_uid")
    out["dc_type"] = _LANE_TYPE.get(row.get("s03_lane") or "")
    if text:
        out["dc_language"] = "en"
    out["dc_rights"] = ("Access determined by the accession's terms; see the "
                        "supervising archivist.")
    date = _date_from_content(row, text)
    if date:
        out["dc_date"] = date

    # ---- generated: inferred, and marked ---------------------------------
    if row.get("dc_title"):
        # Already set by the vision lane. Do not overwrite a model's title with
        # a filename.
        generated.append("dc_title")
    else:
        title, inferred = _title_from_text(text, row.get("filename") or "")
        if title:
            out["dc_title"] = title
            if inferred:
                generated.append("dc_title")

    if row.get("s04_description"):
        out["dc_description"] = row["s04_description"]
        generated.append("dc_description")
    elif text:
        snippet = re.sub(r"\s+", " ", text[:300]).strip()
        if snippet:
            out["dc_description"] = snippet + ("…" if len(text) > 300 else "")
            generated.append("dc_description")

    subs = _subjects(text)
    if subs:
        out["dc_subject"] = "; ".join(subs)
        generated.append("dc_subject")

    creator = accession.get("profile_person")
    if creator and not str(creator).upper().startswith(("UNRESOLVED", "NONE")):
        out["dc_creator"] = str(creator).split(".")[0][:120]

    if generated:
        out["s05_generated_fields"] = generated
        out["s05_generated_by"] = f"{STAGE_VERSION}"
        out["s05_generated_at"] = datetime.now(timezone.utc)
        out["s05_human_reviewed"] = False
    return out


def flag(row: dict) -> dict:
    """
    The decision an archivist acts on: priority, or retained.

    Precedence, not arithmetic. Sensitivity outranks score, score outranks
    nothing at all. `retained` is the ordinary queue and not a rejection —
    disposal is only ever `discard_candidate`, set by the rules.
    """
    decision = "retained"
    why = None

    if row.get("s02_decision") == "restricted_review":
        decision = "priority"
        why = ("routed to a supervising archivist: "
               + (row.get("s02_rule_matched") or "a sensitivity outcome")
               + ". Sensitivity takes precedence over ranking.")
    elif row.get("s04_sensitivity_flags"):
        decision = "priority"
        why = ("sensitivity flagged: "
               + ", ".join(row["s04_sensitivity_flags"]))
    elif row.get("s02_band") == "high":
        decision = "priority"
        why = row.get("s02_rationale") or "ranked high against the accession's criteria"
    elif row.get("retained_by_association"):
        why = ("kept because of its neighbours rather than on its own merits. "
               "Not understood; not prioritised.")
    else:
        why = row.get("s02_rationale") or "no criterion in the form matched"

    return {
        "s05_decision": decision,
        "s05_score": row.get("s02_score"),
        "s05_band": row.get("s02_band"),
        "s05_rationale": why,
        "s05_version": STAGE_VERSION,
        "s05_status": "ok",
    }


def run(rows: list[dict], accession: dict) -> dict:
    counts = Counter()
    gen_fields = Counter()
    dated = 0
    for r in rows:
        if r.get("layer") == 0:
            r["s05_status"] = "skipped"
            continue
        meta = describe(r, accession)
        r.update(meta)
        r.update(flag(r))
        r["layer"] = M.compute_layer(r)
        counts[r["s05_decision"]] += 1
        for f in meta.get("s05_generated_fields", []):
            gen_fields[f] += 1
        if meta.get("dc_date"):
            dated += 1
    return {
        "stage_version": STAGE_VERSION,
        "decisions": dict(counts),
        "generated_fields": dict(gen_fields),
        "with_a_date": dated,
        "note": ("dc_date is taken from content only. File mtime records when "
                 "the material was copied, not when it was made."),
    }
