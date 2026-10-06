# First Qwen experiment: synthetic description smoke test
Owner: Gauri. Prepared 2026-10-06. Status: protocol draft, not run.

## What this tests
Can Gauri open the published branch in Colab, load one Qwen candidate, generate descriptions for one readable and one abstention case, preserve results and return a reviewed report through GitHub? This is workflow/schema/refusal verification, not creator/date extraction, production certification or a model ranking.

## Exact files
- notebooks/colab-model-evaluation.ipynb: synthetic Colab runner.
- src/workbench/fixtures.py: synthetic corpus generator.
- src/workbench/evaluate.py: case builder, caller harness and technical scoring.
- validation/test_recovered_harness.py: eight offline regression checks.
- validation/GRADING.md and FRONTIER-JUDGING.md: quality rubric and future judge route.
- validation/experiments/TEMPLATE.md and results/TEMPLATE.md: protocol and report formats.

## Prerequisites
Tayler must publish the validation branch and provide its verified link/commit. Gauri creates a gauri/<experiment> branch from that reviewed base. Verify authorized Colab/account use on her University computer. No local installation, AITS access, paid API or credential sharing is needed. If GPU/model access is unavailable, report the blocker rather than buying compute or improvising credentials.

## Procedure
1. Read START-HERE, root/nested AGENTS and COLAB-WORKFLOW. Open the notebook from the published branch. Set its clone cell to that same branch (it currently defaults to main) and record git rev-parse HEAD.
2. Run python -B validation/test_recovered_harness.py from the cloned repository root. Passing stub checks is not a model result.
3. Inspect GPU and package versions. Review runtime-only install/download cells. Start with Qwen/Qwen2.5-7B-Instruct, 4-bit configuration from the notebook. Record model revision and configuration; memory fit is not guaranteed. Qwen3 is a later, explicitly configured candidate.
4. Build corpus/cases using the notebook cells. Select one readable and one abstention case deterministically. After defining caller, run the following instead of the full-run cell:

```python
smoke = [next(c for c in cases if not c.expects_abstention),
         next(c for c in cases if c.expects_abstention)]
smoke_attempts = E.run_model(MODEL, caller, smoke, repeats=1)
for a in smoke_attempts:
    print(a.case_id, a.error, a.seconds, a.raw, a.parsed)
```

5. Record actual responses, errors and case IDs. Required-key checking expects nonempty string title/description, while the prompt permits null title for unreadable input. Report schema checks and explicit readable=false refusal separately; do not mislabel a correct refusal solely from that required-key mismatch. Parseability is tolerant JSON recovery, not strict JSON-schema validation. Neither metric establishes factual correctness.
6. Store temporary synthetic output in validation/local-runs/ or the Colab runtime; it is not committed automatically. Put a reviewed summary in validation/results/<experiment>.md using the template. Do not upload entire runtime directories or real material. Save Python helper changes separately from notebook saves.
7. Clear notebook outputs/execution counts before GitHub submission. Review the diff and create a draft PR through her own authorized account. Record the actual tested commit separately from the later report commit.

## Completion evidence
Correct branch and fixture versions recorded; eight offline tests pass; two model calls attempted with preserved results/errors; refusal versus parse/required-key metrics correctly distinguished; output-free notebook/report draft PR accessible to Tayler. A failed model response is a result, not a reason to erase the run. A failed environment setup is a documented blocker.

No model-quality threshold or winner is assigned by this smoke test. After protocol review, run the actual built case set twice and report the observed case/abstention counts. Independent frontier judging remains pending funded access and tested adapters. No human grading step is required for this initial synthetic run.
