"""
stage03.py — route, extract, score. Still no GPU.

This is the stage that turns a manifest of file properties into something an
archivist can read: what each file is, what it says, how it ranks against this
collection's own stated priorities, and why.

Order matters and is not arbitrary:

    route    -> which lane, and is that lane's handler fit to run
    extract  -> text, for the lanes with a working CPU extractor
    score    -> rank against the intake form, using that text

Scoring runs last because it is only as good as the evidence it has. Score
before extraction and almost everything in a folder comes back "retained by
association" — kept because of its neighbours rather than understood — since
the only evidence available is the path. That flag is meant to be the
exception. Extraction is what makes it one.

Nothing here writes s02_decision. Disposition belongs to the rules in stage
02a; this stage decides order and description.
"""
from __future__ import annotations

import time
from collections import defaultdict

from . import extract, lanes, relevance

STAGE_VERSION = "s03-0.1.0"

# Lanes with a working CPU extractor today. Email, image and av are routed and
# counted but not extracted: email needs POC 1's defect 7 fixed, image needs a
# vision model and the GPU, av has no handler at all.
# Email joined this once RFC822 parsing landed: headers and body need no GPU,
# and reading them is what lets the appraisal rules see a message instead of a
# filename.
EXTRACTABLE = {"document", "tabular", "email"}


def run(rows: list[dict], accession: dict, form: dict,
        use_embeddings: bool = False, extract_text: bool = True) -> dict:
    """Route, extract and score one accession's rows in place."""
    t0 = time.perf_counter()

    plan = lanes.plan(rows, accession)

    extracted = defaultdict(int)
    chars = 0
    if extract_text:
        for r in rows:
            if r.get("s03_lane") not in EXTRACTABLE:
                r["s03_status"] = "skipped"
                r["s03_error"] = (
                    f"lane {r.get('s03_lane')!r} has no CPU extractor; "
                    f"routed and counted, not read")
                r["s03_version"] = STAGE_VERSION
                continue
            if r.get("duplicate_of") or r.get("s02_structural_exclusion"):
                r["s03_status"] = "skipped"
                r["s03_error"] = "excluded at stage 02a; not extracted"
                r["s03_version"] = STAGE_VERSION
                continue
            result = extract.extract(r)
            text = result.pop("_text", "")
            # Mail that declares itself machine traffic becomes a Layer 0
            # exclusion, recorded with the header evidence that identified it.
            # Nothing is deleted; a person can see and reverse every one.
            if result.get("mail_exclusion"):
                r["s02_structural_exclusion"] = result["mail_exclusion"]
                r["s02_exclusion_evidence"] = result.get("mail_evidence")
            r.update(result)
            extracted[result["s03_status"]] += 1
            chars += len(text)

    scoring = relevance.run(rows, form, use_embeddings=use_embeddings)

    assoc = sum(1 for r in rows if r.get("retained_by_association"))
    understood = sum(1 for r in rows
                     if r.get("s03_text_len") and not r.get("retained_by_association"))

    return {
        "stage_version": STAGE_VERSION,
        "seconds": round(time.perf_counter() - t0, 2),
        "routing": plan,
        "extraction": {
            "attempted": sum(extracted.values()),
            "by_status": dict(extracted),
            "characters": chars,
        },
        "scoring": scoring,
        "retained_by_association": assoc,
        "understood_from_content": understood,
    }


def ranked(rows: list[dict], limit: int = 25) -> list[dict]:
    """
    The reviewer's default view: highest-ranked first, with the reason.

    restricted_review sorts to the top regardless of score. A file routed to a
    supervising archivist must not sit below a well-scored one — compute_layer
    already returns 3 for it, and this mirrors that.
    """
    def key(r):
        return (0 if r.get("s02_decision") == "restricted_review" else 1,
                -(r.get("s02_score") or 0.0),
                r.get("path_norm") or "")

    out = []
    for r in sorted(rows, key=key)[:limit]:
        out.append({
            "filename": r.get("filename"),
            "lane": r.get("s03_lane"),
            "band": r.get("s02_band"),
            "score": r.get("s02_score"),
            "decision": r.get("s02_decision"),
            "rule": r.get("s02_rule_matched"),
            "by_association": bool(r.get("retained_by_association")),
            "why": r.get("s02_rationale"),
        })
    return out
