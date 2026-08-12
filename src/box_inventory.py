"""
box_inventory.py — build the manifest from Box metadata alone.

Walks a Box folder tree and records one row per file. Downloads nothing.
Box returns name, size, sha1, timestamps and the full folder path in the same
call that lists the folder, so stages 00-02 (inventory, dedupe, structural
filtering) can all run before a single byte is transferred.

Resumable: writes a checkpoint after every folder, so a restart picks up where
it stopped rather than re-crawling.

    python box_inventory.py --folder 318353711369 --out manifest/

Requires a .env with BOX_CLIENT_ID, BOX_CLIENT_SECRET, BOX_ENTERPRISE_ID.
See docs/setup/box-integration.md for how to get those and why the Service Account
must be collaborated onto the folder.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

# Ask for everything we need in the listing call itself. Requesting these up
# front is the difference between one API call per 1,000 files and one per file.
FIELDS = [
    "id", "type", "name", "size", "sha1", "extension",
    "created_at", "modified_at", "item_status", "path_collection",
]

PAGE = 1000          # Box maximum
CHECKPOINT_EVERY = 25   # folders


def client_from_env():
    """
    Two ways in, tried in order:

    1. BOX_DEVELOPER_TOKEN — a 60-minute token from the Developer Console that
       acts as *you*. Use this to test before the admin has authorized the app.
       No Service Account and no folder collaboration needed, because your own
       account already has access. Regenerate it when it expires.

    2. Client Credentials Grant — the Service Account. This is the real path,
       and it only works after a Box admin authorizes the app AND the folder has
       been collaborated to the generated Service Account.
    """
    from box_sdk_gen import BoxClient, BoxCCGAuth, BoxDeveloperTokenAuth, CCGConfig

    load_dotenv()

    token = os.getenv("BOX_DEVELOPER_TOKEN")
    if token:
        print("auth: developer token (expires ~60 min, acts as your own account)")
        return BoxClient(auth=BoxDeveloperTokenAuth(token=token))

    missing = [k for k in ("BOX_CLIENT_ID", "BOX_CLIENT_SECRET", "BOX_ENTERPRISE_ID")
               if not os.getenv(k)]
    if missing:
        sys.exit(
            f"Missing in .env: {', '.join(missing)}\n"
            "Either add those, or set BOX_DEVELOPER_TOKEN to test before the\n"
            "app has been authorized (Developer Console -> your app -> "
            "Developer Token -> Generate)."
        )

    print("auth: client credentials grant (Service Account)")
    auth = BoxCCGAuth(config=CCGConfig(
        client_id=os.environ["BOX_CLIENT_ID"],
        client_secret=os.environ["BOX_CLIENT_SECRET"],
        enterprise_id=os.environ["BOX_ENTERPRISE_ID"],
    ))
    return BoxClient(auth=auth)


def with_retry(fn, *args, tries=6, **kwargs):
    """Honour Box's Retry-After on 429, back off exponentially otherwise."""
    delay = 2.0
    for attempt in range(tries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            status = getattr(e, "status", None) or getattr(e, "status_code", None)
            if status == 429:
                hdrs = getattr(e, "headers", {}) or {}
                wait = float(hdrs.get("Retry-After", delay))
                print(f"    rate limited, waiting {wait:.0f}s")
            elif status is not None and 500 <= int(status) < 600:
                wait = delay
                print(f"    server error {status}, retrying in {wait:.0f}s")
            else:
                raise
            if attempt == tries - 1:
                raise
            time.sleep(wait)
            delay *= 2
    raise RuntimeError("unreachable")


def folder_path(item) -> str:
    """Reconstruct the human-readable path from Box's path_collection."""
    entries = getattr(getattr(item, "path_collection", None), "entries", None) or []
    parts = [e.name for e in entries if e.name != "All Files"]
    return "/".join(parts)


def crawl(client, root_id: str, out_dir: Path, resume: bool = True):
    out_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = out_dir / "_checkpoint.json"
    rows_path = out_dir / "box_inventory.parquet"

    queue = deque([root_id])
    seen_folders: set[str] = set()
    rows: list[dict] = []

    if resume and ckpt_path.exists():
        ck = json.loads(ckpt_path.read_text())
        queue = deque(ck["queue"])
        seen_folders = set(ck["seen"])
        if rows_path.exists():
            rows = pd.read_parquet(rows_path).to_dict("records")
        print(f"resuming: {len(rows):,} files already recorded, "
              f"{len(queue):,} folders still queued")

    folders_done = 0
    started = time.time()

    while queue:
        fid = queue.popleft()
        if fid in seen_folders:
            continue
        seen_folders.add(fid)

        marker, page_no = None, 0
        while True:
            resp = with_retry(
                client.folders.get_folder_items,
                fid, limit=PAGE, marker=marker, usemarker=True, fields=FIELDS,
            )
            for it in resp.entries:
                if it.type == "folder":
                    queue.append(it.id)
                elif it.type == "file":
                    rows.append({
                        "box_id": it.id,
                        "name": it.name,
                        "extension": (getattr(it, "extension", "") or "").lower(),
                        "size_bytes": getattr(it, "size", None),
                        "box_sha1": getattr(it, "sha1", None),
                        "created_at": getattr(it, "created_at", None),
                        "modified_at": getattr(it, "modified_at", None),
                        "item_status": getattr(it, "item_status", None),
                        "box_folder_id": fid,
                        "box_path": folder_path(it),
                        "full_path": f"{folder_path(it)}/{it.name}".lstrip("/"),
                        "inventoried_at": datetime.now(timezone.utc).isoformat(),
                    })
            marker = getattr(resp, "next_marker", None)
            page_no += 1
            if not marker:
                break

        folders_done += 1
        if folders_done % CHECKPOINT_EVERY == 0:
            save(rows, rows_path)
            ckpt_path.write_text(json.dumps(
                {"queue": list(queue), "seen": sorted(seen_folders)}))
            rate = len(rows) / max(time.time() - started, 1)
            print(f"  {folders_done:,} folders · {len(rows):,} files · "
                  f"{rate:,.0f} files/sec · {len(queue):,} queued")

    save(rows, rows_path)
    if ckpt_path.exists():
        ckpt_path.unlink()
    return pd.DataFrame(rows)


def save(rows, path: Path):
    if rows:
        pd.DataFrame(rows).to_parquet(path, index=False)


def summarise(df: pd.DataFrame):
    if df.empty:
        print("\nNo files found.")
        print("If the folder is not empty, the Service Account probably is not a")
        print("collaborator on it — see docs/setup/box-integration.md, 'the step everyone misses'.")
        return

    total = len(df)
    size = df["size_bytes"].fillna(0).sum()
    dupes = total - df["box_sha1"].nunique(dropna=True)
    archives = df["extension"].isin(["zip", "gz", "tar", "7z", "rar", "iso", "tgz"]).sum()
    empty = (df["size_bytes"].fillna(0) == 0).sum()

    print(f"\n{'='*58}\nINVENTORY\n{'='*58}")
    print(f"  files                {total:>12,}")
    print(f"  total size           {size/1e9:>12,.1f} GB")
    print(f"  distinct sha1        {df['box_sha1'].nunique(dropna=True):>12,}")
    print(f"  exact duplicates     {dupes:>12,}  ({dupes/total*100:.1f}%)")
    print(f"  zero-byte            {empty:>12,}")
    print(f"  archives to expand   {archives:>12,}")
    print(f"  distinct extensions  {df['extension'].nunique():>12,}")
    print(f"\n  top 15 extensions by count")
    for ext, n in df["extension"].value_counts().head(15).items():
        print(f"    {(ext or '(none)'):<14} {n:>10,}")
    print(f"\nNo files were downloaded. Run triage against this manifest,")
    print(f"then fetch only what survives.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", default=os.getenv("BOX_ROOT_FOLDER_ID", "0"))
    ap.add_argument("--out", default="manifest")
    ap.add_argument("--no-resume", action="store_true")
    a = ap.parse_args()

    print(f"Crawling Box folder {a.folder} — metadata only, no downloads.\n")
    df = crawl(client_from_env(), a.folder, Path(a.out), resume=not a.no_resume)
    summarise(df)
    print(f"\nManifest: {Path(a.out)/'box_inventory.parquet'}")


if __name__ == "__main__":
    main()
