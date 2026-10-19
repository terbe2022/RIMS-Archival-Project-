# Gauri: Qwen smoke review and recovered notebook

October 19, 2026. This is a repair of the recovered 54-case experiment, not the
separate three-case shared-pipeline notebook in PR #94. Colab remains optional;
this repair does not grant University model API access or require buying compute.

## Review of PR #87

The report is useful technical smoke evidence: Gauri reports eight offline tests,
two parsed responses, one explicit abstention, and a subjects-as-string defect.
It correctly limits its conclusions; it does not claim archival accuracy.
The saved notebook still used the old tensor-only tokenizer caller. The report
contains enough detail to reconstruct the BatchEncoding workaround; Gauri need
not recover an expired runtime for that fix. Other unsaved edits are not known.
The report does not preserve complete raw responses or package versions, so its
schema and model-quality observations cannot all be independently reproduced
from the report alone. Keep the original report unchanged as dated evidence.

## What changed

- Saved caller uses return_dict=True, moves every tensor to the model device,
  passes input_ids and attention_mask to generate, and slices only new tokens.
- Additional structural metric accepts null titles for explicit abstention and
  flags subjects strings. It never coerces a string into a list. Legacy parse/key
  measures stay available; none is substantive description-quality evidence.
- Default run is fixture-000 and fixture-027, once each. RUN_FULL is off by default.
- Full mode is 54 fixed cases × 2 repeats = 108 attempts; image-labelled cases are
  text surrogates here, not vision inference. Existing prompt/fixtures are unchanged.
- Fresh Git checkout resolves a recorded commit; model/tokenizer use one resolved
  model revision. Reports record prompt/case hashes, versions, settings and GPU.
- Each completed attempt saves to JSONL. Final ZIP includes raw outputs/errors,
  metrics and provenance, including partial attempts after an interruption.
  Colab storage remains temporary: download before disconnecting.
- Failure inspection uses actual fixture labels instead of obsolete case-ID prefixes.
- Grading instructions respect the selected frontier-judge protocol; no paid
  grading calls or automatic model winner are introduced.

The original prompt says subjects are topic terms without explicitly specifying
an array. Record that ambiguity along with the observed type defect. Clarifying
the prompt is a new condition after the unchanged baseline, not a silent repair.

## Gauri's next steps

1. Open the repaired Colab notebook link provided with the repair PR; this is the
   recovered Qwen experiment, not shared-pipeline-colab.ipynb. Select an available
   T4 GPU and run the notebook. No manual caller editing is needed. No paid tier
   or alternative compute purchase is required by this guide.
2. Keep RUN_FULL unchecked. The notebook runs 13 offline checks, resolves code
   and model revisions, and runs the two reported smoke cases once. Download ZIP.
3. Inspect readable/abstention, raw responses and structural errors. A persistent
   subjects-format defect is a baseline observation, not a reason to erase results.
4. After protocol and smoke review, check RUN_FULL and rerun the execution cell
   while the model remains loaded. Expect 108 attempted calls, 54 repeated cases
   and 32 expected-abstention attempts. Preserve failures in the denominator.
5. Download the new ZIP before leaving. Return the technical table, error/schema
   findings, code/model revisions and limitations in a reviewed report PR. Keep
   raw artifacts outside public Git unless reviewed as synthetic/non-sensitive.

GPU execution of this repaired notebook is still pending. Passing the local
mock/stub tests verifies plumbing, not Qwen quality or GPU compatibility. Colab
package installation is not an isolated environment in this legacy notebook;
new dependency failures must be recorded rather than met with blanket upgrades.
A direct University API experiment is a separate configuration/baseline and must
not be relabelled as a reproduction of Qwen NF4 on a Colab T4.

## Validation performed

Eight original recovery tests plus five new offline regressions passed. The new
checks cover dict tokenizer outputs/attention masks and generated-token slicing;
subjects-type defects without coercion; correct null-title abstention; preserving
completed attempts across interruption and refusing checkpoint overwrite; and a
full 108-attempt stub run with 54 repeated cases. Notebook code sources parse and
saved outputs/execution counts are empty. No model download/inference or paid calls.

The repair PR targets the PR #80 recovery branch to avoid duplicating the whole
unmerged validation kit against main. PR #87 remains Gauri's report; no message
was sent to Gauri and no review/comment was posted on her behalf.
