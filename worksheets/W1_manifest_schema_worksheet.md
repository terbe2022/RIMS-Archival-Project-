# Manifest Schema — Design Worksheet

**Status:** Not started. Nothing has been built yet.
**Owners:** Tayler Erbe + Gauri Bhasin
**Target:** Complete together in Week 1, before any pipeline code is written.

---

## Why this comes first

The manifest is one row per file, with columns added as the file moves through the pipeline.
Every stage takes the manifest in and hands it back enriched. That makes each stage
independently testable, makes the pipeline resumable (which stage a file has reached is
visible from which columns are populated), and makes it possible for me to hand over
components that Gauri can assemble without rewriting them to fit each other.

If we don't settle this first, "here are the building blocks, connect them" turns into
"rewrite these so they fit." So we answer these questions before we write stage code.

**How to use this:** work through it together. Write the answer under each question. Where we
can't decide yet, write down what would let us decide and who we need to ask. A partial
answer with a named blocker is more useful than a guess.

---

## Section 1 — Identity and keys

**1.1 What is the primary key for a row?**
Candidates: full original path; a hash of the path; a generated UUID; drive ID + path.
Consider that the same file content can appear at many paths, and the same path can appear
on multiple drives.

> Answer:

**1.2 How do we represent a file that appears at multiple paths with identical content?**
One row with a list of paths, or many rows pointing at one canonical row?

> Answer:

**1.3 How do we handle files inside archives (zip, tar, disk images)?**
Does `report.pdf` inside `backup.zip` get its own row? If so, what does its path look like?
How deep do we recurse before we stop?

> Answer:

**1.4 What identifies the source?**
Drive serial number, accession number, donor name, an internal ID we assign? This has to
survive into the final metadata as provenance.

> Answer:

**1.5 Do path strings get normalised, or stored verbatim?**
Verbatim preserves provenance exactly. Normalising makes joins and matching far easier.
We probably want both — a raw column and a normalised one. Confirm.

> Answer:

**1.6 How do we handle paths that break things?**
Non-UTF-8 bytes, paths over 260 characters, trailing spaces, reserved Windows names,
characters legal on one filesystem and not another. Old drives have all of these.

> Answer:

---

## Section 2 — Storage format and scale

**2.1 What format?**
Parquet is the default answer — columnar, compressed, typed, fast to filter. Confirm or
argue for something else (SQLite, DuckDB, Delta).

> Answer:

**2.2 How do we partition it?**
By source drive, by top-level folder, by format class, by fixed row count? This determines
whether Gauri can work on a slice on her laptop without loading everything.

> Answer:

**2.3 What is the largest manifest we should design for?**
We don't know real drive sizes yet. Pick a design target and note it as an assumption.
A million rows with ~60 columns is comfortably a laptop-scale Parquet file. Ten million
is not.

> Answer:

**2.4 Where does the manifest physically live during processing, and where does it land after?**

> Answer:

**2.5 Do we keep one manifest per drive, or one across all drives?**
Per drive is simpler and matches how accessions arrive. Cross-drive deduplication argues
for a shared hash index alongside.

> Answer:

---

## Section 3 — Stage ownership of columns

For each stage, list the columns it writes. No stage writes a column owned by another stage.

**3.1 Stage 00 — Source & access**

> Columns:

**3.2 Stage 01 — Inventory & identify**
Expected: path, filename, extension, size, created, modified, accessed, depth, sha256,
PUID, format name, format version, ID confidence, ID method.

> Columns:

**3.3 Stage 02 — Triage & appraisal**
Expected: duplicate_of, nsrl_hit, structural_exclusion, peek_text, peek_method, embedding,
folder_score, file_score, band, decision, decision_rationale, decision_version.

> Columns:

**3.4 Stage 03 — Extraction & routing**
Expected: lane, extractor, extract_status, extract_error, text, text_length, page_count,
header_facts (nested), extraction_duration.

> Columns:

**3.5 Stage 04 — Enrichment**
Expected: summary, description, doc_type, pii_entities, pii_masked_text, sensitivity_flags,
model_name, prompt_version, enrichment_duration.

> Columns:

**3.6 Stage 05 — Metadata**
Expected: the Dublin Core and IPTC fields, plus provenance.

> Columns:

**3.7 Stage 06 — Index & delivery**

> Columns:

---

## Section 4 — Types and nulls

**4.1 What does "not yet processed" look like versus "processed, no value found"?**
This matters enormously for resumability. If `summary` is null, has the file not reached
stage 04, or did stage 04 run and find nothing worth summarising? Options: a separate status
column per stage, or a sentinel value, or a processing-log table.

> Answer:

**4.2 How do we record failures?**
A file that crashes the PDF extractor needs to be distinguishable from one that was skipped
and one that succeeded with empty output. What are the status values?

> Answer:

**4.3 Do we store embeddings in the manifest or beside it?**
A 384-dimension float32 vector is ~1.5 KB per row. At a million rows that's 1.5 GB in the
manifest. Probably a separate vector store keyed on the manifest key. Decide.

> Answer:

**4.4 Where does extracted text live?**
Full text of a long PDF can be megabytes. In the manifest, or on disk with a pointer column?

> Answer:

**4.5 What are the datetime conventions?**
Timezone-aware or naive? Filesystem timestamps on old drives are frequently wrong or
epoch-zero. What do we do with an obviously invalid mtime?

> Answer:

**4.6 Nested structures — allowed or flattened?**
`header_facts` for a GeoTIFF and for an HDF5 file have completely different shapes. Options:
a JSON string column, a struct column, or a separate side-table per lane.

> Answer:

---

## Section 5 — Versioning and reprocessing

**5.1 How do we record which pipeline version produced each field?**
Every generated field needs model name, prompt version, and pipeline version. Per-field is
verbose; per-stage is probably enough. Decide the granularity.

> Answer:

**5.2 What happens on reprocessing?**
When we re-run stage 04 with a better model in a year: overwrite in place, add versioned
columns, or write a new manifest generation and keep the old one?

> Answer:

**5.3 Can a stage be re-run for a subset of rows?**
E.g. re-run enrichment only for files where the model version is older than X.

> Answer:

**5.4 How do we handle a schema change mid-project?**
We will change this schema. What is the migration story — a version column on the manifest
itself, and a documented changelog?

> Answer:

---

## Section 6 — Decisions and reversibility

**6.1 How is a triage decision recorded so it is auditable and reversible?**
We never delete. So a decision is a column value plus a rationale plus a timestamp plus the
version of the policy that produced it.

> Answer:

**6.2 How do we record a human overriding a machine decision?**
Separate columns for machine_decision and final_decision? A review log table?

> Answer:

**6.3 How do we record the layered importance tiers?**
The design is: first pass narrows, metadata generation enriches, second pass re-ranks with
that richer signal, human sees only the final layer but can drill into any earlier one.
That means we need a score and a rationale at each layer, not just a final answer.

> Answer:

**6.4 What does the reviewer's view of a row look like?**
This determines which columns must be human-readable rather than machine-only.

> Answer:

---

## Section 7 — Practical

**7.1 What are the column naming conventions?**
snake_case, stage prefixes (`s02_score`), or plain names? Prefixes make ownership obvious
and make it easy to drop a stage's output and re-run.

> Answer:

**7.2 Where does the schema definition live in code?**
A single Python module with a dataclass or a pyarrow schema, imported by every stage, so
the schema is enforced rather than assumed.

> Answer:

**7.3 How do we validate a manifest?**
A checker that confirms required columns exist, types match, and stage invariants hold.
Worth writing early — it catches integration errors before they compound.

> Answer:

**7.4 What is the smallest useful test manifest?**
We want a fixture of maybe 50 rows covering every format class and every status, committed
to the repo so tests run without a real drive.

> Answer:

---

## Assumptions we are making

Record anything we decided without evidence, so we can revisit it when a real drive arrives.

| # | Assumption | Why we assumed it | What would change it |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |

---

## Blocked items

| # | Question | Who can answer | Asked on | Answer |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |

---

## Sign-off

| | Name | Date |
|---|---|---|
| Drafted by | | |
| Reviewed by | | |
| Schema v1 frozen | | |
