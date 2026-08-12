# Open Questions — Organised by Who Needs to Answer Them

> **SUPERSEDED by [`docs/stakeholders/open-questions.md`](../../docs/stakeholders/open-questions.md).**
> Answers received 12 Aug 2026 are recorded in
> [`answers-2026-08.md`](../../docs/stakeholders/answers-2026-08.md); what remains open moved to
> the new file. This one is kept only to show what was asked and when.


Working list. Every question that currently blocks or shapes a decision, grouped by who I
need to put it to. Fill in the answer and the date when I get one.

**Legend:** 🔴 blocking · 🟡 shapes a decision · ⚪ good to know

---

## Joanne Kaczmarek — University Library / Archives

### Appraisal and selection

| | Question | Answer | Date |
|---|---|---|---|
| 🔴 | Who writes the appraisal policy, and by when? Without a written definition of what "important" means, triage cannot be built or measured. | | |
| 🔴 | Can the Archives hand-label 300–500 files as a gold set? That set is simultaneously the specification and the way we measure whether triage works. | | |
| 🟡 | What are the categories of material that must always be retained, regardless of anything else? | | |
| 🟡 | What is routinely disposable — drafts, duplicates, personal material unrelated to university work? | | |
| 🟡 | Does the Archives have an existing accessioning procedure this pipeline should feed rather than sit beside? | | |

### Software and standards

| | Question | Answer | Date |
|---|---|---|---|
| 🔴 | Does the Library or Archives already license Preservica, or run Archivematica? If either, stages 05 and 06 shrink significantly. | | |
| 🟡 | Do you already run DROID as part of accessioning? If so we should match its output conventions. | | |
| 🟡 | Dublin Core simple or qualified? Is EAD expected for collection-level finding aids? | | |
| 🟡 | Is there an institutional metadata profile we should target instead of plain Dublin Core? | | |
| ⚪ | Do you use any tool for email archives currently — ePADD or otherwise? | | |

### Scale and scheduling

| | Question | Answer | Date |
|---|---|---|---|
| 🔴 | Can I get a directory listing of one representative drive, even before full access is sorted? It costs nothing to produce and it gives me format mix and file counts, which are the two variables that dominate processing time. | | |
| 🟡 | How many drives are queued, and what is the size range? | | |
| 🟡 | Is there a prioritisation among them — collection significance, donor deadlines, media degradation? | | |
| 🟡 | What turnaround per drive would you consider acceptable? | | |

### Review capacity

| | Question | Answer | Date |
|---|---|---|---|
| 🔴 | How many items per week can the Archives team realistically review? Thresholds set without knowing this produce a queue nobody works through. | | |
| 🟡 | Who reviews sensitivity flags — you, Bethany, someone else? | | |
| 🟡 | Are the proposed oversight thresholds acceptable, or do they need adjusting? | | |

---

## Brent West — Information Governance / RIMS

| | Question | Answer | Date |
|---|---|---|---|
| 🔴 | What retention obligations constrain disposal here? Does "quarantine, never delete" satisfy them? | | |
| 🔴 | Who has authority to approve deletion, and at what granularity — file, folder, batch, accession? | | |
| 🟡 | Are any queued accessions under litigation hold or open FOIA request? | | |
| 🟡 | What email tooling has RIMS been using for archiving and e-discovery? Is ePADD in the picture? | | |
| 🟡 | Does anything here need Records Management sign-off beyond you and Joanne? | | |
| 🟡 | For deceased faculty — what donor agreements or estate restrictions govern access? | | |
| ⚪ | The word-frequency redaction approach you developed — should that be a lane alongside Presidio, or has it been superseded? | | |

---

## Bethany Anderson — Archives

| | Question | Answer | Date |
|---|---|---|---|
| 🟡 | From an archival appraisal standpoint, what signals actually indicate enduring value in a personal digital collection? | | |
| 🟡 | How much does folder structure and naming carry meaning in practice, in your experience with these collections? | | |
| 🟡 | What would make a generated finding aid useful to you versus something you'd rewrite from scratch? | | |
| 🟡 | Should generated description be visibly distinguished from human-written description in the delivered metadata? | | |

---

## Data Privacy & Governance

| | Question | Answer | Date |
|---|---|---|---|
| 🔴 | What is the approved chain of custody for media containing unreviewed PII? | | |
| 🔴 | Is processing this content with locally-hosted open-weight models on university hardware acceptable, given nothing leaves our infrastructure? | | |
| 🔴 | Is sending any of this content to a hosted AI service categorically excluded? I am assuming yes and designing accordingly. | | |
| 🟡 | Does copying a drive to university network storage constitute a disclosure requiring notice? | | |
| 🟡 | Encryption requirements at rest and in transit? | | |
| 🟡 | Who may see unreviewed content during processing — does Gauri's role permit it? | | |
| 🟡 | Does generated metadata derived from sensitive content inherit the same handling requirements as the source? | | |
| ⚪ | Is there a training or agreement requirement before handling this material? | | |

---

## Infrastructure / Sysadmins

| | Question | Answer | Date |
|---|---|---|---|
| 🔴 | Can a drive be attached to a machine I can reach remotely? What is the approval path and timeline? | | |
| 🟡 | What storage capacity is available to the processing host, and what does expanding cost? | | |
| 🟡 | Network throughput between storage and processing host? | | |
| 🟡 | Monitoring on the processing host — if a multi-day job fails at hour 30, how do I find out? | | |
| 🟡 | Backup position for working storage during processing? | | |
| ⚪ | Procurement timeline for additional GPU capacity, if the throughput model shows we need it? | | |

---

## My supervisor

| | Question | Answer | Date |
|---|---|---|---|
| 🟡 | What would Gauri need to have completed before server access can be reconsidered? Currently declined; worth knowing the bar. | | |
| 🟡 | Is there budget for additional storage or GPU capacity if the sizing model shows we need it? | | |
| ⚪ | How does this project relate to the other AI initiatives — should any components be built to be shared? | | |

---

## Questions Gauri and I answer ourselves

These don't need anyone else — they're design decisions we make and record.

| | Question | Where it gets answered |
|---|---|---|
| 🔴 | The full manifest schema | `docs/design/manifest-schema.md` |
| 🔴 | Which existing software we adopt | `worksheets/W2_software_evaluation_task.md` |
| 🟡 | Which models we standardise on | Model comparison, Week 2 |
| 🟡 | Text peek strategy and budget | Pipeline design, stage 02 |
| 🟡 | Whether we adopt ePADD for email or keep our own lane | After Brent answers on RIMS tooling |
| 🟡 | Partitioning strategy for the manifest | Manifest worksheet |
| ⚪ | Repo conventions, branch strategy, notebook style | Week 1 |

---

## Answered

Move rows here as answers come in, with the date and who gave them.

| Question | Answer | Who | Date |
|---|---|---|---|
| | | | |
