#!/usr/bin/env python3
"""
export_workbench.py — one payload for the whole workbench UI.

    python3 scripts/export_workbench.py runs/2026-09-06/manifest.parquet \\
        --intake intake --out demo/workbench --thumbs

Differs from export_review.py in three ways. It carries EVERY accession rather
than one, so the UI can show a list and let a person move between them. It
carries each accession's intake form, so the form is a page rather than a
footnote. And with --thumbs it writes downscaled JPEGs next to the payload, so
images can be seen rather than described.

On thumbnails
-------------
These are copies of archival images. They are written only under --thumbs, they
are 160px and heavily compressed, and they inherit every access condition of the
originals. ACC-2026-020 is `status: draft` precisely because nobody has said
what those images depict, and its form asks that anything showing identifiable
living people, private residences or documents containing personal information
be flagged for a person. Generating thumbnails does not change any of that — it
makes the material easier to look at, which is the point and also the risk.

--public refuses to write thumbnails at all.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import pyarrow.parquet as pq

THUMB_PX = 160

FIELDS = [
    "file_uid", "accession_uid", "filename", "path_norm", "path_raw",
    "parent_folder",
    "extension", "size_bytes", "depth",
    "s01_format_name", "s01_id_method", "s01_puid",
    "s02_decision", "s02_rule_matched", "s02_band", "s02_score",
    "s02_rationale", "s02_structural_exclusion", "duplicate_of",
    "s03_lane", "s03_status", "s03_text_len", "s03_text_sample",
    "s03_needs_ocr",
    "s04_description", "s04_summary", "s04_sensitivity_flags",
    "s05_decision", "s05_rationale", "s05_generated_fields",
    "s05_human_reviewed",
    "dc_title", "dc_date", "dc_type", "dc_subject", "dc_creator",
    "dc_format", "dc_rights",
    "layer", "retained_by_association",
]

# What happens to a file next. This is the archivist's decision surface, and it
# is deliberately NOT the same vocabulary as s02_decision — disposition is about
# where material ends up, not about what a rule concluded.
DISPOSITIONS = {
    "medusa_open": "To Medusa, openly available",
    "medusa_closed": "To Medusa, closed pending review",
    "supervisor": "Held for a supervising archivist",
    "not_selected": "Not selected — retained during the review window",
    "excluded": "Excluded — duplicate or structural noise",
}


def disposition(row: dict) -> str:
    """
    Proposed disposition. A proposal, never an action.

    Nothing here deletes. The lowest outcome is "not selected", which means the
    file is kept for the retention window and a person may still change their
    mind. Disposal is a separate, later, human act.
    """
    if row.get("layer") == 0:
        return "excluded"
    if row.get("s02_decision") == "restricted_review" or row.get("s04_sensitivity_flags"):
        return "supervisor"
    if row.get("s02_decision") == "not_selected":
        return "not_selected"
    if row.get("s05_decision") == "priority":
        return "medusa_closed"
    return "medusa_open"


def make_thumb(src: str, dest: Path) -> bool:
    try:
        from PIL import Image
        with Image.open(src) as im:
            im = im.convert("RGB")
            im.thumbnail((THUMB_PX, THUMB_PX))
            dest.parent.mkdir(parents=True, exist_ok=True)
            im.save(dest, "JPEG", quality=72)
        return True
    except Exception:
        return False


def folder_rollup(items: list[dict]) -> list[dict]:
    """
    Folder-level summary.

    In a working research computer the folder a file sits in carries the
    creator's own judgement about what it relates to, so a folder is a more
    meaningful unit than a file for someone deciding what to look at first.
    """
    by: dict[str, list[dict]] = defaultdict(list)
    for it in items:
        folder = "/".join((it.get("path_norm") or "").split("/")[:-1]) or "(root)"
        by[folder].append(it)

    out = []
    for folder, group in sorted(by.items()):
        scores = [g.get("s02_score") or 0 for g in group]
        subjects: dict[str, int] = {}
        for g in group:
            for w in (g.get("dc_subject") or "").split("; "):
                if w:
                    subjects[w] = subjects.get(w, 0) + 1
        out.append({
            "folder": folder,
            "files": len(group),
            "priority": sum(1 for g in group if g.get("s05_decision") == "priority"),
            "needs_person": sum(1 for g in group
                                if g.get("s02_decision") == "restricted_review"),
            "by_association": sum(1 for g in group if g.get("retained_by_association")),
            "read": sum(1 for g in group if g.get("s03_text_len")),
            "top_score": round(max(scores), 3) if scores else 0,
            "lanes": sorted({g.get("s03_lane") for g in group if g.get("s03_lane")}),
            "subjects": [k for k, _ in sorted(subjects.items(),
                                              key=lambda kv: -kv[1])[:8]],
        })
    return sorted(out, key=lambda f: -f["priority"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("parquet")
    ap.add_argument("--intake", default="intake")
    ap.add_argument("--out", default="demo/workbench")
    ap.add_argument("--public", action="store_true",
                    help="strip filenames, paths and text; refuses thumbnails")
    ap.add_argument("--thumbs", action="store_true",
                    help="write downscaled image copies. See the module note.")
    ap.add_argument("--snippet", type=int, default=280,
                    help="characters of original text to carry per file")
    args = ap.parse_args()

    if args.public and args.thumbs:
        print("--public and --thumbs are contradictory: a thumbnail IS the "
              "content. Refusing.", file=sys.stderr)
        return 2

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    have = [c for c in FIELDS if c in pq.read_schema(args.parquet).names]
    rows = pq.read_table(args.parquet, columns=have).to_pylist()

    forms = {}
    for p in sorted(Path(args.intake).glob("ACC-*.json")):
        f = json.loads(p.read_text())
        forms[f["accession"]] = f

    by_uid: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_uid[r.get("accession_uid")].append(r)

    # accession_uid -> form, from the registry rather than guessed.
    #
    # Matching on source_folder inside path_norm does not work: paths are
    # relative to the accession root, so the folder name that identifies the
    # accession is exactly the one segment the paths do not contain. The
    # registry already holds this mapping; asking it is both correct and
    # shorter than inferring it.
    uid_to_form = {}
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from workbench import accessions as accmod
        reg = Path(args.intake) / "accession_registry.json"
        if reg.exists():
            built, _ = accmod.resolve(args.intake, reg, allow_provisional=True)
            uid_to_form = {v["accession_uid"]: k for k, v in built.items()}
    except Exception as exc:
        print(f"  registry lookup failed ({exc}); accessions will be unnamed",
              file=sys.stderr)
    for uid in by_uid:
        uid_to_form.setdefault(uid, None)

    thumbs_made = 0
    accessions = []
    items_by_uid = {}

    for uid, group in sorted(by_uid.items()):
        acc_id = uid_to_form.get(uid)
        form = forms.get(acc_id, {})
        items = []
        for n, r in enumerate(group, 1):
            it = {k: r.get(k) for k in have}
            # path_raw is the absolute server path. It is needed to READ the
            # file for a thumbnail, and it must never reach the browser — it
            # discloses the share layout and is useless to a reviewer.
            it.pop("path_raw", None)
            it["disposition"] = disposition(r)
            if args.public:
                it["filename"] = f"item-{n:04d}" + (
                    f".{r.get('extension')}" if r.get("extension") else "")
                for k in ("path_norm", "parent_folder", "s03_text_sample",
                          "s04_description", "dc_title", "dc_subject", "dc_creator"):
                    it[k] = None
            else:
                it["snippet"] = (r.get("s03_text_sample") or "")[:args.snippet]
                if args.thumbs and r.get("s03_lane") == "image":
                    name = f"{r['file_uid'][:16]}.jpg"
                    # path_raw is not exported, so thumbs need the manifest's
                    # own copy of it; fall back silently when absent.
                    src = r.get("path_raw")
                    if src and make_thumb(src, out / "thumbs" / name):
                        it["thumb"] = f"thumbs/{name}"
                        thumbs_made += 1
            items.append(it)

        counts = defaultdict(int)
        for it in items:
            counts[it["disposition"]] += 1
        lanes = defaultdict(int)
        for it in items:
            lanes[it.get("s03_lane") or "unroutable"] += 1

        accessions.append({
            "accession_uid": uid,
            "accession_id": acc_id,
            "name": form.get("name") or uid,
            "status": form.get("status"),
            "job_type": form.get("job_type"),
            "provisional": uid.startswith("999"),
            "files": len(items),
            "dispositions": dict(counts),
            "lanes": dict(sorted(lanes.items(), key=lambda kv: -kv[1])),
            "form": form if not args.public else {
                k: form.get(k) for k in ("accession", "name", "valuable",
                                         "exclude", "access", "status")},
            "folders": folder_rollup(items)[:60],
        })
        items_by_uid[uid] = items

    payload = {
        "public": args.public,
        "disposition_labels": DISPOSITIONS,
        "accessions": accessions,
        "items": items_by_uid,
    }
    (out / "workbench-data.json").write_text(json.dumps(payload, default=str))
    total = sum(len(v) for v in items_by_uid.values())
    print(f"wrote {out/'workbench-data.json'}  "
          f"{len(accessions)} accessions, {total} files, {thumbs_made} thumbnails")
    if not args.public:
        print("  Contains real filenames, paths and text. Do not publish.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
