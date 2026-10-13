# Result: Qwen2.5-7B synthetic description smoke test

Status: COMPLETED SMOKE TEST
Protocol: validation/FIRST-EXPERIMENT.md
Issue: not yet linked
Run date: 2026-10-10
Operator: Gauri
Repository revision: 1d61479ba308844a71d693007fa06e3bbdc76e6c
Model: Qwen/Qwen2.5-7B-Instruct
Model revision: a09a35458c702b33eeacc393d103063234e8bc28
Data classification: synthetic only; no real accession data used

## Sample and reproducibility

Google Colab runtime using Tesla T4 GPU with 15360 MiB memory.

Model configuration:
- Qwen/Qwen2.5-7B-Instruct
- 4-bit NF4 quantization
- float16 compute dtype
- greedy decoding / do_sample=False

Synthetic corpus:
- 54 total cases
- 34 documents
- 16 emails
- 4 images
- 16 cases expected to abstain
- 13 cases expected to route to a person

This smoke test used two deterministic cases:
- fixture-000: readable case
- fixture-027: expected-abstention case

Before model execution, eight offline regression checks passed:

`python -B validation/test_recovered_harness.py`

Result: 8 tests passed.

Protocol deviation / environment issue:
The recovered notebook caller initially failed because the installed Transformers version returned a BatchEncoding object from `apply_chat_template()`, while the notebook expected an object with a direct `.shape` attribute. The runtime caller was adjusted to use `return_dict=True`, move returned tensors to the model device, and read the input length from `inputs["input_ids"].shape[-1]`.

This was a notebook/runtime compatibility issue, not a model failure.

## Measures

| Candidate | JSON parseability | Schema checks | Abstention | Repeat consistency | Timing | Errors |
|---|---|---|---|---|---|---|
| Qwen2.5-7B-Instruct / a09a35458c702b33eeacc393d103063234e8bc28 | 2/2 parsed | One observed subjects-type inconsistency | Correct on the one abstention case | NA — one repeat only | 20.38s readable; 11.17s abstention | 0 model-call errors |

## Findings and reviewed examples

### fixture-000

Expected: readable document.

Observed:
- parsed successfully
- abstained: false
- readable: true
- genre: report
- title: "Referee Report"
- runtime: 20.38 seconds

The model returned `subjects` as one comma-separated string rather than as a list. This is a schema-format observation and should be checked in later runs.

### fixture-027

Expected: abstain because the source does not support a meaningful description.

Observed:
- parsed successfully
- abstained: true
- readable: false
- title: null
- genre: unknown
- runtime: 11.17 seconds

The model correctly declined to treat the input as a normal readable archival document.

## Recommendation and uncertainty

The smoke test successfully verified the basic Colab/model workflow, parsing path, and one expected-abstention behavior.

This test does not establish model quality, model ranking, production readiness, or appraisal-policy accuracy.

A full 54-case comparison with the approved repeat/settings protocol should only follow after protocol review.

## Artifact review

No real accession content, credentials, model weights, or protected University data were used or included.

Only synthetic results and technical observations are reported here.
