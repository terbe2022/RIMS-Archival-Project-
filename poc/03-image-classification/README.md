# POC 3 — Image Classification & Sensitivity Flagging

> **Context note, 12 Aug 2026.** The Archives has given written appraisal guidance that the
> nine-category sensitivity taxonomy should be checked against — HR and personnel matters,
> discipline records, FMLA, personal finance. A PII scanner will not catch *"the discipline
> hearing for the groundskeeper"*, and that material is now routed to a supervising archivist
> rather than to discard. The 12,000-image corpus is also confirmed as a **separate backlog**
> from the 49 personal-papers collections, so its figures do not generalise to the document
> work. See [`docs/stakeholders/answers-2026-08.md`](../../docs/stakeholders/answers-2026-08.md).


**Status:** Complete, with a clear methodological finding.
**Corpus:** 1,000 archival TIFFs (production corpus is 12,125).

## What it did

| Notebook | Purpose |
|---|---|
| `00_Quickstart.ipynb` | Environment check and file indexing |
| `01_Downsampling_Images.ipynb` | Resize TIFFs, extract basic metadata |
| `02_Metadata_Extraction.ipynb` | Deep EXIF / TIFF / IPTC extraction |
| `03_Sensitivity_Flagging_LLaVA.ipynb` | Method 2 — direct LLaVA classification |
| `04_Sensitivity_Flagging_Semantic.ipynb` | Method 1 — semantic similarity |

**Method 1 — semantic similarity.** LLaVA generates a description → embed with
`all-mpnet-base-v2` → cosine similarity against a 9-category taxonomy of keywords → flag at
≥ 0.45. Flagged 79/1000 in about 9 minutes.

**Method 2 — direct LLaVA moderation prompting.** Structured JSON output with `offensive`,
`category`, `rationale`. Flagged 0/1000 at ~2–2.5 min/image.

## The finding that matters

LLaVA produced rationales that correctly described racialised content while still returning
`offensive: false`. The description was right; the judgment was wrong.

**Take-away: description and classification should be separate, independently auditable
steps.** That is what Method 1 does, and it is why Method 1 worked and was ~200× faster.

## Throughput — superseded

The ~2–2.5 min/image figure was the starting point of a performance investigation, not the
current state. Migrating from Ollama to vLLM took the 12,125-image corpus from 22.2 hours to
3.7 hours on the same L4 — a 6.22× speedup, of which 3.6× is purely the serving stack.

See: https://taylererbe.com/archival-image-throughput-evaluation.html

## Known issues

1. **Accuracy on flagged items was low.** Of 79 flags: 13 clearly correct, 8 clearly wrong,
   58 (73%) ambiguous. The 73% is the important number — it indicates the criteria were never
   defined precisely enough for anyone, human or model, to be consistent. This is a
   specification problem, not a model problem, and it is why the appraisal policy and gold set
   are prerequisites.
2. **The notebooks had a malformed metadata block** that prevented them opening in Jupyter.
   Repaired in these copies.
3. Model is dated — worth re-testing with a current vision model on the same 1,000 images so
   results are comparable.

## Assets

- `data/Sensitive_Content_Taxonomy_DataFrame.csv` — the 9-category taxonomy with keyword lists
- `docs/Documentation_Image_Classification.md` — full technical documentation, prompts, results

Result CSVs and images are not committed. Stored in Box.
