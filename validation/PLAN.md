# Archival Accession Processing Tool validation plan

Last edited: 2026-10-06. Last source/code review: 2026-10-06. Last server verification: not performed in this reconciliation.
Owner: Gauri. Status: proposed plan; no model or production evaluation was run in this reconciliation.

## 1. Synthetic model comparison

Use versioned synthetic fixtures and fixed prompts/settings. Measure JSON parseability separately from strict output-schema validity, explicit readable:false abstention, complete-response repeat consistency, runtime/resource use, and frontier-model-judged description quality. The recovered harness tolerates fences/preambles and checks title/description; it is not a full JSON-schema validator. Abstention expectations are labels/design assumptions and must be documented. Synthetic success does not establish real-data performance.

The locally repaired fixture suite has 54 cases, including 16 labelled for abstention. Compare the same cases across candidates. Preserve prompt, model/version, serving stack, hardware, fixture hash, date and configuration. A linear hours-for-150k extrapolation is a planning estimate, not a production benchmark. Empty or failed repeated parses must never count as successful consistency.

Blind sheets contain complete synthetic source text and candidate tags; keep the model key separate before sharing with graders. Report accuracy, genre, specificity and restraint separately. Record unsupported facts as failures. The original rubric conflicts between any accuracy zero and more than one in fifty; selection thresholds must be agreed before evaluating results, not inferred here. A single observed failure warrants investigation but does not establish a population rate or an intrinsic model property independent of configuration.

The user selected frontier-model grading for synthetic comparisons, replacing the
previous blind-human grading plan. Use FRONTIER-JUDGING.md and GRADING.md; retain
independent model judgments/disagreements. Automated grades are not gold labels.
Paid judge API execution remains pending funding.

## 2. Context ablation

Pre-register the same cases, model, serving stack, settings, grading and comparison design for context supplied versus withheld. Only permitted descriptive intake fields enter context; valuable/exclude criteria never enter description prompts. Keep paired case identifiers and blind condition keys. Compare each quality dimension and refusal behavior, including uncertainty and reviewer agreement. No dedicated context-ablation harness or completed results were recovered; the two notebooks do not implement this experiment as delivered.

## 3. Gold set and pipeline judgment

Proposed starting exercise: 50 stratified files, two independent archivists, adjudication and inter-rater agreement. Real material stays University-side. Test ranking, association retention, folder threshold, identifier/sensitivity false positives and false negatives, evidence/rationale fidelity, escalation and reviewed-release behavior. Ratify policy first or explicitly document unresolved criteria. Model comparison is not pipeline appraisal validation.

## Publication and workflow

Use gauri/* branches and PRs. No protected source text, identifying paths or real-data notebook outputs enter public GitHub. Include notebooks individually in sync only after review and enforce output/execution-count stripping. The server notebook must run only on approved University infrastructure; its real-manifest path must be verified there. Colab uses synthetic fixtures only. Do not install its dependencies or execute its model-download cells during a documentation review.

Results remain pending. Link non-sensitive aggregate evidence from Issues; do not imply the recovered brief is a completed experiment. Production defects discovered by evaluation go to a separate engineering change.
