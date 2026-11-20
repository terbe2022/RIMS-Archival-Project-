"""Generate very large stress-test files on demand (not committed to Git).

    python3 generator/make_large_files.py --size-gb 2      # writes corpus/Achterberg_Desktop/LabDrive_BIG/

Files land inside the accession so a pipeline run over the folder meets them in
place; labels/large_files_labels.jsonl records their ground truth. The folder is
git-ignored. Sizes scale with --size-gb (per file, approximate).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT, ROOT_NAME, LABELS, SITES, sha256  # noqa: E402

BIG = "Documents/Research/Prairie_Bee_Survey/LabDrive_BIG"


def big_csv(path: Path, target: int):
    rng = np.random.default_rng(1)
    with open(path, "w") as fh:
        fh.write("site,timestamp,temp_c,rh_pct,par_umol,soil_moist,logger_id\n")
        t0 = np.datetime64("2016-01-01T00:00:00")
        sec = 0
        while fh.tell() < target:
            n = 200_000
            ts = (t0 + (np.arange(sec, sec + n) * 10).astype("timedelta64[s]")).astype(str)
            site = SITES[(sec // n) % len(SITES)][0]
            temp = rng.normal(20, 6, n); rh = rng.normal(65, 12, n); par = np.abs(rng.normal(800, 500, n)); sm = rng.uniform(.05, .45, n)
            fh.writelines(f"{site},{a},{b:.2f},{c:.1f},{d:.0f},{e:.3f},HOBO-{site}-02\n" for a, b, c, d, e in zip(ts, temp, rh, par, sm))
            sec += n


def big_tiff(path: Path, target: int):
    side = int((target / 3) ** .5)
    w, h = side * 3 // 2, side * 2 // 3
    rng = np.random.default_rng(2)
    arr = np.empty((h, w, 3), np.uint8)
    for y0 in range(0, h, 1024):
        y1 = min(h, y0 + 1024)
        base = np.linspace(60, 140, w, dtype=np.float32)[None, :, None]
        arr[y0:y1] = np.clip(base + rng.normal(0, 25, (y1 - y0, w, 3)), 0, 255).astype(np.uint8)
    Image.MAX_IMAGE_PIXELS = None
    Image.fromarray(arr).save(path, "TIFF")


def big_video(path: Path, target: int):
    seconds = max(60, int(target / (8_000_000 / 8)))     # ~8 Mbit/s
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"testsrc2=size=1920x1080:rate=30:duration={seconds}",
                    "-f", "lavfi", "-i", f"sine=frequency=300:duration={seconds}", "-c:v", "libx264", "-b:v", "8M",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(path)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size-gb", type=float, default=1.0)
    ap.add_argument("--only", choices=["csv", "tiff", "video"], nargs="*")
    a = ap.parse_args()
    target = int(a.size_gb * (1 << 30))
    out = ROOT / BIG
    out.mkdir(parents=True, exist_ok=True)
    jobs = {
        "csv": ("HOBO_10s_all_sites_2016-2022_FULL.csv", big_csv, "tabular", "text/csv (very large)",
                "Full-resolution microclimate logger export (10-second interval, all sites, 2016-2022)",
                "Very large CSV of temperature, humidity, light and soil moisture logged every 10 seconds at all survey sites; requires streaming and sampling."),
        "tiff": ("BRF_orthomosaic_2022_full_res.tif", big_tiff, "image", "tiff (uncompressed, very large)",
                 "Full-resolution drone orthomosaic of the remnant (2022)",
                 "Very large uncompressed orthomosaic raster of the remnant prairie; must be downsampled or tiled before any vision model."),
        "video": ("GoPro_transect_walk_2022-07-01.mp4", big_video, "av", "mp4 (1080p30, long)",
                  "Long GoPro transect walk video (2022)",
                  "Long 1080p video of a transect walk (test-pattern content with tone); requires keyframe sampling rather than full decoding."),
    }
    labels = []
    for key, (name, fn, lane, fmt, title, summary) in jobs.items():
        if a.only and key not in a.only:
            continue
        p = out / name
        print(f"writing {p} (~{a.size_gb} GB) ...", flush=True)
        fn(p, target)
        labels.append({"path": f"{ROOT_NAME}/{BIG}/{name}", "relevance": "high",
                       "relevance_rationale": "Original research data / field recordings of survey sites (stress-test scale)",
                       "sensitivity": ["sensitive_location"] if "BRF" in name else ["none"], "lane": lane,
                       "expected_action": "appraise", "gt_title": title, "gt_summary": summary,
                       "gt_keywords": ["large file", "downsampling", "streaming"], "tags": ["large_file", "on_demand"],
                       "true_format": fmt, "extension": p.suffix, "size_bytes": p.stat().st_size, "sha256": sha256(p),
                       "nominal_date": "2022-07-01", "container": "", "duplicate_of": "", "difficulty": "subtle"})
    LABELS.mkdir(exist_ok=True)
    with open(LABELS / "large_files_labels.jsonl", "w") as fh:
        for l in labels:
            fh.write(json.dumps(l) + "\n")
    print("done; labels in labels/large_files_labels.jsonl")


if __name__ == "__main__":
    main()
