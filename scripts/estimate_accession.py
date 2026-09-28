#!/usr/bin/env python3
"""
estimate_accession.py — how long will each of these take, before running any.

    python3 scripts/estimate_accession.py data/sample_1k/* --runs runs
    python3 scripts/estimate_accession.py /mnt/share/incoming/* --json

Walks each folder, learns per-lane rates from runs already completed, and
reports cost per accession ordered cheapest first. Reads no file contents and
touches nothing, so it is safe to point at material nobody has looked at yet.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from workbench import estimate as E


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folders", nargs="+")
    ap.add_argument("--runs", default="runs",
                    help="directory of completed runs to learn rates from")
    ap.add_argument("--no-describe", action="store_true",
                    help="cost the CPU pass only")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rates = E.learn(args.runs)
    measured = [l for l, p in rates["provenance"].items() if p["measured"]]

    estimates = {}
    for f in args.folders:
        p = Path(f)
        if not p.is_dir():
            continue
        estimates[p.name] = E.estimate(E.scan(p), rates,
                                       describe=not args.no_describe)

    if args.json:
        print(json.dumps({"rates": rates, "estimates": estimates}, indent=2))
        return 0

    print(f"Rates learned from {rates['reports_read']} run report(s).")
    print(f"  measured for: {', '.join(sorted(measured)) or 'nothing yet — all defaults'}")
    for lane in sorted(rates["cpu_seconds_per_file"]):
        pr = rates["provenance"].get(lane, {})
        if pr.get("measured"):
            print(f"    {lane:12s} {rates['cpu_seconds_per_file'][lane]*1000:6.1f} ms/file"
                  f"  from {pr['files']:,} files")
    print()

    for row in E.rank(estimates):
        est = estimates[row["accession"]]
        print(f"{row['accession']}")
        print(f"    {row['files']:>7,} files   {row['gigabytes']:>7.2f} GB")
        print(f"    CPU pass      {row['cpu_minutes']:>7.1f} min   "
              f"— routing, exclusions, rules, ranking")
        if row["describe_hours"]:
            parts = ", ".join(f"{k} {v}h" for k, v in
                              sorted(est["describe_by_lane"].items(),
                                     key=lambda kv: -kv[1]))
            print(f"    Description   {row['describe_hours']:>7.2f} h     — needs the GPU ({parts})")
        for w in est["warnings"]:
            print(f"    ! {w}")
        print()

    print("Ordered cheapest CPU pass first. That pass produces the routing, the "
          "exclusions, the rule outcomes and the ranking — most of what is "
          "needed to decide anything. Three accessions triaged is usually worth "
          "more than one described.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
