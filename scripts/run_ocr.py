#!/usr/bin/env python3
"""
run_ocr.py — read the files nothing could read.

    python3 scripts/run_ocr.py --manifest runs/final/manifest.parquet \\
        --out runs/final/ocr.jsonl

    python3 scripts/run_ocr.py --manifest ... --accession 2620191-... --limit 20

Finds every row with no usable text, rasterises and OCRs it, and writes JSON
Lines. Checkpointed and resumable like the other model lanes, though this one
needs no GPU — Tesseract is CPU work and runs alongside anything else.

Merge the output with:

    python3 scripts/run_cpu_pass.py ... --ocr-outputs runs/final/ocr.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pyarrow.parquet as pq

from workbench import ocr


def done_already(path: Path) -> set:
    if not path.exists():
        return set()
    seen = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                seen.add(json.loads(line).get("file_uid"))
            except json.JSONDecodeError:
                continue
    return seen


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--accession")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--lang", default="eng")
    ap.add_argument("--max-pages", type=int, default=ocr.MAX_PAGES)
    ap.add_argument("--engine", choices=["auto", "tesseract", "vlm"],
                    default="auto",
                    help="auto prefers tesseract and falls back to the vision "
                         "model, which needs no system packages")
    ap.add_argument("--url", default="http://127.0.0.1:11435")
    ap.add_argument("--model", default="llava-llama3")
    args = ap.parse_args()

    have = ocr.available()
    print(f"  tools: {have}")
    engine = args.engine
    if engine == "auto":
        engine = "tesseract" if have["tesseract"] else (
            "vlm" if have["pypdfium2"] else None)
    if engine == "tesseract" and not have["tesseract"]:
        print("  tesseract not installed", file=sys.stderr); return 2
    if engine == "vlm" and not have["pypdfium2"]:
        print("  pypdfium2 not installed — pip install --user pypdfium2",
              file=sys.stderr); return 2
    if not engine:
        print("  no OCR path available. Either install tesseract and "
              "poppler-utils, or pip install --user pypdfium2 to read scans "
              "with the vision model already serving.", file=sys.stderr)
        return 2
    print(f"  engine: {engine}"
          + (f" ({args.model} at {args.url})" if engine == "vlm" else ""))

    cols = ["file_uid", "accession_uid", "filename", "path_raw", "s03_lane",
            "s03_text_len", "layer", "size_bytes"]
    have_cols = [c for c in cols if c in pq.read_schema(args.manifest).names]
    rows = pq.read_table(args.manifest, columns=have_cols).to_pylist()

    todo = [r for r in rows if ocr.needs_ocr(r)]
    if args.accession:
        todo = [r for r in todo if r.get("accession_uid") == args.accession]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    seen = done_already(out)
    todo = [r for r in todo if r["file_uid"] not in seen]
    if args.limit:
        todo = todo[:args.limit]

    print(f"  {len(todo)} files with no usable text, {len(seen)} already done")
    if not todo:
        return 0

    ok = failed = low = 0
    t0 = time.perf_counter()
    with open(out, "a", encoding="utf-8") as fh:
        for i, r in enumerate(todo, 1):
            src = r.get("path_raw")
            if not src:
                res = {"text": "", "error": "no path recorded", "confidence": None}
            elif engine == "vlm":
                res = ocr.ocr_file_vlm(src, args.url, args.model, args.max_pages)
            else:
                res = ocr.ocr_file(src, args.lang, args.max_pages)
            rec = {"file_uid": r["file_uid"], "filename": r.get("filename"),
                   "accession_uid": r.get("accession_uid"), **res}
            rec.pop("rejected_text", None)      # keep the file small
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            if res.get("text"):
                ok += 1
            elif "below the" in str(res.get("error") or ""):
                low += 1
            else:
                failed += 1
            if i % 10 == 0 or i == len(todo):
                rate = i / max(time.perf_counter() - t0, 1e-9) * 60
                print(f"    {i}/{len(todo)}  {rate:.1f}/min  "
                      f"{ok} read, {low} too low to trust, {failed} failed")

    print(f"\n  {ok} read, {low} rejected below the confidence floor, "
          f"{failed} failed, {round(time.perf_counter()-t0,1)}s")
    print(f"  merge with: --ocr-outputs {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
