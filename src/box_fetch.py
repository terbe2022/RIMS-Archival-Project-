"""
box_fetch.py — download only the files triage selected, and expand archives safely.

Reads the manifest produced by box_inventory.py, takes the rows where
`selected == True`, downloads them with retry and resume, verifies against Box's
sha1, computes SHA-256 locally, and expands any archives into child manifest rows.

    python box_fetch.py --manifest manifest/box_inventory.parquet --dest data/raw
    python box_fetch.py --manifest ... --limit 200        # try a slice first

Never re-downloads a file that is already present and verifies.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import tarfile
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from box_inventory import client_from_env, with_retry

ARCHIVE_EXTS = {"zip", "tar", "gz", "tgz", "7z", "rar", "iso"}

# Guards for untrusted archives — these are not theoretical on drives of
# unknown provenance.
MAX_EXPANDED_BYTES = 20 * 1024**3    # 20 GB out of any single archive
MAX_EXPANSION_RATIO = 200            # compressed:uncompressed
MAX_DEPTH = 3                        # nested archives


def sha256_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def sha1_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def safe_join(root: Path, member: str) -> Path | None:
    """Reject archive members that escape the extraction root."""
    target = (root / member).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return None
    return target


def expand_archive(path: Path, dest: Path, depth: int = 0) -> tuple[list[dict], str]:
    """Expand one archive. Returns (child rows, status)."""
    if depth >= MAX_DEPTH:
        return [], "depth_limit"

    dest.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    comp = path.stat().st_size or 1

    try:
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as z:
                if any(i.flag_bits & 0x1 for i in z.infolist()):
                    return [], "password_protected"
                total = sum(i.file_size for i in z.infolist())
                if total > MAX_EXPANDED_BYTES or total / comp > MAX_EXPANSION_RATIO:
                    return [], "expansion_guard"
                for info in z.infolist():
                    if info.is_dir():
                        continue
                    out = safe_join(dest, info.filename)
                    if out is None:
                        rows.append({"virtual_path": info.filename,
                                     "status": "path_traversal_blocked"})
                        continue
                    out.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(info) as src, out.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
                    rows.append(child_row(out, path, info.filename, depth))

        elif tarfile.is_tarfile(path):
            with tarfile.open(path) as t:
                members = [m for m in t.getmembers() if m.isfile()]
                total = sum(m.size for m in members)
                if total > MAX_EXPANDED_BYTES or total / comp > MAX_EXPANSION_RATIO:
                    return [], "expansion_guard"
                for m in members:
                    out = safe_join(dest, m.name)
                    if out is None:
                        rows.append({"virtual_path": m.name,
                                     "status": "path_traversal_blocked"})
                        continue
                    out.parent.mkdir(parents=True, exist_ok=True)
                    src = t.extractfile(m)
                    if src is None:
                        continue
                    with src, out.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
                    rows.append(child_row(out, path, m.name, depth))
        else:
            return [], "unsupported_archive"     # 7z / rar need py7zr / rarfile

    except Exception as e:
        return [], f"expand_error:{type(e).__name__}"

    # recurse into nested archives
    nested = [r for r in rows
              if r.get("extension") in ARCHIVE_EXTS and r.get("local_path")]
    for r in nested:
        inner = Path(r["local_path"])
        kids, st = expand_archive(inner, inner.parent / f"{inner.stem}__expanded", depth + 1)
        r["status"] = st
        rows.extend(kids)

    return rows, "expanded"


def child_row(out: Path, container: Path, member: str, depth: int) -> dict:
    return {
        "local_path": str(out),
        "name": out.name,
        "extension": out.suffix.lstrip(".").lower(),
        "size_bytes": out.stat().st_size,
        "sha256": sha256_of(out),
        "parent_archive": container.name,
        "virtual_path": f"{container.name}!/{member}",
        "archive_depth": depth + 1,
        "status": "ok",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def fetch_one(client, row: dict, dest_root: Path) -> dict:
    rel = row.get("box_path") or ""
    out = dest_root / rel / row["name"]
    out.parent.mkdir(parents=True, exist_ok=True)

    # already have it and it verifies? skip.
    if out.exists() and row.get("box_sha1"):
        if sha1_of(out) == row["box_sha1"]:
            return {**row, "local_path": str(out), "status": "already_present",
                    "sha256": sha256_of(out)}

    try:
        stream = with_retry(client.downloads.download_file, row["box_id"])
        with out.open("wb") as f:
            shutil.copyfileobj(stream, f)
    except Exception as e:
        return {**row, "status": f"download_error:{type(e).__name__}"}

    got = sha1_of(out)
    if row.get("box_sha1") and got != row["box_sha1"]:
        return {**row, "local_path": str(out), "status": "sha1_mismatch"}

    return {**row, "local_path": str(out), "sha256": sha256_of(out),
            "status": "ok", "fetched_at": datetime.now(timezone.utc).isoformat()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--dest", default="data/raw")
    ap.add_argument("--workers", type=int, default=6,
                    help="concurrent downloads; >8 trips Box rate limits for no gain")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--no-expand", action="store_true")
    a = ap.parse_args()

    df = pd.read_parquet(a.manifest)
    if "selected" in df.columns:
        todo = df[df["selected"] == True]                          # noqa: E712
    else:
        print("No 'selected' column — triage has not run yet.")
        print("Fetching everything is usually the wrong move; use --limit to sample.")
        todo = df
    if a.limit:
        todo = todo.head(a.limit)

    dest = Path(a.dest)
    dest.mkdir(parents=True, exist_ok=True)
    rows = todo.to_dict("records")
    print(f"Fetching {len(rows):,} of {len(df):,} files "
          f"({len(rows)/max(len(df),1)*100:.1f}%) with {a.workers} workers\n")

    client = client_from_env()
    results, done, started = [], 0, time.time()

    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futures = {pool.submit(fetch_one, client, r, dest): r for r in rows}
        for fut in as_completed(futures):
            results.append(fut.result())
            done += 1
            if done % 50 == 0:
                rate = done / max(time.time() - started, 1)
                print(f"  {done:,}/{len(rows):,} · {rate:.1f} files/sec")

    out_df = pd.DataFrame(results)

    if not a.no_expand:
        archives = [r for r in results
                    if r.get("status") in ("ok", "already_present")
                    and (r.get("extension") or "").lower() in ARCHIVE_EXTS]
        if archives:
            print(f"\nExpanding {len(archives):,} archives")
            kids = []
            for r in archives:
                p = Path(r["local_path"])
                ch, st = expand_archive(p, p.parent / f"{p.stem}__expanded")
                r["status"] = st
                kids.extend(ch)
                print(f"  {p.name}: {st}, {len(ch):,} files")
            if kids:
                out_df = pd.concat([out_df, pd.DataFrame(kids)], ignore_index=True)

    out_path = Path(a.manifest).with_name("fetched.parquet")
    out_df.to_parquet(out_path, index=False)

    print(f"\n{'='*54}")
    for status, n in out_df["status"].value_counts().items():
        print(f"  {status:<32} {n:>8,}")
    print(f"{'='*54}\nWrote {out_path}")


if __name__ == "__main__":
    main()
