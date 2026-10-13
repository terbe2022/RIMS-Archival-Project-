#!/usr/bin/env python3
"""Build a private review payload or a content-free public demonstration.

Private mode retains paths and text for approved internal use. Public mode uses
only generated identities, typed statistics and fixed enums; policy prose,
rationales and unknown fields are omitted. Source selection and publication
still require approval. This is not the reviewed archival release workflow.
"""
from __future__ import annotations

import argparse
import json
import math
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
    if public:
        # No source identifiers or free-form policy/format/rationale text crosses
        # this boundary. Publication still requires selection and human review.
        safe = []
        enums = {"s02_decision": {"selected", "not_selected", "restricted_review", "discard_candidate"},
                 "s02_band": {"high", "mid", "low"},
                 "s03_lane": {"document", "email", "image", "tabular", "scientific", "av", "code", "archive"},
                 "s03_status": {"ok", "empty", "skipped", "failed", "partial"}}
        for i, row in enumerate(rows, 1):
            r = {"file_uid": f"item-{i:04d}", "accession_uid": "demo"}
            for key in ("depth", "size_bytes", "s02_score", "s03_text_len", "layer"):
                value = row.get(key)
                if type(value) in (int, float) and math.isfinite(value):
                    r[key] = value
            for key in ("retained_by_association", "s01_ext_mismatch", "s03_needs_ocr"):
                if type(row.get(key)) is bool:
                    r[key] = row[key]
            for key, allowed in enums.items():
                value = row.get(key)
                if isinstance(value, str) and value in allowed:
                    r[key] = value
            safe.append(r)
        rows, form = safe, None

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

    # Intake prose is retained only in the private payload.
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
    if payload.get("criteria") or payload.get("name"):
        problems.append("free-form accession or intake text present")
    if payload.get("accession") not in (None, "demo"):
        problems.append("source accession identifier present")
    allowed = {"file_uid", "accession_uid", "depth", "size_bytes", "s02_score",
               "s03_text_len", "layer", "retained_by_association", "s01_ext_mismatch",
               "s03_needs_ocr", "s02_decision", "s02_band", "s03_lane", "s03_status",
               "filename", "folder"}
    for n, item in enumerate(payload["items"], 1):
        if set(item) - allowed:
            problems.append("unexpected item field")
        if item.get("file_uid") != f"item-{n:04d}" or item.get("filename") != f"item-{n:04d}":
            problems.append("source item identifier present")
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
