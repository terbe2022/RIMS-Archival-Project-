# Manifest schema — changelog

Every change to the manifest schema, with a date and a reason. Required by
[`manifest-schema.md`](manifest-schema.md) §5.4.

**Rules.** Minor = adding a nullable column; no migration, readers tolerate missing columns.
Major = renaming, retyping, or changing meaning; needs a migration script in
`src/schema/migrations/` and increments `manifest_generation`.

---

## v1.1 — 12 August 2026 · **major**

**Driver:** [`../stakeholders/answers-2026-08.md`](../stakeholders/answers-2026-08.md)
**Migration:** none required — no production manifest existed. This is the entire value of
having asked before building.

### Breaking

| Change | Reason |
|---|---|
| `source_id` → `record_series`, plus derived `record_group`, `series`, `subseries` | Answer 2.1 — these are record series numbers, not accession numbers |
| **New `accession_uid`; `file_uid` now derives from it, not from `record_series`** | A record series number is not unique per delivery. Two accessions from the same office share one, so the old derivation would have produced **silent key collisions** — not a crash, two files mapping to one row |
| `TMP-<slug>` provisional identifiers removed entirely | Answer 2.3 — material without a number does not enter the pipeline. Removes the holding pen, the reconciliation logic, and the re-crawl-after-correction path |
| `s02_decision` enum extended from 2 values to 4 | Answer 3.3 — HR material is both discardable and sensitive, and those are different dispositions |
| `s06_access_level` drops `closed` | Answer 7.3 — the Archives uses `open` and `restricted` |
| Partition key `source_id` → `accession_uid` | Follows the key change |

### Added

| Column / table | Reason |
|---|---|
| `accession_type` on every row | Answers 3.2, 3.3, 8.2 — personal papers and administrative records have different rules and different SLAs |
| `accessions.parquet` — profile, archivist, Deed of Gift ref, retention clock | Facts true of a whole accession do not belong on every row |
| `s01_upstream_present` / `_source` / `_format` / `_json` / `_agrees` | Answer 1.2 — Tracy Popp already produces preservation metadata and format identification. **Speculative until we see real output** |
| `s02_rule_matched`, `s02_ruleset` | Which named rule fired, and from which ruleset |
| `s05_generated_by`, `s05_generated_at`, `s05_human_reviewed` | Answer 5.3 — generated description must be visibly marked. *Which* fields is not enough; *what wrote them*, *when*, and *was it checked* are three separate questions |
| `s06_preservation_ref`, `s06_access_ref`, `s06_catalogue_ref`, `s06_delivery_status` | Answer 5.4 — delivery is a three-way fork, not one destination |
| `rv_role`, `rv_sample_selected` | Answers 3.4, 6.2 — accessioning and supervising archivists are different reviewers. Sample marking makes audit coverage measurable |
| `dp_*` disposal block (7 columns) | Answer 5.7 — disposal is part of the lifecycle, on a clock |

### Changed without breaking

- Design target cut from 5M rows per accession to **100–10,000 files** (answer 1.7). Sharding
  retained as a safety valve but is now effectively dead code.
- Assumptions 1 and 2 retired; three new ones added (total bytes, Tracy's output format,
  180-day retention default).

### New validation rules

- `record_series` is 6 or 7 digits; `record_group` appears in the published classification list
- `accession_uid` resolves to a row in `accessions.parquet`
- `accession_type` set on every row and consistent with the accession record
- **No row carries `s02_decision = 'discard_candidate'` and a sensitivity flag** — hard
  assertion, because this is the failure mode with real consequences
- No row proposed for disposal before `dp_eligible_at`
- `s05_generated_fields` and `s05_generated_by` are set together or not at all

### Not yet frozen

Blocked on the PII mapping store question (D5). It determines whether `s04_pii_map_ref` is a
path, a URI, or a key into an access-controlled store — a type decision, cheaper to make before
freeze than after.

---

## v1.0 — 7 August 2026 · initial

Drafted by Tayler Erbe from the blank worksheet. 116 columns, per-stage ownership, deterministic
`file_uid`, Parquet + DuckDB, layered decisions, per-stage status columns.

Archived at [`../superseded/2026-08-07-manifest-schema-v1.md`](../superseded/2026-08-07-manifest-schema-v1.md).

Nine items were flagged for follow-up. Seven were resolved by the 12 Aug answers — **including
flag 1, which came back wrong**, which is why the flag existed.

Two bugs found during testing, both worth remembering:

- **NaN is truthy in Python.** `if row.get("duplicate_of")` classified every row as layer 0, so
  triage would have looked like it was rejecting everything.
- **Adding ~100 columns one at a time fragments the DataFrame.** Fine at 5 rows, awful at scale.
  Less critical now that the scale target dropped, but still the wrong pattern.
