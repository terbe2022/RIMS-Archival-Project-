#!/usr/bin/env python3
"""
review_packet.py — hand an accession to a reviewer, and take the answers back.

    # make the packet
    python3 scripts/review_packet.py export demo/aw/prototype-data.json \\
        --accession ACC-2026-021 --out review/ACC-2026-021-packet.json

    # after the reviewer returns decisions.json
    python3 scripts/review_packet.py ingest demo/aw/prototype-data.json \\
        --decisions review/ACC-2026-021-decisions.json \\
        --reviewer "Simulated reviewer (demonstration)"

The packet carries what a person actually needs to decide: title, summary,
folder, file type, what the pipeline proposed and why, and the accession form
itself — because the form is what the decision is supposed to be measured
against.

What the packet does NOT carry
------------------------------
No file paths, no raw extracted text beyond a short summary, and no PII vault.
A reviewer deciding what to keep does not need the server layout, and a packet
that travels should carry as little as will do the job.

On honesty
----------
`ingest` records whatever reviewer name it is given, and stamps `reviewSource`
so the decision record shows where the decision came from. If the reviewer is a
model standing in for a person during a demonstration, name it that way. The
decision log is the artefact that answers "who decided this" years later, and
quietly writing a person's name against a machine's judgement would poison
exactly the thing the log exists for.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

VALID = {"selected", "not_selected", "restricted_review", "discard_candidate"}


def two_sentences(text: str, limit: int = 300) -> str:
    if not text:
        return ""
    import re
    parts = re.findall(r"[^.!?]+[.!?]+", text) or [text]
    return " ".join(parts[:2]).strip()[:limit]


def do_export(args) -> int:
    data = json.loads(Path(args.payload).read_text())
    job = next((j for j in data["jobs"] if j["id"] == args.accession), None)
    if not job:
        print("accessions available: " + ", ".join(j["id"] for j in data["jobs"]))
        return 2

    recs = [r for r in data["records"] if r.get("jobId") == args.accession]

    # Folder context, so a reviewer can apply the 60% rule rather than guess.
    by_folder: dict[str, list] = {}
    for r in recs:
        by_folder.setdefault(r.get("folder") or "(root)", []).append(r)
    folders = {
        f: {
            "files": len(g),
            "ranked_high_or_medium": sum(
                1 for x in g if x.get("importance") in ("high", "medium")),
            "file_types": sorted({(x.get("filename") or "").split(".")[-1].lower()
                                  for x in g if "." in (x.get("filename") or "")})[:8],
        }
        for f, g in by_folder.items()
    }

    items = []
    for r in recs:
        if args.limit and len(items) >= args.limit:
            break
        items.append({
            "file_uid": r["id"],
            "filename": r.get("filename"),
            "folder": r.get("folder"),
            "file_type": r.get("kind"),
            "format": r.get("format"),
            "title": r.get("title"),
            "summary": two_sentences(r.get("description") or ""),
            "subjects": (r.get("keywords") or [])[:8],
            "date": r.get("date") or None,
            "size_kb": r.get("sizeKB"),
            "was_read": bool(r.get("body")),
            "pipeline_flags": r.get("flags") or [],
            "pipeline_rank": r.get("importance"),
            "pipeline_reason": r.get("rationale"),
        })

    packet = {
        "accession": args.accession,
        "accession_name": job.get("name"),
        "accession_status": job.get("status"),
        "provisional_identity": job.get("provisional", False),
        "intake_form": job.get("intake", {}),
        "folder_context": folders,
        "instructions": (
            "Apply docs/appraisal-rubric-v0.1.md to every item. Return a JSON "
            "array only — one object per item, no prose and no code fences. "
            "Every file_uid in this packet must appear exactly once in your "
            "answer."),
        "items": items,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(packet, indent=1, default=str))
    kb = out.stat().st_size / 1024
    print(f"wrote {out}  {len(items)} items, {len(folders)} folders, {kb:.0f} KB")
    described = sum(1 for i in items if i["summary"])
    print(f"  {described} of {len(items)} carry a summary; the rest give the "
          f"reviewer only a filename and folder, which is itself worth knowing")
    print("  Contains titles, summaries and folder names from real material. "
          "Do not publish.")
    return 0


def do_ingest(args) -> int:
    p = Path(args.payload)
    data = json.loads(p.read_text())
    raw = Path(args.decisions).read_text().strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        raw = raw[raw.find("["):] if "[" in raw else raw
    decisions = json.loads(raw)
    if isinstance(decisions, dict):
        decisions = decisions.get("decisions") or decisions.get("items") or []

    by_uid = {d.get("file_uid"): d for d in decisions if d.get("file_uid")}
    now = datetime.now().isoformat(timespec="seconds").replace("T", " ")
    applied, skipped = Counter(), Counter()

    for r in data.get("records", []):
        d = by_uid.get(r["id"])
        if not d:
            continue
        dec = d.get("decision")
        if dec not in VALID:
            skipped[f"invalid decision {dec!r}"] += 1
            continue
        r["dispo"] = dec
        r["decidedAt"] = now
        r["decidedBy"] = args.reviewer
        r["reviewSource"] = args.source
        r["reviewReason"] = d.get("reason")
        r["reviewCriterion"] = d.get("criterion")
        r["reviewConfidence"] = d.get("confidence")
        r.pop("autoApplied", None)          # a real decision replaces a proposal
        if d.get("by_association"):
            r["flags"] = list(dict.fromkeys(
                (r.get("flags") or []) + ["kept by association"]))
        if d.get("sensitivity"):
            r["flags"] = list(dict.fromkeys(
                (r.get("flags") or []) + [str(d["sensitivity"])]))
        # Did the reviewer confirm the pipeline or overrule it? This is the
        # question the decision record exists to answer.
        proposed = ("restricted_review" if r.get("importance") == "high"
                    else "selected")
        r["agreedWithPipeline"] = (dec == proposed)
        applied[dec] += 1

    p.write_text(json.dumps(data, default=str))
    total = sum(applied.values())
    print(f"applied {total} decisions from {len(by_uid)} returned")
    for k, v in applied.most_common():
        print(f"    {k:20s} {v:>6}")
    for k, v in skipped.most_common():
        print(f"    skipped: {k} ({v})")
    agreed = sum(1 for r in data["records"] if r.get("agreedWithPipeline") is True)
    over = sum(1 for r in data["records"] if r.get("agreedWithPipeline") is False)
    print(f"  {agreed} confirmed the pipeline, {over} overrode it")
    print(f"  recorded as: {args.reviewer}  (source: {args.source})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("export")
    e.add_argument("payload")
    e.add_argument("--accession", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--limit", type=int, default=0)
    e.set_defaults(fn=do_export)

    i = sub.add_parser("ingest")
    i.add_argument("payload")
    i.add_argument("--decisions", required=True)
    i.add_argument("--reviewer", required=True,
                   help="named on every decision. If a model stood in for a "
                        "person, say so here.")
    i.add_argument("--source", default="model-assisted, demonstration",
                   help="recorded alongside the name")
    i.set_defaults(fn=do_ingest)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
