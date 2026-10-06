# Validation — Agent Instructions

These instructions apply to validation/ and supplement the repository root AGENTS.md.

## Owner and mission
Gauri's primary lane is model and pipeline validation. The goal is to build the evidence base needed to say what works, what fails, and with what uncertainty. Validation is not a rubber stamp for a finished system.

## Workstreams, in order

### 1. Model selection
Compare candidate open-weight models using the existing synthetic validation material where possible.

Measure separately:
- schema adherence
- abstention behavior
- self-consistency
- cost/resource requirements
- blind description quality

Do not collapse these into a single unexplained score.

### 2. Context-block experiment
Test the load-bearing assumption that intake context improves description quality.

Use the same files, model, settings, and grading process in both conditions:
- context supplied
- context withheld

Record the experimental design before inspecting results. Report effect by quality dimension, not merely a winner.

### 3. Pipeline judgement / gold set
Model selection is not equivalent to validating appraisal decisions.

The end-to-end evaluation should eventually test:
- ranking/order quality
- retained_by_association behavior
- the folder-level threshold
- sensitivity and identifier detection
- false positives and false negatives
- abstentions and escalation behavior
- rationale/evidence quality

Build a reproducible labelling protocol and measure agreement between independent human reviewers.

## Data rules
Real accession content must not be uploaded to Colab or other unapproved cloud environments. Use synthetic fixtures for cloud-executed model experiments. This file grants no exception to the root University-only boundary for real accession content.

Never commit sensitive archival material, PII, credentials, private keys, tokens, or server runtime artifacts.

## Git workflow
Use gauri/<task> branches. Keep experimental code, fixtures, protocols, and aggregate/non-sensitive results reviewable in Git. Open PRs into main.

Do not change production pipeline behavior as a side effect of a validation experiment. If validation reveals a production defect, document it and propose the engineering change separately unless explicitly assigned to fix it.

## Scientific practice
Predefine metrics and comparison conditions where practical. Preserve raw non-sensitive evaluation outputs needed for reproducibility. Distinguish observed results from interpretation. Record model/version, prompt/configuration, fixture version, run date, and grading method.

Do not claim pipeline accuracy before an appropriate human-labelled reference set exists.
