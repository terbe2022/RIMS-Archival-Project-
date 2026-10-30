# Meeting: give Gauri a usable evaluation role

October 13, 2026. Start with execution access and ownership, not another notebook walkthrough.

## What to say

"I started with three dataset-specific proofs of concept: images, emails and
mixed files. We are integrating them into an accession tool. It is still under
construction. I need you to shape and test the components as we build, including
metadata quality, model choice, long documents, reliability and performance.
You do not have to wait for the whole pipeline to be finished.

I have access to a University-hosted Nemotron model API. Your computer does not
need a GPU to use it: the server runs the model. We have not established your
permission or connectivity yet. Let's identify that blocker first. Colab is an
optional fallback, not your required work environment."

## Fifteen-minute agenda

| Time | Action | Outcome |
| --- | --- | --- |
| 0–3 min | Explain project scope and Gauri's evaluation/performance ownership | Shared role, not just running notebooks |
| 3–7 min | Identify NIM service owner and her permission; if authorized check model listing from her computer | Permission/network/auth status, separately recorded |
| 7–10 min | If authorized and a client is ready, one bounded synthetic inference request; otherwise record owner/action | Evidence or precise blocker, not assumed access |
| 10–13 min | Choose text metadata plus one extraction/email failure boundary | First source-labelled experiment she owns |
| 13–15 min | Agree standing run limits, coding support, deliverables and next owner | Clear next action without per-run Tayler gatekeeping |

Tayler reports NIM serving `nvidia/nemotron-3-nano`; exact served ID and her access
are unverified. Internal endpoint is delivered privately. More models can be
requested, not assumed already available. Do not conflate this service with the
archival pipeline server. No paid compute or external API funding is authorized.

## Decisions to leave with

- Who owns the NIM service and may authorize Gauri?
- Is API-only access permitted, and what network/auth route does she use?
- What standing synthetic workload limits allow her to work independently?
- Who implements the lightweight client (Codex) and supports access failures?
- Which component experiment and deliverables does Gauri own first?

If access is blocked: Gauri can produce a capability ledger, synthetic case
specifications and a preregistered comparison; measured model work remains blocked
until an execution route exists. Do not present this as a complete long-term setup.

Read [current project guide](../docs/PROJECT-GUIDE.md), [code/evaluation map](GAURI-CODE-EVALUATION-GUIDE.md),
[API access](API-ACCESS.md) and [first experiment](FIRST-EXPERIMENT.md).
Original-content access and archival reference judgements remain separate approvals.
