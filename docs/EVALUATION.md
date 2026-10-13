# Quality and performance evaluation

Proposed starting protocol, October 13, 2026. Gauri owns evaluation; archival reviewers own reference appraisal judgements. No thresholds or model winners here are approved production claims.

## Starting point

Adapted from [Tayler's vLLM evaluation case study](https://tayler-erbe.github.io/tayler-portfolio/vllm-inference-throughput-evaluation.html#optimization): controlled comparisons, substantive grading alongside structural checks, checking automated proxies within models, and workload-aware performance measurements. The legislation study reports cases where valid structured output did not track substantive quality. Transfer its method, not its model recommendation, scores, hardware throughput or acceptance thresholds.

## Evaluation funnel

1. Verify raw-file/metadata mapping, accession context, output contracts and reference labels. Split development and held-out cases by accession/folder to prevent leakage.
2. Smoke-test routing, extraction, errors, schema and abstention. The shared harness's three synthetic text cases and two drawings are smoke checks, not corpus validation.
3. Compare substantive quality on identical source cases and extraction inputs; blind model identities while grading.
4. Tune chunk/context size and output budget separately for each model. Compare a common baseline and each model's tuned configuration on held-out cases, recording equal tuning opportunities. Test proxies within each model, not just across model families.
5. After quality checks, measure bounded concurrency and repeated runs; check whether quality changes under load. Obtain authorization for large workloads.
6. Validate representative original material on approved infrastructure before recommending deployment.

## Description rubric

Proposed anchors for reviewer calibration, scored separately rather than as one unexplained total:

| Dimension | 0 | 1 | 2 |
| --- | --- | --- | --- |
| Accuracy | Central facts invented/contradicted | Mostly grounded with material ambiguity/error | Claims supported by source evidence |
| Specificity | Generic or misleading | Some distinctive detail, key vagueness | Identifies actual purpose/subject |
| Completeness | Central content missed or truncation hidden | Main theme captured with important omissions | Essential content covered within stated scope |
| Archivist usefulness | Cannot support informed triage | Useful but substantial checking needed | Concise contextual description with clear uncertainty |

Record evidence spans/pages, reviewer, uncertainty and not-applicable dimensions. Critical hallucinations and missed sensitive identifiers are separate failure flags; a good average cannot conceal them. Grade chunks against their chunk, file summaries against the whole file/aggregation, and folder summaries against the folder. Off-section drift or importing facts from another file must be visible even if those facts are correct elsewhere.

## Appraisal and sensitive information

Build accession case packs with permitted descriptive background, archivist-authored valuable/exclude criteria, source hashes/IDs, independent expected relevance/sensitivity labels and rationale evidence. Description prompts exclude valuable/exclude criteria; appraisal uses them separately. Compare allowed descriptive context supplied versus withheld with other factors fixed.

Measure important-file precision/recall and false negatives, ranking quality, association retention, folder thresholds, rationale support and uncertainty/escalation. Sensitivity evaluation measures detection precision/recall by category, severe misses, over-redaction and restricted-release behavior. Include unflagged files: sampling only model flags hides false negatives. No automatic disposal follows a low score.

Use independent archival reviewers, record agreement/adjudication and preserve unresolved cases. Existing pipeline decisions are not ground truth. Repeated passes from the same model judge test consistency, not independent correctness. Synthetic frontier judging remains subject to funded access and an approved cap; no paid calls are authorized here.

## Coverage and long files

Cover photos/scans/OCR, email headers/bodies/attachments, native text/PDF/DOCX/PPTX, duplicates and folder associations, empty/corrupt files, misleading extensions and unsupported formats. Report actual supported lanes.

Stratify by bytes AND extracted tokens/pages: short, typical, long, near-limit and over-limit. Place important/sensitive evidence at beginning/middle/end. Vary chunk size, overlap and aggregation; isolate output-budget effects. Include short tail chunks; distinguish genuine absence from extraction failure or truncation. Report per-file and per-chunk measures so large files do not dominate through chunk count.

Check schema/parse success and model confidence against substantive labels across models AND within model/configuration pairs. Valid JSON is not factual accuracy; self-reported confidence is not calibrated confidence. Predeclare cases/rubric/settings, start with a small synthetic pilot, record skipped/failed cells, then expand. A small stress test is not a representative corpus.

## Reproducibility and performance

Record code SHA, dataset version/mapping, model revision/quantization, prompt hash, tokenizer/context limit, chunk/overlap/aggregation, output budget, decoding/seed, dependencies, hardware, serving backend, concurrency, warmup and repeats.

Measure successful files/sec, token counts, p50/p95/p99 latency, time to first token/decode timing where exposed, extraction versus inference time, failures/retries and GPU memory/utilization. Separate cold starts/downloads. Include failed requests in denominators and disclose variability/small sample uncertainty; a few requests cannot establish a stable p99.

Project capacity from actual accession format/length distributions and measured chunks per file, not stress cases alone. Keep quality, safety and operational measures separate. Quality-qualified throughput can supplement them but cannot hide critical errors. Acceptance thresholds require Joanne/Tayler agreement; no archival model winner or system accuracy is established by this document.

## Deliverables

Gauri supplies environment smoke evidence, coverage/reference-labelling protocol, blinded synthetic comparisons, approved original-file pilots and a findings register (case, expected/actual, evidence, severity, configuration, owner, retest). Tayler implements reviewed fixes; Gauri retests affected cases and regressions. Close cards against acceptance evidence, not uploads.

Every experiment records question/design, provenance, configurations, per-case results or approved private references, grading evidence, errors, variability and limitations. Public Git receives safe synthetic material and aggregate non-sensitive results. Original accession content stays out of Colab and prompts under current AGENTS.md; private-repo access does not extend cloud-processing approval.
