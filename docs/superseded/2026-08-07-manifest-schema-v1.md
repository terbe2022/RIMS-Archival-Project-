# Manifest Schema — v1

> **SUPERSEDED by [`docs/design/manifest-schema.md`](../design/manifest-schema.md) (v1.1), 12 Aug 2026.**
> v1.0 assumed the Box folder prefixes were accession numbers. They are record series numbers,
> and they are not unique per delivery — so `file_uid` derived from `source_id` would have
> collided. Kept because the reasoning is still worth reading and because the changelog refers
> back to it. **Do not build against this file.**


**Status:** Decided. Drafted by Tayler Erbe, 7 Aug 2026. For review with Gauri Bhasin.
**Supersedes:** the blank worksheet.

Decisions are made so we can move. Where a decision rests on something we don't know yet, it
is recorded as an assumption with what would change it. Nine items are flagged for follow-up —
listed at the end. Gauri: if any of this looks wrong to you, say so. Several are judgement
calls rather than facts.

---

## Section 1 — Identity and keys

### 1.1 Primary key

**`file_uid`** — a deterministic 32-character hex digest of `source_id + "\x00" + path_norm`,
using BLAKE2b truncated to 128 bits.

Deterministic rather than a generated UUID, because re-crawling the same accession must produce
the same keys. If keys changed on every run, nothing downstream could be joined back and every
reprocess would orphan its own history. Scoped by `source_id` so the same path on two different
accessions cannot collide.

Not the path itself: paths on real drives contain non-UTF-8 bytes, exceed 260 characters, and
carry characters that break Parquet partitioning.

### 1.2 Duplicate content at multiple paths

**One row per path. Always.** Never collapse.

A file appearing in three places is three archival facts — where it sat is evidence about how
the person worked, and that is exactly the kind of context an archivist cares about.
Deduplication is a *decision*, not a *representation*.

So: every path gets a row. `content_sha256` is shared. `duplicate_of` on non-canonical rows
points at the canonical `file_uid`. Canonical = lowest `path_norm` in sort order — arbitrary,
but stable across runs, which is what matters.

Downstream, expensive stages process only rows where `duplicate_of IS NULL`. The duplicates
still exist, still carry their paths, and still appear in search results pointing at the
canonical content.

### 1.3 Files inside archives

Own row, same as any other file.

- `virtual_path` — `backup.zip!/reports/2003/q1.pdf`
- `parent_uid` — the containing archive's `file_uid`
- `archive_depth` — 0 for a file on the drive, 1 inside one archive, and so on
- The archive itself keeps its own row, with `s03_status` recording how expansion went

**Recursion limit: 3.** Deeper than that on real material is almost always a backup of a backup
of a backup, and the guard matters more than the content. Anything hitting the limit is flagged
rather than silently dropped.

### 1.4 Source identity

**Use the Archives' existing accession numbers.** The Box folders are named `2620267_FemTech`,
`2620191_MichaelHart`, `1513059_DonCrummey`, `2415001_VCResearch` — those leading numbers are
almost certainly accession numbers already in use. Inventing a parallel identifier scheme when
one exists would be a mistake we'd regret at delivery.

| Column | Meaning | Example |
|---|---|---|
| `source_id` | Archives accession number | `2620191` |
| `source_label` | Human-readable name | `MichaelHart` |
| `source_media` | How it arrived | `box` / `drive` / `share` / `image` |
| `source_ref` | Where it came from | Box folder ID, drive serial, image SHA |
| `source_received` | Date of custody | ISO date |

Where no accession number exists yet, `source_id` is `TMP-<slug>` and gets corrected later —
which is safe precisely because `file_uid` is derived from it, so a correction means one clean
re-crawl rather than a migration.

> **⚑ FLAG 1 — Joanne:** confirm those numbers are accession numbers, and confirm the format.
> If the Archives has a different identifier we should be using, now is the time.

### 1.5 Path normalisation

**Both, always.**

- `path_raw` — byte-faithful, decoded with `surrogateescape` so nothing is lost or corrupted
- `path_norm` — forward slashes, Unicode NFC, leading and trailing whitespace stripped,
  case preserved
- `path_norm_ci` — lowercase of the above, for matching only

`path_raw` is what appears in the finding aid and in provenance. `path_norm` is what we join
on. Never show `path_norm` to a researcher as though it were the original.

### 1.6 Paths that break things

Store the raw path, flag the problem, never fail the crawl and never rename anything.

`path_flags` is a list column, any of: `non_utf8`, `over_260`, `trailing_space`,
`reserved_name` (CON, PRN, AUX, NUL, COM1–9, LPT1–9), `control_chars`, `leading_dot`,
`no_extension`.

Every one of these appears on old drives, and a crawler that dies on the first one is useless.
The flags also feed triage — a file named `AUX` is more likely to be an artefact than a record.

---

## Section 2 — Storage and scale

### 2.1 Format

**Parquet**, queried with **DuckDB**.

Parquet gives columnar compression and predicate pushdown, so triage can read three columns
out of eighty without loading the rest — which is what makes this work on Gauri's 16 GB
machine. DuckDB queries Parquet in place, so there's no separate database to keep in sync.
SQLite would need everything loaded and rewritten; Delta is more machinery than a two-person
project needs.

### 2.2 Partitioning

**By `source_id`.** One directory per accession.

That matches how the work actually arrives and how it gets delivered, and it means a single
accession can be worked on in isolation.

Within a source, add `shard` — the first two hex characters of `file_uid`, giving up to 256
even buckets — **only when a single source exceeds 2 million rows**. Below that it is
unnecessary complexity. Above it, Gauri can process shard `00` on her laptop without touching
the rest.

### 2.3 Design target

**5 million rows, ~90 columns, per accession.**

At that size a Parquet file is roughly 2–4 GB on disk and a three-column projection is a few
hundred MB in memory — comfortable on a 16 GB laptop.

> **Assumption.** No accession has been measured. If a real drive comes in at 20 million files,
> sharding becomes mandatory rather than conditional and some column-pruning discipline gets
> stricter. The first full inventory tells us.

### 2.4 Where it lives

| Phase | Location |
|---|---|
| During processing | Local scratch on the processing host, `manifest/{source_id}/` |
| Working copy | Google Drive when Gauri is on Colab |
| Delivered | Box, alongside the outputs |
| Archived | With the accession's preservation package |

**Not in GitHub.** Manifests contain real filenames from real accessions. `.gitignore` blocks
`*.parquet`; the discipline is not uploading them by hand.

### 2.5 One manifest per accession, plus a shared content index

Per-accession manifests, plus a single global `content_index.parquet` holding
`content_sha256`, `first_seen_source_id`, `first_seen_uid`, `occurrence_count`.

Small — one row per distinct piece of content — and it catches the case where the same
committee report exists on four people's drives. That is genuinely useful to an archivist, and
it would be invisible if each accession were processed in isolation.

---

## Section 3 — Column ownership by stage

Rule: **no stage writes a column another stage owns.** Prefixes make ownership visible, which
means a stage's output can be dropped and re-run without touching anything else.

### Core identity — written at Stage 00, never modified

| Column | Type | Notes |
|---|---|---|
| `file_uid` | string(32) | primary key |
| `source_id` | string | accession number |
| `source_label` | string | human name |
| `source_media` | string | box / drive / share / image |
| `source_ref` | string | Box folder ID, drive serial, image hash |
| `source_received` | date | custody date |
| `manifest_generation` | int8 | increments on full reprocess |
| `schema_version` | string | e.g. `1.0` |

### Stage 01 — Inventory and identify (`s01_`)

| Column | Type | Notes |
|---|---|---|
| `path_raw` | string | verbatim, surrogateescape |
| `path_norm` | string | joins use this |
| `path_norm_ci` | string | matching only |
| `filename` | string | |
| `extension` | string | lowercase, no dot |
| `parent_folder` | string | |
| `depth` | int16 | |
| `path_flags` | list\<string\> | see 1.6 |
| `size_bytes` | int64 | |
| `mtime` / `ctime` / `atime` | timestamp\[us, UTC\] | null when invalid |
| `mtime_raw` | string | original value, always kept |
| `date_flags` | list\<string\> | `epoch_zero`, `future`, `pre_1980`, `missing` |
| `content_sha256` | string(64) | computed locally |
| `content_sha1` | string(40) | from Box when available |
| `s01_puid` | string | PRONOM ID from Siegfried |
| `s01_format_name` | string | |
| `s01_format_version` | string | |
| `s01_id_confidence` | string | `exact` / `container` / `extension` / `none` |
| `s01_id_method` | string | `siegfried` / `magic` / `extension` |
| `s01_ext_mismatch` | bool | extension disagrees with identified format |
| `parent_uid` | string | archive container, null otherwise |
| `virtual_path` | string | `container!/inner/path` |
| `archive_depth` | int8 | 0 on the drive |
| `s01_status` | string | see 4.1 |
| `s01_error` | string | |
| `s01_version` | string | pipeline version |

`s01_ext_mismatch` earns its place: it directly measures how wrong POC 2's extension-based
routing was, and it is a real triage signal — a `.txt` that is actually an executable is
interesting.

### Stage 02 — Triage pass 1 (`s02_`)

| Column | Type | Notes |
|---|---|---|
| `duplicate_of` | string(32) | canonical `file_uid`, null if canonical |
| `duplicate_count` | int32 | on the canonical row only |
| `s02_nsrl_hit` | bool | known OS/application file |
| `s02_structural_exclusion` | string | `zero_byte` / `temp` / `cache` / `lock` / `vcs` / null |
| `s02_peek_text` | string | ≤8 KB, structured sample |
| `s02_peek_method` | string | `head_tail_strided` / `header_only` / `filename_only` |
| `s02_peek_tier` | int8 | 0–3, escalation ladder |
| `s02_keywords` | list\<string\> | extracted from peek |
| `s02_has_embedding` | bool | vector held separately |
| `s02_folder_score` | float32 | |
| `s02_file_score` | float32 | pre-folder-weighting |
| `s02_score` | float32 | final pass-1 score |
| `s02_band` | string | `high` / `mid` / `low` |
| `s02_decision` | string | `selected` / `not_selected` |
| `s02_rationale` | string | human-readable |
| `s02_policy_version` | string | appraisal policy version |
| `s02_status` / `s02_error` / `s02_version` | string | |

Keeping `s02_file_score` and `s02_folder_score` separate is deliberate. "Included because it
sits in a folder that is 70% significant" is an auditable reason; a single blended number is
not.

### Stage 03 — Extraction and routing (`s03_`)

| Column | Type | Notes |
|---|---|---|
| `s03_lane` | string | `document` / `email` / `image` / `tabular` / `scientific` / `av` / `code` / `archive` |
| `s03_extractor` | string | `tika` / `libreoffice` / `docling` / `gdal` / `h5py` / … |
| `s03_text_path` | string | pointer; text is not in the manifest |
| `s03_text_len` | int64 | |
| `s03_text_sample` | string | first 2 KB, for eyeballing |
| `s03_page_count` | int32 | |
| `s03_header_facts_json` | string | JSON; shapes differ per lane |
| `s03_needs_ocr` | bool | |
| `s03_duration_ms` | int32 | |
| `s03_status` / `s03_error` / `s03_version` | string | |

### Stage 04 — Enrichment (`s04_`)

| Column | Type | Notes |
|---|---|---|
| `s04_summary` | string | |
| `s04_description` | string | images |
| `s04_doc_type` | string | inferred |
| `s04_pii_entities_json` | string | types and counts, **not values** |
| `s04_pii_map_ref` | string | pointer to the restricted mapping store |
| `s04_masked_text_path` | string | pointer |
| `s04_sensitivity_flags` | list\<string\> | the nine-category taxonomy |
| `s04_sensitivity_scores_json` | string | per-category similarity |
| `s04_model` | string | e.g. `qwen2.5-vl:7b-awq` |
| `s04_prompt_version` | string | |
| `s04_duration_ms` | int32 | |
| `s04_status` / `s04_error` / `s04_version` | string | |

**The PII mapping never goes in the manifest.** POC 1 wrote the placeholder-to-real-value
dictionary into a column beside the masked text, which is convenient and defeats the point of
masking. `s04_pii_map_ref` points at a separately access-controlled store.

> **⚑ FLAG 2 — Data Privacy / Brent:** where does the PII mapping store live, who can read it,
> and does it need encryption at rest?

### Stage 05 — Triage pass 2 and metadata (`s05_`)

| Column | Type | Notes |
|---|---|---|
| `s05_score` | float32 | re-ranked using generated metadata |
| `s05_band` | string | |
| `s05_decision` | string | `priority` / `retained` |
| `s05_rationale` | string | |
| `dc_title` … `dc_rights` | string | the 15 Dublin Core elements |
| `iptc_*` | string | images only |
| `s05_generated_fields` | list\<string\> | which DC fields were machine-written |
| `s05_status` / `s05_error` / `s05_version` | string | |

`s05_generated_fields` matters: an archivist reading a finding aid should be able to tell what
a machine wrote. Blank beats confidently wrong.

### Stage 06 — Index and delivery (`s06_`)

| Column | Type | Notes |
|---|---|---|
| `s06_indexed` | bool | |
| `s06_index_id` | string | vector store reference |
| `s06_cluster_id` | int32 | topic cluster |
| `s06_delivery_path` | string | where it landed for the Archives |
| `s06_access_level` | string | `open` / `restricted` / `closed` |

### Review (`rv_`) — written by humans, not by any stage

| Column | Type | Notes |
|---|---|---|
| `rv_machine_decision` | string | snapshot before override |
| `rv_final_decision` | string | what actually holds |
| `rv_reviewer` | string | |
| `rv_at` | timestamp | |
| `rv_reason` | string | |
| `rv_layer` | int8 | which layer they were looking at |

---

## Section 4 — Types, nulls, failures

### 4.1 Not-yet-processed vs processed-and-found-nothing

**A per-stage `sNN_status` column. Null means not reached.**

| Value | Meaning |
|---|---|
| `null` | Stage has not run on this row |
| `ok` | Ran, produced output |
| `empty` | Ran, legitimately found nothing (a blank text file has no text) |
| `skipped` | Deliberately bypassed — record why in `sNN_error` |
| `failed` | Errored |
| `partial` | Some output, some failure |

Unambiguous, cheap to filter, and it makes resumability trivial: `WHERE s03_status IS NULL`
is the work queue.

### 4.2 Recording failures

`sNN_status = 'failed'` plus `sNN_error` holding `ExceptionClass: first 200 chars`.

**No tracebacks in the manifest.** They are large, they vary between runs, and they wreck
compression. Full tracebacks go to a per-run log file keyed on `file_uid`.

### 4.3 Embeddings

**Beside the manifest, not in it.**

`embeddings/{source_id}.parquet` — `file_uid`, `vector` (fixed-size list\<float32\>),
`model`, `created_at`. The manifest keeps `s02_has_embedding` and the model name.

At 384 dimensions a vector is ~1.5 KB. Five million rows is 7.5 GB, which would make every
triage query slow for the sake of a column almost nothing reads.

### 4.4 Extracted text

**On disk, pointer in the manifest.**

`s03_text_path` points at `text/{source_id}/{uid[:2]}/{uid}.txt`. `s03_text_sample` holds the
first 2 KB so a human can eyeball a row without opening a file. `s03_text_len` supports
filtering.

A 300-page PDF is megabytes of text. Multiply by even a thousand files and the manifest stops
being a manifest.

### 4.5 Datetimes

- Stored as `timestamp[us, tz=UTC]`, always timezone-aware
- The original string is kept in `mtime_raw`, regardless
- A timestamp is **suspect** if it is before 1980-01-01 (the FAT epoch floor — nothing genuine
  predates it), after `now + 1 day`, or exactly epoch zero
- Suspect timestamps: `mtime` set null, raw retained, flag added to `date_flags`

Old drives are full of wrong dates — epoch-zero from bad copies, 2099 from dead CMOS batteries.
Silently trusting them corrupts any date-based appraisal.

### 4.6 Nested structures

**JSON string columns, plus typed side tables per lane.**

`s03_header_facts_json` holds the raw facts. A GeoTIFF yields CRS, extent, bands; an HDF5 file
yields dataset names, shapes, units. Forcing those into one schema would be mostly nulls.

Where a lane gets heavy use, add `lanes/{lane}_{source_id}.parquet` with proper columns, keyed
on `file_uid`. Build those when a lane earns it, not up front.

---

## Section 5 — Versioning and reprocessing

### 5.1 Granularity

**Per stage, not per field.** Every stage writes `sNN_version` (pipeline version). LLM stages
also write `sNN_model` and `sNN_prompt_version`.

Per-field provenance would roughly double the column count to answer a question nobody asks.
Per-stage answers the real one: *what produced this, and can I trust it?*

### 5.2 Reprocessing

**New generation. Never overwrite in place.**

`manifest/{source_id}/gen{N}/` — increment `manifest_generation`, keep the prior generation.
Because `file_uid` is deterministic, generations join cleanly and you can diff them: what
changed when we swapped models, and did it get better?

Prune old generations only on an explicit decision, never automatically.

### 5.3 Subset re-runs

**Yes** — that is what the version columns are for.

```sql
WHERE s04_model != 'qwen2.5-vl:7b' OR s04_status = 'failed'
```

Re-runs write in place *within a generation* only for `failed` and `null` rows. Anything
changing already-successful output starts a new generation.

### 5.4 Schema changes

- `schema_version` on every row, semantic versioning
- **Minor** (adding a nullable column) — no migration; readers tolerate missing columns
- **Major** (renaming, retyping, changing meaning) — migration script in
  `src/schema/migrations/`, and the generation increments
- `docs/schema-changelog.md` records every change with a date and a reason

---

## Section 6 — Decisions and reversibility

### 6.1 Auditable triage decisions

A decision is never a bare value. It is always five things: the decision, the score, a
human-readable rationale, the policy version that produced it, and a timestamp.

Applies at both passes — `s02_*` and `s05_*`. **Nothing is ever deleted**, so a decision is a
label, not an action.

### 6.2 Human overrides

`rv_*` columns, plus an append-only `review_log.parquet` recording every review event.

The machine decision is preserved in `rv_machine_decision` when overridden. Disagreement
between machine and human is the most valuable training signal we will ever get — and it is
also how we find out the appraisal policy is ambiguous.

### 6.3 Layered importance

`layer` — an int8 recording how far a file got:

| Layer | Meaning |
|---|---|
| 0 | Excluded by free filters — duplicate, NSRL, structural junk |
| 1 | Not selected by pass 1 |
| 2 | Enriched, then not prioritised by pass 2 |
| 3 | Priority — the reviewer's default view |

Every layer keeps its scores and rationale. The reviewer sees layer 3 by default and can drill
into any layer beneath. Layer is derived, not authored — recomputed from the decision columns —
so it can never drift out of sync with them.

### 6.4 The reviewer's view

A fixed column subset, defined once in `src/schema/views.py`:

`file_uid`, `path_raw`, `filename`, `extension`, `size_bytes`, `mtime`, `s01_format_name`,
`s03_text_sample`, `s04_summary`, `s04_sensitivity_flags`, `s05_score`, `s05_rationale`,
`layer`, `dc_title`, `dc_date`, `s05_generated_fields`

Those columns must be human-readable. Everything else is machine-facing and can be as terse as
it likes.

---

## Section 7 — Practical

### 7.1 Naming

`snake_case`. Stage prefixes `s01_` through `s06_`, `rv_` for review, `dc_`/`iptc_` for
metadata standards. Core identity and filesystem facts unprefixed, because they belong to the
file rather than to a stage.

Prefixes make it obvious who owns what, and let a stage's output be dropped with a
`SELECT * EXCLUDE (s04_*)` and re-run cleanly.

### 7.2 Where the schema lives

**`src/schema/manifest.py`** — a single pyarrow schema plus helpers, imported by every stage.
The schema is enforced, not assumed. Nothing writes a Parquet file without going through it.

### 7.3 Validation

**`src/schema/validate.py`**, run after every stage:

- required columns present, types match
- `file_uid` unique and non-null
- `duplicate_of` references an existing `file_uid` and is never self-referential
- `parent_uid` references an existing archive row
- `archive_depth` ≤ 3
- status values within the allowed enum
- files with `sNN_status = 'ok'` have the outputs that stage promises
- `layer` matches what the decision columns imply

Cheap to run, and it catches integration errors before they compound across stages.

### 7.4 Test fixture

**`tests/fixtures/manifest_50.parquet`** — 50 synthetic rows, committed, covering every format
class, every status value, every path flag, duplicates, archive children at depths 1–3, and
rows at each layer. No real content, so it is safe in a public repo.

Tests run without Box, without a drive, and without credentials.

---

## Assumptions

| # | Assumption | Why | What would change it |
|---|---|---|---|
| 1 | ≤5M files per accession | No accession measured; Box extracts suggest hundreds | First full drive inventory |
| 2 | Box folder prefixes are accession numbers | `2620267_`, `1513059_` look like an existing scheme | Joanne confirming or correcting |
| 3 | 384-dim embeddings | MiniLM/bge-small default | Switching to a larger embedding model |
| 4 | Recursion depth 3 is enough | Deeper is almost always backup-of-backup | Real archives hitting the limit often |
| 5 | Per-stage provenance is sufficient | Per-field doubles columns for little gain | An audit requirement demanding field-level |
| 6 | 1980 is a valid floor for timestamps | FAT epoch; nothing genuine predates it | Material genuinely digitised earlier |

---

## Flagged for follow-up

| # | Item | Who | Why it matters |
|---|---|---|---|
| 1 | Confirm accession-number format and that Box prefixes are real accession numbers | Joanne | `source_id` feeds `file_uid`; changing it means a re-crawl |
| 2 | Where the PII mapping store lives, who reads it, encryption at rest | Data Privacy / Brent | Blocks Stage 04 |
| 3 | Dublin Core simple or qualified; EAD needed for collection level | Joanne | Fixes the `dc_*` columns |
| 4 | Retention rules for layer 0–1 material — how long do we keep what was not selected | Brent | Storage cost, and legally material |
| 5 | Access levels vocabulary for `s06_access_level` | Joanne / Bethany | Should match Archives practice, not invented |
| 6 | Whether the Archives wants file-level or folder-level description delivered | Joanne | Changes what stage 05 produces |
| 7 | Sensitivity taxonomy — is the nine-category set from POC 3 still right | Bethany | Fixes `s04_sensitivity_flags` |
| 8 | Whether duplicate paths across accessions should be surfaced to researchers | Joanne | Justifies the shared content index |
| 9 | Confirm SHA-256 rather than SHA-1 as canonical, given Box gives SHA-1 | Gauri + Tayler | We compute both; confirm which is authoritative |

---

## Sign-off

| | Name | Date |
|---|---|---|
| Drafted by | Tayler Erbe | 2026-08-07 |
| Reviewed by | Gauri Bhasin | |
| Schema v1 frozen | | |
