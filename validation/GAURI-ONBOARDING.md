# Gauri's practical onboarding

Updated October 13, 2026. Begin with [START-HERE](START-HERE.md) and the
[meeting/access plan](MEETING-ACCESS-PLAN.md). Gauri's GitHub collaborator access
is reported accepted. Her server shell access, model API access, local software
availability and coding-agent tools must be checked separately.

## What you need

You do not need local GPU hardware or model weights to use an approved University
model API. You need permission, a working network route, any approved personal
authentication, and a lightweight experiment client. Codex can build the client;
it is not yet a provisioned browser experiment application.

Tayler reports access to University NVIDIA NIM serving `nvidia/nemotron-3-nano`.
Use [API-ACCESS](API-ACCESS.md) to verify your own access. Obtain the exact served
model ID from the service rather than assuming the reported name is its API ID.
The API host is different from the archival pipeline server; do not conflate them.
Do not share credentials or work around the server-access decision.

## Three independent capabilities to establish

| Capability | Evidence | If absent |
| --- | --- | --- |
| Repository reading and contribution | Read current guide/code; prepare a harmless gauri-branch change/PR through own account | Resolve GitHub permission with repository owner |
| Coding/test tools | Available approved local or connected coding agent can edit files and run offline checks | Codex in Tayler's workspace can implement Gauri's specifications; do not infer tool access from ChatGPT membership |
| Model execution | Owner-approved API access plus a successful bounded synthetic request from Gauri's computer | Record permission/network/auth/service blocker and owner; no model-quality result yet |

Agent/account integrations and software installation follow institution-approved
setup. Sign in personally; do not put tokens in prompts, notebooks, commands or
GitHub. Exact ChatGPT/Codex entitlement is not inferred from a subscription price.

## Autonomy to agree with the service owner

Ask for standing synthetic experiment permission with named allowed models,
request/token/concurrency limits, work windows, storage, cancellation and a route
for requesting additional models. Gauri then chooses cases/settings and runs
within that scope without asking Tayler to launch every experiment. API-only
permission need not include administration or access to original files.

Gauri owns scientific design and findings; Codex implements fixtures, clients,
tests and assigned repairs; Tayler reviews integration; archivists ratify appraisal
criteria/reference labels. No provider spending or blanket server workloads are
approved by this document. Original-data permission remains separate.

## First deliverables

An access outcome/owner, a code capability ledger, a small source-labelled
synthetic experiment protocol, and an implementation PR prepared with Codex.
After access: preserved baseline outputs/errors, agreed grading and a report,
then bounded performance experiments and defect retesting. A notebook opening
is setup evidence, not the entire assignment or proof of model accuracy.

Colab remains an [optional fallback](COLAB-WORKFLOW.md); it is not guaranteed
compute and is not required for University API evaluation. The larger validation
kit still requires its matching published branch until PR #80 merges.
