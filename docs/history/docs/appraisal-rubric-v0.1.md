> Historical source preserved during the October 7, 2026 documentation reconciliation. Descriptions, schedules and approvals below are dated evidence, not current operating instructions. See the [current documentation map](../../README.md).

# Appraisal rubric — v0.1 draft

For a reviewer deciding, file by file, what an archives should keep.

**This rubric is a draft and has never been ratified by the University
Archives.** It is written from the intake forms and the appraisal language in
them. Where it disagrees with an archivist, the archivist is right and the
rubric is the thing that changes.

---

## The four outcomes

Use exactly these. They are the manifest vocabulary and they mean different
things.

| Outcome | Meaning |
|---|---|
| `selected` | Keep. Matches something the accession form says is worth keeping. |
| `not_selected` | No criterion matched. **Not a decision to destroy** — retained through the review window. |
| `restricted_review` | A person more senior must look. Sensitivity, not value. |
| `discard_candidate` | Proposed for disposal after the retention window. Use sparingly. |

Never use `delete`, `keep` or `archive`. Those collapse distinctions this
vocabulary exists to preserve.

---

## Order of operations

Apply these in order and stop at the first that fires. This is precedence, not
scoring — do not average them.

### 1. Sensitivity — always wins
If the file contains, or plausibly contains, any of:

- personal identifiers (SSN, financial account, medical information)
- student records or anything FERPA-adjacent
- personnel or HR matters, including evaluative judgements about named people
- referee reports or peer review naming living people
- material under a confidentiality obligation (consulting, contracts)
- content warranting a note at publication — offensive historical language or
  imagery **in the material being described**

→ `restricted_review`. Regardless of how valuable or worthless it is.

Note carefully: a photograph *of* a difficult historical subject is not
sensitive because of its subject. It is flagged so a person can write a content
note. Flagging is a description task, never a reason to discard.

### 2. Structural exclusion
Exact duplicates, system files, application working files, zero-byte files,
cache and temp paths, blank scanner separator sheets.

→ `discard_candidate`.

### 3. Match against the accession form
Read the form's `valuable` field. If the file's title, summary or folder
matches any criterion in it → `selected`, and **name the criterion you matched**.

Read the form's `exclude` field. If it matches → `discard_candidate`, and name
the criterion.

### 4. Folder context
If the file itself is unidentifiable but **60% or more** of its folder is
`selected`, mark it `selected` and set `by_association: true`.

This is the distinction that matters most in the whole rubric. A file kept
because we understand it and a file kept because of its neighbours are
different claims, and a reviewer later must be able to tell them apart.

### 5. Nothing matched
→ `not_selected`. This means "no criterion had an opinion", not "worthless".

---

## What counts as valuable, in general

When the form is thin, these hold across academic collections:

**Keep** evidence of *how* work was done, not only its results — drafts with
revisions, correspondence with collaborators, referee reports, meeting records,
grant administration. Keep material that exists nowhere else. Keep the first and
last item of a sequence, which usually carries identifying information. Keep
anything carrying text that identifies what it is: a label, a caption card, a
date board, an accession number.

**Do not keep** published work by other authors held as reference copies with no
annotation. Duplicate downloads. Software installers. Automated mail — bounces,
auto-replies, subscription confirmations. Personal material unrelated to the
professional record, which should be offered back rather than accessioned.

---

## Calibration

Two rules that resolve most hard cases.

**Asymmetry.** Wrongly discarding a unique record is unrecoverable. Wrongly
keeping a worthless one costs storage. When genuinely torn, keep — and say you
were torn in `confidence`.

**Abstention is a valid answer.** If the metadata does not support a decision,
say so: `not_selected` with `confidence: "low"` and a reason naming what you
would need. A confident decision on evidence that does not support one is worse
than no decision, because it looks reliable.

---

## Output

One JSON object per file, in a JSON array. Nothing else — no prose, no fences.

```json
{
  "file_uid": "copy exactly from the input",
  "decision": "selected | not_selected | restricted_review | discard_candidate",
  "by_association": false,
  "criterion": "the sentence from the accession form you matched, or null",
  "reason": "one sentence, in your own words, that an archivist could disagree with",
  "confidence": "high | medium | low",
  "sensitivity": null
}
```

`sensitivity` is a short label when and only when the decision is
`restricted_review` — for example "referee report naming a living person",
"consulting material under possible confidentiality", "content note at
publication".

Do not invent `criterion`. If you did not match a specific sentence in the
form, set it to null and explain in `reason`.
