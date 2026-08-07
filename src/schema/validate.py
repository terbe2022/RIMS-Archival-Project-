"""
validate.py — check a manifest holds together. Run after every stage.

Cheap, and it catches integration errors before they compound across stages.
"""
from __future__ import annotations
import pandas as pd
from manifest import (MANIFEST_SCHEMA, STATUS, BANDS, LANES, MAX_ARCHIVE_DEPTH,
                      compute_layer)


def validate(df: pd.DataFrame, strict: bool = False) -> list[str]:
    """Returns a list of problems. Empty list means the manifest is sound."""
    p: list[str] = []
    cols = set(df.columns)

    for f in ("file_uid", "source_id", "path_raw", "path_norm"):
        if f not in cols:
            p.append(f"missing required column: {f}")
    if p:
        return p

    if df["file_uid"].isna().any():
        p.append(f"{df['file_uid'].isna().sum()} rows have a null file_uid")
    dupes = df["file_uid"].duplicated().sum()
    if dupes:
        p.append(f"{dupes} duplicate file_uid values — the key is not unique")

    uids = set(df["file_uid"].dropna())

    if "duplicate_of" in cols:
        d = df["duplicate_of"].dropna()
        orphan = set(d) - uids
        if orphan:
            p.append(f"{len(orphan)} duplicate_of values reference no existing row")
        self_ref = (df["duplicate_of"] == df["file_uid"]).sum()
        if self_ref:
            p.append(f"{self_ref} rows are marked as duplicates of themselves")

    if "parent_uid" in cols:
        orphan = set(df["parent_uid"].dropna()) - uids
        if orphan:
            p.append(f"{len(orphan)} parent_uid values reference no existing archive row")

    if "archive_depth" in cols:
        too_deep = (df["archive_depth"].fillna(0) > MAX_ARCHIVE_DEPTH).sum()
        if too_deep:
            p.append(f"{too_deep} rows exceed archive depth {MAX_ARCHIVE_DEPTH}")

    for s in ("s01", "s02", "s03", "s04", "s05"):
        c = f"{s}_status"
        if c in cols:
            bad = set(df[c].dropna().unique()) - STATUS
            if bad:
                p.append(f"{c} has invalid values: {sorted(bad)}")

    for c in ("s02_band", "s05_band"):
        if c in cols:
            bad = set(df[c].dropna().unique()) - BANDS
            if bad:
                p.append(f"{c} has invalid values: {sorted(bad)}")

    if "s03_lane" in cols:
        bad = set(df["s03_lane"].dropna().unique()) - LANES
        if bad:
            p.append(f"s03_lane has invalid values: {sorted(bad)}")

    # a stage claiming success must have produced what it promises
    if {"s03_status", "s03_text_path", "s03_text_len"} <= cols:
        broken = df[(df["s03_status"] == "ok") &
                    df["s03_text_path"].isna() &
                    (df["s03_text_len"].fillna(0) > 0)]
        if len(broken):
            p.append(f"{len(broken)} rows: s03_status=ok with text but no text_path")

    if {"s04_status", "s04_summary"} <= cols:
        broken = df[(df["s04_status"] == "ok") & df["s04_summary"].isna()]
        if len(broken):
            p.append(f"{len(broken)} rows: s04_status=ok but no summary")

    # layer is derived — it must match what the decision columns imply
    if "layer" in cols:
        expected = df.apply(lambda r: compute_layer(r.to_dict()), axis=1)
        drift = (df["layer"].fillna(-1).astype(int) != expected).sum()
        if drift:
            p.append(f"{drift} rows where layer disagrees with the decision columns")

    if strict:
        extra = cols - {f.name for f in MANIFEST_SCHEMA}
        if extra:
            p.append(f"columns not in the schema: {sorted(extra)}")

    return p


def report(df: pd.DataFrame, strict: bool = False) -> bool:
    probs = validate(df, strict)
    if not probs:
        print(f"manifest valid — {len(df):,} rows, {len(df.columns)} columns")
        return True
    print(f"manifest INVALID — {len(probs)} problem(s):")
    for x in probs:
        print(f"  - {x}")
    return False
