#!/usr/bin/env python3
"""
run_all_lanes.py — send every accession through every lane it has material for.

    python3 scripts/run_all_lanes.py --manifest runs/demo/manifest.parquet \\
        --out runs/2026-09-11 --url http://127.0.0.1:11435

Until now each lane was run by hand against one accession, which is why the
Hanratty tree had 167 undescribed images and 237 unsummarised documents while
the scanning programme had 684 descriptions. Routing was never the problem —
the handlers simply were not run.

Sequential on purpose. There is one GPU, the two models are about 5 GB each,
and running them concurrently makes Ollama evict one to load the other on every
request. That is what produced a 37% success rate earlier; in sequence it was
99.7%.

Resumable. Each lane writes its own JSON Lines file and skips what is already
there, so an interrupted run continues rather than restarting.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
IMAGE_LANES = {"image"}
TEXT_LANES = {"document", "email", "tabular"}


def lane_counts(manifest: Path) -> dict:
    cols = ["accession_uid", "s03_lane", "s03_text_len", "layer"]
    have = [c for c in cols if c in pq.read_schema(manifest).names]
    rows = pq.read_table(manifest, columns=have).to_pylist()
    out: dict = {}
    for r in rows:
        if r.get("layer") == 0:
            continue
        acc = out.setdefault(r.get("accession_uid"), {"image": 0, "text": 0})
        lane = r.get("s03_lane")
        if lane in IMAGE_LANES:
            acc["image"] += 1
        elif lane in TEXT_LANES and (r.get("s03_text_len") or 0) >= 120:
            acc["text"] += 1
    return out


def form_for(uid: str, intake: Path) -> Path | None:
    """Map an accession_uid back to its intake form via the registry."""
    try:
        sys.path.insert(0, str(HERE.parent))
        sys.path.insert(0, str(HERE.parent / "src"))
        from workbench import accessions as acc
        built, _ = acc.resolve(intake, intake / "accession_registry.json",
                               allow_provisional=True)
        for acc_id, row in built.items():
            if row["accession_uid"] == uid:
                p = intake / f"{acc_id}.json"
                return p if p.exists() else None
    except Exception:
        return None
    return None


def run(cmd: list[str]) -> int:
    print("    " + " ".join(cmd[1:6]) + " …", flush=True)
    return subprocess.call(cmd)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True, help="directory for the jsonl files")
    ap.add_argument("--intake", default="intake")
    ap.add_argument("--url", default="http://127.0.0.1:11435")
    ap.add_argument("--vision-model", default="llava-llama3")
    ap.add_argument("--text-model", default="llama3.1:8b")
    ap.add_argument("--redacted-root",
                    help="runs/<date>/redacted — summarise the pseudonymised "
                         "text rather than the raw extraction")
    ap.add_argument("--skip-images", action="store_true")
    ap.add_argument("--skip-text", action="store_true")
    args = ap.parse_args()

    manifest = Path(args.manifest)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    intake = Path(args.intake)
    counts = lane_counts(manifest)

    print(f"{len(counts)} accessions in {manifest}")
    for uid, c in sorted(counts.items()):
        print(f"  {uid}  {c['image']:>5} images  {c['text']:>5} text files")
    print()

    # Validate every text input before launching any model work.
    if not args.skip_text and any(c["text"] for c in counts.values()):
        if not args.redacted_root:
            print("--redacted-root is required for text descriptions", file=sys.stderr)
            return 2
        for uid, c in counts.items():
            if not c["text"]:
                continue
            form = form_for(uid, intake)
            acc_id = form.stem if form else uid
            red = Path(args.redacted_root) / acc_id / "reading_room"
            if not red.is_dir():
                print(f"missing pseudonymized input directory: {red}", file=sys.stderr)
                return 2

    produced = []
    failed = False
    for uid, c in sorted(counts.items(), key=lambda kv: -kv[1]["image"]):
        form = form_for(uid, intake)
        acc_id = form.stem if form else uid
        if not form:
            print(f"  {uid}: no intake form found — running without collection "
                  f"context, descriptions will be generic")

        if c["image"] and not args.skip_images:
            f = out / f"vis-{acc_id}.jsonl"
            print(f"  {acc_id}: {c['image']} images")
            rc = run([sys.executable, str(HERE / "run_vision.py"),
                      "--manifest", str(manifest), "--accession", uid,
                      "--out", str(f), "--url", args.url,
                      "--model", args.vision_model]
                     + (["--form", str(form)] if form else []))
            if rc == 0:
                produced.append(f)
            else:
                failed = True

        if c["text"] and not args.skip_text:
            f = out / f"desc-{acc_id}.jsonl"
            print(f"  {acc_id}: {c['text']} text files")
            cmd = [sys.executable, str(HERE / "run_describe.py"),
                   "--manifest", str(manifest), "--accession", uid,
                   "--out", str(f), "--url", args.url,
                   "--model", args.text_model]
            if form:
                cmd += ["--form", str(form)]
            # Summarise the pseudonymised text where it exists. A summary built
            # from raw text can repeat the identifiers redaction removed, in a
            # field nobody thinks to check because it reads like description.
            if args.redacted_root:
                red = Path(args.redacted_root) / acc_id
                if red.exists():
                    cmd += ["--redacted", str(red)]
                else:
                    print(f"    missing redacted text at {red}", file=sys.stderr)
                    return 2
            if run(cmd) == 0:
                produced.append(f)
            else:
                failed = True

    combined = out / "all-descriptions.jsonl"
    with open(combined, "w", encoding="utf-8") as fh:
        for f in produced:
            if f.exists():
                fh.write(f.read_text(encoding="utf-8"))
    total = sum(1 for _ in open(combined, encoding="utf-8")) if combined.exists() else 0
    ok = 0
    if total:
        for line in open(combined, encoding="utf-8"):
            try:
                ok += 1 if json.loads(line).get("success") else 0
            except json.JSONDecodeError:
                pass
    print(f"\n{ok} of {total} succeeded — {combined}")
    print(f"Merge with:\n  python3 scripts/run_cpu_pass.py --data data/sample_1k "
          f"--out runs/final --provisional --name-detector presidio "
          f"--image-outputs {combined}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
