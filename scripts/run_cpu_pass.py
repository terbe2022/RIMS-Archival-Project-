#!/usr/bin/env python3
"""
run_cpu_pass.py — stage 01 and 02a over the sample. No GPU required.

    python3 scripts/run_cpu_pass.py --data data/sample_1k --out runs/$(date +%F)

Writes a manifest-conformant parquet plus a JSON run report carrying the
reduction percentage, its breakdown by cause, its caveats, and the hardware it
ran on. A throughput number without a card attached is unusable, so the report
records the machine whether or not anyone asked.
"""
from __future__ import annotations

import argparse
import json
import platform
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import logging

# pypdf logs a warning per malformed cross-reference entry and per unimplemented
# CJK encoding. On a corpus of 1990s scanned correspondence that is thousands of
# lines of noise around the three lines that matter. The conditions are recorded
# per file in s03_error, which is where they belong.
for _noisy in ("pypdf", "pypdf.generic", "pypdf._cmap", "pypdf._page",
               "pypdf._reader", "pypdf.filters", "pdfminer", "PIL"):
    logging.getLogger(_noisy).setLevel(logging.ERROR)
    logging.getLogger(_noisy).propagate = False

import pandas as pd

from workbench import (accessions, context, stage01, stage02a, stage03,
                       stage04, stage05, vision)
from workbench.schema import manifest as M


def hardware() -> dict:
    """Named, always. See handoff 11."""
    try:
        import os
        cpus = os.cpu_count()
    except Exception:
        cpus = None
    return {
        "host": socket.gethostname(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cpu_count": cpus,
        "gpu": "not used — stage 01/02a are CPU-only by design",
    }


def load_provenance(data_dir: Path) -> dict:
    """
    Read _sample_manifest.csv if present.

    It is the sampling record, not stage 01 output: no hashes, no format
    identification. What it does carry is why each file was chosen, which is
    provenance worth keeping, and 573 skipped rows with reasons, which are the
    defensible answer to "why isn't this file in the demo".
    """
    p = data_dir / "_sample_manifest.csv"
    if not p.exists():
        return {}
    df = pd.read_csv(p, encoding="utf-8-sig")
    out = {}
    for _, r in df[df.Action == "copied"].iterrows():
        key = M.normalise_path(str(r.Source)).split("/")[-1]
        out[key] = {"sample_reason": r.Reason, "sample_group": r.Group}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/sample_1k")
    ap.add_argument("--intake", default="intake")
    ap.add_argument("--registry", default="intake/accession_registry.json")
    ap.add_argument("--out", default="runs/cpu-pass")
    ap.add_argument("--no-images", action="store_true",
                    help="skip perceptual near-duplicate hashing")
    ap.add_argument("--no-stage03", action="store_true",
                    help="skip routing, extraction and scoring")
    ap.add_argument("--name-detector", default="heuristic",
                    choices=["heuristic", "spacy", "presidio"],
                    help="how to find person names. The heuristic matches "
                         "capitalised word pairs and produces a lot of noise "
                         "('Ohio State', 'In February'); presidio or spacy are "
                         "materially better. Falls back with a warning if the "
                         "dependency is missing.")
    ap.add_argument("--no-pii", action="store_true",
                    help="skip stage 04 pseudonymisation")
    ap.add_argument("--image-outputs",
                    help="an existing image-classification outputs.jsonl to merge "
                         "(no GPU needed; the work is already done)")
    ap.add_argument("--ocr-outputs",
                    help="an ocr.jsonl from scripts/run_ocr.py. Merged BEFORE "
                         "scoring, because OCR text is the file's own content "
                         "and has to be present when the file is ranked.")
    ap.add_argument("--provisional", action="store_true",
                    help="run accessions that have no record series yet, using a "
                         "conspicuously fake 999-prefixed identity. For "
                         "demonstration only; output is marked on every row.")
    ap.add_argument("--embeddings", action="store_true",
                    help="use sentence-transformers for scoring (CPU, slower)")
    args = ap.parse_args()

    data = Path(args.data)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    rows_by_acc, problems = accessions.resolve(args.intake, args.registry,
                                               allow_provisional=args.provisional)
    forms_by_id = accessions.load_intake(args.intake)
    for p in problems:
        print(f"  BLOCKED  {p}", file=sys.stderr)
    if not rows_by_acc:
        print("\nNo accession can be processed. Nothing was written.", file=sys.stderr)
        print("This is the intended behaviour, not a crash: record_series and "
              "accession_type are assigned by an accessioning archivist and the "
              "pipeline will not invent them.", file=sys.stderr)
        return 2

    provenance = load_provenance(data)
    nsrl = stage02a.NSRL()          # no known-file set installed; see the class
    all_rows: list[dict] = []
    per_accession = {}
    t0 = time.perf_counter()

    for acc_id, acc in sorted(rows_by_acc.items()):
        root = data / (acc["_source_folder"] or "")
        if not root.exists():
            print(f"  SKIP     {acc_id}: {root} does not exist", file=sys.stderr)
            continue
        t1 = time.perf_counter()
        rows = stage01.crawl(root, acc)
        for r in rows:
            r.update(provenance.get(r["filename"], {}))
        report = stage02a.run(rows, acc, nsrl=nsrl, do_images=not args.no_images)
        report["seconds"] = round(time.perf_counter() - t1, 2)
        report["files_per_second"] = round(len(rows) / max(report["seconds"], 1e-9), 1)
        form = forms_by_id.get(acc_id, {})

        # What the form contributes to any model call for this accession, and
        # what is deliberately withheld from it. Recorded per accession so a
        # reader of the report can see which fields conditioned the results.
        report["form_context"] = context.describe_usage(form)
        fhash = report["form_context"]["form_hash"]
        for r in rows:
            r["s04_prompt_version"] = f"form:{fhash}"

        if not args.no_stage03:
            report["stage03"] = stage03.run(rows, acc, form,
                                            use_embeddings=args.embeddings)

        # OCR first. It produces the file's OWN text, which is level-3
        # content evidence — the same standing as a text layer. Descriptions
        # are a model's account of the file and rank no higher. Merging OCR
        # after scoring would repeat the mistake that left 990 images ranked
        # on their filenames.
        if args.ocr_outputs and Path(args.ocr_outputs).exists():
            from workbench import ocr as _ocr
            by_uid = {r["file_uid"]: r for r in rows}
            read = rejected = 0
            with open(args.ocr_outputs, encoding="utf-8") as fh:
                for line in fh:
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    row = by_uid.get(rec.get("file_uid"))
                    if not row:
                        continue
                    _ocr.apply(row, rec)
                    if rec.get("text"):
                        read += 1
                    else:
                        rejected += 1
            report["ocr"] = {"read": read, "not_recovered": rejected,
                             "version": _ocr.STAGE_VERSION}
            print(f"    OCR merged: {read} files read, {rejected} not recovered")
            if read:
                from workbench import relevance as _rel
                _rel.run(rows, form, use_embeddings=args.embeddings)

        # Image and text descriptions from an earlier model run, merged rather
        # than recomputed.
        if args.image_outputs and Path(args.image_outputs).exists():
            v = vision.ingest_jsonl(rows, args.image_outputs)
            v["rerouted_to_review"] = vision.apply_flags(rows)

            # Score again, now that the descriptions exist.
            #
            # stage03 routes, extracts AND scores. Merging descriptions after
            # it means relevance ranked every image on its path alone and never
            # saw the description — which is why the retained-by-association
            # count did not move when descriptions were added. A description is
            # content evidence; it has to be present before the file is scored,
            # or the whole point of generating it is lost.
            from workbench import relevance as _rel
            before = sum(1 for r in rows if r.get("retained_by_association"))
            v["rescored"] = _rel.run(rows, form,
                                     use_embeddings=args.embeddings)
            after = sum(1 for r in rows if r.get("retained_by_association"))
            v["association_before"] = before
            v["association_after"] = after
            print(f"    rescored with descriptions: "
                  f"{before} -> {after} retained by association")
            report["vision"] = v

        if not args.no_pii:
            report["stage04"] = stage04.run(
                rows, acc, out / "redacted" / acc_id,
                name_detector=args.name_detector)
            report["stage04"]["name_detector"] = args.name_detector

        # Recompute the layer assignment after stage 03/04.
        #
        # Stage 02a assigns layers from what it knows at that point: duplicates
        # and structural noise. Mail exclusions are only discovered once the
        # messages are parsed, which happens in stage 03 — so a run that
        # reported the stage 02a figure would show 0% excluded on an accession
        # that is four-fifths automated traffic. Sensitivity flags from the
        # image lane move rows too. The number has to be taken after every
        # stage that can change it.
        post = stage02a.reduction_report(rows, nsrl)
        report["by_cause"] = post["by_cause"]
        report["layer_0"] = post["layer_0"]
        report["reduction_pct"] = post["reduction_pct"]

        # Stage 05 last: it reads the sensitivity outcome, the rule match and
        # the relevance band, so it has to run after everything that sets them.
        report["stage05"] = stage05.run(rows, acc)

        report["top_ranked"] = stage03.ranked(rows, limit=15)
        report["form_status"] = acc["_form_status"]
        per_accession[acc_id] = report
        all_rows.extend(rows)
        if acc.get("provisional_identity"):
            print(f"  PROVISIONAL  {acc_id}: no record series assigned. Identity "
                  f"{acc['accession_uid']} is fabricated for demonstration and "
                  f"must not be used as an accession number.", file=sys.stderr)
        line = (f"  {acc_id}  {len(rows):>5} files  "
                f"layer0 {report['layer_0']:>4} ({report['reduction_pct']}%)  "
                f"{report['seconds']}s")
        s5 = report.get("stage05")
        if s5 and s5.get("decisions"):
            d = s5["decisions"]
            print(f"    flagged priority: {d.get('priority', 0)}, "
                  f"retained: {d.get('retained', 0)}; "
                  f"dc_date found for {s5['with_a_date']}")
        s4 = report.get("stage04")
        if s4 and s4.get("with_identifiers"):
            print(f"    identifiers found in {s4['with_identifiers']} files; "
                  f"{s4['vault_entries']} distinct labels allocated")
        s3 = report.get("stage03")
        if s3:
            line += (f"  |  lanes {len(s3['routing']['by_lane'])}"
                     f"  extracted {s3['extraction']['attempted']}"
                     f"  assoc {s3['retained_by_association']}")
        print(line)

    if not all_rows:
        print("No files found.", file=sys.stderr)
        return 2

    for r in all_rows:
        r.pop("_text", None)

    # Filenames on disk are bytes, not text. A name carrying bytes that are not
    # valid UTF-8 — a Latin-1 accented character written by a 1990s system, say
    # — comes back from os.walk surrogate-escaped as \udcXX, and Arrow refuses
    # to write surrogates. The escaped form is what lets us reopen the file, so
    # it is kept in memory through extraction and only cleaned at write time.
    #
    # This is not cosmetic. Such a name is itself evidence about the material's
    # provenance, so the substitution is counted and reported rather than done
    # silently.
    mangled = 0
    for r in all_rows:
        for k, v in list(r.items()):
            if isinstance(v, str) and any("\ud800" <= c <= "\udfff" for c in v):
                r[k] = v.encode("utf-8", "replace").decode("utf-8")
                if k == "filename":
                    mangled += 1
    if mangled:
        print(f"  {mangled} filename(s) held bytes that are not valid UTF-8; "
              f"substituted for storage. The files were read normally.")

    df = pd.DataFrame(all_rows)
    # provenance columns are carried on the rows but are not schema columns yet
    df = df.drop(columns=["sample_reason", "sample_group",
                          "retained_by_association", "s04_review_hint",
                          "s02_exclusion_evidence", "mail_subject", "mail_date",
                          "mail_has_attachment", "mail_exclusion",
                          "mail_evidence"], errors="ignore")
    # A list-typed column that is empty for every row arrives as float64 NaN
    # and Arrow cannot convert that to list<string>. Coerce every list field in
    # the schema to object dtype holding real lists or None, so an all-empty
    # column still writes with the right type.
    import pyarrow as pa
    for f in M.MANIFEST_SCHEMA:
        if pa.types.is_list(f.type) and f.name in df.columns:
            df[f.name] = df[f.name].apply(
                lambda v: v if isinstance(v, (list, tuple)) else None
            ).astype(object)

    table = M.enforce(df)
    import pyarrow.parquet as pq
    pq.write_table(table, out / "manifest.parquet")

    overall = stage02a.reduction_report(all_rows, nsrl)
    run_report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": M.SCHEMA_VERSION,
        "policy_version": per_accession and next(iter(per_accession.values()))
                          .get("rules", {}).get("ruleset"),
        "hardware": hardware(),
        "tools": stage01.detect_tools(),
        "elapsed_seconds": round(time.perf_counter() - t0, 2),
        "overall": overall,
        "per_accession": per_accession,
        "blocked": problems,
        "non_utf8_filenames": mangled,
    }
    (out / "run_report.json").write_text(json.dumps(run_report, indent=2, default=str))

    print(f"\n  reduction {overall['reduction_pct']}%  "
          f"({overall['layer_0']}/{overall['total_files']} in layer 0)")
    for c in overall["caveats"]:
        print(f"    caveat: {c}")
    print(f"\n  wrote {out/'manifest.parquet'} and {out/'run_report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
