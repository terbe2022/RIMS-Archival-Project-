#!/usr/bin/env python3
"""
run_describe.py — generate titles, summaries and subject terms for text.

    python3 scripts/run_describe.py --manifest runs/2026-09-06/manifest.parquet \\
        --accession 9996021-20260903-01 --form intake/ACC-2026-021.json \\
        --out runs/2026-09-06/describe.jsonl --model llama3.1:8b

The image lane has had real descriptions since the vision run. Documents and
email have not: what the interface shows for them is the first few hundred
characters of extracted text, which is evidence but not description. This is the
missing half.

Emits the same JSON Lines shape as run_vision.py, so `vision.ingest_jsonl`
merges either without knowing which produced it.

What the model is and is not told
---------------------------------
It gets the collection context block from `context.build()` — source, owner,
role, scope, research, background. It does NOT get `valuable` or `exclude`.
Those are what relevance.py scores the output against, and a model told what the
archivist values will describe an ambiguous document in exactly those words;
the score would then be measuring the prompt rather than the file.

Abstention
----------
The prompt requires the model to say when the text does not support a
description, and the parser keeps that answer rather than discarding it. A
confident summary of an empty or truncated extraction manufactures retention
signal, and on this corpus — scanned PDFs with no text layer, mail bodies that
are one line of quoted header — that case is common rather than rare.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pyarrow.parquet as pq
import requests

from workbench import context

MIN_CHARS = 120          # below this there is nothing to summarise

PROMPT = """You are cataloguing a file from a university archives.

Describe ONLY what the text below actually contains. Do not infer what it might
be from the collection it came from. If the text is too short, garbled, or
contains no discernible subject, say so — that is a correct and useful answer,
and a confident summary of unreadable text is worse than none.

Rules:
- title: MAX 10 WORDS. A noun phrase, not a sentence. If the text has its own
  heading or subject line, prefer that.
- description: 2-3 sentences. What this document IS (a referee report, a
  contract, list traffic, a draft with revisions) as well as what it is about.
  Genre matters as much as subject for an archival record.
- subjects: 3-6 short topic terms, lowercase.
- genre: one of: correspondence, report, draft, minutes, form, dataset,
  publication, notes, list traffic, administrative, unknown.
- readable: true only if the text supports a real description. false if it is
  empty, truncated mid-word, boilerplate only, or unintelligible.
- If readable is false, set title to null and say why in description.

Reply with ONE JSON object and nothing else. No markdown fences.

{"title": "...", "description": "...", "subjects": ["..."], "genre": "...",
 "readable": true, "confidence": "high"}

--- TEXT BEGINS ---
%s
--- TEXT ENDS ---"""

LANES = {"document", "email", "tabular"}


def call_ollama(prompt: str, url: str, model: str, timeout: int) -> str:
    r = requests.post(f"{url}/api/generate", timeout=timeout, json={
        "model": model, "prompt": prompt, "stream": False,
        "options": {"temperature": 0, "num_predict": 400}})
    r.raise_for_status()
    return r.json().get("response", "")


def call_vllm(prompt: str, url: str, model: str, timeout: int) -> str:
    r = requests.post(f"{url}/v1/chat/completions", timeout=timeout, json={
        "model": model, "temperature": 0, "max_tokens": 400,
        "messages": [{"role": "user", "content": prompt}]})
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


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
    ap.add_argument("--accession")
    ap.add_argument("--form")
    ap.add_argument("--out", required=True)
    ap.add_argument("--backend", choices=["ollama", "vllm"], default="ollama")
    ap.add_argument("--url", default="http://localhost:11434")
    ap.add_argument("--model", default="llama3.1:8b")
    ap.add_argument("--chars", type=int, default=6000,
                    help="characters of extracted text sent per file")
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--redacted",
                    help="stage 04 output directory, e.g. "
                         "runs/2026-09-06/redacted/ACC-2026-021. When given, "
                         "summaries are generated from the pseudonymised text "
                         "rather than the raw extraction.")
    ap.add_argument("--allow-raw", action="store_true",
                    help="summarise raw text even where a redacted version "
                         "exists. Off by default, and it should stay off.")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    if not args.redacted and not args.allow_raw:
        print("--redacted is required unless --allow-raw is explicitly authorized", file=sys.stderr)
        return 2

    cols = ["file_uid", "accession_uid", "filename", "path_norm", "s03_lane",
            "s03_text_sample", "s03_text_len", "layer"]
    have = [c for c in cols if c in pq.read_schema(args.manifest).names]
    rows = pq.read_table(args.manifest, columns=have).to_pylist()

    rows = [r for r in rows
            if r.get("s03_lane") in LANES
            and r.get("layer") != 0
            and (r.get("s03_text_len") or 0) >= MIN_CHARS]
    if args.accession:
        rows = [r for r in rows if r.get("accession_uid") == args.accession]

    # Prefer the pseudonymised text.
    #
    # Summarising the raw extraction means the summary is built from text
    # containing names, phone numbers and account numbers — and that summary
    # goes into the manifest, into the export, and onto the screen. It would
    # carry exactly the identifiers stage 04 exists to remove, in a field
    # nobody thinks to check because it reads like description rather than
    # content.
    redacted = Path(args.redacted) / "reading_room" if args.redacted else None
    if redacted and not redacted.exists():
        print(f"  {redacted} does not exist — run stage 04 first, or pass "
              f"--allow-raw to summarise unredacted text deliberately",
              file=sys.stderr)
        return 2

    prefix = ""
    if args.form:
        form = json.loads(Path(args.form).read_text())
        prefix = context.build(form)
        u = context.describe_usage(form)
        print(f"  context: {u['fields_included']}  (withheld: {u['fields_withheld']})")
        if not prefix:
            print("  context: NONE — the form carries no descriptive content, "
                  "so descriptions will be generic. Say so when showing them.")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    seen = done_already(out)
    todo = [r for r in rows if r["file_uid"] not in seen]
    if args.limit:
        todo = todo[:args.limit]

    print(f"  {len(rows)} eligible, {len(seen)} already done, {len(todo)} to do")
    if not todo:
        return 0

    call = call_vllm if args.backend == "vllm" else call_ollama
    ok = failed = unreadable = 0
    from_redacted = 0
    t0 = time.perf_counter()

    with open(out, "a", encoding="utf-8") as fh:
        for i, r in enumerate(todo, 1):
            source = "raw"
            text = ""
            if redacted:
                cand = redacted / f"{r['file_uid']}.txt"
                if cand.exists():
                    text = cand.read_text(encoding="utf-8", errors="replace")
                    source = "redacted"
            if not text:
                if not args.allow_raw:
                    # Missing/empty redacted output is not evidence that raw text is safe.
                    failed += 1
                    print(f"    {r['file_uid']}: missing or empty pseudonymized text; skipped", file=sys.stderr)
                    continue
                text = r.get("s03_text_sample") or ""
            text = text[:args.chars]
            rec = {"file_uid": r["file_uid"], "image_path": r.get("path_norm"),
                   "model": args.model, "backend": args.backend,
                   "lane": r.get("s03_lane"), "text_source": source,
                   "is_warmup": False}
            t1 = time.perf_counter()
            try:
                rec["output"] = call(prefix + PROMPT % text, args.url,
                                     args.model, args.timeout)
                rec["success"] = True
                ok += 1
                if source == "redacted":
                    from_redacted += 1
                if '"readable": false' in rec["output"].replace("'", '"').lower():
                    unreadable += 1
            except Exception as exc:
                rec.update(success=False, error=f"{type(exc).__name__}: {exc}")
                failed += 1
            rec["wall_time_sec"] = round(time.perf_counter() - t1, 3)
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            if i % 20 == 0 or i == len(todo):
                rate = i / max(time.perf_counter() - t0, 1e-9) * 60
                print(f"    {i}/{len(todo)}  {rate:.1f}/min  "
                      f"~{(len(todo)-i)/max(rate,1e-9):.0f} min left  "
                      f"({failed} failed, {unreadable} not readable)")

    print(f"\n  {ok} described, {unreadable} reported as not readable, "
          f"{failed} failed, {round(time.perf_counter()-t0,1)}s")
    if redacted:
        print(f"  {from_redacted} summarised from pseudonymised text, "
              f"{ok - from_redacted} from explicitly requested raw text")
    elif ok:
        print("  WARNING: summaries were generated from RAW text. If any file "
              "contained personal information, the summary may repeat it. "
              "Pass --redacted to summarise the pseudonymised version.")
    print(f"  merge with: --image-outputs {out}")
    return 0 if ok and not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
