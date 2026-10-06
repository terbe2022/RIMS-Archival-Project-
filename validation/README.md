# RIMS Validation & Evaluation

This directory is the collaboration lane for model and end-to-end pipeline validation.

## Why this exists
RIMS needs evidence at two different levels:

1. Does a candidate model describe material reliably?
2. Does the complete system make useful, defensible appraisal and sensitivity judgements?

Those are different questions and require different experiments.

## Program

### Phase 1 — Model comparison
Start with the existing synthetic corpus/validation kit. Compare schema adherence, abstention, self-consistency, resource/cost behavior, and blind description quality.

### Phase 2 — Context ablation
Run the same material through the same model with and without the intake context block. This tests whether contextual conditioning actually improves description quality.

### Phase 3 — Gold set / pipeline validation
Create a human-labelled reference set with independent archivist review. Use it to evaluate ranking, folder association behavior, sensitivity/identifier detection, false positives/negatives, abstention, escalation, and evidence quality.

## Collaboration
Gauri should use gauri/<task> branches and pull requests. Engineering changes should remain separate from experimental changes whenever possible.

## Data boundary
Synthetic fixtures may be used in approved cloud experimentation. Real accession material remains on approved University infrastructure and must not be committed to this public repository or uploaded to Colab.

## Next repository task
Inventory the validation materials already present in notebooks/, docs/, scripts/, src/, and other existing directories before moving or duplicating them. The initial setup intentionally does not reorganize existing files until that inventory is reviewed.
