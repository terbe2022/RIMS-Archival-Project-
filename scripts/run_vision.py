#!/usr/bin/env python3
"""
run_vision.py — describe an accession's images. The only stage that needs a GPU.

    python3 scripts/run_vision.py --manifest runs/2026-09-05b/manifest.parquet \\
        --accession 9996020-20260903-01 --form intake/ACC-2026-020.json \\
        --out runs/2026-09-05b/vision.jsonl

Writes JSON Lines in the same shape the existing image pipeline produces, so
`workbench/vision.py --image-outputs` merges it into the manifest without
knowing which of the two produced it.

Checkpointed per image, deliberately. The card is shared with the legislation
pipeline, its allocation only changes at the next vLLM start, and the embedder
there has already failed once after the GPU came back. A run that loses the
card at image 700 of 993 must resume at 700, not at 1. Re-running the same
command skips whatever is already in the output file.

Backends
--------
vLLM is roughly six times faster than Ollama at concurrency 8 on this hardware
(55.4 vs 8.9 images/min measured on an L4), but wants about 14 GB for a 7B model
at FP16. Ollama holds ~6 GB and fits alongside the legislation server without
anyone restarting anything. Pick by what the card has free, not by preference.
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pyarrow.parquet as pq
import requests

from workbench import context

# The locked prompt from the 1,200-call experiment. Its central rule — the
# image CONTAINS sensitive content versus the image's SUBJECT is a difficult
# historical topic — is what makes the flag usable on archival material, and it
# is the reason a photograph of a war protest is not violent content.
PROMPT = (
    "You are analyzing an archival photograph or document scan.\n\n"
    "CRITICAL RULE — READ FIRST:\n"
    "The 'offensive' flag means the IMAGE ITSELF contains content from one of "
    "the allowed sensitivity categories. It does NOT mean the image's SUBJECT "
    "is controversial, sad, political, or about a difficult historical period.\n\n"
    "EXAMPLES OF WHAT IS NOT OFFENSIVE (set offensive=false):\n"
    "- A photo of war protesters holding 'Stop the War' signs.\n"
    "- A photo of soldiers in uniform.\n"
    "- Civil rights marches, political rallies, demonstrations.\n"
    "- Documentation of any difficult historical event.\n\n"
    "EXAMPLES OF WHAT IS OFFENSIVE (set offensive=true):\n"
    "- A swastika or other hate symbol visibly displayed.\n"
    "- Graphic violence happening in the image (blood, weapon mid-use).\n"
    "- Visible nudity.\n"
    "- Visible patient records or medical chart with identifiable info.\n\n"
    "OTHER RULES:\n"
    "- title: MAX 8 WORDS. Noun phrase, NOT a sentence.\n"
    "- description: up to 4 sentences. Only observable details.\n"
    "- offense_category: if offensive=true, exactly ONE of: historical "
    "racialized performance, human remains, Native American imagery, "
    "nudity/sexual content, violence/graphic content, hate symbols, "
    "medical/health records, student/PII records, Other sensitive categories. "
    "Use the exact category name. NEVER invent new categories.\n"
    "- Reply with ONE JSON object and nothing else. No markdown fences.\n\n"
    'Return: {"title": "...", "description": "...", "offensive": false, '
    '"offense_evidence": "where in the frame you see it; if there is no '
    'observable evidence, set offensive to false", '
    '"offense_category": null, "offense_reason": null, "confidence": "high"}\n'
)

IMAGE_PUIDS = {"fmt/43", "fmt/11", "fmt/353", "fmt/3", "fmt/4"}


def encode(path: Path, max_px: int = 1400) -> str | None:
    """
    Base64 JPEG, downscaled.

    Originals here run to 6378x4718. Sending those wastes decode time on detail
    no vision model at this resolution can use, and the scans are access
    derivatives rather than masters, so nothing preservation-relevant is lost.
    """
    try:
        from PIL import Image
        import io
        with Image.open(path) as im:
            im = im.convert("RGB")
            if max(im.size) > max_px:
                ratio = max_px / max(im.size)
                im = im.resize((int(im.width * ratio), int(im.height * ratio)))
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=88)
            return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None


def call_ollama(b64: str, prompt: str, url: str, model: str, timeout: int) -> str:
    r = requests.post(f"{url}/api/generate", timeout=timeout, json={
        "model": model, "prompt": prompt, "images": [b64], "stream": False,
        "options": {"temperature": 0}})
    r.raise_for_status()
    return r.json().get("response", "")


def call_vllm(b64: str, prompt: str, url: str, model: str, timeout: int) -> str:
    r = requests.post(f"{url}/v1/chat/completions", timeout=timeout, json={
        "model": model, "temperature": 0, "max_tokens": 400,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url",
             "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}]})
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def done_already(path: Path) -> set:
    """Image paths already written. Makes re-running the command a resume."""
    if not path.exists():
        return set()
    seen = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                seen.add(json.loads(line).get("image_path"))
            except json.JSONDecodeError:
                continue
    return seen


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--accession", help="accession_uid; omit to do all images")
    ap.add_argument("--form", help="intake form, for collection context")
    ap.add_argument("--out", required=True)
    ap.add_argument("--backend", choices=["ollama", "vllm"], default="ollama")
    ap.add_argument("--url", default="http://localhost:11434")
    ap.add_argument("--model", default="llava-llama3")
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    t = pq.read_table(args.manifest, columns=[
        "file_uid", "accession_uid", "path_raw", "filename", "s01_puid",
        "extension", "layer"])
    rows = [r for r in t.to_pylist()
            if (r.get("s01_puid") in IMAGE_PUIDS
                or (r.get("extension") or "").lower() in
                ("jpg", "jpeg", "tif", "tiff", "png"))
            and r.get("layer") != 0]
    if args.accession:
        rows = [r for r in rows if r.get("accession_uid") == args.accession]

    prompt = PROMPT
    if args.form:
        form = json.loads(Path(args.form).read_text())
        block = context.build(form)
        if block:
            prompt = block + "\n" + PROMPT
            print(f"  collection context: "
                  f"{context.describe_usage(form)['fields_included']}")
        else:
            # ACC-2026-020. Nobody has said what these images are, so there is
            # nothing to condition on and the descriptions will be generic.
            # That is worth stating when the results are shown.
            print("  collection context: NONE — the intake form has no "
                  "descriptive content. Descriptions will be generic.")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    seen = done_already(out)
    todo = [r for r in rows if r["path_raw"] not in seen]
    if args.limit:
        todo = todo[:args.limit]

    print(f"  {len(rows)} images, {len(seen)} already done, {len(todo)} to do")
    if not todo:
        return 0

    call = call_vllm if args.backend == "vllm" else call_ollama
    ok = failed = 0
    t0 = time.perf_counter()

    with open(out, "a", encoding="utf-8") as fh:
        for i, r in enumerate(todo, 1):
            rec = {"image_path": r["path_raw"], "file_uid": r["file_uid"],
                   "model": args.model, "backend": args.backend,
                   "is_warmup": False}
            t1 = time.perf_counter()
            b64 = encode(Path(r["path_raw"]))
            if b64 is None:
                rec.update(success=False, error="image could not be read")
                failed += 1
            else:
                try:
                    rec["output"] = call(b64, prompt, args.url, args.model,
                                         args.timeout)
                    rec["success"] = True
                    ok += 1
                except Exception as exc:
                    rec.update(success=False,
                               error=f"{type(exc).__name__}: {exc}")
                    failed += 1
            rec["wall_time_sec"] = round(time.perf_counter() - t1, 3)
            fh.write(json.dumps(rec) + "\n")
            fh.flush()          # a lost card must not lose completed work
            if i % 25 == 0 or i == len(todo):
                rate = i / max(time.perf_counter() - t0, 1e-9) * 60
                left = (len(todo) - i) / max(rate, 1e-9)
                print(f"    {i}/{len(todo)}  {rate:.1f} img/min  "
                      f"~{left:.0f} min left  ({failed} failed)")

    print(f"\n  {ok} described, {failed} failed, "
          f"{round(time.perf_counter()-t0,1)}s")
    print(f"  merge with: scripts/run_cpu_pass.py --image-outputs {out}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
