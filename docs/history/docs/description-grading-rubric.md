> Historical source preserved during the October 7, 2026 documentation reconciliation. Descriptions, schedules and approvals below are dated evidence, not current operating instructions. See the [current documentation map](../../README.md).

> Recovered September validation source, transferred October 6, 2026. Original body preserved for provenance; read validation/PLAN.md and validation/RECOVERY.md for current review limits. Not evidence of completed experiments.

> The original rejection thresholds conflict (any accuracy zero versus more than one in fifty). Agree thresholds before use; observed failures are not population rates or intrinsic model properties independent of configuration.

# Grading rubric — generated descriptions

For scoring the descriptions a model writes, when comparing candidate models.

Grade **blind**. The sheet gives each candidate a tag rather than a model name,
because knowing which model wrote a description changes how it reads. The
mapping is kept separately and rejoined after the grades are in.

---

## Four dimensions, graded separately

Never collapse them into one score. A description can be accurate and useless,
or fluent and wrong, and averaging hides exactly the failure you are looking
for.

### 1. Accuracy — is it true of this file?

| | |
|---|---|
| **3** | Everything stated is supported by the text. No invented names, dates, organisations or events. |
| **2** | Substantially true, with one detail that overreaches — a date inferred, a role assumed. |
| **1** | Contains a claim the text does not support. |
| **0** | Describes a document that does not exist. Names a person, place or event not present. |

A 0 on accuracy disqualifies the model for this corpus regardless of every
other score. Invented metadata in a finding aid is worse than no finding aid,
because a researcher trusts it.

### 2. Genre — does it say what KIND of thing this is?

| | |
|---|---|
| **3** | Names the form: a referee report, a draft with revisions, list traffic, a signed agreement, minutes. |
| **2** | Implies the form without naming it. |
| **1** | Subject only, no sense of form. |
| **0** | Wrong form — calls a draft a publication, a bounce a letter. |

This carries unusual weight here. An archivist appraising a collection needs to
know what a thing *is* at least as much as what it is about, because form is
what distinguishes a record from a copy.

### 3. Specificity — could you find this file again from the description?

| | |
|---|---|
| **3** | Distinguishes this file from its neighbours. Names the actual subject. |
| **2** | Accurate but generic; would match twenty files in the same folder. |
| **1** | So general it carries no information — "a document about university matters". |
| **0** | Empty of content. |

Test: read the description, then try to pick the file out of its folder. A 1 is
the most common failure and the least visible, because it reads like a
description.

### 4. Restraint — does it stay inside what it knows?

| | |
|---|---|
| **3** | Says plainly what is unclear. Marks uncertainty where it exists. |
| **2** | Neutral; neither hedges nor overreaches. |
| **1** | States inferences as fact. |
| **0** | Confident about something unknowable — assigns a date, an author or a purpose with no evidence. |

---

## Scoring the set

Report each dimension's **median and range**, not a total. Then three counts
that matter more than any average:

- **Accuracy zeros.** Any model with more than one in fifty is not a candidate.
- **Specificity ones.** How much output is fluent and empty.
- **Restraint zeros.** Confident invention, which is the failure that reaches
  the manifest looking like description.

## Disqualifying findings

Stop and record rather than continuing, if a model:

- invents a person's name that does not appear in the text
- assigns a date the document does not carry
- describes a blank or unreadable input as though it had content
- returns different content for the same input at temperature 0

Each of these is a property of the model, not of a sample. One clear instance
is enough to report; you do not need a rate.

## Sample size

Fifty files gets you a usable comparison between two or three models. Twenty
tells you which are obviously unusable, which is often the whole question.

Stratify rather than taking the first fifty: documents, email and images in
roughly the proportion the corpus has them, plus a handful that the pipeline
scored as unreadable. A model's behaviour on the material it handles badly is
the thing an aggregate score hides.

## What this rubric cannot tell you

Whether the description is *useful to an archivist*. That needs an archivist,
and it is a different exercise from this one. This measures whether the model
describes files correctly; it does not measure whether correct descriptions
help someone appraise a collection. Keep the two questions apart.
