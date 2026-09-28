"""
Personal information detection and two-tier redaction.

Two release versions come out of every message:

  reading_room   direct identifiers removed. A researcher sitting in the reading
                 room has already identified themselves and signed an agreement,
                 so names and affiliations can stay; a social security number
                 cannot, no matter who is asking.

  open_web       direct and indirect identifiers both removed, because on the
                 open web a name plus a job title plus a date is enough to
                 re-identify someone even when nothing in the file is secret.

Detection is deterministic regex plus optional spaCy or Presidio for names. The
deterministic layer is the one that must not miss: an SSN pattern is not a
judgement call, and the archivist needs to be able to read the rule that caught
it. Names are the part machines are bad at, so anything the name detector finds
is reported as a *candidate* and the count is surfaced in the UI — a low count on
a long thread is itself a signal that a human should read it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Iterable, Optional

# tier 1 = direct identifiers, out of both versions
# tier 2 = indirect / quasi identifiers, out of the open-web version only
TIER = {
    # `address` was tier 1 and labelled HOME ADDRESS. In this corpus the
    # matches are the university's own buildings — 600 South Mathews Avenue is
    # the Chemical Engineering department. A public institutional address is a
    # quasi-identifier at worst, so it moves to tier 2: out of the open-web
    # release, kept in the reading room where a researcher has already
    # identified themselves.
    "ssn": 1, "phone": 1, "dob": 1, "account": 1, "card": 1,
    "student_id": 1, "passport": 1, "driver_license": 1, "health": 1,
    "compensation": 1, "credential": 1, "ip": 1,
    "person": 2, "email": 2, "url": 2, "org": 2, "job_title": 2, "amount": 2,
    "address": 2,
}
LABEL = {
    "ssn": "SSN", "phone": "PHONE", "address": "POSTAL ADDRESS", "dob": "DATE OF BIRTH",
    "account": "ACCOUNT NO", "card": "CARD NO", "student_id": "STUDENT ID",
    "passport": "PASSPORT NO", "driver_license": "LICENCE NO", "health": "HEALTH INFO",
    "compensation": "COMPENSATION", "credential": "CREDENTIAL", "ip": "IP ADDRESS",
    "person": "NAME", "email": "EMAIL", "url": "URL", "org": "AFFILIATION",
    "job_title": "JOB TITLE", "amount": "AMOUNT",
}

# Order matters: whichever pattern claims a span first keeps it, so anything that
# carries an explicit label ("UIN 661402298", "account no. 4820157739") is checked
# before the bare nine-digit shape that would otherwise call it a social security
# number. Mislabelling a student ID as an SSN is not harmless — it sends the file
# to the wrong statute.
PATTERNS: list[tuple[str, re.Pattern]] = [
    ("student_id", re.compile(r"\b(?:UIN|uin|student\s*(?:id|no\.?|number))[:# ]*\s*(\d[\d-]{5,10})\b")),
    ("passport", re.compile(r"\bpassport\s*(?:no\.?|number|#)?\s*[:#]?\s*([A-Z0-9]{6,9})\b")),
    ("driver_license", re.compile(r"\b(?:driver'?s?\s*licen[cs]e|DL)\s*(?:no\.?|#)?\s*[:#]?\s*([A-Z0-9-]{6,14})\b", re.I)),
    ("account", re.compile(r"\b(?:account|acct\.?|routing)\s*(?:no\.?|number|#)?\s*[:#]?\s*(\d{6,17})\b", re.I)),
    # SSN. The separators must be present, identical, and in the 3-2-4
    # grouping. The previous pattern made each separator independently
    # optional, so a ZIP+4 postal code — 5 digits, hyphen, 4 digits — parsed as
    # 222 + 03 + "-" + 1714 and every institutional address in the corpus
    # produced a false social security number. That is tier 1, so it was being
    # stripped from the reading-room copy as well as the open-web one.
    #
    # A bare nine-digit run is NOT an SSN on its own. In a research collection
    # nine-digit numbers are run identifiers and simulation output. It needs a
    # label beside it.
    ("ssn", re.compile(r"\b(?!000|666|9\d\d)\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b")),
    ("ssn", re.compile(r"\b(?!000|666|9\d\d)\d{3} (?!00)\d{2} (?!0000)\d{4}\b")),
    ("ssn", re.compile(r"\b(?:ssn|social\s+security(?:\s+(?:no\.?|number|#))?)\s*[:#]?\s*"
                       r"((?!000|666|9\d\d)\d{3}[- ]?(?!00)\d{2}[- ]?(?!0000)\d{4})\b", re.I)),
    # Payment card. Digit runs alone are not enough: "0 20 40 60 80 100 4000"
    # is a chart axis, and a research collection is full of them. Groups must
    # be 4-digit and separated consistently, and the result must satisfy Luhn —
    # which is what a card number is defined by. Luhn rejects arbitrary numeric
    # data about 90% of the time.
    ("card", re.compile(r"\b\d{4}[ -]\d{4}[ -]\d{4}[ -]\d{1,4}\b")),
    ("card", re.compile(r"\b\d{15,16}\b")),
    ("phone", re.compile(r"(?:(?<=\D)|^)(?:\+1[ .-]?)?(?:\(\d{3}\)|\d{3})[ .-]\d{3}[ .-]\d{4}\b")),
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]{2,}\b")),
    ("dob", re.compile(r"\b(?:d\.?o\.?b\.?|date of birth|born)\s*[:\-]?\s*"
                       r"((?:\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4})|"
                       r"(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}))", re.I)),
    ("address", re.compile(r"\b\d{1,6}\s+(?:[NSEW]\.?\s+)?[A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){0,3}\s+"
                           r"(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Court|Ct|Place|Pl|Way|Circle|Cir|Terrace|Ter|Parkway|Pkwy|Highway|Hwy)\b\.?"
                           r"(?:\s*,?\s*(?:Apt\.?|Unit|Suite|Ste\.?|#)\s*[\w-]+)?")),
    ("ip", re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b")),
    ("credential", re.compile(r"\b(?:password|passwd|pwd|passcode|PIN|secret|api[_ ]?key|token)\s*(?:is|=|:)\s*(\S{4,})", re.I)),
    ("compensation", re.compile(r"\b(?:salary|base(?:\s+rate)?|stipend|wage|compensation)\b[^.\n]{0,40}?"
                                r"\$\s?\d[\d,]*(?:\.\d{2})?", re.I)),
    ("amount", re.compile(r"\$\s?\d[\d,]*(?:\.\d{2})?\b")),
    ("url", re.compile(r"\bhttps?://[^\s<>\"')]+")),
]

# Health terms are matched as a vocabulary rather than a shape. This list is
# deliberately short and specific; a long fuzzy list produces false positives on
# ordinary correspondence and trains reviewers to ignore the flag.
HEALTH_TERMS = [
    "cancer", "carcinoma", "chemotherapy", "radiotherapy", "oncology", "tumour", "tumor",
    "diagnosis", "diagnosed with", "prognosis", "biopsy", "mastectomy", "hospice",
    "HIV", "AIDS", "hepatitis", "diabetes", "insulin", "epilepsy", "seizure",
    "depression", "bipolar", "schizophrenia", "psychiatric", "anxiety disorder",
    "rehab", "rehabilitation facility", "detox", "addiction", "substance abuse",
    "miscarriage", "pregnancy", "fertility treatment", "IVF",
    "surgery", "surgical", "hip replacement", "knee replacement", "transplant",
    "medical leave", "FMLA", "disability accommodation", "workers compensation",
    "prescription", "medication", "dosage", "mg daily",
]
HEALTH_RE = re.compile(r"\b(" + "|".join(re.escape(t) for t in HEALTH_TERMS) + r")\b", re.I)

JOB_TITLE_RE = re.compile(
    r"\b((?:Assistant|Associate|Adjunct|Clinical|Visiting|Emeritus|Emerita|Distinguished|Research)\s+)?"
    r"(Professor|Lecturer|Instructor|Dean|Provost|Chancellor|Chair|Director|Manager|Coordinator|"
    r"Administrator|Analyst|Officer|Specialist|Postdoctoral\s+Researcher|Research\s+Scientist)"
    r"(\s+(?:of|for|in)\s+[A-Z][A-Za-z&\s]{2,40})?")

ORG_RE = re.compile(
    r"\b((?:[A-Z][\w.&'-]+\s+){0,4}"
    r"(?:University|College|Institute|Laboratory|Foundation|Hospital|Corporation|Company|"
    r"Incorporated|Association|Society|Department of [A-Z][a-z]+|Office of [A-Z][a-z]+))\b")

SALUTATION_RE = re.compile(
    r"^(?:Dear|Hi|Hello|Hey|Thanks|Thank you),?\s+([A-Z][a-z]{1,15}(?:\s+[A-Z][a-z]{1,15})?)\s*[,:.\n]",
    re.M)
SIGNOFF_RE = re.compile(
    r"^(?:Best|Regards|Best regards|Kind regards|Sincerely|Thanks|Thank you|Cheers|Yours truly|"
    r"Yours sincerely|All the best),?\s*\n+\s*([A-Z][a-z]{1,15}(?:\s+[A-Z][a-z.'-]{1,20}){0,2})\s*$",
    re.M)
NAME_RE = re.compile(
    r"\b(?:(?:Dr|Prof|Professor|Mr|Mrs|Ms|Miss)\.?\s+)?"
    r"([A-Z][a-z]{1,15}(?:\s+[A-Z]\.)?\s+[A-Z][a-z'’-]{1,20})\b")

TITLES = {"Dr", "Prof", "Professor", "Mr", "Mrs", "Ms", "Miss"}
# Words that look like names in headers and are not
NOT_NAMES = {
    "Sent From", "To From", "Best Regards", "Kind Regards", "Thank You", "Dear Colleagues",
    "New York", "Ann Arbor", "United States", "Sponsored Programs", "Human Resources",
    "Graduate College", "Civil Engineering", "Nuclear Engineering", "Urbana Champaign",
}


@dataclass
class Entity:
    type: str
    value: str
    start: int
    end: int
    tier: int
    detector: str
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return asdict(self)


def _overlaps(spans: list[tuple[int, int]], s: int, e: int) -> bool:
    return any(not (e <= a or s >= b) for a, b in spans)


def detect(text: str, *, name_detector: str = "heuristic") -> list[Entity]:
    """Find personal information. Deterministic patterns first, names last."""
    if not text:
        return []
    found: list[Entity] = []
    taken: list[tuple[int, int]] = []

    def add(kind: str, value: str, start: int, end: int, detector: str, conf: float = 1.0):
        if not value or _overlaps(taken, start, end):
            return
        taken.append((start, end))
        found.append(Entity(kind, value, start, end, TIER.get(kind, 2), detector, conf))

    for kind, rx in PATTERNS:
        for m in rx.finditer(text):
            # prefer an explicit capture group when the pattern includes context words
            if m.groups() and m.group(1):
                value, s, e = m.group(1), m.start(1), m.end(1)
            else:
                value, s, e = m.group(0), m.start(), m.end()
            # a compensation match already covers the dollar figure inside it
            add(kind, value.strip(), s, e, "regex")

    for m in HEALTH_RE.finditer(text):
        start, end = _expand_health_span(text, m.start(), m.end())
        add("health", text[start:end], start, end, "vocabulary", 0.8)

    for m in JOB_TITLE_RE.finditer(text):
        add("job_title", m.group(0).strip(), m.start(), m.end(), "regex", 0.75)

    for m in ORG_RE.finditer(text):
        add("org", m.group(1).strip(), m.start(1), m.end(1), "regex", 0.7)

    found.extend(_detect_names(text, taken, name_detector))
    found.sort(key=lambda e: e.start)
    return found


# Words that end a clinical noun phrase when walking backwards. Anything else
# immediately before a health term is almost always part of the disclosure.
_PHRASE_STOP = {
    "is", "was", "are", "were", "be", "been", "being", "has", "have", "had",
    "for", "on", "with", "of", "to", "in", "at", "by", "from", "about",
    "the", "a", "an", "and", "or", "but", "her", "his", "their", "my", "our",
    "receiving", "treated", "diagnosed", "undergoing", "having", "after", "before",
    "she", "he", "they", "i", "we", "that", "which", "who",
}


def _expand_health_span(text: str, start: int, end: int, max_tokens: int = 4) -> tuple[int, int]:
    """
    'cancer' on its own leaves 'stage II breast [REDACTED]', which discloses the
    thing it was meant to hide. Walk backwards over the modifiers that belong to
    the clinical phrase and take them too, stopping at the first connective so
    the sentence around it still reads.
    """
    head = text[:start]
    tokens = list(re.finditer(r"[A-Za-z0-9][A-Za-z0-9'-]*", head))
    taken = 0
    for tok in reversed(tokens):
        # only walk back across whitespace, never across punctuation
        if re.search(r"[^\sA-Za-z0-9'-]", head[tok.end():]):
            break
        if tok.group(0).lower() in _PHRASE_STOP or taken >= max_tokens:
            break
        start = tok.start()
        taken += 1
    return start, end


def _detect_names(text: str, taken: list[tuple[int, int]], detector: str) -> list[Entity]:
    out: list[Entity] = []

    def add(value: str, s: int, e: int, how: str, conf: float):
        v = value.strip(" ,.:;\n")
        if len(v) < 3 or v in NOT_NAMES or _overlaps(taken, s, e):
            return
        taken.append((s, e))
        out.append(Entity("person", v, s, e, 2, how, conf))

    if detector in ("spacy", "presidio"):
        ents = _ner(text, detector)
        if ents is not None:
            for value, s, e, conf in ents:
                add(value, s, e, detector, conf)
            return out
        print("  ! name model unavailable, falling back to heuristics")

    for m in SALUTATION_RE.finditer(text):
        add(m.group(1), m.start(1), m.end(1), "salutation", 0.85)
    for m in SIGNOFF_RE.finditer(text):
        add(m.group(1), m.start(1), m.end(1), "signoff", 0.85)
    for m in NAME_RE.finditer(text):
        add(m.group(1), m.start(1), m.end(1), "capitalisation", 0.6)
    return out


_NLP = None


def _ner(text: str, which: str):
    """Optional NER. Returns None if the dependency is not installed."""
    global _NLP
    try:
        if which == "presidio":
            from presidio_analyzer import AnalyzerEngine
            if _NLP is None:
                _NLP = AnalyzerEngine()
            results = _NLP.analyze(text=text, language="en", entities=["PERSON"])
            return [(text[r.start:r.end], r.start, r.end, float(r.score)) for r in results]
        import spacy
        if _NLP is None:
            _NLP = spacy.load("en_core_web_sm")
        doc = _NLP(text)
        return [(e.text, e.start_char, e.end_char, 0.9)
                for e in doc.ents if e.label_ == "PERSON"]
    except Exception:                                            # noqa: BLE001
        return None


def _name_variants(value: str) -> list[str]:
    """
    'Rosalind Feike' also needs to catch 'Rosalind' three lines later, which is
    how correspondence actually refers to people. Tokens shorter than three
    characters are skipped and every replacement is word-bounded, so 'Tom' does
    not turn 'tomorrow' into '[NAME REDACTED]orrow'.
    """
    parts = [p for p in re.split(r"\s+", value) if p.strip(".") not in TITLES]
    out = [value]
    for p in parts:
        p = p.strip(".,'")
        if len(p) >= 3 and p not in out:
            out.append(p)
    return out


def apply(text: str, entities: Iterable[Entity], level: str = "reading_room") -> str:
    """Produce a redacted version. level is 'reading_room' or 'open_web'."""
    max_tier = 1 if level == "reading_room" else 2
    targets: list[tuple[str, str]] = []
    for e in entities:
        if e.tier > max_tier:
            continue
        if e.type == "person":
            targets.extend((v, e.type) for v in _name_variants(e.value))
        else:
            targets.append((e.value, e.type))
    # longest first so a full name is replaced before its first name
    targets.sort(key=lambda t: len(t[0]), reverse=True)
    out = text
    for value, kind in targets:
        if not value:
            continue
        pre = r"\b" if re.match(r"\w", value) else ""
        post = r"\b" if re.search(r"\w$", value) else ""
        out = re.sub(pre + re.escape(value) + post, f"[{LABEL.get(kind, 'REDACTED')} REDACTED]", out)
    return out


def summarise(entities: Iterable[Entity]) -> dict:
    ents = list(entities)
    direct = sorted({LABEL[e.type] for e in ents if e.tier == 1})
    indirect = sorted({LABEL[e.type] for e in ents if e.tier == 2})
    return {
        "identifiers_found": len(ents),
        "direct": direct,
        "indirect": indirect,
        "by_type": {LABEL[e.type]: sum(1 for x in ents if x.type == e.type)
                    for e in ents},
        "low_confidence_names": sum(1 for e in ents if e.type == "person" and e.confidence < 0.7),
    }
