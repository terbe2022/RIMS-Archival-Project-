# Decision log

Every decision that shapes the build, with its status and who owns it. **This is the single
source of truth for decisions** — the kickoff agenda and the scope document both carried their
own D-numbered tables and they drifted apart within a week. Those are superseded by this file.

**Status values:** `open` · `answered` · `decided` · `superseded`

An **answered** decision is one where a stakeholder gave us the input we needed. A **decided**
one is where we then made the call and recorded the reasoning. Some go straight to decided
because they were ours to make.

Last updated 12 August 2026, against
[`../stakeholders/answers-2026-08.md`](../stakeholders/answers-2026-08.md).

---

## Open — blocking work

| # | Decision | Owner | Blocks | Notes |
|---|---|---|---|---|
| **D5** | Where the PII mapping store lives, who can read it, encryption at rest | **Brent West** | Stage 04, and freezing the schema | Asked in the questions document (7.4) and came back blank. Chase directly. Determines whether `s04_pii_map_ref` is a path, a URI, or a key — a type decision, cheaper now than later |
| **D6** | Read access to the Archives network share | Joanne → Infrastructure | Everything on real material | Replaces the old "remote drive access" decision, which was solving the wrong problem — see D6-old below |
| **D7** | What Tracy Popp's preservation processing produces | Joanne → Tracy Popp | Stage 01 scope | May *remove* work rather than add it. Highest-value unanswered item |
| **D8** | Where the working copy of a full accession lives during processing | Joanne | Stage 00 | "I will find out" (answer 5.6). Holds unreviewed personal information, so it needs a location, access control and a clearing rule |
| **D9** | Metadata standard the output must conform to | Joanne | Stage 05 | Answer 5.1 was "unsure how to answer" — our question was too abstract. Re-asking as a proposal: **Dublin Core + PREMIS, mapped to the destination**. What we do know: EAD finding aids at collection level, and collection-level description already exists |
| **D10** | Archives review capacity, in concrete units | Joanne | Threshold tuning | Answer 6.1 gave no number and the question was underspecified. Re-asking as "how long would a queue of 200 flagged documents take?" |
| **D11** | Labelled sample — 50 files, two archivists independently | Archives + Tayler | Scoring work | Now easier to ask for: we can draft the ruleset from answers 3.2/3.3 first, so this becomes a check on our reading rather than a blank-page request |
| **D12** | Retention window length for unselected material | Joanne | Disposal workflow | Answer 5.7 asks for "a clear time period" without naming one. Schema defaults to 180 days pending her answer |
| **D13** | How item-level description attaches to a folder-level finding aid | Joanne + Tayler | Stage 05 output | Joanne asked this back at us (answer 5.8). Likely shape: description in our store, link at folder level in ArchivesSpace |
| **D14** | Access model for email — reading-room workstation vs catalogue links; index vs browse | Joanne | Stage 06 | From her covering email. A genuine fork, not a detail |
| **D15** | Gauri's server / L4 access | Supervisor | GPU-bound work | Declined; revisit ~4 weeks from early Aug. CPU-first split holds meanwhile |

---

## Answered — input received, our call still to make

| # | Decision | Answer received | What we still owe |
|---|---|---|---|
| **D1** | Appraisal policy in writing | **Partial, 12 Aug.** Answers 3.2 and 3.3 give retain and discard categories for both accession types — the first written guidance we have | Draft the two rulesets from it and send back for confirmation. Not a policy, but enough to build against |
| **D2** | Which archival software the University licenses | **Full, 12 Aug.** Preservica no · Archivematica no · DROID unsure · ePADD experimented with · **BitCurator yes**. Administered by Tracy Popp | Fold BitCurator into the software evaluation; ask Tracy about DROID |
| **D3** | ePADD — adopt for the email lane, or keep our own | **Input received.** RIMS has nothing in place (Ringtail was e-discovery, not archival). ePADD uncommitted. **Library IT may block it over Java runtime vulnerabilities** | See D3 below under Decided — we have now made this call |
| **D4** | Where selected material and its metadata end up | **Answered, 12 Aug.** Medusa for preservation, Library Digital Library for access copies, ArchivesSpace for description with links out. **Not IDEALS.** Medusa itself is due for replacement | Design the repository-neutral package + adapter layer |

---

## Decided

| # | Decision | Call | Date | Reasoning |
|---|---|---|---|---|
| **D3** | Email lane: ePADD or our own | **Build on POC 1. Do not adopt ePADD as the processing engine.** Borrow its sensitivity lexicons. Revisit only as a possible *delivery* interface | 12 Aug | Architectural fit, not capability. ePADD wants a curated mailbox handed over as a unit; answer 1.7 says email arrives as loose `.eml` and `.pst` scattered inside personal-papers accessions. Routing it to a separate desktop application would put the appraisal decision for someone's correspondence in a different system from the decision about their papers — when answer 3.2 says the correspondence matters *because* it references the research in those papers. The Java runtime constraint is real but is the second reason, not the first. Full assessment: [`email-lane-epadd-evaluation.md`](email-lane-epadd-evaluation.md) |
| **D16** | Accession identity | **Carry both.** `record_series` for provenance (theirs), `accession_uid` for delivery scope (ours). `file_uid` derives from `accession_uid` | 12 Aug | A record series number identifies where material came from, not a delivery event — two batches from one office share a number. Keying to it would have collided silently |
| **D17** | Material with no record series number | **Does not enter the pipeline** | 12 Aug | Answer 2.3. Deletes the whole provisional-identifier and reconciliation path from the design |
| **D18** | Two accession types with separate rulesets | **`personal_papers` and `administrative`, branching in triage** | 12 Aug | Answers 3.2, 3.3, 8.2 — different retain rules, different discard rules, different turnaround targets. One averaged ruleset would be wrong for both |
| **D19** | Discardable vs sensitive | **Different dispositions. Sensitivity hard-beats discard, as precedence not weight** | 12 Aug | Answer 3.3 lists HR material as both. Collapsing them would let the system bin personnel files unseen |
| **D20** | Human oversight thresholds | **Approved as proposed, unchanged** | 12 Aug | Answer 6.3 was a flat yes. Now configured defaults rather than a proposal |
| **D21** | Access level vocabulary | **`open` and `restricted`. Two values** | 12 Aug | Answer 7.3. Their vocabulary, not ours |
| **D22** | Disposal | **The pipeline never deletes autonomously, but does provide a recorded batched deletion action, plus a retention clock** | 12 Aug | Answer 5.7 corrected our position. The Archives disposes deliberately after selection; the absence of a clock is what created the backlog |
| **D23** | Hosted AI services for archive content | **Ruled out** | Aug (v0.2) | FERPA-covered and unreviewed PII. Local open-weight models need no approval and have no per-token cost. Treat as closed unless Data Privacy says otherwise in writing |
| **D24** | Manifest storage format | **Parquet, queried with DuckDB** | 7 Aug | Columnar projection is what makes triage work on a 16 GB laptop. No separate database to keep in sync |
| **D25** | Duplicate handling | **One row per path, always. Never collapse** | 7 Aug | A file in three places is three archival facts. Dedupe is a decision (`duplicate_of`), not a representation |
| **D26** | Office extraction | **Tika + LibreOffice headless, replacing `win32com`** | Aug (v0.2) | COM automation will not run in Colab or on the Linux L4 host, cannot be parallelised safely, and hangs on malformed files |

---

## Superseded

| # | Was | Why it went away |
|---|---|---|
| D6-old | "Remote access to a real drive, or a directory listing" | Answer 1.2 — material is already off the media and on a network share, preservation-processed. The ask became read permission on a share, which is a much smaller thing. Replaced by D6 |
| D-old | "Confirm Data Privacy sign-off extends to full accessions" | Sign-off was granted for the POCs and the position has not changed. Not re-litigating |
| D-old | "Whether accessions arrive through Box or on physical media" | Answered: neither, in the sense that mattered. They arrive various ways, are processed by Tracy, and reach us on a share |

---

## How to use this file

Add a row when a decision appears; move it between tables as it progresses; never delete a
row — supersede it with a reason. The date and the reasoning columns are the point. In six
months the question will not be *what did we decide*, it will be *why*, and a decision without
its reasoning is just an assertion.
