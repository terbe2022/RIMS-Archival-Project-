# POC 1 — Email Processing

**Status:** Complete. Proved the end-to-end email chain.
**Corpus:** Michael Brewer / Abbott Power Plant collection, supplied by Brent West. ~20+ years old.

## What it did

| Step | Notebook | Result |
|---|---|---|
| Parse `.eml` files to a table | `01_convert_eml_to_csv.ipynb` | 44,677 emails parsed |
| Explode threads into messages, extract headers, mask PII, summarise | `02_parse_pii_summarize.ipynb` | 79,676 individual messages |
| Vector search sketch | `03_haystack_search_sketch.ipynb` | Never developed past a stub |

Pipeline: walk `.eml` files → parse with the `email` stdlib → split threads on
`-----Original Message-----` → regex-extract headers → Presidio PII detection and masking →
Llama 3.2 summarisation of masked text → LDA topic modelling with LLM-generated topic titles.

## What is reusable

- The eml walk and parse (`01`) — solid, port as-is
- Presidio configuration and the mask-then-summarise ordering — the ordering is important and
  correct; do not summarise before masking
- The PII placeholder scheme (`<PERSON1>`, `<DATE_TIME3>`) with a recoverable mapping dict
- The resume-from-checkpoint batch pattern

## Known defects — read before reusing

1. **Header regex assumes a fixed field order** (`From`, `Sent`, `To`, optional `Cc`,
   `Subject`, optional `Importance`) and silently returns `None` for every field when it
   doesn't match. Real mail has many variants.
2. **Thread splitting only matches the English delimiter.** Misses forwards, non-English
   clients, HTML mail, and Outlook variants.
3. **Presidio misclassified a US phone number as `UK_NHS`.** The entity set needs tuning for
   US institutional records.
4. **34.8 sec/row throughput** came from `subprocess.run()` against the Ollama CLI, which
   reloads model weights on every call. Use the HTTP API against a persistent server. Do not
   copy this pattern.
5. **Hardcoded Windows paths** (`C:\Emails_Archiving\...`) throughout.
6. **PII mapping stored in a column beside the masked text** — convenient, and a disclosure
   risk. Needs an access-control decision.

## Data

Output CSVs are not committed — they are large and contain PII. Stored in Box.
See the repo README for the link.
