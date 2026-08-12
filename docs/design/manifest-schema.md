# Manifest Schema — v1.1

**Status:** Revised, not yet frozen. Drafted by Tayler Erbe 7 Aug 2026; revised 12 Aug 2026
against the Archives' answers. For review with Gauri Bhasin.
**Supersedes:** v1.0 (7 Aug 2026).
**Source of the changes:** `docs/archives-answers-2026-08.md`

Decisions are made so we can move. Where a decision rests on something we don't know yet, it
is recorded as an assumption with what would change it. Gauri: if any of this looks wrong to
you, say so. Several are judgement calls rather than facts.

---

## What changed in v1.1, and why

Joanne's answers landed on 12 August. Seven of the nine flags in v1.0 are now resolved, and
one of them — flag 1 — was resolved by being **wrong**, which is the good outcome. It was
caught before the schema froze rather than after 49 accessions were keyed to it.

| Change | Where | Driver |
|---|---|---|
| `source_id` was not an accession number — it is a **record series number**, and it is not unique per delivery | §1.4 | Answer 2.1 |
| New `accession_uid`, a delivery-scoped key. `file_uid` now derives from it | §1.1, §1.4 | Answer 2.1 |
| `TMP-<slug>` removed entirely — unnumbered material does not enter the pipeline | §1.4 | Answer 2.3 |
| New `accession_type` — personal papers and administrative records have **different appraisal rules and different SLAs** | §1.7, §3 | Answers 3.2, 3.3, 8.2 |
| New accession profile side table — the bio context is a rule selector, not just model context | §1.8 | Answers 3.1, 3.2 |
| Design target cut from 5M rows to **10k files per accession** | §2.3 | Answer 1.7 |
| Sharding demoted from conditional to effectively dead | §2.2 | Answer 1.7 |
| `source_media` reordered — network share is the normal case, not the exception | §1.4 | Answers 1.1, 1.2 |
| New `s01_upstream_*` columns for Tracy Popp's existing preservation metadata | §3 Stage 01 | Answer 1.2 |
| **New disposition split: `discard` and `sensitive` are not the same thing** | §3 Stage 02, §6.5 | Answer 3.3 |
| New retention-clock columns — unselected material now gets disposed of, on a timer | §6.5 | Answer 5.7 |
| `s06_access_level` drops `closed` — the Archives uses two values, not three | §3 Stage 06 | Answer 7.3 |
| Delivery is a **fork**, not one destination: preservation copy + access copy + catalogue link | §3 Stage 06 | Answer 5.4, covering email |
| New `accession_archivist` — owns escalation *and* deletion authority | §1.8, Review | Answers 3.4, 6.5 |
| New `rv_role` — accessioning vs supervising archivist are different reviewers | Review | Answers 3.4, 6.2 |
| New Deed of Gift reference and restrictions on the accession record | §1.8 | Answers 6.4, 7.1 |
| Oversight thresholds are now **approved defaults**, recorded here | §6.6 | Answer 6.3 |
| Assumptions 1 and 2 retired; three new ones added | Assumptions | — |

Two flags remain genuinely open, both with Brent, and one of them still blocks Stage 04.

---

## Section 1 — Identity and keys

### 1.1 Primary key

**`file_uid`** — a deterministic 32-character hex digest of `accession_uid + "\x00" + path_norm`,
using BLAKE2b truncated to 128 bits.

Deterministic rather than a generated UUID, because re-crawling the same accession must produce
the same keys. If keys changed on every run, nothing downstream could be joined back and every
reprocess would orphan its own history.

**Changed in v1.1:** scoped by `accession_uid` rather than `source_id`. The reason is §1.4 —
`source_id` turned out not to be unique per delivery, so scoping by it would have collided the
moment a second batch arrived from an office we had already processed. This is precisely the
failure mode flag 1 was raised to catch.

Not the path itself: paths on real drives contain non-UTF-8 bytes, exceed 260 characters, and
carry characters that break Parquet partitioning.

### 1.2 Duplicate content at multiple paths

*Unchanged from v1.0.*

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

*Unchanged from v1.0.*

Own row, same as any other file.

- `virtual_path` — `backup.zip!/reports/2003/q1.pdf`
- `parent_uid` — the containing archive's `file_uid`
- `archive_depth` — 0 for a file on the drive, 1 inside one archive, and so on
- The archive itself keeps its own row, with `s03_status` recording how expansion went

**Recursion limit: 3.** Deeper than that on real material is almost always a backup of a backup
of a backup, and the guard matters more than the content. Anything hitting the limit is flagged
rather than silently dropped.

> **Note, new in v1.1.** `.pst` is in the confirmed format list (answer 1.7) and behaves like an
> archive — it is a container holding many messages. It is handled in the email lane rather than
> the archive lane, but it does produce child rows with `parent_uid` set, and those children
> count against the depth guard. A `.pst` inside a `.zip` is depth 2.

### 1.4 Source identity — **rewritten in v1.1**

v1.0 assumed the leading numbers on the Box folders (`2620267_FemTech`, `2620191_MichaelHart`)
were accession numbers. **They are not.** Per answer 2.1 they are **record series numbers**,
which encode provenance:

```
2620191
││││└┴┴──  sub-series   (2 or 3 digits)
││└┴─────  series        (2 digits)
└┴───────  record group  (2 digits)
```

Published classification list:
<https://archon.library.illinois.edu/archives/index.php?p=collections/classifications>

The consequence that matters: **a record series number identifies where material came from, not
a delivery event.** Two separate deliveries from the same office share a number. So it cannot
be the scope for `file_uid`, and it cannot be the partition key.

We therefore carry both — theirs for provenance, ours for delivery.

| Column | Meaning | Example |
|---|---|---|
| `record_series` | Archives record series number, verbatim | `2620191` |
| `record_group` | Derived — first 2 digits | `26` |
| `series` | Derived — next 2 digits | `20` |
| `subseries` | Derived — remaining 2–3 digits | `191` |
| `accession_uid` | **Ours.** Delivery-scoped key | `2620191-20260812-01` |
| `source_label` | Human-readable mnemonic. **Never parsed, never keyed on** | `MichaelHart` |
| `source_media` | How it arrived | see below |
| `source_ref` | Where it came from | share path, Box folder ID, drive serial, image SHA |
| `source_received` | Date of custody | ISO date |

**`accession_uid` format:** `{record_series}-{received:YYYYMMDD}-{seq:02d}`. The sequence
disambiguates two deliveries on the same day from the same series. Human-readable on purpose —
it appears in directory names and in conversation with archivists, and an opaque UUID there
helps nobody.

**`source_media` values**, reordered from v1.0 to reflect how material actually arrives
(answers 1.1, 1.2):

| Value | When |
|---|---|
| `share` | **The normal case.** Already on the Archives network drive, preservation-processed |
| `drive` | Directly attached media, mounted |
| `image` | A disk image, mounted read-only |
| `box` | Box folder — pilot material and one-off transfers only |

Optical media, floppies and USB sticks do not appear here. Per answer 1.2 those are handled
upstream by Tracy Popp before material reaches us; by the time we see it, it is files on a
share. If that ever changes, add a value — but do not build acquisition tooling we have no use
for.

#### Material with no record series number

**It does not enter the pipeline.** Per answer 2.3:

> If it does not have a number when we are formally accessioning, I think we need to set it
> aside (not put it into the pipeline) until it has a number.

The `TMP-<slug>` fallback from v1.0 is **deleted**. This is a real simplification — no holding
pen, no provisional identifiers, no reconciliation logic, no re-crawl-after-correction path.
Ingest validates the number at the door and refuses with a clear message.

#### Validation

The number is human-assigned by an accessioning archivist (answer 2.2), so the software
**never generates one**. It only checks:

- shape — 6 or 7 digits, no separators
- `record_group` appears in the published classification list, loaded from a local copy
  refreshed on a schedule
- unrecognised → **flag for a person**, never auto-correct, never guess

### 1.5 Path normalisation

*Unchanged from v1.0.*

**Both, always.**

- `path_raw` — byte-faithful, decoded with `surrogateescape` so nothing is lost or corrupted
- `path_norm` — forward slashes, Unicode NFC, leading and trailing whitespace stripped,
  case preserved
- `path_norm_ci` — lowercase of the above, for matching only

`path_raw` is what appears in the finding aid and in provenance. `path_norm` is what we join
on. Never show `path_norm` to a researcher as though it were the original.

### 1.6 Paths that break things

*Unchanged from v1.0.*

Store the raw path, flag the problem, never fail the crawl and never rename anything.

`path_flags` is a list column, any of: `non_utf8`, `over_260`, `trailing_space`,
`reserved_name` (CON, PRN, AUX, NUL, COM1–9, LPT1–9), `control_chars`, `leading_dot`,
`no_extension`.

Every one of these appears on old drives, and a crawler that dies on the first one is useless.
The flags also feed triage — a file named `AUX` is more likely to be an artefact than a record.

### 1.7 Accession type — **new in v1.1**

`accession_type`, an enum on every row, set once at ingest:

| Value | Meaning |
|---|---|
| `personal_papers` | Faculty, alumni, personal donations |
| `administrative` | University office records — Chancellor's Files, President's Office, deans |

This is not cosmetic. Answers 3.2, 3.3 and 8.2 make the two types genuinely different systems:

| | `personal_papers` | `administrative` |
|---|---|---|
| Always keep | Correspondence, grant applications and reports, books and articles, committee and board material, courses taught | Dean/Director communications, annual reports, task force reports, minutes and agendas, budgets, enrolment statistics, curriculum change drafts and finals |
| Nearly always discard | OS and application files, installers, personal finance, commercial entertainment | Accounting detail — purchases, payroll, timesheets |
| Sensitive, **never auto-discard** | Personal finance, family correspondence | HR — FMLA, discipline matters, personnel discussions |
| Drafts | **Depends on discipline** — discardable for a scientist, valuable for a humanities scholar (see §1.8) | Keep, both drafts and finals |
| Target turnaround | 3–6 months | ≤ 3 months |

Triage branches on this column. It was not in v1.0 and its absence would have produced one
averaged rule set that was wrong for both.

### 1.8 Accession record — **new in v1.1**

Per-file columns are the wrong home for facts that are true of a whole accession. These live
in `accessions.parquet`, one row per `accession_uid`, joined at read time.

| Column | Type | Notes |
|---|---|---|
| `accession_uid` | string | key |
| `record_series` | string | |
| `source_label` | string | |
| `accession_type` | string | see §1.7 |
| `source_media` | string | |
| `source_ref` | string | |
| `source_received` | date | |
| `accession_archivist` | string | **Owns escalation and deletion authority** (answers 3.4, 6.5) |
| `profile_person` | string | Whose material this is |
| `profile_department` | string | |
| `profile_field` | string | Discipline — **selects the drafts rule**, see §1.7 |
| `profile_active_years` | string | e.g. `1978–2004` |
| `profile_summary` | string | Half a page. What they worked on |
| `profile_source` | string | Who wrote it, when |
| `deed_of_gift_ref` | string | Pointer only. The Deed itself stays in Library central storage |
| `deed_restrictions` | string | Restrictions it imposes, in enforceable terms |
| `legal_hold` | bool | Freezes the accession. Currently false everywhere (answer 7.2) |
| `selection_completed_at` | timestamp | **Starts the retention clock** — see §6.5 |
| `retention_window_days` | int32 | Default 180, configurable per accession |

**On the profile.** Answer 3.1 confirmed the Archives can produce these and agreed they should
exist. v1.0 treated context as something to pass to a model; that undersells it. `profile_field`
is a **rule selector** — it decides whether drafts are junk or the most valuable thing on the
drive. That is a branch in the code, not a hint in a prompt.

**On the Deed of Gift.** Answer 7.1 was a misunderstanding of my question, and it was my
question's fault. To be clear about what this is: the Deeds stay where they are, in Library
central storage and with the U of I Foundation. What we carry is a **reference plus the
restrictions in enforceable form**, so the system applies them automatically rather than
depending on someone remembering. Still to be confirmed with Joanne, rephrased.

---

## Section 2 — Storage and scale

### 2.1 Format

*Unchanged from v1.0.*

**Parquet**, queried with **DuckDB**.

Parquet gives columnar compression and predicate pushdown, so triage can read three columns
out of eighty without loading the rest. DuckDB queries Parquet in place, so there's no separate
database to keep in sync. SQLite would need everything loaded and rewritten; Delta is more
machinery than a two-person project needs.

### 2.2 Partitioning — **revised in v1.1**

**By `accession_uid`** (was `source_id`). One directory per delivery.

`manifest/{accession_uid}/gen{N}/`

The sharding scheme from v1.0 — first two hex characters of `file_uid`, triggered above 2
million rows — **stays in the schema but is now effectively dead code.** Per answer 1.7 a real
accession runs 100 to 10,000 files. Nothing will approach the threshold. Keep the trigger as a
safety valve, delete the expectation that anyone will ever hit it, and do not spend engineering
time on it.

### 2.3 Design target — **revised substantially in v1.1**

**Was:** 5 million rows, ~90 columns, per accession.
**Now:** **100 to 10,000 files per accession, ~49 accessions in the backlog.**

From answer 1.7:

> If it is from someone copying a laptop or workstation, we'll have everything from "My
> Computer" — 25 or 30 folders, and file counts from 100 to 10,000.

And answer 1.4: 49 collections in the personal-papers backlog, all already on a network drive.

At 3,000 files average, the entire personal-papers backlog is roughly **150,000 files.** That
is three orders of magnitude below what v1.0 was designed for.

**What this changes in practice:**

- A whole accession fits in memory. Comfortably. On Gauri's 16 GB laptop.
- Sharding is unnecessary — see §2.2.
- **We should stop optimising for throughput.** Combined with answer 8.2 (3–6 months acceptable
  turnaround), there is no scale pressure at all here. Every design choice between *faster* and
  *more accurate, more auditable, more human-checked* should now go the second way. The
  cheap-filters-first architecture stays because it is good design and keeps costs down, not
  because we need it to survive the volume.
- The throughput model and drive sizing calculator need rebuilding around these numbers. What
  was a capacity-planning exercise is now closer to a cost estimate.

**Still unknown:** total bytes. 10,000 files could be 2 GB of documents or 800 GB with video —
and `.mov` and `.mp4` are both in the confirmed format list. **File count is settled; size is
not.** One `du -sh` on the network share answers it.

The two backlogs excluded from the 49 remain unquantified: email, and the 12,000 images already
seen in the pilot.

### 2.4 Where it lives — **revised in v1.1**

| Phase | Location |
|---|---|
| During processing | Local scratch on the processing host, `manifest/{accession_uid}/` |
| Working copy | Google Drive when Gauri is on Colab |
| Delivered | See Stage 06 — this is now a fork, not one destination |
| Archived | With the accession's preservation package |

**Not in GitHub.** Manifests contain real filenames from real accessions. `.gitignore` blocks
`*.parquet`; the discipline is not uploading them by hand.

> **⚑ FLAG A — Joanne (was flag 4, partially answered):** where the *working copy* of a full
> accession may live during processing is still open — Joanne said "I will find out." This
> holds unreviewed personal information, so it needs a location, access control, and a clearing
> rule. The retention side is now answered (§6.5); the location side is not.

### 2.5 One manifest per accession, plus a shared content index

*Unchanged in substance; keyed on `accession_uid` rather than `source_id`.*

Per-accession manifests, plus a single global `content_index.parquet` holding
`content_sha256`, `first_seen_accession_uid`, `first_seen_uid`, `occurrence_count`.

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
| `accession_uid` | string | **new in v1.1** — delivery-scoped, see §1.4 |
| `record_series` | string | **renamed in v1.1** — was `source_id` |
| `record_group` | string(2) | **new** — derived |
| `series` | string(2) | **new** — derived |
| `subseries` | string | **new** — derived, 2–3 digits |
| `accession_type` | string | **new in v1.1** — see §1.7 |
| `source_label` | string | human mnemonic, never parsed |
| `source_media` | string | share / drive / image / box |
| `source_ref` | string | share path, Box folder ID, drive serial, image hash |
| `source_received` | date | custody date |
| `manifest_generation` | int8 | increments on full reprocess |
| `schema_version` | string | `1.1` |

### Stage 01 — Inventory and identify (`s01_`)

*Unchanged from v1.0 except for the upstream block at the end.*

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

#### Upstream preservation metadata — **new in v1.1**

Answer 1.2 revealed that Tracy Popp already performs format identification and produces
descriptive, preservation and administrative metadata **before material reaches the network
drive we read from.** Some of Stage 01 may therefore be duplicated work.

| Column | Type | Notes |
|---|---|---|
| `s01_upstream_present` | bool | Existing preservation metadata found for this file |
| `s01_upstream_source` | string | Which tool produced it — BitCurator, DROID, other |
| `s01_upstream_format` | string | Their format identification, verbatim |
| `s01_upstream_json` | string | Their full record, unaltered |
| `s01_upstream_agrees` | bool | Their format ID matches ours |

**We do not overwrite their work and we do not silently discard it.** We record it, run our own
identification alongside, and flag disagreement — which is a useful signal in both directions.

**These columns are speculative until we see Tracy's actual output.** The shape may be wrong.
This is a placeholder that makes the intent explicit, not a finished design.

> **⚑ FLAG B — Joanne → Tracy Popp (new in v1.1):** what does the existing preservation
> processing produce? Which tool, what fields, what format, and does it travel with the content
> onto the share? This is the highest-value unanswered question in the project right now, and
> it may let us delete code rather than write it.

### Stage 02 — Triage pass 1 (`s02_`) — **revised in v1.1**

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
| `s02_decision` | string | **enum revised — see below** |
| `s02_rule_matched` | string | **new** — which named retain/discard rule fired |
| `s02_ruleset` | string | **new** — `personal_papers` or `administrative`, from §1.7 |
| `s02_rationale` | string | human-readable |
| `s02_policy_version` | string | appraisal policy version |
| `s02_status` / `s02_error` / `s02_version` | string | |

#### The decision enum — **the most important change in this section**

v1.0 had `s02_decision ∈ {selected, not_selected}`. That binary cannot express what answer 3.3
actually describes. Joanne listed HR material — FMLA, discipline matters, personnel discussions
— as **both** routinely discardable **and** sensitive. Those are different dispositions and
collapsing them is dangerous: it would let the system route sensitive personnel material onto
the discard pile on a rule match, with no human ever seeing it.

| Value | Meaning | What happens next |
|---|---|---|
| `selected` | Retain — matched a keep rule or scored high | Continues to enrichment |
| `not_selected` | Retain-pending — did not make the cut | Sits in layer 1, subject to the retention clock |
| `discard_candidate` | Matched a discard rule, nothing sensitive about it | Layer 0, sampled review, then the clock |
| `restricted_review` | **Sensitive. Never auto-discarded, whatever else matched** | Routed to a supervising archivist, always |

**Rule: a sensitivity match always wins over a discard match.** If a file is both "payroll
record" and "personnel discussion", it goes to `restricted_review`. The discard rule does not
get to fire. This is a hard precedence, encoded in the ruleset, not a scoring weight.

Keeping `s02_file_score` and `s02_folder_score` separate remains deliberate. "Included because
it sits in a folder that is 70% significant" is an auditable reason; a single blended number is
not.

### Stage 03 — Extraction and routing (`s03_`)

*Unchanged from v1.0. The lane list is now confirmed rather than assumed.*

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

**Confirmed lane priority, from answer 1.7.** The Archives' own format list is
`.xls .doc .pdf .txt .csv .mov .jpg .mp4 .eml .pst` — which maps to `document`, `tabular`,
`image`, `av` and `email`, in roughly that order of volume. Build those five properly first.

**`.eml` and `.pst` are in the personal-papers accessions themselves.** Email is not a separate
later phase — it arrives inside the same drives as everything else. The email lane is required
in the main line, and the pilot email work is not redundant.

Answer 8.4 confirms specialist disciplines are represented, but the format list above is
office-typical, so `scientific` is the tail rather than the body. An unrecognised specialist
format should **route to human attention, not fail**.

### Stage 04 — Enrichment (`s04_`)

*Unchanged from v1.0.*

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

> **⚑ FLAG C — Brent West (was flag 2, still unanswered):** where does the PII mapping store
> live, who can read it, and does it need encryption at rest? This question was addressed to
> Brent in the questions document and came back blank. **Still blocking Stage 04.** Chase him
> directly rather than routing through Joanne.

**New for the sensitivity taxonomy.** Answer 3.3 names categories the Archives cares about that
should be checked against the nine-category set from POC 3: HR and personnel matters, discipline
records, FMLA and medical leave, personal finance. Personal finance is a double signal — it is
both a discard rule and a PII indicator, and should feed both.

**Cleared to process unredacted content.** Answer 7.5 — both Tayler and Gauri have permission
to see unredacted material during processing. Joanne asked in return whether AITS has a
confidentiality agreement template the Archives could model. That is an owed favour, not a
schema item, but it is recorded here so it does not get lost.

### Stage 05 — Triage pass 2 and metadata (`s05_`) — **revised in v1.1**

| Column | Type | Notes |
|---|---|---|
| `s05_score` | float32 | re-ranked using generated metadata |
| `s05_band` | string | |
| `s05_decision` | string | `priority` / `retained` |
| `s05_rationale` | string | |
| `dc_title` … `dc_rights` | string | the 15 Dublin Core elements |
| `iptc_*` | string | images only |
| `s05_generated_fields` | list\<string\> | which DC fields were machine-written |
| `s05_generated_by` | string | **new** — model and version that wrote them |
| `s05_generated_at` | timestamp | **new** | |
| `s05_human_reviewed` | bool | **new** — has a person checked the generated description |
| `s05_status` / `s05_error` / `s05_version` | string | |

**Answer 5.3 was an unqualified yes:** machine-generated description must be visibly marked as
such. v1.0 had `s05_generated_fields` alone, which records *which* fields but not *what wrote
them*, *when*, or *whether anyone checked*. Those are three separate questions an archivist
reading a finding aid in ten years will want answered, so they are three columns. This is a
schema requirement, not a display convention.

Blank still beats confidently wrong.

> **⚑ FLAG D — Joanne (was flag 3, partially answered):** answer 5.1 was "unsure how to
> answer," which is a fair response to a badly-framed question. Re-ask it as a proposal to
> react to rather than a blank: **Dublin Core for descriptive metadata, PREMIS for preservation
> events, mapped to whatever the destination repository accepts.** Answer 5.2 tells us the
> Archives works in **EAD finding aids at collection level**, and that collection-level
> description already exists for these collections — so we produce file-level description that
> *attaches to* an existing finding aid. We are not generating finding aids and must not
> overwrite them.

### Stage 06 — Index and delivery (`s06_`) — **revised in v1.1**

| Column | Type | Notes |
|---|---|---|
| `s06_indexed` | bool | |
| `s06_index_id` | string | vector store reference |
| `s06_cluster_id` | int32 | topic cluster |
| `s06_access_level` | string | **`open` / `restricted` only** |
| `s06_preservation_ref` | string | **new** — where the preservation copy landed |
| `s06_access_ref` | string | **new** — where the access copy landed, null if restricted |
| `s06_catalogue_ref` | string | **new** — the ArchivesSpace record this hangs off |
| `s06_delivery_status` | string | **new** — per-destination outcome |

#### Access levels

`closed` is **removed**. Answer 7.3: the Archives uses `open` and `restricted`. Two values. We
use their vocabulary rather than inventing gradations they do not have.

#### Delivery is a fork — the architecture v1.0 did not have

Answer 5.4 and Joanne's covering email together describe three destinations, not one:

```
                    ┌──→  Medusa (or its replacement)      preservation copies, all retained material
  Stage 06  ────────┤
                    ├──→  Library Digital Library          access copies, unrestricted material only
                    │
                    └──→  ArchivesSpace                    description + links out to the above
```

Three things follow:

1. **IDEALS is out.** v1.0's assumption was wrong — corrected.
2. **ArchivesSpace is a system we design against, and it was not previously on the list.** It
   is being adopted now ("our soon-to-be archives searchable database"), which means the window
   to influence how digital accession description enters it is open. It also answers §5.8 of
   the questions document in practice: item-level description does not go *into* the finding
   aid, it is *linked from* it.
3. **Medusa is being replaced, likely by a commercial product.** Building tightly to its
   current ingest format is building to something with a known expiry.

**Therefore: the pipeline emits a repository-neutral package, and a thin adapter maps it to
whatever the destination currently is.** `src/delivery/adapters/{medusa,digital_library,
archivespace}.py`. Cheap now, saves a rebuild when Medusa is replaced. This should be recorded
as a design decision in its own right.

> **⚑ FLAG E — Joanne (new in v1.1):** access model may differ by material type. Her email
> raises a stand-alone workstation in the Archives for email access, versus catalogue links for
> documents — and asks whether that should be a searchable index or a browsing interface. That
> is a real design fork in Stage 06 and needs its own decision, not an assumption.

### Review (`rv_`) — written by humans, not by any stage — **revised in v1.1**

| Column | Type | Notes |
|---|---|---|
| `rv_machine_decision` | string | snapshot before override |
| `rv_final_decision` | string | what actually holds |
| `rv_reviewer` | string | |
| `rv_role` | string | **new** — `accessioning` / `supervising` |
| `rv_at` | timestamp | |
| `rv_reason` | string | |
| `rv_layer` | int8 | which layer they were looking at |
| `rv_sample_selected` | bool | **new** — was this row drawn as part of an audit sample |

**`rv_role` is new because there are two reviewers, not one.** Answer 3.4: the accessioning
archivist handles general appraisal and pulls in subject-matter experts as needed. Answer 6.2:
sensitive content goes to a **supervising archivist**. Different people, different queues,
different authority. Deletion authority sits with the accessioning archivist for their own
accession (answer 6.5), which is why `accession_archivist` is on the accession record in §1.8.

---

## Section 4 — Types, nulls, failures

*This section is unchanged from v1.0 in its entirety. Nothing in the Archives' answers touched
it.*

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

`embeddings/{accession_uid}.parquet` — `file_uid`, `vector` (fixed-size list\<float32\>),
`model`, `created_at`. The manifest keeps `s02_has_embedding` and the model name.

At 384 dimensions a vector is ~1.5 KB. Note that at the revised scale of §2.3 this is now a far
smaller concern — 10,000 rows is 15 MB, not 7.5 GB. The separation stays because it is clean,
not because it is forced.

### 4.4 Extracted text

**On disk, pointer in the manifest.**

`s03_text_path` points at `text/{accession_uid}/{uid[:2]}/{uid}.txt`. `s03_text_sample` holds
the first 2 KB so a human can eyeball a row without opening a file. `s03_text_len` supports
filtering.

A 300-page PDF is megabytes of text. Multiply by even a thousand files and the manifest stops
being a manifest.

### 4.5 Datetimes

- Stored as `timestamp[us, tz=UTC]`, always timezone-aware
- The original string is kept in `mtime_raw`, regardless
- A timestamp is **suspect** if it is before 1980-01-01 (the FAT epoch floor), after
  `now + 1 day`, or exactly epoch zero
- Suspect timestamps: `mtime` set null, raw retained, flag added to `date_flags`

Old drives are full of wrong dates — epoch-zero from bad copies, 2099 from dead CMOS batteries.
Silently trusting them corrupts any date-based appraisal.

### 4.6 Nested structures

**JSON string columns, plus typed side tables per lane.**

`s03_header_facts_json` holds the raw facts. A GeoTIFF yields CRS, extent, bands; an HDF5 file
yields dataset names, shapes, units. Forcing those into one schema would be mostly nulls.

Where a lane gets heavy use, add `lanes/{lane}_{accession_uid}.parquet` with proper columns,
keyed on `file_uid`. Build those when a lane earns it, not up front.

---

## Section 5 — Versioning and reprocessing

*Unchanged from v1.0 except for path keys.*

### 5.1 Granularity

**Per stage, not per field.** Every stage writes `sNN_version`. LLM stages also write
`sNN_model` and `sNN_prompt_version`.

Per-field provenance would roughly double the column count to answer a question nobody asks.
Per-stage answers the real one: *what produced this, and can I trust it?*

The exception is Stage 05 descriptive metadata, which now carries `s05_generated_by`,
`s05_generated_at` and `s05_human_reviewed` — because answer 5.3 makes that specific
provenance a stated requirement of the Archives, not an internal engineering convenience.

### 5.2 Reprocessing

**New generation. Never overwrite in place.**

`manifest/{accession_uid}/gen{N}/` — increment `manifest_generation`, keep the prior generation.
Because `file_uid` is deterministic, generations join cleanly and you can diff them.

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

> **On v1.0 → v1.1 specifically.** This is a major change by that definition — `source_id` is
> renamed and `file_uid`'s derivation changes, which means every key changes. **The migration
> cost is zero because no production manifest exists yet.** That is the entire value of having
> asked the question before freezing. If this had surfaced after 49 accessions were processed,
> it would have been a full re-crawl of everything.

---

## Section 6 — Decisions and reversibility

### 6.1 Auditable triage decisions

A decision is never a bare value. It is always five things: the decision, the score, a
human-readable rationale, the policy version that produced it, and a timestamp.

Applies at both passes — `s02_*` and `s05_*`.

**Revised in v1.1:** v1.0 said "nothing is ever deleted, so a decision is a label, not an
action." The first half of that is no longer true — see §6.5. A decision is still a label, and
the pipeline still never deletes autonomously, but deletion is now an explicit part of the
lifecycle rather than something we ruled out.

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

**New in v1.1:** `restricted_review` rows are **not** assigned a layer by score. They route to
the supervising archivist's queue regardless of where they would otherwise land. A payroll
record flagged as a personnel matter does not sit in layer 0 waiting to be sampled.

### 6.4 The reviewer's view

A fixed column subset, defined once in `src/schema/views.py`:

`file_uid`, `path_raw`, `filename`, `extension`, `size_bytes`, `mtime`, `s01_format_name`,
`s03_text_sample`, `s04_summary`, `s04_sensitivity_flags`, `s05_score`, `s05_rationale`,
`layer`, `dc_title`, `dc_date`, `s05_generated_fields`

**Added in v1.1:** `accession_type`, `s02_rule_matched`, `s05_human_reviewed`.

Those columns must be human-readable. Everything else is machine-facing and can be as terse as
it likes.

### 6.5 Retention and disposal — **new in v1.1, and a correction**

Answer 5.7 corrected a design position I had over-applied, and Joanne is right:

> Which software never deletes? Regardless, once we have COMPLETED the selection stage of
> accessioning, everything else should be deleted. If there is a chance we need more time to
> decide, we will want a clear time period for when that content needs to be acted on. This has
> been one of our challenges — we didn't set such a time period when the backlog content was
> originally brought in.

v1.0 treated never-deleting as a safety property full stop. It is a safety property *of the
software's autonomous behaviour*, not a description of the archival lifecycle. The Archives
does dispose of material, deliberately, after selection — and answer 6.4 confirms nothing
externally prevents it.

**The last sentence of that answer is the important one.** The absence of a retention clock is
what created the backlog in the first place. Building one in addresses the root cause, not just
the symptom.

| Column | Type | Notes |
|---|---|---|
| `dp_eligible_at` | timestamp | `selection_completed_at + retention_window_days` |
| `dp_proposed_at` | timestamp | When the system surfaced it for disposal |
| `dp_approved_by` | string | The accession archivist (answer 6.5) |
| `dp_approved_at` | timestamp | |
| `dp_batch_id` | string | Disposal happens in batches, never per-file |
| `dp_executed_at` | timestamp | |
| `dp_manifest_retained` | bool | **Always true** — see below |

**The rules:**

- The pipeline **never deletes autonomously.** Unchanged, and non-negotiable.
- The pipeline **does** provide a deletion action: batched, explicitly approved by the
  accession archivist, and recorded with who and when.
- The clock starts at `selection_completed_at` on the accession record, not at ingest. Material
  under active consideration is never on a timer.
- **`restricted_review` material is never auto-proposed for disposal.** Sensitive personnel
  material may well be discardable, but that decision is a person's, every time.
- **The manifest row survives deletion of the content.** We keep the record that a file existed,
  its path, its hash, its size, its dates, and the decision and rationale that led to its
  disposal. That is the audit trail, it is tiny, and destroying it would make the disposal
  unaccountable.

### 6.6 Oversight thresholds — **approved, new in v1.1**

Answer 6.3 approved the proposed oversight positions without qualification. They are no longer
a proposal; they are the configured defaults. Each is a parameter in
`src/schema/oversight.py`, not a constant.

| Situation | Oversight |
|---|---|
| Anything flagged sensitive | Full human review, always |
| Discard decisions, first accession | Full review — the first accession is calibration |
| Discard decisions, later accessions | 5–10% sample, plus everything borderline |
| Auto-selected material | 5–10% audit sample |
| Deleting anything | Explicit approval, in batches, recorded |

`rv_sample_selected` marks rows drawn as part of a sample, so audit coverage is measurable
rather than assumed.

---

## Section 7 — Practical

### 7.1 Naming

`snake_case`. Stage prefixes `s01_` through `s06_`, `rv_` for review, `dp_` for disposal,
`dc_`/`iptc_` for metadata standards. Core identity and filesystem facts unprefixed, because
they belong to the file rather than to a stage.

### 7.2 Where the schema lives

**`src/schema/manifest.py`** — a single pyarrow schema plus helpers, imported by every stage.
The schema is enforced, not assumed. Nothing writes a Parquet file without going through it.

**Added in v1.1:** `src/schema/accession.py` for the accession record (§1.8),
`src/schema/rules/{personal_papers,administrative}.py` for the two rule sets (§1.7), and
`src/schema/oversight.py` for §6.6.

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

**Added in v1.1:**

- `record_series` is 6 or 7 digits, and `record_group` appears in the classification list
- `accession_uid` resolves to a row in `accessions.parquet`
- `accession_type` is set on every row and matches the accession record
- **no row has `s02_decision = 'discard_candidate'` while carrying a sensitivity flag** — this
  is the precedence rule from Stage 02, and it is worth a hard assertion rather than trust
- no row is proposed for disposal before `dp_eligible_at`
- `s05_generated_fields` is non-empty wherever `s05_generated_by` is set, and vice versa

### 7.4 Test fixture

**`tests/fixtures/manifest_50.parquet`** — 50 synthetic rows, committed, covering every format
class, every status value, every path flag, duplicates, archive children at depths 1–3, and
rows at each layer. No real content, so it is safe in a public repo.

**Added in v1.1:** the fixture must now also cover both `accession_type` values, all four
`s02_decision` values, the discard-versus-sensitive precedence case, and at least one row past
`dp_eligible_at`. Two accession records, one of each type, in
`tests/fixtures/accessions_2.parquet`.

Tests run without Box, without a drive, and without credentials.

---

## Assumptions

| # | Assumption | Why | What would change it |
|---|---|---|---|
| ~~1~~ | ~~≤5M files per accession~~ | **Retired v1.1** — answer 1.7 gives 100–10,000 | — |
| ~~2~~ | ~~Box folder prefixes are accession numbers~~ | **Retired v1.1 — wrong.** They are record series numbers | — |
| 3 | 384-dim embeddings | MiniLM/bge-small default | Switching to a larger embedding model |
| 4 | Recursion depth 3 is enough | Deeper is almost always backup-of-backup | Real archives hitting the limit often |
| 5 | Per-stage provenance is sufficient | Per-field doubles columns for little gain | An audit requirement demanding field-level |
| 6 | 1980 is a valid floor for timestamps | FAT epoch; nothing genuine predates it | Material genuinely digitised earlier |
| 7 | **New.** Total bytes are modest despite `.mov`/`.mp4` in the format list | File counts are small; video is presumably a minority | One `du -sh` on the share. Until then this is a guess |
| 8 | **New.** Tracy's upstream metadata is machine-readable and travels with the content | It is described as systematic preservation processing | Seeing her actual output — flag B |
| 9 | **New.** A 180-day default retention window is reasonable | Nothing external sets it; answer 6.4 confirms no schedule | Joanne naming a period she prefers |

---

## Flagged for follow-up

**Resolved since v1.0:** flags 1, 3 (partially), 4 (partially), 5, 6, 8, 9.

| # | Item | Who | Status |
|---|---|---|---|
| A | Where the working copy of a full accession may live during processing | Joanne | **Open** — "I will find out." Retention side now answered; location is not |
| B | What Tracy Popp's existing preservation processing produces — tool, fields, format | Joanne → Tracy | **Open, new, high value.** May let us delete Stage 01 code rather than write it |
| C | PII mapping store — location, access, encryption at rest | **Brent** | **Open, still blocking Stage 04.** Went unanswered; chase directly |
| D | Metadata standard — re-ask as a proposal, not a blank | Joanne | Partially answered. EAD at collection level confirmed; the DC/PREMIS proposal is ours to put |
| E | Access model by material type — workstation for email vs catalogue links for documents; index vs browse | Joanne | **Open, new.** From her covering email. A real Stage 06 design fork |
| F | Sensitivity taxonomy — is the nine-category set from POC 3 still right, given answer 3.3 | Bethany | Open. Answer 3.3 names categories to check it against |
| G | Total size on disk of the 49 collections | Joanne / Tracy | Open. File count is settled; bytes are not. One command answers it |
| H | Retention window default — is 180 days the period the Archives wants | Joanne | Open, new. Answer 5.7 asks for "a clear time period" without naming one |
| I | ePADD deployment — will Library IT permit a Java runtime | Joanne → Library IT | Open. **May settle the email lane on security grounds before evaluation finishes** |

---

## Sign-off

| | Name | Date |
|---|---|---|
| Drafted by | Tayler Erbe | 2026-08-07 |
| Revised against Archives answers | Tayler Erbe | 2026-08-12 |
| Reviewed by | Gauri Bhasin | |
| Schema v1.1 frozen | | |

**Not frozen yet, and it should not be until flag C is answered** — the PII mapping store
determines whether `s04_pii_map_ref` is a path, a URI, or a key into something with its own
access-control model. That is a type decision, not a value decision, and it is cheaper to make
now than after.
