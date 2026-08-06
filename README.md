# RIMS Archival Project

Automated appraisal, description and search for born-digital archival collections at the
University of Illinois System.

A drive arrives from a retired or deceased researcher. Somewhere in it is work worth keeping,
and no practical way to find it without opening all of it. This project builds the layer that
answers **which of these files matter** — and then describes the ones that do.

**Status:** Design phase. Three proofs of concept complete, unified pipeline not yet built.

---

## Start here

| If you are | Read |
|---|---|
| New to the project | [`docs/pipeline-design.md`](docs/pipeline-design.md) |
| Setting up your machine | [`docs/onboarding-and-setup.md`](docs/onboarding-and-setup.md) |
| Preparing for the kickoff | [`docs/kickoff-agenda.md`](docs/kickoff-agenda.md) |
| Looking for the interactive scope doc | [Open the scope document](https://terbe2022.github.io/RIMS-Archival-Project-/site/) (GitHub Pages) · source: [`site/index.html`](site/index.html) |

---

## Repository layout

```
docs/           Design and reference documents
worksheets/     Task documents to be filled in — each has a named owner
poc/            The three completed proofs of concept, with code and known defects
site/           Interactive pipeline scope document (GitHub Pages)
```

## Active worksheets

| # | Document | Owner | Status |
|---|---|---|---|
| W1 | [Manifest schema](worksheets/W1_manifest_schema_worksheet.md) | Tayler + Gauri | Not started |
| W2 | [Software evaluation](worksheets/W2_software_evaluation_task.md) | Gauri | Not started |
| W3 | [Storage & ingest assessment](worksheets/W3_storage_and_ingest_assessment.md) | Tayler | Not started |
| W4 | [Questions by stakeholder](worksheets/W4_questions_by_stakeholder.md) | Tayler | Ongoing |

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

- Project folder: https://uofi.box.com/s/479zbfegbem8mk8dr9044mmzcd6wpmr
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
