"""Build the synthetic accessions and their ground-truth labels.

    python3 generator/build.py            # rebuilds every accession
    python3 generator/build.py 001        # just ACC-SYN-2026-001 (+ its alternate-form labels)
    python3 generator/build.py 002        # just ACC-SYN-2026-002

Deterministic: same seed -> same content. (Office/PDF/media containers embed
creation timestamps, so byte hashes can differ between rebuilds even though the
content is identical; labels are regenerated with the corpus.)
"""
from __future__ import annotations

import collections
import csv
import json
import shutil
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import CORPUS, LABELS, Registry  # noqa: E402

FIELDS = ["path", "relevance", "relevance_rationale", "sensitivity", "lane", "expected_action",
          "gt_title", "gt_summary", "gt_keywords", "tags", "true_format", "extension", "size_bytes",
          "sha256", "nominal_date", "container", "duplicate_of", "difficulty"]


def write_labels(reg: Registry, accession: str) -> Path:
    reg.finalise()
    on_disk = {str(p.relative_to(CORPUS)) for p in reg.root.rglob("*") if p.is_file() or p.is_symlink()}
    labelled = {k for k, v in reg.labels.items() if not v.container}
    missing, extra = on_disk - labelled, labelled - on_disk
    if missing or extra:
        raise SystemExit(f"label mismatch\n missing labels: {sorted(missing)}\n labels without files: {sorted(extra)}")

    out = LABELS / accession
    out.mkdir(parents=True, exist_ok=True)
    rows = [asdict(l) for l in sorted(reg.labels.values(), key=lambda l: l.path)]
    with open(out / "ground_truth.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(out / "ground_truth.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, FIELDS); w.writeheader()
        for r in rows:
            r = dict(r)
            for k in ("sensitivity", "gt_keywords", "tags"):
                r[k] = ";".join(r[k])
            w.writerow(r)
    folders = sorted(reg.folders.values(), key=lambda f: f["folder"])
    with open(out / "folder_labels.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, ["folder", "dominant_relevance", "gt_summary"]); w.writeheader(); w.writerows(folders)

    top = [r for r in rows if not r["container"]]
    stats = {
        "accession": accession,
        "corpus_root": reg.root_name,
        "files_on_disk": len(top),
        "archive_or_mailbox_members_labelled": len(rows) - len(top),
        "total_bytes_on_disk": sum(r["size_bytes"] for r in top),
        "by_relevance": collections.Counter(r["relevance"] for r in top),
        "by_lane": collections.Counter(r["lane"] for r in top),
        "by_expected_action": collections.Counter(r["expected_action"] for r in top),
        "by_difficulty": collections.Counter(r["difficulty"] for r in top),
        "by_sensitivity": collections.Counter(s for r in top for s in r["sensitivity"]),
        "by_extension": collections.Counter(r["extension"] or "(none)" for r in top),
        "by_tag": collections.Counter(t for r in rows for t in r["tags"]),
        "folders_labelled": len(folders),
    }
    (out / "summary_stats.json").write_text(json.dumps(stats, indent=2))
    print(json.dumps({k: stats[k] for k in ("accession", "files_on_disk", "by_relevance", "by_difficulty")}, indent=1))
    return out


def build_001():
    from common import reg, ROOT
    import gen_emails, gen_docs, gen_data, gen_media, gen_edge, gen_more, alt_intake
    if ROOT.exists():
        shutil.rmtree(ROOT)
    ROOT.mkdir(parents=True)
    for mod in (gen_emails, gen_docs, gen_data, gen_media, gen_more, gen_edge):
        print(f"[001] building {mod.__name__} ...", flush=True)
        mod.run()
    out = write_labels(reg, "ACC-SYN-2026-001")
    alt_intake.write(reg, out)


def build_002():
    import acc002
    reg2 = acc002.reg
    if reg2.root.exists():
        shutil.rmtree(reg2.root)
    reg2.root.mkdir(parents=True)
    print("[002] building acc002 ...", flush=True)
    acc002.run()
    write_labels(reg2, "ACC-SYN-2026-002")


if __name__ == "__main__":
    which = sys.argv[1:] or ["001", "002"]
    if "001" in which:
        build_001()
    if "002" in which:
        build_002()
