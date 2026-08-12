"""
manifest.py — the single definition of the manifest schema.

Every stage imports from here. Nothing writes a Parquet file without going
through `enforce()`. The schema is enforced, not assumed.

See docs/design/manifest-schema.md for the reasoning behind each decision,
and docs/design/schema-changelog.md for what changed between versions.

v1.1 — 12 Aug 2026. The breaking change is the key.

    v1.0 derived file_uid from `source_id`, on the assumption that the Box
    folder prefixes (2620191_MichaelHart) were accession numbers. They are
    *record series* numbers, and a record series number is NOT unique per
    delivery — two accessions from the same office share one. Keying to it
    would have produced silent collisions, not a crash: two different files
    mapping to the same row.

    So identity now carries both. `record_series` is theirs and describes
    provenance. `accession_uid` is ours and scopes a delivery. file_uid
    derives from accession_uid.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import date, datetime, timedelta, timezone

import pyarrow as pa

SCHEMA_VERSION = "1.1"
MAX_ARCHIVE_DEPTH = 3
FAT_EPOCH_FLOOR = datetime(1980, 1, 1, tzinfo=timezone.utc)
DEFAULT_RETENTION_DAYS = 180          # provisional — Joanne has not named a period

STATUS = {"ok", "empty", "skipped", "failed", "partial"}   # None = stage not reached
BANDS = {"high", "mid", "low"}
LANES = {"document", "email", "image", "tabular", "scientific", "av", "code", "archive"}

# v1.1: two values became four. `discard_candidate` and `restricted_review` are
# different outcomes — see the precedence rule in `resolve_decision()` below.
S02_DECISIONS = {"selected", "not_selected", "discard_candidate", "restricted_review"}
S05_DECISIONS = {"priority", "retained"}

# v1.1: the Archives uses two access levels, not three. `closed` removed.
ACCESS_LEVELS = {"open", "restricted"}

# v1.1: personal papers and administrative records have different appraisal
# rules and different turnaround targets. Triage branches on this.
ACCESSION_TYPES = {"personal_papers", "administrative"}

# v1.1: reordered. `share` is the normal case — material reaches us already
# preservation-processed on an Archives network drive. Optical media, floppies
# and USB sticks are handled upstream and never appear here.
SOURCE_MEDIA = {"share", "drive", "image", "box"}

REVIEWER_ROLES = {"accessioning", "supervising"}

PATH_FLAGS = {"non_utf8", "over_260", "trailing_space", "reserved_name",
              "control_chars", "leading_dot", "no_extension"}
DATE_FLAGS = {"epoch_zero", "future", "pre_1980", "missing"}
RESERVED_NAMES = ({"CON", "PRN", "AUX", "NUL"} |
                  {f"COM{i}" for i in range(1, 10)} | {f"LPT{i}" for i in range(1, 10)})

_S = pa.string
_TS = pa.timestamp("us", tz="UTC")


def _stage_cols(n: str, extra: list[tuple] = None) -> list[pa.Field]:
    """Every stage carries status, error and version. No exceptions."""
    cols = list(extra or [])
    cols += [(f"{n}_status", _S()), (f"{n}_error", _S()), (f"{n}_version", _S())]
    return [pa.field(k, v) for k, v in cols]


# ---------------------------------------------------------------- schema --
CORE = [
    pa.field("file_uid", _S(), nullable=False),
    pa.field("accession_uid", _S(), nullable=False),   # v1.1 — ours, delivery-scoped
    pa.field("record_series", _S(), nullable=False),   # v1.1 — theirs, provenance
    pa.field("record_group", _S()),                    # v1.1 — derived
    pa.field("series", _S()),                          # v1.1 — derived
    pa.field("subseries", _S()),                       # v1.1 — derived
    pa.field("accession_type", _S()),                  # v1.1
    pa.field("source_label", _S()),                    # mnemonic only — never parsed
    pa.field("source_media", _S()),
    pa.field("source_ref", _S()),
    pa.field("source_received", pa.date32()),
    pa.field("manifest_generation", pa.int8()),
    pa.field("schema_version", _S()),
]

S01 = [
    pa.field("path_raw", _S(), nullable=False),
    pa.field("path_norm", _S(), nullable=False),
    pa.field("path_norm_ci", _S()),
    pa.field("filename", _S()),
    pa.field("extension", _S()),
    pa.field("parent_folder", _S()),
    pa.field("depth", pa.int16()),
    pa.field("path_flags", pa.list_(_S())),
    pa.field("size_bytes", pa.int64()),
    pa.field("mtime", _TS), pa.field("ctime", _TS), pa.field("atime", _TS),
    pa.field("mtime_raw", _S()),
    pa.field("date_flags", pa.list_(_S())),
    pa.field("content_sha256", _S()),
    pa.field("content_sha1", _S()),
    pa.field("parent_uid", _S()),
    pa.field("virtual_path", _S()),
    pa.field("archive_depth", pa.int8()),
] + _stage_cols("s01", [
    ("s01_puid", _S()), ("s01_format_name", _S()), ("s01_format_version", _S()),
    ("s01_id_confidence", _S()), ("s01_id_method", _S()), ("s01_ext_mismatch", pa.bool_()),
    # v1.1 — Tracy Popp's preservation processing already produces format ID and
    # technical metadata upstream of us. We record hers, run ours alongside, and
    # flag disagreement. SPECULATIVE until we see a real output file.
    ("s01_upstream_present", pa.bool_()),
    ("s01_upstream_source", _S()),
    ("s01_upstream_format", _S()),
    ("s01_upstream_json", _S()),
    ("s01_upstream_agrees", pa.bool_()),
])

S02 = [
    pa.field("duplicate_of", _S()),
    pa.field("duplicate_count", pa.int32()),
] + _stage_cols("s02", [
    ("s02_nsrl_hit", pa.bool_()), ("s02_structural_exclusion", _S()),
    ("s02_peek_text", _S()), ("s02_peek_method", _S()), ("s02_peek_tier", pa.int8()),
    ("s02_keywords", pa.list_(_S())), ("s02_has_embedding", pa.bool_()),
    ("s02_folder_score", pa.float32()), ("s02_file_score", pa.float32()),
    ("s02_score", pa.float32()), ("s02_band", _S()), ("s02_decision", _S()),
    ("s02_rule_matched", _S()),          # v1.1 — which named rule fired
    ("s02_ruleset", _S()),               # v1.1 — which ruleset it came from
    ("s02_rationale", _S()), ("s02_policy_version", _S()),
])

S03 = _stage_cols("s03", [
    ("s03_lane", _S()), ("s03_extractor", _S()), ("s03_text_path", _S()),
    ("s03_text_len", pa.int64()), ("s03_text_sample", _S()),
    ("s03_page_count", pa.int32()), ("s03_header_facts_json", _S()),
    ("s03_needs_ocr", pa.bool_()), ("s03_duration_ms", pa.int32()),
])

S04 = _stage_cols("s04", [
    ("s04_summary", _S()), ("s04_description", _S()), ("s04_doc_type", _S()),
    ("s04_pii_entities_json", _S()), ("s04_pii_map_ref", _S()),
    ("s04_masked_text_path", _S()), ("s04_sensitivity_flags", pa.list_(_S())),
    ("s04_sensitivity_scores_json", _S()), ("s04_model", _S()),
    ("s04_prompt_version", _S()), ("s04_duration_ms", pa.int32()),
])

DC = [pa.field(f"dc_{e}", _S()) for e in (
    "title", "creator", "subject", "description", "publisher", "contributor",
    "date", "type", "format", "identifier", "source", "language",
    "relation", "coverage", "rights")]

S05 = DC + _stage_cols("s05", [
    ("s05_score", pa.float32()), ("s05_band", _S()), ("s05_decision", _S()),
    ("s05_rationale", _S()), ("s05_generated_fields", pa.list_(_S())),
    # v1.1 — "which fields were generated" is not enough. An archivist reading a
    # finding aid in ten years wants to know what wrote them, when, and whether
    # anyone checked. Three questions, three columns. Answer 5.3 was a flat yes.
    ("s05_generated_by", _S()),
    ("s05_generated_at", _TS),
    ("s05_human_reviewed", pa.bool_()),
])

S06 = [
    pa.field("s06_indexed", pa.bool_()),
    pa.field("s06_index_id", _S()),
    pa.field("s06_cluster_id", pa.int32()),
    pa.field("s06_access_level", _S()),
    # v1.1 — delivery is a three-way fork, not one destination
    pa.field("s06_preservation_ref", _S()),   # Medusa, or its replacement
    pa.field("s06_access_ref", _S()),         # Digital Library; null if restricted
    pa.field("s06_catalogue_ref", _S()),      # ArchivesSpace record this hangs off
    pa.field("s06_delivery_status", _S()),
]

REVIEW = [
    pa.field("rv_machine_decision", _S()),
    pa.field("rv_final_decision", _S()),
    pa.field("rv_reviewer", _S()),
    pa.field("rv_role", _S()),               # v1.1 — accessioning vs supervising
    pa.field("rv_at", _TS),
    pa.field("rv_reason", _S()),
    pa.field("rv_layer", pa.int8()),
    pa.field("rv_sample_selected", pa.bool_()),   # v1.1 — audit coverage measurable
    pa.field("layer", pa.int8()),            # derived, never authored
]

# v1.1 — disposal. The pipeline never deletes autonomously, but the Archives
# does dispose of material deliberately once selection is complete, and the
# absence of a clock is what created the existing backlog (answer 5.7).
DISPOSAL = [
    pa.field("dp_eligible_at", _TS),
    pa.field("dp_proposed_at", _TS),
    pa.field("dp_approved_by", _S()),
    pa.field("dp_approved_at", _TS),
    pa.field("dp_batch_id", _S()),
    pa.field("dp_executed_at", _TS),
    pa.field("dp_manifest_retained", pa.bool_()),   # always True
]

MANIFEST_SCHEMA = pa.schema(
    CORE + S01 + S02 + S03 + S04 + S05 + S06 + REVIEW + DISPOSAL)

# v1.1 — facts true of a whole accession do not belong on every row.
ACCESSION_SCHEMA = pa.schema([
    pa.field("accession_uid", _S(), nullable=False),
    pa.field("record_series", _S(), nullable=False),
    pa.field("source_label", _S()),
    pa.field("accession_type", _S(), nullable=False),
    pa.field("source_media", _S()),
    pa.field("source_ref", _S()),
    pa.field("source_received", pa.date32()),
    pa.field("accession_archivist", _S()),     # escalation AND deletion authority
    pa.field("profile_person", _S()),
    pa.field("profile_department", _S()),
    pa.field("profile_field", _S()),           # selects the drafts rule
    pa.field("profile_active_years", _S()),
    pa.field("profile_summary", _S()),
    pa.field("profile_source", _S()),
    pa.field("deed_of_gift_ref", _S()),        # pointer only; Deed stays in Library storage
    pa.field("deed_restrictions", _S()),
    pa.field("legal_hold", pa.bool_()),
    pa.field("selection_completed_at", _TS),   # starts the retention clock
    pa.field("retention_window_days", pa.int32()),
])

# columns the reviewer sees by default — must stay human-readable
REVIEWER_VIEW = [
    "file_uid", "path_raw", "filename", "extension", "size_bytes", "mtime",
    "accession_type", "s01_format_name", "s03_text_sample", "s04_summary",
    "s04_sensitivity_flags", "s02_rule_matched", "s05_score", "s05_rationale",
    "layer", "dc_title", "dc_date", "s05_generated_fields", "s05_human_reviewed",
]


# ---------------------------------------------------------------- identity --
_RECORD_SERIES_RE = re.compile(r"^\d{6,7}$")


def parse_record_series(rs: str) -> dict:
    """
    Split a record series number into its parts.

        2620191  ->  RG 26 - series 20 - sub-series 191

    Two digits record group, two digits series, the remaining two or three
    sub-series. Shape only — whether the record group actually exists is checked
    against the published classification list, which the software never guesses:
    https://archon.library.illinois.edu/archives/index.php?p=collections/classifications
    """
    rs = str(rs).strip()
    if not _RECORD_SERIES_RE.match(rs):
        raise ValueError(
            f"record_series {rs!r} is not 6 or 7 digits. Numbers are assigned by "
            f"an accessioning archivist — flag for a person, never auto-correct."
        )
    return {"record_series": rs, "record_group": rs[:2],
            "series": rs[2:4], "subseries": rs[4:]}


def make_accession_uid(record_series: str, received: date, seq: int = 1) -> str:
    """
    Delivery-scoped key: 2620191-20260812-01

    A record series number identifies *where material came from*, not a delivery
    event — two batches from the same office share one. The date and sequence
    disambiguate. Human-readable on purpose: this appears in directory names and
    in conversation with archivists, where an opaque UUID helps nobody.
    """
    parse_record_series(record_series)          # validates shape, raises if wrong
    return f"{record_series}-{received:%Y%m%d}-{seq:02d}"


def normalise_path(raw: str) -> str:
    """Forward slashes, NFC, trimmed. Joins use this; provenance uses path_raw."""
    p = raw.replace("\\", "/")
    p = unicodedata.normalize("NFC", p)
    return p.strip()


def make_uid(accession_uid: str, path_norm: str) -> str:
    """
    Deterministic 32-hex key. Re-crawling the same accession yields the same
    keys, which is what makes generations joinable and reprocessing safe.

    v1.1: scoped by accession_uid, not record_series. See the module docstring —
    scoping by record_series would have collided across deliveries.
    """
    h = hashlib.blake2b(digest_size=16)
    h.update(accession_uid.encode("utf-8"))
    h.update(b"\x00")
    h.update(path_norm.encode("utf-8", errors="surrogateescape"))
    return h.hexdigest()


# ------------------------------------------------------------------ flags --
def path_flags(raw: str) -> list[str]:
    flags = []
    try:
        raw.encode("utf-8")
    except UnicodeEncodeError:
        flags.append("non_utf8")
    if len(raw) > 260:
        flags.append("over_260")
    name = raw.replace("\\", "/").rsplit("/", 1)[-1]
    if name != name.rstrip() or name.endswith("."):
        flags.append("trailing_space")
    if name.split(".")[0].upper() in RESERVED_NAMES:
        flags.append("reserved_name")
    if any(ord(c) < 32 for c in raw):
        flags.append("control_chars")
    if name.startswith("."):
        flags.append("leading_dot")
    if "." not in name:
        flags.append("no_extension")
    return flags


def date_flags(ts: datetime | None) -> list[str]:
    """Old drives lie about dates. Flag rather than silently trust."""
    if ts is None:
        return ["missing"]
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    flags = []
    if ts.timestamp() == 0:
        flags.append("epoch_zero")
    if ts < FAT_EPOCH_FLOOR:
        flags.append("pre_1980")
    if ts > datetime.now(timezone.utc).replace(microsecond=0):
        flags.append("future")
    return flags


# -------------------------------------------------------------- decisions --
def resolve_decision(rule_decision: str, sensitivity_flags=None) -> str:
    """
    Sensitivity beats discard. Always. This is precedence, not a weight.

    Answer 3.3 lists HR material — FMLA, discipline matters, personnel
    discussions — as BOTH routinely disposable AND sensitive. Those are
    different dispositions, and collapsing them would let the system route a
    personnel file onto the discard pile on a rule match, with no human ever
    seeing it.

    So: if anything flagged it sensitive, the discard rule does not get to fire.
    Over-routing to review is recoverable. The other way is not.
    """
    if rule_decision not in S02_DECISIONS:
        raise ValueError(f"unknown decision {rule_decision!r}")
    if sensitivity_flags is not None and len(sensitivity_flags) > 0:
        return "restricted_review"
    return rule_decision


def _truthy(v) -> bool:
    """
    None and NaN are both 'absent'. Plain `if row.get(x)` treats NaN as True,
    which silently classified every row as layer 0 the first time round.
    """
    if v is None:
        return False
    if isinstance(v, float) and v != v:      # NaN
        return False
    return bool(v)


def compute_layer(row: dict) -> int:
    """
    Derived from the decision columns, never authored, so it cannot drift.
      0 excluded free  1 not selected  2 enriched not prioritised  3 priority

    v1.1: restricted_review does not get a layer by score — it routes to the
    supervising archivist regardless. A payroll record flagged as a personnel
    matter must not sit in layer 0 waiting to be sampled. Returned as 3 so it
    surfaces in the reviewer's default view.
    """
    if row.get("s02_decision") == "restricted_review":
        return 3
    if (_truthy(row.get("duplicate_of")) or _truthy(row.get("s02_nsrl_hit"))
            or _truthy(row.get("s02_structural_exclusion"))
            or row.get("s02_decision") == "discard_candidate"):
        return 0
    if row.get("s02_decision") == "not_selected":
        return 1
    if row.get("s05_decision") == "priority":
        return 3
    return 2


# --------------------------------------------------------------- disposal --
def eligible_at(selection_completed_at: datetime,
                retention_window_days: int = DEFAULT_RETENTION_DAYS) -> datetime:
    """
    The clock starts when selection completes, NOT at ingest. Material still
    under active consideration is never on a timer.

    Joanne identified the absence of exactly this clock as the reason the
    current backlog exists (answer 5.7), so building it in addresses the cause
    rather than the symptom. She has not yet named a window; 180 days is our
    placeholder and should be replaced with hers.
    """
    if selection_completed_at.tzinfo is None:
        selection_completed_at = selection_completed_at.replace(tzinfo=timezone.utc)
    return selection_completed_at + timedelta(days=retention_window_days)


def may_propose_disposal(row: dict, now: datetime | None = None) -> bool:
    """
    Whether a row may be *proposed* for disposal. Proposing is not disposing —
    a person still approves, in batches, with a record.

    Never true for sensitive material. That decision belongs to a person every
    single time, even though answer 3.3 lists much of it as disposable.
    """
    if row.get("s02_decision") == "restricted_review":
        return False
    if _truthy(row.get("dp_executed_at")):
        return False
    elig = row.get("dp_eligible_at")
    if not _truthy(elig):
        return False
    now = now or datetime.now(timezone.utc)
    if getattr(elig, "tzinfo", None) is None:
        elig = elig.replace(tzinfo=timezone.utc)
    return elig <= now


# ---------------------------------------------------------------- writing --
def enforce(df) -> pa.Table:
    """Cast a DataFrame to the schema. Missing columns become nulls."""
    import pandas as pd  # local import; keeps this module importable without pandas
    names = [f.name for f in MANIFEST_SCHEMA]
    missing = [n for n in names if n not in df.columns]
    if missing:
        # build the absent columns in one go — adding ~130 one at a time
        # fragments the frame and is very slow on large manifests
        pad = pd.DataFrame({n: pd.Series([None] * len(df), dtype=object)
                            for n in missing}, index=df.index)
        out = pd.concat([df, pad], axis=1)
    else:
        out = df
    return pa.Table.from_pandas(out[names], schema=MANIFEST_SCHEMA,
                                preserve_index=False)


def enforce_accessions(df) -> pa.Table:
    import pandas as pd
    names = [f.name for f in ACCESSION_SCHEMA]
    missing = [n for n in names if n not in df.columns]
    if missing:
        pad = pd.DataFrame({n: pd.Series([None] * len(df), dtype=object)
                            for n in missing}, index=df.index)
        df = pd.concat([df, pad], axis=1)
    return pa.Table.from_pandas(df[names], schema=ACCESSION_SCHEMA,
                                preserve_index=False)


def empty_table() -> pa.Table:
    return MANIFEST_SCHEMA.empty_table()
