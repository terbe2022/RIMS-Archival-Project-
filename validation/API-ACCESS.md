# Model API access plan

Status: options prepared; no API access provisioned, keys created, spending
authorized or model calls made. Account owner/budget: pending Tayler confirmation.
All hosted-provider comparisons use synthetic cases only. No hosted API exception
for real accessions is created by this plan.

Tayler selected the initial route: open-weight Colab models with synthetic data.
Paid API funding is pending. The hosted provider entries below are future options,
not available credentials or approval to spend. Do not create a paid account or
make paid smoke requests until provider ownership and a cap are explicitly set.

| Route | What Gauri needs | How to compare | What remains pending |
|---|---|---|---|
| Open-weight Colab | Google account, available GPU, model licence acceptance where applicable | Existing synthetic Colab notebook, one model at a time | Runtime availability, dependency/version check, approved candidates |
| OpenAI API | Approved API project/access and secret injection by account owner | Adapter to the existing harness; record model revision, token use and errors | Funding, project role, model access, approved request/cost ceiling, adapter implementation |
| Claude API | Approved Anthropic account/workspace and API credential | Provider-specific adapter; same fixture/prompt semantics | Funding/access, supported parameters and adapter implementation |
| Gemini API | Approved Google project/key and relevant model access | Provider-specific adapter; same fixture/prompt semantics | Funding/access, model/settings equivalence and adapter implementation |
| University Ollama | Explicit host/data/run permission and confirmed local service | Existing University notebook after review | Gauri access, server state, workload authorization |

API accounts are separate capabilities from a ChatGPT subscription or GitHub
collaborator role. Do not assume API credits, models, write tools or GPU access
from either. Verify actual account entitlements; this document quotes no prices
or promised free quota. University-provided API services may be another route
after their owner identifies the service and grants the appropriate project role.

## Account-owner setup, performed personally

1. Select approved provider/project and synthetic-only scope.
2. Grant Gauri the least project access needed; separate experiments from production.
3. Set available spend/rate controls and a run-level maximum request/token budget.
   Do not assume a billing alert is a hard stop. Record the approved cap in protocol.
4. Store/inject credentials through approved secret controls outside Git. Never
   paste keys into chat, issue bodies, notebook source, PRs or shell-history commands.
   Agents should check whether the secret exists, not print its value.
5. Gauri approves one synthetic smoke request, checks response/error and cost,
   then explicitly approves the full comparison. Do not start with an unbounded loop.

## Runner implementation task

The existing harness accepts a callable per model. Provider adapters must use
official APIs, pass the same synthetic Case text and approved prompt, return raw
model text, and keep secrets out of errors. Log model/version, effective settings,
input/output tokens where available, status, latency and denominators. Document
unsupported decoding settings rather than pretending providers are identical.
Set timeout, bounded retry/backoff, maximum attempts and output-token limits.
Network allow-list and credential injection must be approved in the chosen runner.
Do not upload real data or allow a config switch to substitute real fixtures.

Implement adapters only after account/provider selection; test with mocked HTTP
responses first. First run is a paid/synthetic smoke test only after approval.
The recovered notebook evaluates local open-weight models; it is not already a
multi-provider API runner. An automated judge is a distinct experimental condition.

## Official setup references (checked 2026-10-06)

- [OpenAI API quickstart](https://developers.openai.com/api/docs/quickstart)
- [Claude API overview](https://platform.claude.com/docs/en/api/overview)
- [Gemini API keys](https://ai.google.dev/gemini-api/docs/api-key)
- [Codex Cloud environments](https://learn.chatgpt.com/docs/cloud)

API/SDK choices and availability change; verify the official provider docs when
implementing the selected adapter. No credential handling is needed to read them.

Frontier judge candidates and Qwen implementation: [FRONTIER-JUDGING.md](FRONTIER-JUDGING.md). User-selected grading uses models; paid access/funding still pending.
