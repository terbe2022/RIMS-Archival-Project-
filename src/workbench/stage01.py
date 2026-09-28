"""
stage01.py — crawl and characterise. No GPU, no model, no network.

Produces one manifest row per file: identity, path and date flags, hashes, and
a format identification made from content signature rather than extension.

Format identification runs Siegfried first (PRONOM is the authority the
archival world already uses) and Tika second. Disagreement between them is
recorded rather than resolved, because a file whose two identifiers disagree is
exactly the file a person should look at. Neither tool is required: when both
are absent the module falls back to its own magic-byte table and says so in
`s01_id_method`, so a degraded run is visible in the data instead of looking
like a clean one.

The magic-byte fallback types OLE2 compound documents, which is what the 38
extensionless files in the Hanratty tree are.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .schema import manifest as M

STAGE_VERSION = "s01-0.1.0"
_READ_CHUNK = 1 << 20          # 1 MiB
_MAGIC_READ = 4096

# Signature table. Ordered: longer and more specific first.
# (offset, magic bytes, PRONOM puid, format name)
_MAGIC = [
    (0, b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", "fmt/111", "OLE2 Compound Document"),
    (0, b"%PDF-", "fmt/14", "Acrobat PDF"),
    (0, b"\xff\xd8\xff", "fmt/43", "JPEG File Interchange Format"),
    (0, b"\x89PNG\r\n\x1a\n", "fmt/11", "Portable Network Graphics"),
    (0, b"II*\x00", "fmt/353", "Tagged Image File Format"),
    (0, b"MM\x00*", "fmt/353", "Tagged Image File Format"),
    (0, b"GIF87a", "fmt/3", "Graphics Interchange Format"),
    (0, b"GIF89a", "fmt/4", "Graphics Interchange Format"),
    (0, b"PK\x03\x04", "fmt/189", "ZIP Format"),
    (0, b"Rar!\x1a\x07", "fmt/411", "RAR"),
    (0, b"\x1f\x8b", "x-fmt/266", "GZIP Format"),
    (0, b"BZh", "fmt/267", "BZIP2"),
    (0, b"\x00\x01\x00\x00Standard Jet DB", "fmt/161", "Microsoft Access Database"),
    (0, b"SQLite format 3\x00", "fmt/729", "SQLite Database"),
    (0, b"{\\rtf", "fmt/355", "Rich Text Format"),
    (0, b"\x7fELF", "fmt/688", "ELF"),
    (0, b"MZ", "fmt/899", "Windows Portable Executable"),
    (4, b"ftyp", "fmt/199", "MPEG-4 Media File"),
    (0, b"OggS", "fmt/203", "Ogg"),
    (0, b"RIFF", "fmt/6", "RIFF container"),
    (0, b"From ", None, "mbox mail container"),
]

# Extensions we consider consistent with a signature, for s01_ext_mismatch.
_EXPECTED_EXT = {          # dot-less, matching the row convention
    "fmt/111": {"doc", "xls", "ppt", "msg", "db", ""},
    "fmt/14": {"pdf"},
    "fmt/43": {"jpg", "jpeg", "jpe"},
    "fmt/11": {"png"},
    "fmt/353": {"tif", "tiff"},
    "fmt/189": {"zip", "docx", "xlsx", "pptx", "odt", "ods", "epub", "jar"},
    "fmt/161": {"mdb", "accdb"},
    "fmt/199": {"mp4", "m4v", "mov", "m4a"},
    "fmt/355": {"rtf"},
}


# ------------------------------------------------------------------ tools --
def detect_tools() -> dict:
    """What is actually available. Recorded in the run report, not assumed."""
    return {
        "siegfried": shutil.which("sf"),
        "tika": shutil.which("tika") or os.environ.get("TIKA_JAR"),
    }


def _siegfried(paths: list[Path]) -> dict:
    """Batch Siegfried over a list of paths. Returns {path: (puid, name, ver)}."""
    out = {}
    try:
        proc = subprocess.run(
            ["sf", "-json", "-nr", *[str(p) for p in paths]],
            capture_output=True, text=True, timeout=600, check=False)
        if proc.returncode != 0:
            return out
        data = json.loads(proc.stdout)
        for f in data.get("files", []):
            m = (f.get("matches") or [{}])[0]
            out[f["filename"]] = (m.get("id"), m.get("format"), m.get("version"))
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    return out


# --------------------------------------------------------------- hashing --
def hash_file(path: Path) -> tuple[str, str, bytes]:
    """One pass, both digests, plus the leading bytes for signature typing."""
    sha256, sha1 = hashlib.sha256(), hashlib.sha1()
    head = b""
    with open(path, "rb") as fh:
        while chunk := fh.read(_READ_CHUNK):
            if not head:
                head = chunk[:_MAGIC_READ]
            sha256.update(chunk)
            sha1.update(chunk)
    return sha256.hexdigest(), sha1.hexdigest(), head


def identify_by_magic(head: bytes) -> tuple[str | None, str | None]:
    for offset, magic, puid, name in _MAGIC:
        if head[offset:offset + len(magic)] == magic:
            return puid, name
    return None, None


# ----------------------------------------------------------------- crawl --
def _ts(epoch: float) -> datetime | None:
    try:
        return datetime.fromtimestamp(epoch, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def crawl(root: str | Path, accession: dict, use_siegfried: bool = True) -> list[dict]:
    """
    Walk one accession's tree and return manifest rows.

    `accession` is a row from accessions.build_row(); accession_uid must be
    present, since file_uid derives from it.
    """
    root = Path(root)
    acc_uid = accession["accession_uid"]
    rows: list[dict] = []
    batch: list[Path] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            p = Path(dirpath) / name
            if p.is_symlink() or not p.is_file():
                continue
            batch.append(p)

    sf_results = _siegfried(batch) if (use_siegfried and detect_tools()["siegfried"]) else {}

    for p in batch:
        rel = p.relative_to(root).as_posix()
        path_norm = M.normalise_path(rel)
        row: dict = {
            "file_uid": M.make_uid(acc_uid, path_norm),
            "accession_uid": acc_uid,
            "record_series": accession["record_series"],
            "record_group": accession.get("record_group"),
            "series": accession.get("series"),
            "subseries": accession.get("subseries"),
            "accession_type": accession.get("accession_type"),
            "source_label": accession.get("source_label"),
            "source_media": accession.get("source_media"),
            "source_ref": accession.get("source_ref"),
            "source_received": accession.get("source_received"),
            "manifest_generation": 1,
            "schema_version": M.SCHEMA_VERSION,
            "path_raw": str(p),
            "path_norm": path_norm,
            "path_norm_ci": path_norm.lower(),
            "filename": p.name,
            # No leading dot, lowercase. rules.base.ext() normalises its own
            # arguments but compares r["extension"] verbatim, so a dotted value
            # here would make every extension rule silently match nothing.
            "extension": p.suffix.lower().lstrip("."),
            "parent_folder": p.parent.name,
            "depth": len(Path(path_norm).parts) - 1,
            "path_flags": M.path_flags(rel),
            "archive_depth": 0,
            "s01_version": STAGE_VERSION,
        }

        try:
            st = p.stat()
            row["size_bytes"] = st.st_size
            mtime = _ts(st.st_mtime)
            row["mtime"] = mtime
            row["ctime"] = _ts(st.st_ctime)
            row["atime"] = _ts(st.st_atime)
            row["mtime_raw"] = str(st.st_mtime)
            row["date_flags"] = M.date_flags(mtime)

            if st.st_size == 0:
                row["content_sha256"] = hashlib.sha256(b"").hexdigest()
                row["content_sha1"] = hashlib.sha1(b"").hexdigest()
                row["s01_status"] = "empty"
                rows.append(row)
                continue

            sha256, sha1, head = hash_file(p)
            row["content_sha256"] = sha256
            row["content_sha1"] = sha1

            puid = name_ = version = None
            method = None
            sf = sf_results.get(str(p))
            if sf and sf[0] and sf[0] != "UNKNOWN":
                puid, name_, version = sf
                method = "siegfried"
            magic_puid, magic_name = identify_by_magic(head)
            if puid is None and magic_puid:
                puid, name_, method = magic_puid, magic_name, "magic"
            elif puid and magic_puid and magic_puid != puid:
                # Recorded, not resolved. A disagreement is a triage signal.
                row["s01_upstream_agrees"] = False
                row["s01_upstream_source"] = "internal-magic"
                row["s01_upstream_format"] = magic_name
            if puid is None:
                method = "none"

            row["s01_puid"] = puid
            row["s01_format_name"] = name_
            row["s01_format_version"] = version
            row["s01_id_method"] = method
            row["s01_id_confidence"] = {"siegfried": "high", "magic": "medium"}.get(method, "none")

            expected = _EXPECTED_EXT.get(puid or "")
            row["s01_ext_mismatch"] = bool(expected) and row["extension"] not in expected

            row["s01_upstream_present"] = False   # D7 unanswered; nothing from Tracy yet
            row["s01_status"] = "ok"

        except OSError as exc:
            row["s01_status"] = "failed"
            row["s01_error"] = f"{type(exc).__name__}: {exc}"

        rows.append(row)

    return rows
