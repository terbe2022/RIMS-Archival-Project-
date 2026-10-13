# First experiment: establish access, then a Nemotron text baseline

Updated October 13, 2026. Gauri owns design and evidence. This replaces the
Colab-first Qwen assignment as the proposed next step; earlier Qwen reports and
PR #80/#87 remain historical/separate evidence, not proof of Nemotron access.

## Phase 1: access acceptance

Follow [API-ACCESS](API-ACCESS.md). Confirm permission with the service owner;
from Gauri's computer verify network/model listing; then make one authorized,
bounded synthetic request. Record exact endpoint privately, actual served model
ID, network/auth requirements, response/error and duration. Keep credentials out
of reports. No GPU or weights are installed on Gauri's laptop.

Completion means her own client can request inference and save results within
approved scope. A successful test on Tayler's computer does not meet this criterion.
If blocked, name whether permission, network, authentication, service or client
setup failed, and assign the responsible owner. Do not buy compute to hide it.

## Phase 2: component quality baseline

Gauri defines three to six fictional text sources: minutes, correspondence,
unreadable/insufficient input, a hard negative and evidence located late in a
long input. Each has independent expected facts, prohibited unsupported claims,
uncertainty and source evidence. Start with the exact deployed Nemotron ID after
verification; do not assume vision or embedding capability from the name.

Use canonical description prompts and allowed context; withhold valuable/exclude
criteria. Freeze input, settings and limits. Codex implements the bounded client,
fixture tests and reports in a gauri branch, using mocked network failures first.
Existing shared smoke fixtures can check integration but do not replace the
richer quality cases. Use a recorded reviewed commit and retain failures.

Report schema/parse validity, abstention, unsupported facts, coverage, specificity
and usefulness separately, under the agreed grading method. Frontier judging
awaits funding; do not silently substitute paid calls or treat model self-grades
as independent truth. Record limitations and define acceptance with Tayler/Joanne.

## Phase 3: performance and comparison

After the baseline succeeds, Gauri proposes contrasting candidates by task and
resource requirements for the service owner to provision. Measure cold/warm
latency and failure rates, then bounded throughput/concurrency with authorization.
Report input/output tokens, effective context/quantization and variability where
exposed; no archival model winner or system accuracy follows from a smoke run.

Deliver protocol, source-labelled fixtures, access outcome, baseline report and
findings register. Use [code guide](GAURI-CODE-EVALUATION-GUIDE.md),
[experiment template](experiments/TEMPLATE.md) and [result template](results/TEMPLATE.md).
Colab is optional fallback for synthetic cases; original content stays off Colab
and out of AI prompts. A full end-to-end pipeline is not required for component
experiments; integration/original-data validation follows separately.
