# Kickoff — Agenda, Software Position, and Decisions

**Draft v0.2** · Tayler Erbe
Rewritten from v0.1: software section restated as a position rather than a recollection;
hosted AI services ruled out on privacy grounds; POC summaries point to the repo.

---

## Agenda

| # | Item | Time | Outcome |
|---|---|---|---|
| 1 | Where the project stands — three POCs, what each proved | 15 | Shared context |
| 2 | The architecture: two-pass triage with metadata generation between | 15 | Agreement on the approach |
| 3 | Walk the pipeline diagram end to end | 20 | Gauri can explain it back |
| 4 | Manifest schema — the contract between stages | 10 | Worksheet assigned |
| 5 | Environment, hardware, models | 10 | Setup plan settled |
| 6 | Software we may already have | 10 | Evaluation task assigned |
| 7 | Two-week plan and ownership | 10 | Checklist agreed |
| 8 | Questions to take to Joanne, Brent, Data Privacy | 10 | Question list confirmed |

---

## 1. What the three POCs established

Code and notebooks are in the repo under `poc/`. Each folder has a README covering what it
proved, what is reusable, and what is known to be broken.

**POC 1 — Email processing** (`poc/01-email-processing/`)
44,677 `.eml` files parsed and exploded into 79,676 individual messages, headers extracted,
PII detected and masked with Presidio, summaries generated with Llama 3.2, LDA topic modelling
with LLM-generated topic titles.

Proved the full email chain works end to end. Known weak points: the header regex assumes a
fixed field order; thread splitting only matches the English `-----Original Message-----`
delimiter; Presidio tagged a US phone number as `UK_NHS`. The 34.8 sec/row throughput was an
artefact of calling the Ollama CLI once per row.

**POC 2 — File smart search** (`poc/02-file-smart-search/`)
Box authentication and ingest preserving original paths, per-extension text extraction across
about seventeen format families, Llama summarisation with pre-truncation, FAISS HNSW index,
natural-language search, KMeans topic clustering.

This is the piece stakeholders responded to most strongly and it should survive into the new
system largely intact. Known weak points: Windows COM dependency that will not run on Colab
or on our Linux server, extension-based routing, and several formats never implemented.

**POC 3 — Image classification** (`poc/03-image-classification/`)
1,000 archival TIFFs, two methods compared. Semantic similarity flagged 79/1000 in about nine
minutes. Direct LLaVA moderation prompting flagged 0/1000.

The finding worth carrying forward: LLaVA produced rationales that correctly described
racialised content while still returning `offensive: false`. The description was right and the
judgment was wrong. Description and classification should be separate, independently auditable
steps — which is what the semantic method does, and why it worked.

Note that the notebooks in this project had a malformed metadata block that prevented them
opening in Jupyter. Fixed in the repo copies.

**Throughput work** — both POC 1 and POC 3 have since been through performance investigations
that changed the numbers substantially. Image classification went from 22.2 hours to 3.7 hours
on the same 12,125-image corpus, and text throughput improved comparably. See the case studies
linked in the repo README. Any planning should use the post-optimisation figures.

---

## 2. Software position

We may already have access to software that does a large part of the first-pass layer. Some of
it is open source and we can install it today. Some is commercial and would need a licence the
University may or may not hold. Before building anything, we should know which.

The list below is ranked by how likely each is to be free, quick to stand up, and immediately
useful. Gauri is running the evaluation — the task and scoring criteria are in
`worksheets/W2_software_evaluation_task.md`.

### Free and open source — install now

| Tool | Licence | What it does | Where it fits |
|---|---|---|---|
| **Siegfried** | Apache 2.0 | PRONOM format identification, CLI, thousands of files/sec, JSON output | Stage 01. Expected primary tool. |
| **Apache Tika** | Apache 2.0 | Text and metadata extraction, ~1,400 formats, one interface | Stage 03. Retires the Windows COM code. |
| **ExifTool** | Artistic/GPL | Embedded metadata, native IPTC and XMP | Stages 01 and 05 |
| **DROID** | BSD | Same PRONOM signatures, GUI and reporting | Human-facing reports; Siegfried inside the pipeline |
| **NSRL RDS** | Public | NIST hashsets of known OS and application files | Stage 02, free exclusion of system noise |
| **Docling** | MIT | PDF to structured markdown, layout-aware | Stage 03, cheaper than a vision model on scans |

### Free and open source — larger commitment

| Tool | Licence | What it does | Decision needed |
|---|---|---|---|
| **BitCurator** | Open source | Forensic acquisition, disk imaging, PII scanning for archival media | Whether these accessions warrant forensic imaging |
| **ePADD** | Apache 2.0 | Email appraisal, redaction, discovery | Adopt as the email delivery interface, or keep our own lane |
| **Archivematica** | AGPL (paid support optional) | Full OAIS preservation workflow, AIP/DIP packaging | Whether we feed it or duplicate it |

### Commercial

| Tool | What it does | Question |
|---|---|---|
| **Preservica** | Enterprise digital preservation platform | Does the University already hold a licence? If yes, stages 05 and 06 change substantially. |

### The strategic point

We should not be building a preservation system. Archivematica and Preservica already do that
and they do it better than we would. What does not exist anywhere is **appraisal and
description at this scale** — deciding what is worth keeping from an unsorted drive and
generating usable metadata for it. That is our contribution, and everything else should be
borrowed.

That framing also strengthens the proposal to Joanne's group: we are not proposing to rebuild
a records system, we are proposing to build the layer that no vendor sells.

---

## 3. Hosted AI services — ruled out

These drives will contain personal email, unreviewed PII, medical and tax records, and student
records covered by FERPA. Sending that content to Copilot, Azure OpenAI, or any hosted API is
not something we can justify, and I do not want the architecture to depend on approval we are
unlikely to get.

The position going forward: **all processing of archive content happens on locally-hosted
open-weight models on university hardware.** This is a design constraint, not a fallback. It
needs no approval, has no per-token cost, and removes an entire category of risk.

Two things this does not rule out:

- **AI assistance for building the pipeline.** Claude, Copilot and similar tools helping us
  write and debug code involve no archive content. That is a straightforward productivity gain
  and we should use it.
- **Local agentic loops on our own hardware.** Open-weight models with tool-calling on the L4,
  nothing leaving our infrastructure. Useful for folder and collection-level synthesis and for
  exception handling. Not useful at file scale, because an agent loop costs many model calls
  where a classification costs one.

I still want the position confirmed by Data Privacy in writing. Questions are in
`worksheets/W3_storage_and_ingest_assessment.md`.

---

## 4. Storage and ingest

Box worked for POC 2 because the dataset was small. It scales poorly for full-drive ingest —
everything has to be downloaded before processing, API limits bite on large file counts, and
original paths have to be reconstructed rather than being native.

The framing I want to use: **separate the ingest layer from the delivery layer.**

| Role | Direction |
|---|---|
| Ingest — where we read the drive | Direct attach or SMB/NFS mount to a processing host. Forensic image first if the accession warrants it. |
| Working storage | Local scratch on the processing server |
| Delivery — what the Archives team uses | Box is genuinely fine here. Outputs and selected originals, not the raw drive. |

I am working this through with Data Privacy and Infrastructure —
`worksheets/W3_storage_and_ingest_assessment.md`.

**Current blocker:** no remote access to a real drive. Everything so far has run on small
samples, which hides every problem that appears at scale. Failing full access, a directory
listing of one representative drive would give us file counts and format mix, which are the
two variables that dominate processing time. That costs nothing to produce.

---

## 5. Decisions needed

| # | Decision | Owner | Needed by |
|---|---|---|---|
| D1 | Appraisal policy in writing | Joanne / Bethany / Brent | Before triage development |
| D2 | Gold-standard labelled set, 300–500 files | Archives | Before any scoring work |
| D3 | Metadata target confirmed | Joanne | Before stage 05 |
| D4 | Which software the University already licenses | Joanne / Brent | Kickoff + 1 week |
| D5 | Remote drive access, or a directory listing | Tayler / Infrastructure | ASAP — blocking |
| D6 | Human review capacity per week | Joanne | Before threshold tuning |
| D7 | Data Privacy sign-off on local model processing | Data Privacy | Before processing real content |
| D8 | Gauri's server access | My supervisor | Declined for now; revisit ~4 weeks |
| D9 | Manifest schema v1 | Tayler + Gauri | Week 1 |
| D10 | ePADD — adopt or build our own email lane | Tayler + Brent | Week 4 |

---

## 6. Questions for the group

Full list organised by stakeholder in `worksheets/W4_questions_by_stakeholder.md`. The ones I
want raised at the group meeting:

1. What does the Archives do today when a drive arrives — is there a workflow we should feed?
2. What retention obligations constrain disposal, and does "quarantine, never delete" satisfy
   them?
3. How many drives are queued, what size range, and can I get a directory listing of one?
4. Who reviews sensitivity flags, and what is their realistic weekly capacity?
5. Do the queued drives span disciplines with specialist formats — ArcGIS, 3D imaging,
   instrument data? Which ones, so we prioritise those lanes?
6. Does the Library license Preservica, or run Archivematica or DROID already?
