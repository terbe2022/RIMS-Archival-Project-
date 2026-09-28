#!/usr/bin/env python3
"""
prelabel.py — apply the pipeline's own proposals as decisions, so the export
has something to package when nobody has had time to review.

    python3 scripts/prelabel.py demo/aw/prototype-data.json

This is a demonstration convenience and it is labelled as one. Every decision it
writes carries `decidedBy: "auto-applied proposal — NOT reviewed by a person"`,
and the interface shows that rather than a name. A prototype that silently
presented machine proposals as human decisions would be lying about the one
property the whole design exists to protect.

What it will not decide
-----------------------
Anything routed to a supervising archivist, flagged sensitive, or carrying
detected identifiers is left undecided. Those are exactly the files the system
is built to put in front of a person, and auto-deciding them to make a demo
tidier would invert the point of it.

Files nothing was read from are also left alone: a proposal about a file with no
extracted content is not a proposal, it is a guess about a filename.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

STAMP = "auto-applied proposal — NOT reviewed by a person"

# importance band -> what the pipeline would propose
PROPOSAL = {"high": "selected", "medium": "selected", "low": "not_selected"}

HOLD_FLAGS = ("needs a person", "identifier", "sensitive", "restricted")


def holds(rec: dict) -> str | None:
    """Reasons never to auto-decide. Returns the reason, or None."""
    flags = [str(f).lower() for f in rec.get("flags") or []]
    if rec.get("dispo") == "restricted_review":
        return "already routed to a supervising archivist"
    if any(h in f for f in flags for h in HOLD_FLAGS):
        return "flagged for a person"
    if rec.get("importance") == "high" and not rec.get("body"):
        return "ranked high but nothing was read from it"
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("payload", help="prototype-data.json to label in place")
    ap.add_argument("--accession", help="limit to one accession id")
    ap.add_argument("--only-read", action="store_true",
                    help="decide only files the pipeline actually read")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    p = Path(args.payload)
    data = json.loads(p.read_text())
    now = datetime.now().isoformat(timespec="seconds").replace("T", " ")

    applied, held = Counter(), Counter()
    for rec in data.get("records", []):
        if args.accession and rec.get("jobId") != args.accession:
            continue
        if rec.get("dispo") and rec.get("decidedBy") != STAMP:
            continue                      # a real decision is never overwritten
        reason = holds(rec)
        if reason:
            held[reason] += 1
            continue
        if args.only_read and not rec.get("body"):
            held["nothing was read from it"] += 1
            continue
        d = PROPOSAL.get(rec.get("importance"), "not_selected")
        if not args.dry_run:
            rec["dispo"] = d
            rec["decidedAt"] = now
            rec["decidedBy"] = STAMP
            rec["autoApplied"] = True
        applied[d] += 1

    total = sum(applied.values()) + sum(held.values())
    print(f"{total} records considered")
    print("  applied:")
    for k, v in applied.most_common():
        print(f"    {k:20s} {v:>6}")
    print("  left for a person:")
    for k, v in held.most_common():
        print(f"    {k:40s} {v:>6}")

    if args.dry_run:
        print("\ndry run — nothing written")
        return 0

    p.write_text(json.dumps(data, default=str))
    print(f"\nwrote {p}")
    print("Every applied decision is stamped as unreviewed. The interface shows "
          "that stamp instead of a reviewer name, and the decision export "
          "records it, so nothing here can be mistaken for archival judgement.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
