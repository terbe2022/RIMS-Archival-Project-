# Documentation

Reorganised 12 August 2026. Everything used to sit flat in `docs/`, which made it impossible to
tell what was authoritative from what was a one-off setup note, or what had been superseded.

Four folders, split by **how often the thing changes and who reads it**:

| Folder | What it holds | Who reads it | Changes |
|---|---|---|---|
| [`design/`](design/) | What we are building and why | Everyone, constantly | Often — treat as live |
| [`stakeholders/`](stakeholders/) | What the Archives has told us | Everyone | When we get answers |
| [`setup/`](setup/) | Getting a machine working | Gauri, mostly once | Rarely |
| [`superseded/`](superseded/) | Old versions, kept for provenance | Nobody, day to day | Never |

**The rule:** if `design/` and `superseded/` disagree, `design/` wins. If `design/` and
`stakeholders/` disagree, **`stakeholders/` wins** — that is the record of what the Archives
actually said, and our interpretation is the thing that should change.

---

## design/ — the live documentation

Start here if you are new.

| File | What it is |
|---|---|
| [`pipeline-design.md`](design/pipeline-design.md) | **Read this first.** The whole system: problem, architecture, eight stages, oversight, delivery. v0.3 |
| [`manifest-schema.md`](design/manifest-schema.md) | The manifest contract every stage reads and writes. v1.1, not yet frozen |
| [`schema-changelog.md`](design/schema-changelog.md) | Every schema change, with dates and reasons |
| [`decisions.md`](design/decisions.md) | **Single source of truth for decisions.** Open, answered, decided, superseded |
| [`file-type-gap-analysis.md`](design/file-type-gap-analysis.md) | What POC 2 handled, what it did not, how to close the gaps |
| [`email-lane-epadd-evaluation.md`](design/email-lane-epadd-evaluation.md) | Assessment of POC 1 against ePADD, with the recommendation and the fix list |

## stakeholders/ — the record

| File | What it is |
|---|---|
| [`answers-2026-08.md`](stakeholders/answers-2026-08.md) | Joanne's answers to the questions document, with what each one changes. **Authoritative** |
| [`open-questions.md`](stakeholders/open-questions.md) | What is still outstanding, by who owes it |

Answered questions move *out* of `open-questions.md` and *into* `answers-*.md`. The open list
should shrink over time; if it grows, that is worth seeing.

## setup/ — getting started

Mostly written for Gauri, mostly stable, mostly one-time.

| File | What it is |
|---|---|
| [`onboarding-and-setup.md`](setup/onboarding-and-setup.md) | Machine setup, hardware notes, week-one orientation |
| [`colab-setup.md`](setup/colab-setup.md) | How Colab connects to the repo, and the code-lives-in-`src/` rule |
| [`box-for-gauri.md`](setup/box-for-gauri.md) | Getting into Box, what is in there, what to run first |
| [`box-integration.md`](setup/box-integration.md) | Architecture, rate limits, the metadata-only crawl strategy |
| [`box-run-now.md`](setup/box-run-now.md) | The short version — running it today with a developer token |

All three Box documents carry a scope note: **Box is pilot infrastructure, not the ingest path.**
Real accessions live on an Archives network share. The Box work is still worth doing — it
produces the first real measurements — but it is not how production material arrives.

## superseded/ — do not work from these

| File | Superseded by |
|---|---|
| `2026-08-07-manifest-schema-v1.md` | [`design/manifest-schema.md`](design/manifest-schema.md) — v1.0 keyed `file_uid` to a number that is not unique per delivery |
| `2026-08-07-kickoff-agenda.md` | The event happened; live content moved to `design/decisions.md` and `stakeholders/` |

Each carries a banner explaining what replaced it and why. Kept rather than deleted because the
reasoning is often still worth reading, and because knowing *what we got wrong* is part of the
project record.

---

## Also in the repo

- [`../worksheets/`](../worksheets/) — task documents with named owners. W2 is live; W1, W3 and
  W4 are in `worksheets/superseded/`, largely because the August answers resolved them.
- [`../poc/`](../poc/) — the three completed proofs of concept, with known defects documented.
  Read the defects before reusing anything.
- [`work-tracking.md`](work-tracking.md) — how issues, the board and this repo fit together.

## Conventions

**Date-stamp anything that is a snapshot.** `answers-2026-08.md`, `2026-08-07-kickoff-agenda.md`.
A document that records what was true on a day should say which day in its filename.

**Version anything that evolves.** The pipeline design is v0.3, the schema is v1.1. Both carry a
changes-from-previous block at the top, so someone who read the last version can see what moved
without re-reading the whole thing.

**Supersede, do not delete.** Move it to `superseded/`, add a banner saying what replaced it.
Deleting a document destroys the record of what we believed and when.
