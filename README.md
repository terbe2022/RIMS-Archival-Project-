# RIMS Archival Project

Automated appraisal, description and search for born-digital archival collections at the
University of Illinois System.

A drive arrives from a retired or deceased researcher. Somewhere in it is work worth keeping,
and no practical way to find it without opening all of it. This project builds the layer that
answers **which of these files matter** — and then describes the ones that do.

**Status:** Design phase, moving to build. Three proofs of concept complete. The Archives
answered the outstanding scoping questions on 12 Aug 2026 — see
[`docs/stakeholders/answers-2026-08.md`](docs/stakeholders/answers-2026-08.md), which is the
authoritative record and supersedes earlier assumptions in several places.

---

## Start here

| If you are | Read |
|---|---|
| New to the project | [`docs/design/pipeline-design.md`](docs/design/pipeline-design.md) |
| Looking for any document | [`docs/README.md`](docs/README.md) — the map |
| Setting up your machine | [`docs/setup/onboarding-and-setup.md`](docs/setup/onboarding-and-setup.md) |
| Wondering what was decided, and why | [`docs/design/decisions.md`](docs/design/decisions.md) |
| Wondering what the Archives said | [`docs/stakeholders/answers-2026-08.md`](docs/stakeholders/answers-2026-08.md) |
| Building against the manifest | [`docs/design/manifest-schema.md`](docs/design/manifest-schema.md) |
| Looking for the interactive scope doc | **[Open the scope document](https://terbe2022.github.io/RIMS-Archival-Project-/)** · source: [`index.html`](index.html) |

---

## Repository layout

```
docs/
  design/         What we are building — pipeline, schema, decisions. Live
  stakeholders/   What the Archives told us, and what is still open. Authoritative
  setup/          Machine setup and Box access. Stable, mostly one-time
  superseded/     Old versions, kept for provenance. Do not work from these
worksheets/     Task documents with named owners
src/            Pipeline code — schema, Box ingest, stages to follow
notebooks/      Colab-facing notebooks; they import from src/, not the reverse
poc/            The three completed proofs of concept, with known defects
index.html      Interactive pipeline scope document (GitHub Pages)
```

Docs were reorganised on 12 Aug 2026. [`docs/README.md`](docs/README.md) explains the split and
the conventions — date-stamp snapshots, version anything that evolves, supersede rather than
delete.

## Active worksheets

| # | Document | Owner | Status |
|---|---|---|---|
| W2 | [Software evaluation](worksheets/W2_software_evaluation_task.md) | Gauri | Live — add BitCurator, it is already in use |
| ~~W1~~ | Manifest schema worksheet | — | Superseded by [`docs/design/manifest-schema.md`](docs/design/manifest-schema.md) |
| ~~W3~~ | Storage & ingest assessment | — | Largely answered 12 Aug — material arrives on a network share, not on media we attach |
| ~~W4~~ | Questions by stakeholder | — | Split into [`answers-2026-08.md`](docs/stakeholders/answers-2026-08.md) and [`open-questions.md`](docs/stakeholders/open-questions.md) |

## Proofs of concept

| # | Project | What it proved | Notes |
|---|---|---|---|
| 1 | [Email processing](poc/01-email-processing/) | Full email chain — parse, PII mask, summarise, topic model | 44,677 emails → 79,676 messages |
| 2 | [File smart search](poc/02-file-smart-search/) | Semantic search across heterogeneous file types | ~17 format families |
| 3 | [Image classification](poc/03-image-classification/) | Sensitivity flagging; description and classification must be separate steps | 1,000 TIFFs, two methods compared |

Each POC folder has a README covering what is reusable and what is known to be broken. Read
the defects before reusing anything.

## Performance case studies

Both the image and text pipelines have been through performance investigations that changed
the numbers substantially. Use the post-optimisation figures for any planning.

- [Archival Image Pipeline — vLLM vs Ollama Throughput](https://taylererbe.com/archival-image-throughput-evaluation.html) — 12,125 images from 22.2 hrs to 3.7 hrs, 6.22× on the same L4
- [vLLM Model Evaluation — Illinois Legislation Pipeline](https://tayler-erbe.github.io/tayler-portfolio/vllm-inference-throughput-evaluation.html) — model selection and concurrency methodology
- [Archival Image Intelligence](https://taylererbe.com/archival-image-intelligence.html) — POC 3 overview

## Shared storage

Data files, sample corpora and documents that cannot be committed live in Box.

- Project folder: https://uofi.box.com/s/81rl4der7gh815mkk44fpe1y21b7hqsn
- Proposal document: https://uofi.box.com/s/cdfk4c98jpxiwuxgjgev2gu5mc8ns0kq

## Team

| Name | Role |
|---|---|
| Tayler Erbe | Data Scientist, AITS — architecture, performance, infrastructure |
| Gauri Bhasin | Developer — triage layer, software evaluation, pipeline assembly |
| Joanne Kaczmarek | University Library / Archives — appraisal policy, metadata standards |
| Brent West | Information Governance, RIMS — retention, records policy |
| Bethany Anderson | Archives — appraisal expertise |

## Conventions

- Python 3.11, dependencies pinned in `requirements.txt`
- No hardcoded absolute paths — config cell or environment variables
- Notebooks: a markdown cell before each code cell explaining what and why
- No data files, PII, or credentials committed. Box for anything that can't go here.


## What we know about the material

Confirmed by the Archives, 12 Aug 2026. These numbers are the design target; earlier documents
assumed something much larger.

| | |
|---|---|
| Personal-papers backlog | **49 collections**, already on an Archives network share |
| Per accession | **100–10,000 files**, 25–30 top-level folders |
| Confirmed formats | `.xls` `.doc` `.pdf` `.txt` `.csv` `.mov` `.jpg` `.mp4` `.eml` `.pst` |
| Also queued, separately | An unquantified email backlog, and ~12,000 images |
| Acceptable turnaround | 3–6 months personal papers · ≤3 months administrative records |
| Total bytes | **Still unknown** — one `du -sh` away |

The bottleneck is not acquisition. Media processing already happens upstream. What does not
happen is the appraisal review after material lands on the share, which is where the backlog
accumulates and what this project is for.
