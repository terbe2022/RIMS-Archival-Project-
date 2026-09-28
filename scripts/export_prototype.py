#!/usr/bin/env python3
"""
export_prototype.py — feed the accession-workbench UI real data.

    python3 scripts/export_prototype.py runs/2026-09-06/manifest.parquet \\
        --intake intake --out demo/aw

The workbench prototype builds its own records from a seeded generator. This
emits the same two structures — `jobs` and `records` — from the actual manifest,
so the interface stays exactly as designed and only the data changes.

Two mappings need stating, because they are where the prototype's vocabulary and
the schema's disagree.

**Disposition.** The prototype offers keep / archive / delete. Manifest v1.1
removed that vocabulary deliberately: `discard_candidate` and
`restricted_review` are different outcomes and conflating them is the mistake
the schema exists to prevent. This exporter does NOT emit a `dispo` — every
record arrives undecided, which is honest, because no person has decided
anything yet. The pipeline's own proposal travels in `rationale` and
`importance` where a reviewer can see it and disagree.

**Importance.** The prototype's high/medium/low maps onto the manifest's band,
with one override: anything routed to a supervising archivist is `high`
regardless of score, because sensitivity outranks ranking.

`confidence` is NOT invented. Where the pipeline scored lexically rather than by
embedding it says so, and a made-up percentage next to a real title would be the
most misleading thing on the screen.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

KIND = {"image": "image", "email": "email", "document": "document",
        "tabular": "document", "av": "media", "archive": "other",
        "code": "other", "scientific": "other"}

FIELDS = [
    "file_uid", "accession_uid", "filename", "path_norm", "path_raw",
    "parent_folder", "extension", "size_bytes",
    "s01_format_name", "s02_decision", "s02_rule_matched", "s02_band",
    "s02_score", "s02_rationale", "s03_lane", "s03_text_len",
    "s03_text_sample", "s04_description", "s04_sensitivity_flags",
    "s04_pii_entities_json", "s05_decision", "s05_rationale",
    "s05_generated_fields", "dc_title", "dc_date", "dc_subject",
    "layer", "retained_by_association", "duplicate_of",
    "s02_structural_exclusion",
]


def importance(r: dict) -> str:
    if r.get("s02_decision") == "restricted_review" or r.get("s04_sensitivity_flags"):
        return "high"
    band = r.get("s02_band")
    return {"high": "high", "mid": "medium"}.get(band, "low")


def flags(r: dict) -> list[str]:
    """
    Short labels a reviewer scans. Each is a fact from the manifest, never a
    summary of one — "kept by association" and "sensitive" are different claims
    and must not collapse into a single badge.
    """
    out = []
    if r.get("s02_decision") == "restricted_review":
        out.append("needs a person")
    for f in (r.get("s04_sensitivity_flags") or []):
        out.append(str(f))
    if r.get("retained_by_association"):
        out.append("kept by association")
    if r.get("duplicate_of"):
        out.append("duplicate")
    if r.get("s02_structural_exclusion"):
        out.append(str(r["s02_structural_exclusion"]).replace("_", " "))
    if r.get("s03_lane") and not r.get("s03_text_len"):
        out.append("not read")
    try:
        ents = json.loads(r.get("s04_pii_entities_json") or "[]")
        if ents:
            out.append(f"{len(ents)} identifiers")
    except (ValueError, TypeError):
        pass
    return out[:6]


def rationale(r: dict) -> dict:
    """
    Two separate statements, never one string.

    The old version joined them, producing sentences that said "no rule
    matched" and then quoted a retention criterion the file had matched. A
    reviewer reading the ledger correctly concluded the field was unreliable
    and ignored it. Both halves were true; they answer DIFFERENT questions,
    and concatenating them made a contradiction out of two facts.

      disposition — what the appraisal ruleset concluded. Rules only.
      ranking     — why it sorted where it did, quoting the intake form.

    Disposition and rank are independent by design: a file can match no rule
    and still rank high because the form's criteria describe it.
    """
    d = r.get("s02_decision") or "not_selected"
    rule = r.get("s02_rule_matched")
    disposition = (f"{d} — rule {rule} matched" if rule
                   else f"{d} — no appraisal rule had an opinion about it")

    rank = re.sub(r"^\[[^\]]+\]\s*", "", r.get("s02_rationale") or "").strip()
    method = "embedding"
    if "[lexical]" in (r.get("s02_rationale") or ""):
        method = "lexical"

    extra = (r.get("s05_rationale") or "").strip()
    if extra and extra not in rank:
        rank = (rank + " " + extra).strip() if rank else extra

    return {
        "disposition": disposition,
        "ranking": rank or "Nothing in the form matched; ranked on topical fit alone.",
        "method": method,
    }


def confidence(r: dict):
    """
    None when the score came from lexical matching.

    The prototype renders `confidence 82%` beside a title. Printing a number
    there for a run that matched words rather than meaning would be the most
    misleading element on the screen, so the field is omitted and the UI shows
    nothing rather than something invented.
    """
    rat = r.get("s02_rationale") or ""
    if "[lexical]" in rat or not r.get("s02_score"):
        return None
    return round(float(r["s02_score"]), 3)


def build(rows: list[dict], forms: dict, uid_to_form: dict,
          snippet: int) -> tuple[list, list]:
    by_uid: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_uid[r.get("accession_uid")].append(r)

    jobs, records, n = [], [], 0
    for uid, group in sorted(by_uid.items()):
        acc_id = uid_to_form.get(uid)
        form = forms.get(acc_id, {})
        kinds = defaultdict(int)

        for r in group:
            n += 1
            kind = KIND.get(r.get("s03_lane") or "", "other")
            kinds[kind] += 1
            body = r.get("s03_text_sample") or ""
            records.append({
                "id": f"r{n:05d}",
                "jobId": acc_id or uid,
                "kind": kind,
                "filename": r.get("filename"),
                "folder": "/".join((r.get("path_norm") or "").split("/")[:-1]),
                "boxPath": r.get("path_norm"),
                "boxFileId": (r.get("file_uid") or "")[:12],
                "sizeKB": round((r.get("size_bytes") or 0) / 1024, 1),
                "date": r.get("dc_date") or "",
                "title": r.get("dc_title") or r.get("filename"),
                "description": (r.get("s04_description")
                                or body[:snippet] or "Not read. No text was "
                                "extracted from this file, so nothing is known "
                                "about its contents."),
                "keywords": [k for k in (r.get("dc_subject") or "").split("; ") if k],
                "flags": flags(r),
                "importance": importance(r),
                "confidence": confidence(r),
                "rationale": rationale(r)["disposition"]
                             + "  ·  " + rationale(r)["ranking"],
                "why": rationale(r),
                "dispo": None,          # nobody has decided anything yet
                "decidedAt": None,
                "generated": list(r.get("s05_generated_fields") or []),
                "lane": r.get("s03_lane"),
                "format": r.get("s01_format_name"),
                "body": body[:2000] or None,
                "email": None, "exif": None, "entities": [],
            })

        jobs.append({
            "id": acc_id or uid,
            "name": form.get("name") or uid,
            "type": form.get("job_type") or "mixed",
            "status": "complete" if form.get("status") == "queued" else "draft",
            "accessionUid": uid,
            "provisional": uid.startswith("999"),
            "files": len(group),
            "sizeKB": round(sum((r.get("size_bytes") or 0) for r in group) / 1024, 1),
            "counts": dict(kinds),
            "intake": {k: form.get(k) for k in
                       ("source", "owner", "role", "scope", "research", "bio",
                        "valuable", "exclude", "access", "notes")},
        })
    return jobs, records


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("parquet")
    ap.add_argument("--intake", default="intake")
    ap.add_argument("--out", default="demo/aw")
    ap.add_argument("--snippet", type=int, default=420)
    args = ap.parse_args()

    have = [c for c in FIELDS if c in pq.read_schema(args.parquet).names]
    rows = pq.read_table(args.parquet, columns=have).to_pylist()
    for r in rows:
        r.pop("path_raw", None)          # server layout never reaches a browser

    forms = {}
    for p in sorted(Path(args.intake).glob("ACC-*.json")):
        f = json.loads(p.read_text())
        forms[f["accession"]] = f

    uid_to_form = {}
    try:
        from workbench import accessions as accmod
        reg = Path(args.intake) / "accession_registry.json"
        if reg.exists():
            built, _ = accmod.resolve(args.intake, reg, allow_provisional=True)
            uid_to_form = {v["accession_uid"]: k for k, v in built.items()}
    except Exception as exc:
        print(f"  registry lookup failed ({exc})", file=sys.stderr)

    jobs, records = build(rows, forms, uid_to_form, args.snippet)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "prototype-data.json").write_text(
        json.dumps({"jobs": jobs, "records": records}, default=str))
    print(f"wrote {out/'prototype-data.json'}  {len(jobs)} accessions, "
          f"{len(records)} records")
    for j in jobs:
        print(f"  {j['id']}  {j['files']:>5} files  {j['status']}"
              f"{'  PROVISIONAL' if j['provisional'] else ''}  {j['counts']}")
    print("  Contains real filenames, paths and text. Do not publish.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
