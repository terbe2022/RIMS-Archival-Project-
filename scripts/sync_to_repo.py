#!/usr/bin/env python3
"""
sync_to_repo.py — put the current server code into the repository.

    # see what would move, change nothing
    python3 scripts/sync_to_repo.py --dry-run

    # stage it, and build the public demonstration payload too
    python3 scripts/sync_to_repo.py --repo ~/RIMS-Archival-Project- --public

Manual copying is how the repository fell six weeks behind the server. This
copies what belongs in version control and nothing else, and it decides that by
an allow-list rather than by excluding things one at a time.

Why an allow-list
-----------------
A deny-list fails open. Forget one pattern and a manifest, a mailbox or a PII
vault is in a public repository forever, because git keeps history. An
allow-list fails closed: a new kind of file is not copied until someone decides
it should be. That asymmetry is the whole argument, and it is why this script
will refuse to copy a file type it has never seen rather than guess.

Every copy is also checked for content that should never leave, regardless of
which folder it came from.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

# What belongs in the repository, as (source glob, destination directory).
INCLUDE = [
    ("workbench/*.py", "src/workbench"),
    ("workbench/schema/*.py", "src/schema"),
    ("workbench/schema/rules/*.py", "src/schema/rules"),
    ("scripts/*.py", "scripts"),
    ("web/accession-workbench.html", "web"),
    ("docs/*.md", "docs"),
    ("intake/accession_registry.json", "intake"),
]

# Never copied, even from an included folder.
NEVER = re.compile(
    r"(^|/)(runs|data|demo|state|logs|_archive|review|public|__pycache__)/"
    r"|\.(parquet|jsonl|eml|mbox|pst|tgz|zip|log)$"
    r"|pii_map|prototype-data|review-data|workbench-data"
    r"|^intake/ACC-",
    re.I)

# Content that must not reach a public repository, checked per file.
LEAKS = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "something shaped like an SSN"),
    (re.compile(r"(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*\S{6,}", re.I),
     "a credential"),
    (re.compile(r"/var/advanalytics/[\w/.-]*(uploads|datashare/[A-Z])", re.I),
     "an absolute share path"),
]


def leaks_in(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    found = []
    for pattern, label in LEAKS:
        m = pattern.search(text)
        if m:
            found.append(f"{label} at line {text[:m.start()].count(chr(10)) + 1}")
    return found


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path.home() / "RIMS-Archival-Project-"),
                    help="a clone of the repository")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--public", action="store_true",
                    help="also build docs/ from the sanitised payload")
    ap.add_argument("--payload", default="demo/aw/prototype-data.json")
    ap.add_argument("--force", action="store_true",
                    help="copy even if a leak check fails. Think first.")
    args = ap.parse_args()

    repo = Path(args.repo)
    if not (repo / ".git").exists():
        print(f"{repo} is not a git clone.\n"
              f"  git clone https://github.com/terbe2022/RIMS-Archival-Project-.git "
              f"{repo}", file=sys.stderr)
        return 2

    copied, skipped, blocked, unchanged = [], [], [], []

    for pattern, dest_dir in INCLUDE:
        for src in sorted(Path(".").glob(pattern)):
            rel = src.as_posix()
            if NEVER.search(rel) or src.name.startswith("."):
                skipped.append(rel)
                continue
            problems = leaks_in(src)
            if problems and not args.force:
                blocked.append((rel, "; ".join(problems)))
                continue
            dest = repo / dest_dir / src.name
            if dest.exists() and digest(dest) == digest(src):
                unchanged.append(rel)
                continue
            if not args.dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
            copied.append(f"{rel} -> {dest_dir}/{src.name}")

    if args.public:
        payload = Path(args.payload)
        if not payload.exists():
            print(f"  no payload at {payload}; skipping the public build")
        else:
            out = repo / "docs" / "prototype-data.json"
            cmd = [sys.executable, "scripts/sanitise_payload.py", str(payload),
                   "--out", str(out)]
            if args.dry_run:
                print("  would run: " + " ".join(cmd))
            else:
                rc = subprocess.call(cmd)
                if rc == 0:
                    shutil.copy2("web/accession-workbench.html",
                                 repo / "docs" / "accession-workbench.html")
                    copied.append("web/accession-workbench.html -> docs/ (public)")
                else:
                    print("  sanitiser refused; the public build was NOT updated",
                          file=sys.stderr)

    print(f"\n{len(copied)} to copy, {len(unchanged)} unchanged, "
          f"{len(skipped)} excluded by rule, {len(blocked)} blocked on content")
    for c in copied:
        print(f"  + {c}")
    for rel, why in blocked:
        print(f"  ! {rel}: {why}")
    if blocked:
        print("\nBlocked files were NOT copied. Look at each one — the check is "
              "crude and a false positive is possible, but a credential or an "
              "identifier in a public repository is permanent.")

    if args.dry_run:
        print("\ndry run — nothing written")
        return 0
    if copied:
        print(f"\nNext:\n  cd {repo}\n  git status --short\n"
              f"  git add -A && git commit -m 'Sync pipeline from the server'\n"
              f"  git push")
    return 1 if blocked and not args.force else 0


if __name__ == "__main__":
    raise SystemExit(main())
