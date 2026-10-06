# Description grading protocol

Status: proposed operational rubric, 2026-10-06. Owner: Gauri. Historical source:
[recovered rubric](../docs/description-grading-rubric.md). Selection thresholds
remain for pre-run human agreement; no conflicting historical threshold is
silently adopted here.

## Frontier judge packet

Use synthetic source text in full, a case ID, condition-blind candidate tags,
and generated descriptions. Never include model names, condition names, or the
grading key in the packet. Randomize candidate order with a recorded seed rather
than consistent model order. Preserve errors separately; do not make failed
responses disappear from the comparison. Do not select the best repeat.

## Four independent dimensions (0â€“3)

| Score | Accuracy: factual support | Genre: document form | Specificity: distinguishability | Restraint: uncertainty |
|---|---|---|---|---|
| 3 | Every claim supported by source | Correct concrete form named | Distinguishes this file using supported details | Clearly marks source limits where needed; no unjustified inference |
| 2 | Mostly supported; minor overreach identified | Correct form implied | Accurate but could fit several neighbors | Neutral, no material overreach; uncertainty handling can improve |
| 1 | Material unsupported claim | Topic only; form unclear | Generic and uninformative | Inference presented as fact |
| 0 | Fabricated document, identity, event or substantive content | Wrong form | Empty or unusable description | Confident claim about unknowable content |

For each score record a source quotation or precise source locator, candidate
claim, reason and grader confidence. A name/date is not automatically acceptable
because it seems plausible. For unreadable fixtures, evaluate refusal against the
predefined expectation; do not penalize correct refusal for lacking a title.
For source cases with genuinely ambiguous expectations, record ambiguity and
adjudicate rather than manufacture a gold label.

## Example grading record

```json
{
  "case_id": "fixture-example",
  "candidate_tag": "blind-tag",
  "grader": "judge-model-and-revision",
  "scores": {"accuracy": 1, "genre": 3, "specificity": 2, "restraint": 1},
  "evidence": "Candidate assigns an author absent from the synthetic source.",
  "unsupported_claims": ["author attribution"],
  "confidence": "high",
  "adjudication_needed": false
}
```

This is an illustration, not a completed grade.

## Review and reporting

User-selected route: [FRONTIER-JUDGING.md](FRONTIER-JUDGING.md).

Use two independent frontier judges under FRONTIER-JUDGING.md; preserve their
original scores and evidence. Report disagreements instead of inventing consensus
truth. No blind human grading step is planned for this synthetic program. Model
grades are evidence, not gold labels or appraisal-policy ratification.

Report count, median/range and distribution for each dimension, unsupported-fact
counts, refusal errors, parse failures and denominators. Do not use a composite
score, inferred accuracy rate or winner unsupported by uncertainty. Model/hardware
configuration is part of the result, not merely the model name.

Before the run agree what triggers investigation, what blocks recommendation,
what minimum schema/refusal behavior is acceptable, and whether new prompts may
be tested in a separately labelled experiment. Historical 'any accuracy zero'
and 'more than one in fifty' statements conflict. Until resolved, report failure
counts without claiming a candidate meets an approved selection threshold.
