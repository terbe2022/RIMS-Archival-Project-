# Open questions — by who needs to answer them

Live list. Replaces `docs/stakeholders/open-questions.md`, which was written before the
August answers and is now mostly historical.

**Answered questions do not live here** — they go to
[`answers-2026-08.md`](answers-2026-08.md) with the answer and what it changed. This file is
only what is still outstanding.

**Legend:** 🔴 blocking · 🟡 shapes a decision · ⚪ good to know

Last updated 12 August 2026.

---

## Joanne Kaczmarek — University Archivist

### Raised on the follow-up call

| | Question | Why it matters | Answer | Date |
|---|---|---|---|---|
| 🔴 | Read access to the network share holding the 49 collections — who grants it, is read-only workable | Replaces the physical-drive ask entirely. Unblocks the directory listing, the size figure, and the first real inventory | | |
| 🔴 | An introduction to Tracy Popp | She owns the step immediately upstream and we have never spoken to her | | |
| 🔴 | Where the working copy of a full accession may live during processing | "I will find out" (5.6). Holds unreviewed personal information — needs a location, access control, and a clearing rule | | |
| 🟡 | Review capacity, re-asked concretely: *if the system handed you 200 flagged documents each with a one-line summary and a suggested disposition, is that an hour, a day, or a week?* | 6.1 gave no number because the question was underspecified. Thresholds set without this produce a queue nobody works through | | |
| 🟡 | Metadata standard, re-asked as a proposal: **Dublin Core for description, PREMIS for preservation events, mapped to whatever the destination accepts.** Does that conflict with anything? | 5.1 was "unsure how to answer" — fair, our question was abstract. Easier to react to a proposal than a blank field | | |
| 🟡 | Deed of Gift, re-asked: the Deeds stay where they are. Should the manifest carry a **pointer plus the restrictions in enforceable form**, so the system applies them rather than someone remembering? | 7.1 was a misunderstanding of our question, and the question was at fault | | |
| 🟡 | Retention window — how long should unselected material sit before disposal is proposed? | 5.7 asks for "a clear time period" without naming one. Schema defaults to 180 days pending her answer | | |
| 🟡 | Which three or four accessions should go first, and **why**? | She offered to make a priority list (8.3). The reasons matter more than the ranking — they tell us what the Archives values, which feeds triage | | |
| 🟡 | Can we be represented in the digital strategies exercise? | A system that appraises and describes born-digital accessions at scale is squarely in its scope, and Medusa's replacement is being decided inside it | | |
| ⚪ | Who to talk to about Medusa | "I will check" (5.5). Given the replacement, this should be someone connected to the strategies exercise | | |

### Things to tell her, not ask

| | Point | Why raise it |
|---|---|---|
| | **The bottleneck reframing.** We are not replacing the front of accessioning — we are unblocking the middle. Everything before the network drive is Tracy's and already works | Her own answer 1.2 says this better than our scope document did. Reflecting it back confirms we understood, and it is also the answer to "is this another proof of concept" |
| | **Our software does not delete on its own — but it will provide a recorded batched deletion action, and a retention clock** | She asked "which software never deletes?" (5.7) and deserves a straight answer, not a restatement of the design. She also identified the missing clock as the cause of the backlog, which we have now built in |
| | **We split discardable from sensitive for HR material** | 3.3 listed personnel matters as both. We made a change on her behalf and she should get to disagree with it |
| | **We will come back on the confidentiality-agreement question** | She asked us something (7.5). Answering it is cheap goodwill |

### Longer-horizon

| | Question | Notes |
|---|---|---|
| 🟡 | How does item-level machine-generated description attach to a folder-level finding aid without swamping it? | She asked this back at us (5.8). Needs a worked proposal, not a conversation. Sousa finding aid is the model |
| 🟡 | Email access model — stand-alone Archives workstation vs catalogue links; searchable index vs browsing | From her covering email. A genuine Stage 06 fork |
| ⚪ | Has ePADD been cleared by Library IT? | Java runtime concerns outstanding. Decides whether ePADD can ever be a delivery interface |

---

## Tracy Popp — Digital Preservation (via Joanne)

**The most important conversation not yet had.** She owns media processing, the tooling, and
the metadata output immediately upstream of us.

| | Question | Why it matters |
|---|---|---|
| 🔴 | What does the preservation processing produce — which tool, what fields, what file format? | Stage 01 does format identification and technical metadata. **She may already be doing both.** This could remove work rather than add it |
| 🔴 | Does that metadata travel with the content onto the share, or live separately? | Determines whether we can ingest it at all |
| 🟡 | Which BitCurator components are actually in use? | Confirmed in use (4.1). It bundles format ID and PII scanning, both of which we planned to build |
| 🟡 | Is DROID running? | Joanne was unsure. Determines whether our format identifiers should match an existing convention |
| 🟡 | Is any PII or sensitivity scanning happening already? | Same logic as above, for Stage 04 |
| 🟡 | Which of the 49 came from disk images vs file copies? | 1.6 says some did. Changes what Stage 00 has to read |
| 🟡 | Total size on disk and file count of the 49 | File counts are known per-accession; totals are not. `du -sh` answers it |
| ⚪ | Where does she see the handoff — what would make her job easier rather than more complex? | She is the person most affected by this system and has not been consulted |

---

## Brent West — RIMS

| | Question | Why it matters |
|---|---|---|
| 🔴 | **Where does the PII mapping store live, who can read it, does it need encryption at rest?** | Asked in the questions document (7.4) and came back blank. Blocks Stage 04 **and** blocks freezing the manifest schema — it is a type decision, not a value decision |
| 🟡 | Does the mapping outlive the processing run? | Same decision, second half |
| 🟡 | Is there an AITS confidentiality-agreement template the Archives could model? | Joanne asked us for this (7.5). Route via Brent |

---

## Bethany Anderson — Archives

| | Question | Why it matters |
|---|---|---|
| 🟡 | Is the nine-category sensitivity taxonomy from POC 3 still right, given answer 3.3? | 3.3 names categories to check it against — HR and personnel matters, discipline records, FMLA, personal finance. A PII scanner will not catch "the discipline hearing for the groundskeeper" |
| 🟡 | Would you and one other archivist label 50 files independently? | If two archivists disagree with each other, that is the finding — the criteria need tightening before scaling the exercise |
| ⚪ | Her 2021 *American Archivist* article on a format registry for born-digital records | Close enough to what we are doing that it should be read before designing further |

---

## Internal

| | Question | Owner |
|---|---|---|
| 🟡 | Gauri's server / L4 access — declined, revisit ~4 weeks | Supervisor |
| ⚪ | Box app authorization — scopes submitted, awaiting admin | Box admin, via Joanne or Brent |

---

## How to use this file

One row per question. Fill in the answer and the date in place. When a question is answered
**and** we have worked out what it changes, move it to `answers-2026-08.md` (or a successor
dated file) and delete the row here.

The point of the separation: this file should shrink. If it grows, we are accumulating
unanswered questions faster than we are resolving them, and that is worth seeing.
