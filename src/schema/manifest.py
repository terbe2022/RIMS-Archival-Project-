"""
manifest.py — the single definition of the manifest schema.

Every stage imports from here. Nothing writes a Parquet file without going
through `enforce()`. The schema is enforced, not assumed.

See docs/W1_manifest_schema_v1.md for the reasoning behind each decision.
"""
from __future__ import annotations

import hashlib
import unicodedata
from datetime import datetime, timezone

import pyarrow as pa

SCHEMA_VERSION = "1.0"
MAX_ARCHIVE_DEPTH = 3
FAT_EPOCH_FLOOR = datetime(1980, 1, 1, tzinfo=timezone.utc)

STATUS = {"ok", "empty", "skipped", "failed", "partial"}   # None = stage not reached
BANDS = {"high", "mid", "low"}
LANES = {"document", "email", "image", "tabular", "scientific", "av", "code", "archive"}
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


CORE = [
    pa.field("file_uid", _S(), nullable=False),
    pa.field("source_id", _S(), nullable=False),
    pa.field("source_label", _S()),
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
])

S06 = [
    pa.field("s06_indexed", pa.bool_()),
    pa.field("s06_index_id", _S()),
    pa.field("s06_cluster_id", pa.int32()),
    pa.field("s06_delivery_path", _S()),
    pa.field("s06_access_level", _S()),
]

REVIEW = [
    pa.field("rv_machine_decision", _S()),
    pa.field("rv_final_decision", _S()),
    pa.field("rv_reviewer", _S()),
    pa.field("rv_at", _TS),
    pa.field("rv_reason", _S()),
    pa.field("rv_layer", pa.int8()),
    pa.field("layer", pa.int8()),          # derived, never authored
]

MANIFEST_SCHEMA = pa.schema(CORE + S01 + S02 + S03 + S04 + S05 + S06 + REVIEW)

# columns the reviewer sees by default — must stay human-readable
REVIEWER_VIEW = [
    "file_uid", "path_raw", "filename", "extension", "size_bytes", "mtime",
    "s01_format_name", "s03_text_sample", "s04_summary", "s04_sensitivity_flags",
    "s05_score", "s05_rationale", "layer", "dc_title", "dc_date",
    "s05_generated_fields",
]


# ---------------------------------------------------------------- helpers --
def normalise_path(raw: str) -> str:
    """Forward slashes, NFC, trimmed. Joins use this; provenance uses path_raw."""
    p = raw.replace("\\", "/")
    p = unicodedata.normalize("NFC", p)
    return p.strip()


def make_uid(source_id: str, path_norm: str) -> str:
    """
    Deterministic 32-hex key. Re-crawling the same accession yields the same
    keys, which is what makes generations joinable and reprocessing safe.
    """
    h = hashlib.blake2b(digest_size=16)
    h.update(source_id.encode("utf-8"))
    h.update(b"\x00")
    h.update(path_norm.encode("utf-8", errors="surrogateescape"))
    return h.hexdigest()


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
    """
    if (_truthy(row.get("duplicate_of")) or _truthy(row.get("s02_nsrl_hit"))
            or _truthy(row.get("s02_structural_exclusion"))):
        return 0
    if row.get("s02_decision") == "not_selected":
        return 1
    if row.get("s05_decision") == "priority":
        return 3
    return 2


def enforce(df) -> pa.Table:
    """Cast a DataFrame to the schema. Missing columns become nulls."""
    import pandas as pd  # local import; keeps this module importable without pandas
    names = [f.name for f in MANIFEST_SCHEMA]
    missing = [n for n in names if n not in df.columns]
    if missing:
        # build the absent columns in one go — adding ~100 one at a time
        # fragments the frame and is very slow on large manifests
        pad = pd.DataFrame({n: pd.Series([None] * len(df), dtype=object)
                            for n in missing}, index=df.index)
        out = pd.concat([df, pad], axis=1)
    else:
        out = df
    return pa.Table.from_pandas(out[names], schema=MANIFEST_SCHEMA,
                                preserve_index=False)


def empty_table() -> pa.Table:
    return MANIFEST_SCHEMA.empty_table()
