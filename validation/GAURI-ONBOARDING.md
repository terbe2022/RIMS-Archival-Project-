# Gauri's onboarding and first assignment

GitHub: gauri-bhasin. Tayler confirms collaborator access already exists. Gauri
uses a University computer and reportedly pays about $20/month for ChatGPT.
Her exact plan, Codex entitlement and enabled tools are not verified from that
price. Start with synthetic-only open-weight Colab models. Paid API funding is
pending; paid provider runs are not authorized by this onboarding.
Prepared 2026-10-06; this workspace is local until published.

## Setup choices

Gauri is not assumed to have used Codex or connected it to this repository.
Use [COLAB-WORKFLOW.md](COLAB-WORKFLOW.md) as the daily coding workflow and
[PROGRAM-MANAGER.md](PROGRAM-MANAGER.md) to activate/check her coordinating agent.
GitHub/Colab browser work can begin without a local Codex installation; agent
repository writes require verified tool-enabled access and a task branch.

Initial route: GitHub web + Colab, requiring no local software installation.
If Codex is available in her actual account, use it to assist protocol/code/offline
tests as Route A describes. Confirm University IT rules before connecting tools,
installing software or using a local development runtime on her machine.

GitHub web access provides repository reading, editing a task branch and opening
a PR; it does not provide a Python/GPU runtime. Ordinary chat is not evidence of
read/write/execution tools. Use a connected Codex task or a local clone with a
coding agent for automated tests. Colab supplies the synthetic model runtime.

### Route A: Codex Cloud, if available in her account

1. Sign in using her own account. Open Codex/Cloud and connect her GitHub identity.
2. Select only terbe2022/RIMS-Archival-Project- for this project. Tayler may need
   to approve the app's repository access; collaborator access alone may not suffice.
3. Prepare the repository environment. Review dependency/tool setup and tests
   before publishing it. Do not attach real data or server credentials.
4. Start with the bootstrap prompt in AGENT-ROLES.md. Verify actual file-edit,
   shell and repository permissions. If unavailable, report that plainly.
5. Use Codex for code/protocol/offline checks; use Colab for approved model/GPU
   comparisons. Do not assume the Codex coding environment has a suitable GPU.
6. Work on gauri/<experiment>; review diff/checks and PR before merging.

### Route B: local clone and local coding agent

Confirm Git and Python are available; no automatic installation or changes to
credentials/Windows policy. If missing, ask Tayler for the approved setup route.
Choose her own permanent development directory; do not copy Tayler's path.

```text
git clone https://github.com/terbe2022/RIMS-Archival-Project-.git
cd RIMS-Archival-Project-
git status --short --branch
git switch -c gauri/model-comparison-design
python -B validation/test_recovered_harness.py
```

These instructions assume recovery has merged. Before merge, use the published
recovery branch as the reviewed base; do not duplicate conflicting work on main.
Open the clone in an available tool-enabled coding agent signed in personally.
Authentication prompts are handled by Gauri, never pasted into chat. Windows
execution policy need not change to use individual Git/Python commands.

### Route C: GitHub web plus Colab

If no Codex/local runtime is available, use GitHub's branch selector to create
gauri/<experiment> from the reviewed base, edit protocol/report files in the web
editor, and open a PR. Open the synthetic notebook in Colab as in START-HERE.md.
ChatGPT may help design/review text, but Gauri performs GitHub edits and Colab runs
herself unless verified tools support those actions. This is a usable fallback,
not a claim that the chat agent can remotely control her notebook.

## First assignment and completion evidence

1. Read operating rules, START-HERE, PLAN, agent roles and GRADING.
2. Demonstrate repository read access and a small protocol change on her own
   branch; open a draft PR if she is authorized. Never test write access on main.
3. Run the eight offline regression checks; attach the result and actual commit.
4. Pre-register one comparison: approved candidate IDs, all 54 synthetic cases,
   two repeats, fixed prompt/settings, explicit failure/refusal metrics and agreed
   judge protocol thresholds. Design changes require a labelled protocol revision.
5. Confirm compute, licences and provider budget in API-ACCESS before execution.
6. Run one synthetic smoke case, then an approved full comparison. Preserve errors.
7. Prepare separate blind sheet/key, full synthetic source and model judging records.
8. Submit an evidence-linked report and PR: recommendation, failures, uncertainty,
   licence/cost notes and next experiment. Tayler reviews integration implications.

Day-one success is verified access, a protocol PR and an offline test report,
not a fabricated model-quality result. After baseline, context ablation is a
separate preregistered task; real-data gold-set work needs University approval.

## Communication

Use the GitHub issue for work state, design questions and blockers. PRs carry
changes/review. Experiment and report files carry durable scientific evidence.
The agent gives Gauri a concise role handoff with artifact links; Gauri approves
design, execution and findings. Do not send messages to other people automatically.

References: [GitHub branch/commit/PR tutorial](https://docs.github.com/en/get-started/using-github/hello-world),
[Codex setup](https://learn.chatgpt.com/docs/cloud),
[API access plan](API-ACCESS.md). Product interfaces/entitlements may vary; confirm
the actual account's features instead of inferring them from ChatGPT membership.

Current grading route: [FRONTIER-JUDGING.md](FRONTIER-JUDGING.md). No blind human grading is planned for synthetic model comparison; independent archivist policy/gold-set work remains separate.
