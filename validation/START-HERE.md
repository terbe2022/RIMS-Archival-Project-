# Gauri: start here

Updated October 13, 2026. The immediate task is to establish a usable execution
route and your evaluation ownership, not to complete a Colab notebook.

## Today's reading path

1. [Meeting and access plan](MEETING-ACCESS-PLAN.md): current facts, unknowns and decisions.
2. [Current project guide](../docs/PROJECT-GUIDE.md): purpose, responsibilities and evidence.
3. [Code and evaluation guide](GAURI-CODE-EVALUATION-GUIDE.md): code boundaries, gaps, cases and performance work you can own.
4. [Quality/performance protocol](../docs/EVALUATION.md), [grading](GRADING.md) and [validation rules](AGENTS.md): how results are assessed and what is prohibited.

Use the code guide's ordered links when exploring implementation; do not start
by reading every historical document. Root [AGENTS.md](../AGENTS.md) also applies.

## Execution route: University model API first, if approved

Tayler reports working access to a University-hosted NVIDIA NIM Nemotron service
set up for this project. Gauri's permission, network reachability and ability to
make inference requests are unverified. See [API access](API-ACCESS.md).
The internal endpoint is supplied privately at the meeting, not in public Git.

A server API runs the model on the server. Gauri's laptop needs a reachable client,
not a GPU or local weights. API-only access is different from server shell access;
neither is automatically granted by GitHub access or Tayler's existing access.
More models may be requested; none are promised installed or approved for her.

Colab is an optional synthetic fallback for an available GPU, not a prerequisite
or guaranteed compute resource. The shared notebook improvements are in draft
PR #94; confirm merge state before assuming main includes them. No paid compute
or provider API spending is authorized.

## First useful work

During the meeting: identify the service owner, confirm permission/scope, check
reachability from Gauri's computer, and if approved make one bounded synthetic
request. Record each outcome separately; access success is not model quality.

Gauri owns a capability ledger, source-labelled synthetic cases, candidate roles,
quality/rubric design, long-input experiments, performance measurements and defect
retests. Codex handles fixture/client/test implementation through reviewed PRs.
If compute access is blocked, she can inspect code and deliver a protocol/fixture
specification now; measured comparisons must wait for an execution route.

[Onboarding](GAURI-ONBOARDING.md) covers setup; [first experiment](FIRST-EXPERIMENT.md)
covers acceptance. Existing larger recovered fixtures/harness are on PR #80's
branch until merged: record the actual executable commit, not only a doc commit.
Use [experiment](experiments/TEMPLATE.md) and [result](results/TEMPLATE.md) templates.
Original content stays on approved infrastructure and out of Colab/AI prompts.
