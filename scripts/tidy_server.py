#!/usr/bin/env python3
"""
tidy_server.py — put the pipeline folder back into a shape someone can read.

    python3 scripts/tidy_server.py --dry-run
    python3 scripts/tidy_server.py

Six weeks of working at speed left the root full of zips, scratch text files,
duplicate copies of modules, and run directories nobody can date. Nothing here
deletes: everything moves into _archive/ with a note saying when and why, so a
file that turns out to matter can be recovered.

The problem worth fixing, specifically
--------------------------------------
Loose copies of modules at the root shadow the real ones in workbench/. Editing
the wrong copy and wondering why nothing changed has cost hours on this project
already. Those get moved first.

Run directories are kept
------------------------
runs/ holds manifests, redacted text and the PII vault. This script never
touches it — deciding which runs matter is an archival judgement about your own
work, and the same rule applies here as to the collections: the machine does not
dispose.
"""
from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path

# Where things belong.
ARCHIVE = Path("_archive")
KEEP_DIRS = {"workbench", "scripts", "web", "docs", "intake", "data", "runs",
             "demo", "review", "public", "_archive", ".git", ".ipynb_checkpoints"}

# Modules that live in workbench/ and must not also sit at the root.
MODULE_NAMES = {
    "accessions", "context", "estimate", "extract", "lanes", "mail", "ocr",
    "redaction", "relevance", "search", "serving", "stage01", "stage02a",
    "stage03", "stage04", "stage05", "stage06", "vision", "config", "intake",
}
SCRIPT_PREFIXES = ("run_", "export_", "prelabel", "review_packet",
                   "sanitise_", "estimate_accession", "sync_to_repo",
                   "decision_server", "tidy_server", "upload_validation")


def classify(p: Path) -> tuple[str, str] | None:
    """Return (destination, why) or None to leave it alone."""
    name = p.name
    stem = p.stem

    if p.is_dir():
        return None if name in KEEP_DIRS else ("archive/dirs", "stray directory")

    if p.suffix in (".zip", ".tgz", ".tar", ".gz"):
        return ("archive/packages", "delivered package, already extracted")
    if p.suffix in (".txt", ".log") and name not in ("requirements.txt",):
        return ("archive/scratch", "scratch output from a run")
    if p.suffix == ".py":
        if stem in MODULE_NAMES:
            return ("archive/duplicate_modules",
                    "a copy of workbench/%s.py — editing this one changes nothing" % stem)
        if any(stem.startswith(x) for x in SCRIPT_PREFIXES):
            return ("scripts", "belongs in scripts/")
        return ("archive/loose_py", "loose python at the root")
    if p.suffix in (".html", ".htm") and name != "index.html":
        return ("archive/old_web", "superseded interface build")
    if p.suffix == ".json" and stem.startswith("ACC-"):
        return ("intake", "intake form belongs in intake/")
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    moves: list[tuple[Path, Path, str]] = []

    for p in sorted(root.iterdir()):
        if p.name.startswith(".") and p.name != ".gitignore":
            continue
        out = classify(p)
        if not out:
            continue
        dest_dir, why = out
        dest = root / (dest_dir if not dest_dir.startswith("archive/")
                       else str(ARCHIVE / dest_dir.split("/", 1)[1]))
        moves.append((p, dest / p.name, why))

    if not moves:
        print("nothing to move — the folder is already tidy")
        return 0

    by_reason: dict[str, int] = {}
    for _, _, why in moves:
        by_reason[why.split(" —")[0]] = by_reason.get(why.split(" —")[0], 0) + 1

    print(f"{len(moves)} items to move:\n")
    for src, dest, why in moves:
        print(f"  {src.name}")
        print(f"      -> {dest.parent.relative_to(root)}/   ({why})")

    if args.dry_run:
        print("\ndry run — nothing moved")
        return 0

    log_lines = [f"# tidied {stamp}", ""]
    for src, dest, why in moves:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            dest = dest.with_name(f"{dest.stem}.{stamp.replace(' ', '_')}{dest.suffix}")
        shutil.move(str(src), str(dest))
        log_lines.append(f"{src.name} -> {dest.relative_to(root)}  ({why})")

    ARCHIVE.mkdir(exist_ok=True)
    with open(ARCHIVE / "MOVED.md", "a", encoding="utf-8") as fh:
        fh.write("\n".join(log_lines) + "\n\n")

    print(f"\nmoved {len(moves)} items. Nothing was deleted.")
    print(f"  record: {ARCHIVE / 'MOVED.md'}")
    print("  runs/, data/, demo/, intake/ and review/ were not touched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
