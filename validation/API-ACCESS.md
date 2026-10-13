# University model API access and execution plan

Updated October 13, 2026. Tayler reports current access to a University-hosted
NVIDIA NIM service set up for this project, serving `nvidia/nemotron-3-nano` with
an OpenAI-compatible API. More models can be requested. These are user-reported
facts, not independent live verification. Gauri's access is unknown.

The exact internal HTTP address is supplied privately at the meeting. It is
not the archival pipeline host. This public guide contains no credentials or
internal API connection details. Current transport is reported plain HTTP;
use synthetic inputs only during checks and get the owner's approved transport
and authentication instructions before transmitting any credentials.

## Permission, network, authentication and inference are separate

1. Identify the service owner and confirm Gauri is allowed to use it for bounded
   synthetic project experiments. Tayler's access and GitHub membership do not
   establish this; absence of a login prompt does not grant permission.
2. From Gauri's computer on the owner-approved network/VPN, open the supplied
   base address with `/v1/models` appended. A model-list response establishes
   reachability/listing only; timeout/DNS failure suggests a network issue;
   401/403 suggests authentication/authorization; 404 suggests routing/version.
   None of these alone resolves the permission question.
3. Verify the exact model ID in the response, authentication method, request
   limits and approved data scope. Do not invent an API key or copy Tayler's.
4. Once authorized, Codex/the prepared client sends one fictional text request
   to `/v1/chat/completions`, with a small output budget, timeout and no retries.
   Preserve status, latency, model ID and output/error. A browser GET does not
   perform this inference test.
5. Record whether Gauri can run and save results independently. If not, record
   the precise blocker, owner and next action; do not call setup complete.

NIM endpoint conventions are documented by
[NVIDIA](https://docs.nvidia.com/nim/large-language-models/latest/reference/api-reference.html).
The installed deployment may differ: inspect its schema/owner guidance. An
OpenAI-compatible interface does not mean calls go to OpenAI or require an OpenAI
paid account. No paid provider API calls are authorized here.

## What her laptop does

The server holds weights and runs inference. Gauri's lightweight client prepares
synthetic requests and evaluates returned outputs. No local GPU or model-sized
RAM is required. Local extraction of very large files can still consume CPU/RAM,
so start with small generated fixtures or approved server-side extraction.
Ten stored models can be compared sequentially if the service owner provisions
them; all ten need not fit GPU memory together. Available capacity, modality,
model loading, queues and concurrency still constrain execution. A new model
request is not proof of installation or access.

## Standing experiment scope to request

Named user/project and allowed endpoints/models; synthetic-only scope; permitted
request count, input/output/context size, concurrency and run windows; queue and
cancellation behavior; result retention and approved sharing; service/support
owner; process for adding models. Separate server administration and original-data
access. This is proposed scope, not an access grant or configured service.

## Client implementation status

The shared text smoke harness already has an explicit vLLM-compatible endpoint
caller, but lacks a complete remote authentication/secret-redaction adapter,
model-discovery workflow, quality grading and performance instrumentation.
Codex should implement those on a gauri branch with mocked HTTP failures before
larger runs. Do not imply the current harness provides every required capability.
Credentials stay outside Git, notebooks and report artifacts. Reports record code
SHA, fixture/model IDs, prompt/configuration, timing, denominators and failures.

Colab is optional synthetic fallback compute. Paid provider comparisons and paid
frontier judging remain deferred until funding, account ownership and a cap are
approved. No new paid accounts, cloud rentals, credentials or services were created.
