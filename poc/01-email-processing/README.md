# POC 1 — Email Processing

**Status:** Complete. Proved the end-to-end email chain.
**Corpus:** Michael Brewer / Abbott Power Plant collection, supplied by Brent West. ~20+ years old.

> **Verdict, 12 Aug 2026 — build on this, do not adopt ePADD.**
> Assessed against ePADD and the decision is to keep our own processing. The reason is
> architectural fit rather than quality: ePADD expects a mailbox handed over as a unit, and the
> Archives confirmed email arrives as loose `.eml` and `.pst` files scattered through the same
> drives as everything else. Routing it to a separate application would split the appraisal
> decision about someone's correspondence from the decision about their papers — the exact
> connection that makes both worth keeping. Worth borrowing from ePADD: its sensitivity term
> lists. Full assessment: [`docs/design/email-lane-epadd-evaluation.md`](../../docs/design/email-lane-epadd-evaluation.md).
>
> **Defects 7 and 9 must be fixed before this runs on a real accession.**

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
- **Thread decomposition** — this is the strongest thing in the POC and nothing else we have
  looked at does it. 738 `.eml` files yielded 1,650 addressable messages, with sender, timestamp
  and subject recovered from the quoted reply block rather than the file envelope. In a real
  accession a forwarded chain is often the only surviving copy of the messages inside it; at file
  level those are invisible to search. **ePADD does not do this** — it treats a forwarded chain as
  one message.
- Presidio entity detection — the spans are found correctly
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
   risk. Needs an access-control decision. Tracked as a blocker; schema v1.1 keeps only
   `s04_pii_map_ref` in the manifest, pointing at a separately access-controlled store.
7. **Placeholders are not stable across documents** — found 12 Aug 2026, and more serious than
   defect 6 on its own. Numbering restarts per row, so `<PERSON1>` means a different person in
   every document. Measured on the 1,650-row corpus: "Beth" maps to `<PERSON1>` 203 times,
   `<PERSON2>` 29 times, `<PERSON3>` 23 times, and so on. The consequence is that **a researcher
   cannot follow a person through the redacted corpus** — while every real name still sits in the
   next column. In an archive the correspondence network is frequently the research object
   itself. Fix: corpus-stable pseudonyms, same person same token everywhere, mapping in a
   separate store. Strictly better on both axes — safer *and* more useful.
8. **No entity resolution.** "Mike" (456), "Mike Brewer" (198) and "Michael K" (147) are counted
   as three people. Same for "Kelly" and "Kelly Kathrens". Prerequisite for defect 7 — you cannot
   assign a stable ID to a person you cannot identify consistently.
9. **Summaries are generated from the masked text, which degrades them.** This reverses a claim
   made in an earlier version of this README. Because the summariser runs on `cleaned_text`, the
   model is summarising a document with the names already removed, and produces output like
   *"the decision has been made, and all relevant parties are informed"* or *"a contact has been
   informed"* — a summary carrying no information. **Summarise the original, then mask the
   summary.** Same inference cost, materially better output. About an hour's work.
10. **13% of stored summaries carry model preamble** — "Here is the rewritten summary:",
    "Summary:" — 215 of 1,598 rows. Cosmetic, trivially fixed by a strip-and-validate pass, but
    it should never have reached a saved artefact.
11. **2% text extraction failure rate** (31 of 1,650 rows). Small, but worth finding out whether
    it clusters on a format class.

## Data

Output CSVs are not committed — they are large and contain PII. Stored in Box.
See the repo README for the link.
