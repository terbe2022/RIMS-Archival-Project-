# POC 2 — File Smart Search

**Status:** Complete. The piece stakeholders responded to most strongly.
**Corpus:** Mixed files from a Box folder.

## What it did

| Step | Notebook |
|---|---|
| Box authentication, download preserving original paths | `01_box_sdk_ingest.ipynb` |
| Per-extension text extraction across ~17 format families | `02_extraction_by_filetype.ipynb` |
| Summarisation, FAISS index, semantic search, topic clustering | `03_vector_search_and_topics.ipynb` |

Pipeline: Box SDK ingest → file inventory by extension → per-format text extraction →
pre-truncation via SentenceTransformer sentence selection → Llama summarisation → MiniLM
embedding → FAISS HNSW index → natural-language search → KMeans topic clustering with
LLM-generated cluster titles.

## What is reusable

- The FAISS HNSW index build and search — port largely intact
- The pre-truncation approach for oversized documents
- The extraction logic for `.pdf`, `.html`, `.rtf`, `.txt`, `.zip` (pure Python, portable)
- The hierarchical topic clustering

## Known defects — read before reusing

1. **Windows COM dependency.** `.doc`, `.xls` and `.ppt` extraction uses `win32com.client` to
   drive actual Microsoft Office. This will not run on Colab or on the Linux server, cannot be
   parallelised safely, and hangs on malformed files. Replacing this is a prerequisite for the
   unified pipeline.
2. **Routing on file extension, not verified format.** The corpus contained extensions like
   `.d1`, `.career2`, `.toc`, `net3852448d` and `00361-00850` — none real formats. Magic-byte
   identification solves this properly.
3. **MiniLM truncates at 256 tokens.** Fine here because it embedded short summaries. It will
   silently cut longer text with no error.
4. **Formats never implemented:** `.eml`/`.mbox` (deferred on size), `.mdb`, `.db`, `.mov` and
   video generally, `.gz`. See `docs/file-type-gap-analysis.md`.
5. **Search ran through a notebook CLI** — not usable by the Archives team.
6. **Hardcoded Windows paths** throughout.

## Related

- `docs/file-type-gap-analysis.md` — full coverage analysis and remediation for each gap
