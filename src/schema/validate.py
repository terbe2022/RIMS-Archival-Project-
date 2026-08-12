"""
validate.py — check a manifest holds together. Run after every stage.

Cheap, and it catches integration errors before they compound across stages.

v1.1 adds checks for the things that would be expensive or dangerous to get
wrong: record series shape, accession linkage, and — the one that matters most
— the assertion that nothing is marked for discard while carrying a sensitivity
flag. That is the failure mode with real consequences, so it gets a hard check
rather than trust in the calling code.
"""
from __future__ import annotations
import pandas as pd
from manifest import (MANIFEST_SCHEMA, ACCESSION_SCHEMA, STATUS, BANDS, LANES,
                      MAX_ARCHIVE_DEPTH, S02_DECISIONS, S05_DECISIONS,
                      ACCESS_LEVELS, ACCESSION_TYPES, SOURCE_MEDIA,
                      REVIEWER_ROLES, compute_layer, parse_record_series)


def _has(v) -> bool:
    """Non-empty list/array. NaN and None are absent."""
    if v is None:
        return False
    if isinstance(v, float) and v != v:
        return False
    try:
        return len(v) > 0
    except TypeError:
        return bool(v)


def validate(df: pd.DataFrame, accessions: pd.DataFrame | None = None,
             strict: bool = False) -> list[str]:
    """Returns a list of problems. Empty list means the manifest is sound."""
    p: list[str] = []
    cols = set(df.columns)

    # v1.1: source_id is gone. accession_uid and record_series replace it.
    for f in ("file_uid", "accession_uid", "record_series", "path_raw", "path_norm"):
        if f not in cols:
            p.append(f"missing required column: {f}")
    if p:
        return p

    # ------------------------------------------------------------ identity --
    if df["file_uid"].isna().any():
        p.append(f"{df['file_uid'].isna().sum()} rows have a null file_uid")
    dupes = df["file_uid"].duplicated().sum()
    if dupes:
        p.append(f"{dupes} duplicate file_uid values — the key is not unique")

    uids = set(df["file_uid"].dropna())

    # v1.1 — record series shape. Assignment is human and judgement-based, so we
    # never generate or correct one; we only check the shape and flag oddities.
    bad_rs = []
    for rs in df["record_series"].dropna().unique():
        try:
            parse_record_series(rs)
        except ValueError:
            bad_rs.append(rs)
    if bad_rs:
        p.append(f"record_series values that are not 6-7 digits: {sorted(bad_rs)[:5]}"
                 f" — flag for an archivist, never auto-correct")

    # v1.1 — every row must resolve to an accession record
    if accessions is not None and "accession_uid" in accessions.columns:
        known = set(accessions["accession_uid"].dropna())
        orphan = set(df["accession_uid"].dropna()) - known
        if orphan:
            p.append(f"{len(orphan)} accession_uid values have no row in accessions.parquet")
        # accession_type must agree between the two
        if "accession_type" in cols and "accession_type" in accessions.columns:
            amap = dict(zip(accessions["accession_uid"], accessions["accession_type"]))
            mism = df[df.apply(
                lambda r: r["accession_uid"] in amap
                and pd.notna(r.get("accession_type"))
                and r["accession_type"] != amap[r["accession_uid"]], axis=1)]
            if len(mism):
                p.append(f"{len(mism)} rows where accession_type disagrees with "
                         f"the accession record")

    # ------------------------------------------------------------ vocabulary --
    for col, allowed, label in (
        ("accession_type", ACCESSION_TYPES, "accession_type"),
        ("source_media", SOURCE_MEDIA, "source_media"),
        ("s02_decision", S02_DECISIONS, "s02_decision"),
        ("s05_decision", S05_DECISIONS, "s05_decision"),
        ("s06_access_level", ACCESS_LEVELS, "s06_access_level"),
        ("rv_role", REVIEWER_ROLES, "rv_role"),
        ("s03_lane", LANES, "s03_lane"),
    ):
        if col in cols:
            bad = set(df[col].dropna().unique()) - allowed
            if bad:
                p.append(f"{label} has invalid values: {sorted(bad)}")

    # v1.1 — `closed` was removed. Call it out specifically, because it will
    # appear in anything written against v1.0 and the message should say why.
    if "s06_access_level" in cols and (df["s06_access_level"] == "closed").any():
        n = (df["s06_access_level"] == "closed").sum()
        p.append(f"{n} rows use s06_access_level='closed' — the Archives uses "
                 f"only 'open' and 'restricted' (answer 7.3)")

    # -------------------------------------------------------- relationships --
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

    # ------------------------------------------- the one that really matters --
    # v1.1. Answer 3.3 lists HR material as both routinely disposable AND
    # sensitive. If those ever collapse into one disposition, the system can
    # bin a personnel file that no human has looked at. Hard assertion.
    if {"s02_decision", "s04_sensitivity_flags"} <= cols:
        bad = df[(df["s02_decision"] == "discard_candidate")
                 & df["s04_sensitivity_flags"].apply(_has)]
        if len(bad):
            p.append(
                f"CRITICAL: {len(bad)} rows marked discard_candidate while carrying "
                f"a sensitivity flag. Sensitivity beats discard — these must be "
                f"restricted_review. Check resolve_decision() is being used.")

    # v1.1 — sensitive material is never proposed for disposal
    if {"s02_decision", "dp_proposed_at"} <= cols:
        bad = df[(df["s02_decision"] == "restricted_review")
                 & df["dp_proposed_at"].notna()]
        if len(bad):
            p.append(f"CRITICAL: {len(bad)} restricted_review rows have been proposed "
                     f"for disposal. That decision belongs to a person, every time.")

    # v1.1 — nothing disposed before its clock ran out
    if {"dp_eligible_at", "dp_proposed_at"} <= cols:
        both = df[df["dp_eligible_at"].notna() & df["dp_proposed_at"].notna()]
        early = both[both["dp_proposed_at"] < both["dp_eligible_at"]]
        if len(early):
            p.append(f"{len(early)} rows proposed for disposal before dp_eligible_at")

    # v1.1 — the manifest row always survives disposal. That is the audit trail.
    if {"dp_executed_at", "dp_manifest_retained"} <= cols:
        bad = df[df["dp_executed_at"].notna()
                 & (df["dp_manifest_retained"] != True)]  # noqa: E712
        if len(bad):
            p.append(f"{len(bad)} disposed rows without dp_manifest_retained — the "
                     f"record that a file existed must outlive the file")

    # ---------------------------------------------------- stage consistency --
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

    # v1.1 — generated-field provenance is set together or not at all.
    # Answer 5.3: an archivist must be able to tell what a machine wrote.
    if {"s05_generated_fields", "s05_generated_by"} <= cols:
        half = df[df["s05_generated_fields"].apply(_has)
                  ^ df["s05_generated_by"].notna()]
        if len(half):
            p.append(f"{len(half)} rows have generated fields without a generator "
                     f"recorded, or vice versa")

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
        if "source_id" in cols:
            p.append("column 'source_id' is from schema v1.0 — it was renamed to "
                     "record_series, and file_uid now derives from accession_uid. "
                     "See docs/design/schema-changelog.md")

    return p


def validate_accessions(df: pd.DataFrame) -> list[str]:
    """The accession record has its own small set of rules."""
    p: list[str] = []
    cols = set(df.columns)
    for f in ("accession_uid", "record_series", "accession_type"):
        if f not in cols:
            p.append(f"missing required column: {f}")
    if p:
        return p

    if df["accession_uid"].duplicated().any():
        p.append("duplicate accession_uid values")

    bad = set(df["accession_type"].dropna().unique()) - ACCESSION_TYPES
    if bad:
        p.append(f"accession_type has invalid values: {sorted(bad)}")

    for rs in df["record_series"].dropna().unique():
        try:
            parse_record_series(rs)
        except ValueError as e:
            p.append(str(e))

    # profile_field selects which ruleset applies to drafts — a missing one
    # means triage silently falls back to a default that may be wrong
    if "profile_field" in cols:
        missing = df[df["profile_field"].isna()
                     & (df["accession_type"] == "personal_papers")]
        if len(missing):
            p.append(f"{len(missing)} personal_papers accessions have no "
                     f"profile_field — the drafts rule cannot be selected")

    return p


def report(df: pd.DataFrame, accessions: pd.DataFrame | None = None,
           strict: bool = False) -> bool:
    probs = validate(df, accessions, strict)
    if accessions is not None:
        probs += validate_accessions(accessions)
    if not probs:
        print(f"manifest valid — {len(df):,} rows, {len(df.columns)} columns")
        return True
    print(f"manifest INVALID — {len(probs)} problem(s):")
    for x in probs:
        print(f"  - {x}")
    return False
