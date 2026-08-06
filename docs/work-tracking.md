# How We Track This Work

**Recommendation:** GitHub Issues + a GitHub Project board. Not the HTML document, not Colab,
not a spreadsheet.

---

## The reasoning

We have three kinds of artefact and they should not live in the same place:

| Artefact | Changes | Lives in |
|---|---|---|
| **Design and scope** — what we're building and why | Slowly, deliberately | The HTML scope document + `docs/` |
| **Task state** — who is doing what, what's blocked, what's done | Daily | GitHub Issues + Project board |
| **Decisions and answers** — filled-in worksheets | As answers arrive | `worksheets/`, committed |

The HTML document is the reference. If we put live task state in it, it goes stale within a
week and then nobody trusts any of it — including the parts that were still accurate. Keeping
task state out of it is what lets it stay authoritative.

## Why GitHub Projects specifically

- **It's already where the code is.** An issue can reference a commit, a pull request, a
  notebook, a line of code. That linkage is the whole point and no external tracker gives it.
- **Free, and no approval needed.** No procurement conversation, no new licence.
- **Gauri learns the standard tooling.** Issues, branches, pull requests and a board are how
  software teams actually work. That's worth more to her career than learning our bespoke
  spreadsheet.
- **It survives us.** When this hands over, the history of why decisions were made is in the
  issue threads, not in someone's inbox.

## Why not the alternatives

**Not the HTML doc** — a scope document with live checkboxes becomes a stale scope document.
The Week 1 list in it is deliberately a *plan*, not a tracker; it links out to the worksheets
and issues rather than trying to hold state.

**Not Colab** — Colab is where notebooks run. It has no concept of tasks, ownership, or
dependencies, and notebook comments are not a work log.

**Not a spreadsheet in Box** — no linkage to code, no history of why something changed, and
two people editing it will conflict.

**Not Jira/Asana/etc.** — would need approval and probably a licence, and adds a tool the
Archives team would have to be onboarded into for very little gain over Issues.

---

## Setup

### 1. Labels

```
stage:00-source        stage:01-inventory     stage:02-triage
stage:03-extraction    stage:04-enrichment    stage:05-metadata
stage:06-index         stage:07-scale

type:build             type:research          type:decision
type:question          type:bug               type:docs

blocked                needs-joanne           needs-brent
needs-privacy          needs-infra            needs-supervisor

owner:tayler           owner:gauri
```

The `needs-*` labels matter more than they look. Filtering by `needs-joanne` before a meeting
gives you the agenda.

### 2. Board columns

```
Backlog  →  This week  →  In progress  →  Blocked  →  Review  →  Done
```

**Blocked** is a column rather than a label on purpose. Something sitting in Blocked with a
named owner and a date is visible; something with a `blocked` label buried in a list of forty
issues is not.

### 3. Milestones

| Milestone | Contains |
|---|---|
| M1 — Foundations | Manifest schema, environment setup, software evaluation |
| M2 — First pass working | Stages 00–02 running on the pilot corpus |
| M3 — Enrichment | Stages 03–05 |
| M4 — Delivery | Stage 06, review interface |
| M5 — Scale | Stage 07, throughput model, processing schedule |

### 4. Seed issues from the Week 1 list

Every row in the HTML document's Week 1 table becomes an issue. Title, the "why" as the body,
owner as assignee, stage label. Takes about twenty minutes and gives the board something real
on day one.

---

## Working conventions

**Issues capture decisions, not just tasks.** When we settle the manifest schema, that goes
in an issue thread with the reasoning. In a year, when someone asks why we partitioned by
drive rather than format class, the answer should be findable.

**Blocked issues name a person and a date.** "Blocked" on its own is not information.
"Blocked on Joanne — appraisal policy — asked 6 Aug" is.

**Worksheets get committed as they fill in.** W1 through W4 are living documents. Commit
partial answers rather than waiting for completeness — a half-answered worksheet with a named
blocker is more useful than an empty one.

**Branch per issue, PR to main.** Even for notebooks. It gives Gauri the review loop, and it
means I see the work before it lands rather than after.

---

## What goes where — quick reference

| Thing | GitHub | Box |
|---|---|---|
| Code and notebooks | ✅ | |
| Design docs, worksheets | ✅ | |
| The HTML scope document | ✅ (`site/`, published via Pages) | |
| Task state | ✅ (Issues/Projects) | |
| Sample data, corpora | | ✅ |
| Anything containing PII | | ✅ |
| Output CSVs, indexes, model files | | ✅ |
| Proposal documents, meeting notes | | ✅ |
| Credentials | Neither — env vars, never committed | |

The rule: **if it contains data, it goes in Box. If it describes or produces data, it goes in
GitHub.**

---

## Publishing the scope document

Settings → Pages → Deploy from branch → `main` → `/` (root).

The document will be at:
```
https://terbe2022.github.io/RIMS-Archival-Project-/site/
```

Its internal links are repo-relative (`../docs/`, `../worksheets/`), so they resolve correctly
from that path. Send that link to Joanne and Brent rather than a document attachment — it
updates when we commit.
