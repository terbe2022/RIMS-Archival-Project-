# Gauri's code and evaluation guide

Prepared October 13, 2026 against GitHub main `bed430ee68aa16fffa87ba87f46f2e12d20de3d6`.
Documentation aligned with main `3c8a765` after PR #93 merged; executable code map remains based on `bed430e`.
This is an implementation map and proposed working agreement, not proof that every
lane works. Gauri owns experiment design, model comparison and defect evidence;
Tayler owns integration and engineering repairs; archivists own appraisal criteria
and reference judgements. Codex can implement fixtures, adapters and fixes through PRs.

## Your computer and independence

When you call a model hosted on a University server, the server loads its weights
and runs inference. Your laptop sends an input and receives an output. It needs
network access and a lightweight client, not a GPU or model-sized RAM. A browser
client could reduce installation requirements further, but a shared experiment UI
has not been implemented or provisioned here.

Ten installed models do not require ten models to be resident simultaneously.
Stored weights consume server disk; loaded models consume server RAM/VRAM;
requests additionally consume context/cache memory. Evaluate candidates sequentially
in batches per model to avoid repeated loading. Whether a particular model fits,
loads acceptably and supports the needed modality must be measured on the server.
An API does not guarantee quick execution: queues, cold loads, long inputs and
shared workloads still matter. Ollama supports memory-dependent scheduling;
vLLM exposes an HTTP inference API. Multiple model files do not by themselves
create ten selectable vLLM endpoints.

References: [vLLM serving](https://docs.vllm.ai/en/stable/serving/online_serving/openai_compatible_server/)
and [Ollama memory/concurrency guidance](https://docs.ollama.com/faq).

The missing capability is approved service access, not a better laptop. Shell
access and inference-only API access are different permissions; denial of shell
access does not grant API access. A service owner must approve a reachable,
authenticated route, permitted models/data, quotas and scheduling. A localhost
address on the server is not reachable from your laptop: `127.0.0.1` on your
computer means your computer. Do not bypass access decisions, share Tayler's
credentials, expose an unprotected model port or start/reconfigure services.

Proposed autonomy: once a standing synthetic-experiment scope is approved, Gauri
can choose fixtures, prompts, settings, run bounded jobs on the allowed models,
inspect results and file defects without asking Tayler for each run. The scope
needs a service owner, allowed models, maximum input/output sizes, request/job
limits, concurrency, run windows, cancellation, result storage and a clear route
for requesting a new model. Original-content access needs separate approval.
This scope is proposed, not configured. No paid API calls or new compute spending
are authorized. University compute has capacity/operational costs even when
there is no per-request provider bill.

## Read these documents in this order

1. [Root operating rules](../AGENTS.md) and [validation rules](AGENTS.md): boundaries and authority.
2. [Current project guide](../docs/PROJECT-GUIDE.md), [quality/performance protocol](../docs/EVALUATION.md), [reported hardware](../docs/HARDWARE.md), then [pipeline design](../docs/design/pipeline-design.md): purpose and proposed architecture. Compare claims with code below.
3. [Manifest contract](../docs/design/manifest-schema.md) and [executable schema](../src/schema/manifest.py): the fields each stage reads/writes.
4. [Accession context](../docs/ai-and-the-accession-form.md), [context implementation](../src/workbench/context.py), and [draft appraisal rules](../docs/design/appraisal-rules-draft.md): descriptive context versus retention/exclusion criteria.
5. [Grading](GRADING.md), [validation plan](PLAN.md), [frontier judging](FRONTIER-JUDGING.md), [experiment template](experiments/TEMPLATE.md), [results template](results/TEMPLATE.md): existing evaluation conventions. Historical numerical thresholds are not approved acceptance criteria.
6. [Data map](../docs/DATA-AND-PROTOTYPES.md) and [shared execution](../docs/SHARED-SERVER-COLAB.md): inputs, output provenance and environments.

Read the three POC READMEs for origin and known defects, after the current code:
[email](../poc/01-email-processing/README.md),
[file smart search](../poc/02-file-smart-search/README.md),
[images](../poc/03-image-classification/README.md). They explain why the project
began as different dataset-specific workflows; they are not acceptance evidence
for the integrated tool. Documentation consolidation merged in PR #93; CPU-safe
Colab/report changes remain in draft PR #94. Inspect its merge state before
assuming those executable changes exist in main. The larger executable validation kit remains on
PR #80's branch; use its code/notebook from the same recorded commit.

## Follow the code from input to reviewed output

| Boundary and code to inspect | What exists | What to test / evidence to request |
|---|---|---|
| Intake: [src/workbench/intake.py](../src/workbench/intake.py), `accessions.py`, `context.py` | Accession resolution and descriptive context; valuable/exclude criteria are withheld from description prompts | Missing/contradictory forms; stable accession IDs; inspect actual included/withheld fields and form hash |
| Inventory: [src/workbench/stage01.py](../src/workbench/stage01.py), [src/schema/manifest.py](../src/schema/manifest.py) | Crawl, identities, file properties and format evidence | Synthetic mixed folder, misleading extensions, empty/corrupt files, duplicate identity and input hash coverage |
| Initial decisions: [src/workbench/stage02a.py](../src/workbench/stage02a.py), [src/schema/rules/base.py](../src/schema/rules/base.py), `personal_papers.py`, `administrative.py` | Structural/rule decisions and layer assignment | Sensitivity precedence, conflicting rules, duplicate treatment, excluded but reviewable outcomes; no automatic deletion |
| Routing: [src/workbench/lanes.py](../src/workbench/lanes.py) | Signature-first routing with extension/container refinement and a readiness report | Correct lane, mismatch note, unknown-format escalation; routing success must not imply extraction success |
| Extraction: [src/workbench/stage03.py](../src/workbench/stage03.py), `extract.py`, `mail.py` | CPU extraction attempts for document, tabular and email lanes, mail-traffic classification, relevance scoring | Read actual extractor table, dependency/error handling, page/body coverage, attachment handling and unsupported outcomes |
| OCR: [src/workbench/ocr.py](../src/workbench/ocr.py), [scripts/run_ocr.py](../scripts/run_ocr.py) | Separate OCR path and output merge | Recover known synthetic text, empty image/no text, OCR errors, source mapping and ranking after OCR merge |
| Redaction: [src/workbench/redaction.py](../src/workbench/redaction.py), `stage04.py` | Entity detection and pseudonymization/vault allocation | Span-level precision/recall, cross-document placeholder consistency, over-redaction, rerun behavior; vault stays private |
| Model descriptions: [scripts/run_describe.py](../scripts/run_describe.py), `run_vision.py`, [src/workbench/serving.py](../src/workbench/serving.py) | Canonical text/vision prompts and model API callers; text descriptions require pseudonymized inputs by default | Grounded claims, omissions, genre/subjects, uncertainty, vision content flags, malformed outputs, missing inputs and endpoint failures |
| Ranking: [src/workbench/relevance.py](../src/workbench/relevance.py), `vision.py` | Clause-based relevance with lexical/embedding methods and explicit association retention; merged descriptions/flags affect downstream evidence | Correct accession criteria, filename versus content evidence, supplied/withheld context, association rationale, sensitivity precedence |
| Description/review/export: [src/workbench/stage05.py](../src/workbench/stage05.py), [scripts/decision_server.py](../scripts/decision_server.py), `export_review.py`, `export_workbench.py` | Metadata/flags, review decisions, exports and audit behavior | Distinguish fallback/heuristic metadata from model output; machine proposals versus human judgement; decision history and release traceability |
| Orchestration: [scripts/run_cpu_pass.py](../scripts/run_cpu_pass.py), `run_all_lanes.py` | CPU pass plus separately invoked model lanes and merges | Trace stage order and outputs; verify actual per-file success instead of command exit alone |
| Retrieval: [src/workbench/search.py](../src/workbench/search.py) | Separate indexing/query path with encoder choices | Search relevance, omitted middle evidence, window/embedding limits, stale index and metadata provenance |

The actual CPU pass first inventories and applies initial rules, then routes,
extracts and scores; optionally merges OCR and model descriptions and rescores;
then performs pseudonymization and later stage processing. The model calls happen
in a separate pass. Read the whole [scripts/run_cpu_pass.py](../scripts/run_cpu_pass.py) rather than assuming
all operations form one automatic linear run. Description input pseudonymization
and sensitivity-first final decisions need explicit tests at their boundaries.

### Gaps that matter to evaluation

`lanes.HANDLERS` still reports historical POC blockers and marks handlers not ready,
while `stage03.EXTRACTABLE` attempts CPU document/tabular/email extraction. These
are different mechanisms and currently inconsistent signals. Gauri should record
this as a readiness reconciliation defect, not infer that everything is unusable
or everything is ready. A declared lane is not a working handler for every format.

`extract._BY_EXT` contains multiple document/text extractors; the router lists
more formats than that table supports. Specialized databases, scientific files,
audio/video, archives and email containers need format-specific evidence. Do not
promise full attachment/container extraction because a filename routes to email.

Long-file behavior is not yet a complete chunk/aggregate evaluation system:
`extract.MAX_TEXT` is 2,000,000; PDF extraction examines up to 500 pages;
`mail.MAX_BODY` is 200,000; `run_describe.py` truncates to its `--chars` limit.
Inspect search windows separately. The earlier POC's beginning/end approach must
not be assumed to describe the current production path. Test important facts at
start, middle and end and report exactly what text each model actually received.

The website demonstrates review and protected metadata retrieval; it is not
proof of live GPU processing or original binary preview integration. A full
original-file end-to-end run, current server regression output and inference
remain unverified. The user-confirmed deployment at `bed430e` had 52 matching
files; code parity does not establish dependency, data or model parity.

## Design evaluations before the complete pipeline exists

Use two levels of evidence. Component experiments isolate one boundary and can
start now; integration experiments later verify that those components exchange
correct inputs and preserve decisions. End-to-end validation needs a working
controlled path and human reference labels, not a promise of handling every
possible format first. Coverage gaps become explicit exclusions/escalations.

For every experiment, write: question, current code boundary/function, input
contract, expected output, fixture labels and evidence, candidate/configuration,
controlled factors, metrics, proposed acceptance criteria, resource limit and
failure report. Freeze the protocol before looking at candidate results.

| Experiment Gauri can own | Synthetic cases to construct | Measures and candidate role |
|---|---|---|
| Extraction/routing | Generated TXT, DOCX, PDF, PPTX, EML, mismatched extension, empty/corrupt/unsupported file | Route/status accuracy, exact key-fact/page coverage, omissions, dependency failure; often no LLM needed |
| Text metadata | Minutes, correspondence, reports, ambiguous and unreadable text; competing titles, dates and subject evidence | Text instruction-model candidates; fact-supported claims, coverage, specificity, useful title/subjects/genre, abstention and schema separately |
| Images | Generated scenes/drawings, document scans, text-bearing images, hard negatives around a defined flag policy | Vision-capable candidates for scene/flag tasks; OCR separately for text; grounded attributes, hallucinations, policy-labelled flag precision/recall |
| Email | Synthetic MIME headers/bodies, reordered headers, auto-replies versus list discussion, quoted threads, repeated people, attachment references | Parser/redaction tests first, then text summarization candidates; thread/event coverage, attribution, missed identifiers and invented attachment claims |
| Accession relevance | Same fictional file under two different accession criteria; relevant, irrelevant and contradictory cases plus meaningful neighbours | Test existing lexical versus embedding methods before adding a new appraisal model; important-file false negatives, ranking and supported rationale |
| Long inputs | Known evidence at start/middle/end, near/over-limit files, short tail chunks and duplicated overlap | Compare truncation baseline versus proposed chunking/aggregation using fixed grading; key-fact omissions and chunk/file consistency |
| Reliability/performance | Repeated bounded requests, malformed output, timeout, unavailable model, interruption and retry | Any candidate backend; completion rate, parse/schema failure, cold/warm latency, tokens, memory and reproducibility |

Not every stage needs a generative model. Deterministic parsing, rules, redaction,
OCR, embedding retrieval and generative descriptions are different tasks. A text
model cannot substitute for a vision model simply because it has a higher benchmark
score. Embedding candidates need their own retrieval/relevance evaluation. Treat
the reported Nemotron installation as a baseline candidate only after verifying
its exact model ID, revision, modality, quantization and endpoint; installation
and GPU execution have not been independently confirmed in this guide.

## Decide whether a model is performing well

Create sources with independently specified expected facts. Grade the output
against those sources, not against an earlier model's answer. Proposed description
rubric: accuracy, specificity, completeness and archivist usefulness, each 0–2
with written anchors and cited source spans. Record unsupported claims, critical
hallucinations and severe sensitivity misses separately; an average cannot hide them.
Use applicable genre/schema/abstention measures alongside substantive grading.

For appraisal, label relevance under that accession's criteria, sensitivity,
association and uncertainty independently. Count missed important files and
sensitive false negatives, including unflagged files. A well-written description
can still yield a wrong appraisal proposal. Original reference labels require
archivist participation and approved infrastructure; model decisions are not gold.
The selected frontier-judge route for synthetic grading awaits funding/cap; do
not silently replace it or call a paid judge. Gauri can define the rubric and
source-backed expectations now; pilot grading authority must be agreed explicitly.

Compare identical fixtures/extraction and baseline prompt/settings; record model
revision, quantization, tokenizer/context size, decoding and output limits. Tune
one factor at a time, with comparable development effort per candidate. Hold out
cases by accession/folder, not randomly split chunks of the same file. Compare
allowed descriptive context supplied/withheld without leaking valuable/exclude
criteria into descriptions. Repeat enough to expose variability and record
reviewer/judge identity, disagreement and uncertainty.

Performance work is part of Gauri's role: separate cold download/load from warm
inference, extraction from inference, and latency from throughput. Record successful
files/sec, token counts, p50/p95 when sample size permits, failure/retry denominators,
GPU memory/utilization and concurrency. Small smoke runs cannot establish p99.
Run bounded sequential baselines before concurrency tests on shared compute;
model switching can measure load overhead rather than useful processing speed.
Select a quality-qualified configuration with disclosed safety failures and resource
tradeoffs. Acceptance thresholds need Joanne/Tayler agreement, not an invented score.
Adapt Tayler's case-study methods (controlled comparisons, substantive grading,
within-model proxy checks and workload-aware performance); transfer no accuracy
claim, model recommendation or throughput number to this archival workload.

## A meaningful first work package

1. Build a capability ledger: code boundary, supported formats, dependencies,
   tested behavior, known defect, missing implementation, and the evidence needed.
2. Design a small text metadata comparison and an email/extraction failure set.
   Each case contains fictional source, expected facts, prohibited claims,
   uncertainty and rationale. Include long inputs and hard negatives.
3. Propose a short model list by task and resource requirements. Ten candidates
   are possible, but start with a few contrasting baselines before installing ten.
   Service owner confirms what can be served; Gauri defines what is worth comparing.
4. Ask Codex to implement the fixtures, a bounded API client and reports on a
   `gauri/*` branch. Mock API failures first. Existing shared text smoke supports
   explicit Ollama/vLLM endpoints; it does not yet supply remote authentication,
   complete grading or performance instrumentation.
5. Once approved API access exists, Gauri runs a recorded commit independently,
   grades/blinds outputs under the agreed method and returns a findings register:
   case ID, expected/actual, source evidence, severity, reproduction/settings,
   proposed owner and retest result. Codex fixes assigned defects through PRs.
6. Add one controlled synthetic end-to-end case with checks at every boundary,
   then expand only the supported paths. Approved original pilots follow separately.

Use [experiment](experiments/TEMPLATE.md) and [result](results/TEMPLATE.md)
templates. A protocol, fixture contribution, measured comparison, performance
report and retested defect are substantive deliverables; a successful notebook
click is only environment setup. Gauri should shape this design while the pipeline
is being built, rather than wait for Tayler to declare it finished.

Suggested Codex task: "Read AGENTS.md, validation/AGENTS.md and
validation/GAURI-CODE-EVALUATION-GUIDE.md. Inspect the exact current code for my
chosen component. Implement a bounded synthetic experiment with source-labelled
fixtures, mocked failures and a reproducible report on a gauri branch. Keep
production behavior unchanged. Do not access original data, credentials, paid
APIs or unapproved server services. Identify observed results, gaps and limitations
separately, and prepare a reviewable PR."
