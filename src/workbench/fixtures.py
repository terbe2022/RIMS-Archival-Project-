"""
fixtures.py — a corpus that behaves like the real one and contains none of it.

Why this exists
---------------
Colab is Google's infrastructure. The material this pipeline processes includes
personal email, unreviewed identifiers, medical and tax records, and
FERPA-covered student records, and the whole architecture exists because that
content stays on university hardware. None of it can go into a hosted notebook.

But model evaluation does not need real content. It needs content that FAILS
the same way. Every generator here is built from a defect actually observed in
the corpus, and the docstring says which. These shapes make the synthetic corpus
useful for testing known failure modes and screening candidate models. Passing
these cases does not guarantee performance on the real corpus; that requires a
separate approved University-side evaluation.

What is reproduced
------------------
Mangled encodings, extensions destroyed by migration, mail headers from a 1993
campus BSMTP system, extractions that return a quoted reply chain and nothing
else, OCR mush from a scan with no text layer, documents whose first page is
blank, list traffic that looks like correspondence, and near-duplicate files
that differ by a byte.

The names, places and subjects are invented. The shapes are not.
"""
from __future__ import annotations

import hashlib
import random
import re

SEED = 20260928

# Invented people and organisations. Deliberately not the real ones.
PEOPLE = ["R. Aldington", "M. Calloway", "P. Okonkwo", "S.Варшава",
          "J. Fitzwilliam-Hayes", "T. Ngo", "A. Bergström", "D. Mwangi"]
ORGS = ["Riverbend Institute", "Northfield Consolidated", "Delta Works Ltd",
        "The Havering Trust", "Calder Polytechnic"]
SUBJECTS = ["sediment transport in braided channels", "the 1987 funding review",
            "copyright terms for orphan works", "kiln temperature calibration",
            "the summer field season roster", "annular flow in vertical pipes"]


def _rng(tag: str) -> random.Random:
    """Deterministic per generator, so a run is reproducible."""
    return random.Random(SEED + int(hashlib.sha1(tag.encode()).hexdigest()[:8], 16))


# ---------------------------------------------------------------- documents --
def referee_report(i: int) -> dict:
    """
    A referee report. In the real corpus these are the highest-value documents
    AND the most sensitive — they name living people and judge their work — so
    a model's handling of them tests value and sensitivity at once.
    """
    r = _rng(f"ref{i}")
    p, s = r.choice(PEOPLE), r.choice(SUBJECTS)
    return {
        "filename": f"referee_report_{i:03d}.doc",
        "lane": "document",
        "text": (
            f"REFEREE REPORT\n\nManuscript: A revised model of {s}.\n"
            f"Reviewer: confidential\n\nRecommendation: major revision.\n\n"
            f"The authors' treatment in Section 3 does not justify the closure "
            f"assumption. I raised this in my earlier report and it has not been "
            f"addressed. The comparison with {r.choice(ORGS)}'s 1994 data is "
            f"selective; the disagreeing runs are omitted without comment.\n\n"
            f"Minor: Figure 4 is unreadable at print size. The reference to "
            f"{p} (1991) is miscited."),
        "expect": {"genre": "report", "sensitive": True,
                   "why": "names a living person and judges their work"},
    }


def draft_with_revisions(i: int) -> dict:
    """A draft carrying tracked changes — the form asks for these explicitly."""
    r = _rng(f"draft{i}")
    return {
        "filename": f"chapter_{i}_DRAFT_v3_MCcomments.doc",
        "lane": "document",
        "text": (
            f"Chapter {i}: {r.choice(SUBJECTS).title()}\n\n"
            f"[deleted: The results are conclusive.] The results are suggestive "
            f"but not conclusive. {r.choice(PEOPLE)} notes in the margin: "
            f"'this overstates it — see the 1989 series'.\n\n"
            f"We therefore propose a revised treatment. [inserted: pending "
            f"confirmation from the second site]"),
        "expect": {"genre": "draft", "sensitive": False,
                   "why": "a draft with revisions is process evidence"},
    }


def published_paper_copy(i: int) -> dict:
    """A reference copy of someone else's paper. The form excludes these."""
    r = _rng(f"pub{i}")
    return {
        "filename": f"{r.choice(PEOPLE).split()[-1]}_1994_reprint.pdf",
        "lane": "document",
        "text": (
            f"Journal of Applied Mechanics, Vol 61, 1994, pp. 213-229\n\n"
            f"{r.choice(SUBJECTS).title()}\n\n{r.choice(PEOPLE)}, "
            f"{r.choice(ORGS)}\n\nABSTRACT We present measurements of ... "
            f"Received 3 March 1993; accepted 18 November 1993."),
        "expect": {"genre": "publication", "sensitive": False,
                   "why": "a reference copy with no annotation"},
    }


# -------------------------------------------------------------------- email --
def campus_mail_1993(i: int) -> dict:
    """
    1993 campus BSMTP mail. In the real corpus this format CRASHED the parser:
    malformed Message-ID headers that the default email policy parses lazily
    and then throws on. The shape is reproduced here.
    """
    r = _rng(f"bsmtp{i}")
    return {
        "filename": f"1993-{r.randint(1,12):02d}-{r.randint(1,28):02d}_msg{i}.eml",
        "lane": "email",
        "text": (
            f"Received: from VMD.CSO.EXAMPLE.EDU by VMD (Mailer R2.07) with "
            f"BSMTP id {r.randint(1000,9999)}; {r.randint(1,28)} Mar 93\n"
            f"Message-ID: <{r.randint(10**6,10**7)}@VMD>\n"
            f"From: {r.choice(PEOPLE).split()[-1].upper()}@VMD.CSO.EXAMPLE.EDU\n"
            f"Subject: Re: {r.choice(SUBJECTS)}\n\n"
            f"Your note arrived garbled at this end. The tape is in the mail. "
            f"I have asked {r.choice(PEOPLE)} to look at the second series."),
        "expect": {"genre": "correspondence", "sensitive": False,
                   "why": "1993 campus mail; retained on age and rarity"},
    }


def listserv_traffic(i: int) -> dict:
    """
    List traffic that LOOKS like correspondence. Distinguishing it is the
    email lane's actual job, and a model that calls this a letter is telling
    you it read the body and ignored the headers.
    """
    r = _rng(f"list{i}")
    return {
        "filename": f"2004-{r.randint(1,12):02d}-{r.randint(1,28):02d}_re-thread_{i}.eml",
        "lane": "email",
        "text": (
            f"List-Id: <discuss.example.org>\n"
            f"List-Unsubscribe: <mailto:discuss-off@example.org>\n"
            f"Subject: [discuss] Re: {r.choice(SUBJECTS)}\n\n"
            f"On Mon, 4 Oct 2004, someone wrote:\n"
            f"> I think the current guidelines are too strict.\n\n"
            f"Agreed, but the alternative has its own problems. See the thread "
            f"from March.\n\n--\nTo unsubscribe send SIGNOFF to the list server."),
        "expect": {"genre": "list traffic", "sensitive": False,
                   "why": "list discussion; a sample is kept, not the bulk"},
    }


def quoted_chain_only(i: int) -> dict:
    """
    An extraction that returned ONLY a quoted reply chain. Common, and a model
    MUST decline it: there is no new content to describe, and a description of
    the quoted material misattributes it to this message.
    """
    return {
        "filename": f"2006-03-{i:02d}_re-re-re_fwd.eml",
        "lane": "email",
        "text": ("-----Original Message-----\nFrom: \nSent: \nTo: \nSubject: \n\n"
                 "> > > see below\n> > see below\n> see below\n"),
        "expect": {"genre": "unknown", "sensitive": False, "abstain": True,
                   "why": "nothing but a quoted chain; no new content"},
    }


# ------------------------------------------------------------ broken inputs --
def mangled_encoding(i: int) -> dict:
    """
    Latin-1 read as UTF-8. Real filenames in the corpus carried non-UTF-8 bytes
    from 1990s systems and crashed the pipeline with UnicodeEncodeError.
    """
    r = _rng(f"mangle{i}")
    clean = f"Notes on {r.choice(SUBJECTS)} by {r.choice(PEOPLE)}"
    broken = clean.replace("o", "Ã´").replace("e", "Ã©").replace("'", "Â\x92")
    return {
        "filename": f"notes_{i}.d1",          # an extension that is not a format
        "lane": "document",
        "text": broken + "\n\nÂ\x95 first point\nÂ\x95 second point",
        "expect": {"genre": "notes", "sensitive": False,
                   "why": "readable despite the encoding damage"},
    }


def ocr_mush(i: int) -> dict:
    """A scan with no text layer, extracted anyway. Must be declined."""
    r = _rng(f"mush{i}")
    src = f"University of Somewhere Office of the Dean {r.choice(SUBJECTS)}"
    return {
        "filename": f"scan_{i:04d}.pdf",
        "lane": "document",
        "text": re.sub(r"[aeiou]", "", src) + " rn1 |-| cl3an 0ffic3 nf th3",
        "expect": {"genre": "unknown", "sensitive": False, "abstain": True,
                   "why": "OCR mush; not text"},
    }


def blank_extraction(i: int) -> dict:
    """Nothing came out. Must be declined."""
    return {"filename": f"image_{i:04d}.jpg", "lane": "image", "text": "",
            "expect": {"genre": "unknown", "sensitive": False, "abstain": True,
                       "why": "no text extracted at all"}}


def truncated(i: int) -> dict:
    """Cut mid-word. Must be declined or flagged as partial."""
    r = _rng(f"trunc{i}")
    full = f"Minutes of the meeting held on 14 June concerning {r.choice(SUBJECTS)}"
    return {"filename": f"minutes_{i}.doc", "lane": "document",
            "text": full[:38], "expect": {
                "genre": "minutes", "sensitive": False, "abstain": True,
                "why": "truncated mid-sentence; not enough to describe"}}


# ----------------------------------------------------------------- personal --
def personal_finance(i: int) -> dict:
    """
    Personal financial material. The form says route it to a person. This also
    tests the SSN/ZIP+4 confusion that was a real tier-1 defect: the ZIP+4 here
    must not be read as a social security number.
    """
    r = _rng(f"fin{i}")
    return {
        "filename": f"statement_{i}.pdf",
        "lane": "document",
        "text": (f"Account summary for {r.choice(PEOPLE)}\n"
                 f"14 Elmfield Road, Somewhere, XX 61801-3792\n"
                 f"Telephone (217) 555-0148\n"
                 f"Balance carried forward ... 1,204.55"),
        "expect": {"genre": "administrative", "sensitive": True,
                   "why": "personal financial material; the 61801-3792 is a "
                          "postal code and must NOT be read as an SSN"},
    }


def near_duplicate(i: int) -> list:
    """Two files differing by one byte — the dedup path's actual test."""
    base = referee_report(900 + i)
    other = dict(base)
    other["filename"] = base["filename"].replace(".doc", " (conflicted copy).doc")
    other["text"] = base["text"] + " "
    other["expect"] = {**base["expect"], "near_duplicate_of": base["filename"]}
    return [base, other]


GENERATORS = [
    (referee_report, 6), (draft_with_revisions, 5), (published_paper_copy, 4),
    (campus_mail_1993, 6), (listserv_traffic, 6), (quoted_chain_only, 4),
    (mangled_encoding, 4), (ocr_mush, 4), (blank_extraction, 4), (truncated, 4),
    (personal_finance, 3),
]


def build_corpus(scale: int = 1) -> list[dict]:
    """
    The whole synthetic corpus. Roughly 50 files at scale=1.

    Deliberately weighted toward broken input — about a third of it cannot
    honestly be described. The real corpus is worse than that, and a test set
    of only clean documents measures the wrong thing.
    """
    out = []
    for fn, n in GENERATORS:
        for i in range(n * scale):
            out.append(fn(i))
    for i in range(2 * scale):
        out.extend(near_duplicate(i))
    for n, row in enumerate(out):
        row["file_uid"] = hashlib.sha1(
            (row["filename"] + str(n)).encode()).hexdigest()[:12]
        row["s03_text_sample"] = row["text"]
        row["s03_text_len"] = len(row["text"])
        row["s03_lane"] = row["lane"]
        row["layer"] = 2
    return out


def summary(corpus: list[dict]) -> str:
    from collections import Counter
    lanes = Counter(r["lane"] for r in corpus)
    abstain = sum(1 for r in corpus if r["expect"].get("abstain"))
    sensitive = sum(1 for r in corpus if r["expect"].get("sensitive"))
    return (f"{len(corpus)} files: {dict(lanes)}\n"
            f"  {abstain} cannot honestly be described (a model must decline)\n"
            f"  {sensitive} should route to a person\n"
            f"  every 'expect' block says WHY, so a disagreement is arguable "
            f"rather than just wrong")
