#!/usr/bin/env python3
"""
export_review.py — turn a manifest parquet into the review UI's payload.

Two modes, and the difference is the whole point.

    (default)   Full payload. Real paths, filenames, extracted text. For
                running locally or behind campus authentication. Never
                publish this.

    --public    Redacted payload for a public demo. Drops paths, filenames,
                text samples and anything derived from file content, keeping
                only counts, lanes, bands, decisions and the form clauses the
                archivist wrote. Safe for GitHub Pages.

--public is a coarse instrument on purpose. It does not attempt to detect
whether a given filename is sensitive; it removes all of them. Presidio's
measured recall on this corpus is 0.69-0.81, so any redaction that decides
field by field will leak. Dropping whole columns cannot.

Even in --public mode this will refuse to write if it finds free text that
could carry personal information, rather than trusting the column list to be
complete.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import pyarrow.parquet as pq

# Columns that may carry personal information, directly or by derivation.
# Dropped wholesale in --public mode.
_IDENTIFYING = {
    "path_raw", "path_norm", "path_norm_ci", "filename", "parent_folder",
    "s03_text_sample", "s03_text_path", "s04_summary", "s04_description",
    "s02_keywords", "sample_reason", "mtime_raw", "source_ref",
    "profile_person", "source_label",
}

# Columns the UI needs and which carry no content.
_KEEP = [
    "file_uid", "accession_uid", "extension", "depth", "size_bytes",
    "s01_puid", "s01_format_name", "s01_id_method", "s01_ext_mismatch",
    "s02_decision", "s02_rule_matched", "s02_band", "s02_score",
    "s02_rationale", "s02_structural_exclusion", "duplicate_of",
    "s03_lane", "s03_status", "s03_text_len", "s03_needs_ocr",
    "layer", "retained_by_association",
]


def _public_filename(row: dict, n: int) -> str:
    """A stable, meaningless label so the UI has something to show."""
    ext = row.get("extension") or ""
    return f"item-{n:04d}" + (f".{ext}" if ext else "")


def load(parquet: Path) -> list[dict]:
    cols = [c for c in _KEEP + list(_IDENTIFYING)
            if c in pq.read_schema(parquet).names]
    return pq.read_table(parquet, columns=cols).to_pylist()


def build(rows: list[dict], form: dict | None, public: bool) -> dict:
    out = []
    for i, r in enumerate(rows, 1):
        item = {k: r.get(k) for k in _KEEP if k in r}
        if public:
            item["filename"] = _public_filename(r, i)
            item["folder"] = f"folder-{(r.get('depth') or 0)}"
        else:
            item["filename"] = r.get("filename")
            item["folder"] = r.get("parent_folder")
            item["path"] = r.get("path_norm")
            item["text"] = (r.get("s03_text_sample") or "")[:600]
        out.append(item)

    # The form's own words are what the rationales quote, so the UI shows them
    # side by side. In public mode the prose stays: it is the archivist's
    # appraisal policy, not anyone's personal information. Owner and scope are
    # dropped because they name people.
    criteria = {}
    if form:
        criteria = {
            "valuable": form.get("valuable"),
            "exclude": form.get("exclude"),
            "access": form.get("access"),
        }
        if not public:
            criteria["owner"] = form.get("owner")
            criteria["research"] = form.get("research")

    layers = {}
    lanes = {}
    decisions = {}
    for r in out:
        layers[str(r.get("layer"))] = layers.get(str(r.get("layer")), 0) + 1
        lanes[r.get("s03_lane") or "unroutable"] = \
            lanes.get(r.get("s03_lane") or "unroutable", 0) + 1
        decisions[r.get("s02_decision") or "none"] = \
            decisions.get(r.get("s02_decision") or "none", 0) + 1

    return {
        "public": public,
        "accession": (rows[0].get("accession_uid") if rows else None),
        "name": (None if public else (form or {}).get("name")),
        "counts": {"files": len(out), "layers": layers, "lanes": lanes,
                   "decisions": decisions},
        "criteria": criteria,
        "items": out,
    }


def audit(payload: dict) -> list[str]:
    """Refuse to publish if free text survived the column drop."""
    problems = []
    for item in payload["items"]:
        for key in ("path", "text"):
            if item.get(key):
                problems.append(f"{key} present on {item.get('file_uid')}")
                break
    return problems[:5]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("parquet")
    ap.add_argument("--form", help="the ACC-*.json this run used")
    ap.add_argument("--out", default="web/review-data.json")
    ap.add_argument("--public", action="store_true",
                    help="redact for publication: drops paths, filenames, text")
    ap.add_argument("--limit", type=int, default=0,
                    help="sample N items (public demos do not need thousands)")
    args = ap.parse_args()

    rows = load(Path(args.parquet))
    if args.limit and len(rows) > args.limit:
        random.seed(20260904)
        keep = [r for r in rows if r.get("s02_decision") == "restricted_review"]
        rest = [r for r in rows if r.get("s02_decision") != "restricted_review"]
        rows = keep + random.sample(rest, max(0, args.limit - len(keep)))

    form = json.loads(Path(args.form).read_text()) if args.form else None
    payload = build(rows, form, args.public)

    if args.public:
        problems = audit(payload)
        if problems:
            print("REFUSING TO WRITE — identifying content survived redaction:",
                  file=sys.stderr)
            for p in problems:
                print(f"  {p}", file=sys.stderr)
            return 2

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=None, default=str))
    kind = "PUBLIC (redacted)" if args.public else "FULL (do not publish)"
    print(f"wrote {out}  {len(payload['items'])} items  [{kind}]")
    if not args.public:
        print("  This payload contains real paths, filenames and extracted "
              "text. It must not be committed or served publicly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
