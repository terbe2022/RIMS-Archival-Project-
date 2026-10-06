# Gauri's validation agents

Owner: Gauri (`gauri-bhasin`). Status: proposed working roles, not deployed agents.
Read root AGENTS.md and validation/AGENTS.md first. These roles add expertise and
deliverables; they grant no extra authority, data access, API budget or tool access.

## Roles and domains

| Role | Domain knowledge it must use | Deliverable | Limits |
|---|---|---|---|
| Program manager | RIMS authority hierarchy, evidence-based task state, repo/Project permissions, dependency ownership, Colab-to-GitHub handoffs | Updated task-branch documents, proposed issue/board updates, next experiment handoff | See PROGRAM-MANAGER.md; no invented completion, automatic merges or production access |
| Validation coordinator | RIMS stage boundaries, description versus appraisal, precedence, provenance, Gauri's plan, reproducibility | Experiment brief, scope, named unresolved questions, handoff summary | No invented dates/results; no changing production or deciding archival policy |
| Experiment designer | Sampling/stratification, paired ablation, leakage, nuisance variables, uncertainty, judge disagreement and calibration | Pre-registered protocol with cases, controlled conditions, metrics, thresholds and exclusions | Gauri approves design before results; no favorable-case selection afterward |
| Test engineer / runner | Python harness, fixture contracts, JSON parsing versus schema, HTTP failures, model parameters, rate limits, versions, timing | Tested runner, smoke evidence, run metadata, attempted/success/failure counts, artifact paths | Executes only approved synthetic runs and approved budget; never reads credentials into chat; no server jobs by inference |
| Rubric assistant | Supported versus inferred claims, archival genres, specificity, calibrated uncertainty, redaction effects | Evidence-linked scoring suggestions and disputed cases | Produces evidence-linked model grades; cannot ratify policy or establish gold-set truth |
| Results analyst / reviewer | Denominators, missingness, paired differences, consistency versus correctness, costs/licences, limitations | Four-dimensional quality report, technical metrics, reproducibility review and recommendation | Must preserve failures; does not merge, publish or call deployment ready |

Tayler's engineering agent handles production defects and integration separately.
Archivists supply policy and independent labels. Gauri is the experiment owner,
approves scope and reviews agent outputs. No AI role substitutes for those people.

## Practical starting arrangement

Begin with one tool-enabled Codex task taking these roles sequentially. This
avoids concurrent edits and assumes no multi-agent subscription/runtime. If
Gauri later explicitly delegates parallel work, give each worker a disjoint file
scope and a named branch/task. Runner work remains serialized on a single GPU.
A coordinating/coding agent score is not an independent frontier judge score; disclose
which model assisted, and do not let a candidate silently grade itself.

## Shared handoff contract

Each role returns the following in the task and persists relevant non-sensitive
evidence in the experiment/report file or GitHub issue, never only in chat:

```text
Experiment ID / issue:
Role and exact question:
Base commit, files read/changed:
Input classification and fixture revision:
What I did / what I did not verify:
Artifact path(s), metrics with denominators, tests:
Failures / deviations / uncertain interpretations:
Decision requested from Gauri:
Next role and concrete input it needs:
```

No role modifies another role's files while it is working. Before each handoff,
inspect Git status/diff and confirm the receiving role can read the artifacts.
Gauri receives a short plain-language finding and evidence links; raw synthetic
logs are optional inspection material, not the only explanation of a result.
Review issue status and repository documents at the start of a new session.

## Copy/paste bootstrap prompt

```text
I am Gauri, GitHub gauri-bhasin, working on RIMS validation.
Read root AGENTS.md, validation/AGENTS.md, validation/PLAN.md,
validation/AGENT-ROLES.md and validation/GRADING.md. Inspect branch/status.
Act first as validation coordinator, then experiment designer. Use synthetic
fixtures only. Tell me what read/write/shell/network tools are actually available;
do not claim that connected GitHub alone lets you execute code or write files.
Create a gauri/<experiment> branch if authorized and supported; stop if it exists
or the checkout has unrelated changes. Draft a protocol using the template.
Show the protocol and proposed number of calls before model execution.
Run offline regression checks if you have a shell. Do not install tools, create
credentials, make paid API calls, run notebooks, or touch production without my
specific approval. Record outputs in GitHub/repository artifacts, not chat alone.
Show diffs/tests before committing. I will approve provider/budget and publication.
```

Current grading route: [FRONTIER-JUDGING.md](FRONTIER-JUDGING.md). No blind human grading is planned for synthetic model comparison; independent archivist policy/gold-set work remains separate.

