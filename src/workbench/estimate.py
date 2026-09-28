"""
estimate.py — how long will this accession take, and what should be done first.

Two jobs. Learn per-lane rates from runs that have already happened, then apply
them to a folder nobody has processed yet, from nothing but a directory walk.

Why this matters to an archivist rather than to an engineer: a backlog is not
one queue, it is a set of accessions competing for the same evening. Knowing
that one is forty minutes and another is nine hours is what makes the choice
between them a decision rather than a guess.

Rates are learned, not asserted
-------------------------------
`learn()` reads run reports and derives seconds per file for each lane from what
actually happened on this hardware. Defaults exist for a first run, and they are
labelled as defaults so nobody mistakes them for measurements. Every estimate
says which rates it used and how many files those rates were derived from.

Nothing here reads file contents. It walks the tree, reads names and sizes, and
guesses the lane from the extension — which is exactly what the pipeline refuses
to do when it matters, and perfectly adequate for an estimate. A wrong lane
costs a few minutes of prediction error; the pipeline still identifies by
content when it runs.
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path

ESTIMATE_VERSION = "estimate-0.1.0"

# Seconds per file, CPU stages only, until real runs replace them. Measured on
# 4 vCPU Xeon Icelake over the September sample.
DEFAULT_CPU = {
    "image": 0.016, "email": 0.004, "document": 0.011, "tabular": 0.020,
    "av": 0.002, "archive": 0.002, "code": 0.002, "scientific": 0.002,
    "unroutable": 0.002,
}

# Seconds per file for the model stages. These dominate everything else by
# three orders of magnitude, which is the whole point of showing them
# separately: the CPU pass is free and the description pass is the cost.
DEFAULT_GPU = {
    "image": 162.0,      # LLaVA on Ollama, measured: 406 images overnight
    "document": 12.0,    # llama3.1:8b over extracted text
    "email": 9.0,
    "tabular": 14.0,
}

_EXT_LANE = {
    "jpg": "image", "jpeg": "image", "tif": "image", "tiff": "image",
    "png": "image", "gif": "image", "bmp": "image", "heic": "image",
    "eml": "email", "msg": "email", "mbox": "email", "pst": "email",
    "doc": "document", "docx": "document", "pdf": "document", "txt": "document",
    "rtf": "document", "ppt": "document", "pptx": "document", "odt": "document",
    "html": "document", "htm": "document", "wpd": "document",
    "xls": "tabular", "xlsx": "tabular", "csv": "tabular", "mdb": "tabular",
    "accdb": "tabular", "db": "tabular", "tsv": "tabular",
    "mov": "av", "mp4": "av", "avi": "av", "mp3": "av", "wav": "av",
    "zip": "archive", "tar": "archive", "gz": "archive", "rar": "archive",
    "py": "code", "c": "code", "f": "code", "m": "code", "r": "code",
}

# Formats with no text layer to extract. Large PDFs in this corpus are scans,
# and a scan costs OCR time the pipeline does not currently spend — so it is
# reported as unpriced work rather than folded into the total.
_SCAN_HINT_MB = 2.0


def learn(runs_dir: str | Path) -> dict:
    """
    Derive seconds per file per lane from completed runs.

    Reports carry a per-accession duration and a lane breakdown, not a per-lane
    duration, so a single-lane accession gives a clean rate and a mixed one
    gives a blended one. Only accessions where a single lane holds 80% or more
    of the files are used, because a blended rate attributed to one lane would
    be worse than the default it replaced.
    """
    seconds: dict[str, list[tuple[float, int]]] = defaultdict(list)
    runs = 0
    for report in sorted(Path(runs_dir).glob("*/run_report.json")):
        try:
            data = json.loads(report.read_text())
        except (ValueError, OSError):
            continue
        runs += 1
        for acc in (data.get("per_accession") or {}).values():
            secs = acc.get("seconds")
            lanes = ((acc.get("stage03") or {}).get("routing") or {}).get("by_lane")
            if not secs or not lanes:
                continue
            total = sum(lanes.values())
            if not total:
                continue
            lane, count = max(lanes.items(), key=lambda kv: kv[1])
            if count / total >= 0.8:
                seconds[lane].append((secs / total, total))

    rates, provenance = dict(DEFAULT_CPU), {}
    for lane, samples in seconds.items():
        files = sum(n for _, n in samples)
        rates[lane] = sum(r * n for r, n in samples) / files
        provenance[lane] = {"measured": True, "files": files,
                            "runs": len(samples)}
    for lane in rates:
        provenance.setdefault(lane, {"measured": False, "files": 0, "runs": 0})
    return {"cpu_seconds_per_file": rates, "provenance": provenance,
            "reports_read": runs}


def scan(root: str | Path, sample_bytes: bool = True) -> dict:
    """Walk a folder and count what is in it. Reads no file contents."""
    lanes: dict[str, int] = defaultdict(int)
    bytes_by_lane: dict[str, int] = defaultdict(int)
    exts: dict[str, int] = defaultdict(int)
    probable_scans = 0
    total = 0
    unknown_ext = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in
                       ("__pycache__", ".git", "node_modules", ".cache")]
        for name in filenames:
            p = Path(dirpath) / name
            ext = p.suffix.lower().lstrip(".")
            lane = _EXT_LANE.get(ext, "unroutable")
            if not ext:
                unknown_ext += 1
            exts[ext or "(none)"] += 1
            lanes[lane] += 1
            total += 1
            if sample_bytes:
                try:
                    size = p.stat().st_size
                except OSError:
                    size = 0
                bytes_by_lane[lane] += size
                if lane == "document" and ext == "pdf" and size > _SCAN_HINT_MB * 1e6:
                    probable_scans += 1

    return {"root": str(root), "files": total, "by_lane": dict(lanes),
            "bytes_by_lane": dict(bytes_by_lane),
            "extensions": dict(sorted(exts.items(), key=lambda kv: -kv[1])[:25]),
            "no_extension": unknown_ext, "probable_scans": probable_scans}


def estimate(counts: dict, rates: dict | None = None,
             describe: bool = True) -> dict:
    """
    Turn a scan into hours, split by what the time is actually spent on.

    CPU and model time are reported separately and never summed into one
    headline, because they are not interchangeable: the CPU pass runs whenever,
    and the model pass needs a card somebody else is using.
    """
    rates = rates or {"cpu_seconds_per_file": DEFAULT_CPU, "provenance": {}}
    cpu_rates = rates.get("cpu_seconds_per_file", DEFAULT_CPU)
    by_lane = counts.get("by_lane", {})

    cpu = sum(n * cpu_rates.get(lane, 0.005) for lane, n in by_lane.items())
    gpu_detail = {lane: round(n * DEFAULT_GPU[lane] / 3600, 2)
                  for lane, n in by_lane.items() if lane in DEFAULT_GPU}
    gpu = sum(gpu_detail.values()) if describe else 0.0

    warnings = []
    if counts.get("no_extension"):
        warnings.append(
            f"{counts['no_extension']} files have no extension. They are "
            f"estimated as unroutable, but the pipeline identifies by content "
            f"and may route them into a slower lane.")
    if counts.get("probable_scans"):
        warnings.append(
            f"{counts['probable_scans']} PDFs are large enough to be scans "
            f"rather than born-digital. Those have no text layer, and OCR is "
            f"not built — so they will be read as empty and this estimate does "
            f"not include the work of fixing that.")
    unmeasured = [l for l in by_lane
                  if not rates.get("provenance", {}).get(l, {}).get("measured")]
    if unmeasured:
        warnings.append(
            f"No measured rate for {', '.join(sorted(unmeasured))} — using "
            f"defaults. The estimate for those lanes is a guess with a number "
            f"attached to it.")

    return {
        "estimate_version": ESTIMATE_VERSION,
        "files": counts.get("files", 0),
        "cpu_hours": round(cpu / 3600, 3),
        "cpu_minutes": round(cpu / 60, 1),
        "describe_hours": round(gpu, 2),
        "describe_by_lane": gpu_detail,
        "gigabytes": round(sum(counts.get("bytes_by_lane", {}).values()) / 1e9, 2),
        "by_lane": by_lane,
        "warnings": warnings,
        "note": ("CPU and description time are not added together. The CPU pass "
                 "can run at any time; description needs the GPU, which is "
                 "shared."),
    }


def rank(estimates: dict[str, dict]) -> list[dict]:
    """
    Order accessions for an archivist choosing what to run tonight.

    Sorted by CPU cost, ascending — the cheapest first. That is deliberate: the
    CPU pass produces the routing, the exclusions, the rules and the ranking,
    which is most of what a person needs to decide anything. Getting three
    accessions triaged tonight is worth more than getting one described.
    """
    out = []
    for name, est in estimates.items():
        out.append({
            "accession": name,
            "files": est["files"],
            "cpu_minutes": est["cpu_minutes"],
            "describe_hours": est["describe_hours"],
            "gigabytes": est["gigabytes"],
            "warnings": len(est["warnings"]),
        })
    return sorted(out, key=lambda e: e["cpu_minutes"])
