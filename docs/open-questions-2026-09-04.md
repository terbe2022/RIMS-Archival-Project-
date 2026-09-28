# RIMS Archival Triage Tool — open questions

Compiled 4 September 2026, from the prototype build. Nothing here blocks
further building; everything here blocks *trusting the output*. Grouped by who
can answer it.

Each item states what we did in the absence of an answer, so that a wrong
assumption is visible rather than buried.

---

## 1. Blocking a run right now

### Q1. Record series numbers for ACC-2026-020 and ACC-2026-021
**Who:** an accessioning archivist (Bethany Anderson / Joanne Kaczmarek)
**Blocks:** both accessions entirely — not appraisal, the crawl itself.

`file_uid` derives from `accession_uid`, which derives from a 6–7 digit record
series number. The pipeline refuses to invent one; `parse_record_series()`
raises rather than guessing, on the reasoning that these are assigned by a
person and checked against the published classification list.

ACC-2026-022 already runs, because `2620191` was recoverable from the Box
prefix `2620191_MichaelHart`. The other two have nothing.

**One number unblocks ACC-2026-021**, which is the accession that exercises
most of the build: the proximity case, the 38 extensionless OLE2 files, and the
drafts rule.

### Q2. What are the ACC-2026-020 images, and whose collection are they?
**Who:** the Archives
**Blocks:** appraisal of 020 (description can proceed without it).

One sentence is enough. Also useful: where the TIFF masters are held, and which
programme or vendor produced the scans.

020 is deliberately `status: draft` and stays that way. Running it produces
rankings that look confident and mean nothing, because the model would score
against a generic appraisal rather than this collection's priorities. The
pipeline enforces this: stage 01 characterises the files, stage 02a refuses to
appraise and records why on every row.

---

## 2. Appraisal policy — rules drafted, never confirmed

The rulesets are `POLICY_VERSION 0.1-draft`, written 13 Aug 2026 from answers
3.2 and 3.3. **They have never been confirmed by the Archives.** Everything
below is a question about what the rules should say, not about whether the code
works.

`schema.rules.to_markdown()` prints any ruleset in plain language for exactly
this conversation.

### Q3. Personal finance — route to review, or set aside?
**Who:** Joanne Kaczmarek

Answer 3.3 listed personal financial material under normally disposable. The
draft routes it to `restricted_review` instead, on the reasoning that
discarding unread financial records is not recoverable and over-routing to
review is.

**Live case, first real run.** Two files of 901 in ACC-2026-022 matched
`pp.sensitive.personal_finance`. Both matched on the word "mortgage" appearing
in the file *path*. One sits in `messages/correspondence/`, one in
`messages/listserv/` — public mailing list traffic.

Two distinct questions fall out:

- Is routing personal finance to a supervising archivist the behaviour you
  want, rather than setting it aside?
- The filenames in this accession are generated from mail subject lines. A rule
  matching on path therefore matches on whatever a correspondent — or a
  spammer posting to a public list — happened to write in a subject. Should
  sensitivity rules apply to email at all before the message body has been
  extracted and read?

### Q4. HR and personnel — the same shape of question
**Who:** Joanne Kaczmarek

Answer 3.3 listed HR and personnel material as routinely disposable while
noting in the same sentence that it is sensitive. The draft treats those as two
outcomes and routes personnel matters to review even when a disposal rule also
matches. This is the single most important safety property in the ruleset and
it is a deliberate departure from what was said. It should be confirmed or
overruled explicitly.

### Q5. Accession type for ACC-2026-021 and ACC-2026-022
**Who:** the Archives

Both are currently set to `personal_papers`, which is our proposal, not their
answer. It selects which of two rulesets applies, so it changes outcomes.

021 (Hanratty, a faculty office computer) is well evidenced. 022 is harder:
the form argues the Hart mail is operational rather than institutional, but the
same folder holds 1994 university administrative correspondence. **A single
accession type is wrong for part of that material**, which is an argument for
splitting the accession rather than for picking a type.

### Q6. Professional field for Hanratty
**Who:** the Archives

Set to `chemical engineering`, from the intake form and the directory tree.

This is load-bearing: the drafts rule keeps working drafts for a humanities
scholar and does not for a chemist. Same files, opposite outcome. It should be
confirmed rather than inferred.

### Q7. Retention window for unselected material — D12
**Who:** Joanne Kaczmarek / Brent West

Schema defaults to 180 days, marked provisional. No period has been named.

---

## 3. What the exclusion percentage can and cannot be measured on

### Q8. Access to material upstream of the sampler
**Who:** whoever holds the pre-sample corpus; ultimately D6

**Issue #15 cannot be answered from `data/sample_1k`.** Measured today:
**0.0% of 901 files** in ACC-2026-022 landed in layer 0.

That is correct and it is not a result about the architecture. `sample_1k` is
the *output* of an exclusion pass — the sampling script already removed the
duplicates and system files that issue #15 defines as free exclusions. Running
an exclusion pass over it finds nothing left to exclude.

The sampler's own record is the best evidence available today, and it is a real
measurement on real material:

| | |
|---|---:|
| Loose files considered, emails group | 672 |
| Excluded before `sample_1k` existed | **573 (85.3%)** |
| — of which duplicate-driven | 561 (83.5%) |
| — mail containers, extracted separately | 7 |
| — system files | 5 |

That is *higher* than the 40–70% working guess in issue #15, but it is not the
number the issue asks for and the difference must be stated. Getting the real
figure needs stage 01/02a pointed at material that has not already been
filtered.

### Q9. Issue #15 is closed as completed
**Who:** repo owner

State is `CLOSED / COMPLETED`, zero comments, and the checkbox reading
"Reduction percentage measured and posted here — this number is the argument
for the architecture" is unchecked. The number was never posted.

Anyone reading the handoff, going to the board and finding #15 closed will
reasonably conclude the work is done. It needs reopening or a successor issue,
so the measurement has somewhere to land.

---

## 4. Environment and infrastructure

### Q10. Siegfried is not installed
**Impact:** 817 of 901 files in the first run were typed `s01_id_method: none`.

Format identification fell back to our internal magic-byte table, which has no
signature for `.eml` — mail is plain text and has no magic bytes. So 800 files
routed on extension alone, which is precisely what stage 01 exists to avoid,
and the Siegfried/Tika disagreement triage signal is unavailable for 90% of the
accession.

Siegfried is a single Go binary and needs no sudo. It matters more for
ACC-2026-021, where 38 extensionless files are the whole point.

### Q11. pandas / pyarrow teardown crash
`read_parquet` followed by `.to_string()` produced `Aborted (core dumped)` and
`terminate called without an active exception` — a C++ abort at interpreter
shutdown, after the query succeeded and printed. The data is fine; the two
libraries disagree about destruction order.

Both should be pinned together in the pipeline's conda env. A crash that
appears on only some access paths will resurface when the review UI reads the
same file.

### Q12. Where does the NSRL known-file set come from?
Issue #15 lists NSRL as a free exclusion. It is not wired up: the RDS is a
multi-gigabyte download and `huggingface.co` and `api.box.com` are blocked from
`urbadvanalytics1`.

The pipeline reports `s02_nsrl_hit: None`, meaning *not checked*, rather than
`False`, which would claim we looked. NSRL is plausibly a large share of the
reduction on a tree like Hanratty's, so the current percentage is a floor.

### Q13. `.mdb` extraction needs `mdbtools`, which needs sudo
The Ethiopian land-tenure databases in ACC-2026-022 have no extractor. Pure
Python has no viable path for Access files. `.mov` and video are also
unhandled; both were on POC 2's never-implemented list.

---

## 5. GPU, and D15

### Q14. The ask is not "when does your run finish"
**Who:** the legislation pipeline team

Observed 4 Sep: `vllm serve` (PID 958792) had been alive 3:10:10 while
`run_daily_with_vllm_check.sh` (PID 960346) had been alive 2:52:06. **The
server is eighteen minutes older than the script said to have launched it**, so
the script found an existing server rather than starting one.

`vllm serve` is a persistent process that outlives any individual pipeline run.
Waiting for the run to complete will not free the card. The ask is either:

- stop the server when the day's runs are done, or
- lower `--gpu-memory-utilization` to leave headroom.

The second is the better ask. An 8B AWQ model does not need 21.33 GiB; vLLM
reserves whatever it is given. That argument is unaffected by the confirmation
that the card is doing real work rather than idling.

### Q15. Any unload must be a trap, not a final line
Today's 04:00 cron run went 04:00:32 → 09:21:30 and **failed at the embedder**.
Failing is currently the normal outcome, so an unload written as the script's
last statement would not fire. It needs to be on the failure path too.

Also relevant: the embedder failed *after* the GPU came back, so it is a
separate fault from memory pressure, and the card may free briefly and at no
predictable hour. The vision stage should therefore be resumable — checkpoint
per batch, survive losing the card mid-run — rather than a single long job.
POC 1's resume-from-checkpoint pattern is the thing to reuse.

---

## 6. Governance

### Q16. What goes in the public repo
**Recommendation: code yes, data never — including redacted data.**

The repo's own conventions already say no data files, PII or credentials. Three
things make it firm rather than cautious:

- The material includes unreviewed PII, medical and tax records.
- The ACC-2026-022 form states nothing from that accession should be published
  until provenance is established, and describes correspondents who wrote to a
  project rather than an archive with no expectation of publication.
- Presidio's measured recall is 0.69–0.81. Redaction is never a zero-leak
  guarantee.

The subtler trap: derived data is not safer than the source. A summary of an
email is still about a real person, and the demo set is specified to include
the messages where PII detection *fired*, chosen because the two release
versions visibly differ. That is a curated set of files known to contain
personal information.

Safe to commit: code, schema, rulesets, taxonomy, run reports carrying counts
and percentages but no paths or filenames, and synthetic fixtures.

**Also: the intake forms should not be committed.** They are not file content,
but 022 names Michael Hart and the Foundation's director, 021 names Hanratty
and his department, and both carry prose about living people and unresolved
permissions.

### Q17. Regulated data must not be pasted into hosted AI tools
This constraint applies to the project's own working practice, not only to the
pipeline. During this build a sensitivity flag fired on a file containing a
named living person's mortgage correspondence. Reading it in the terminal is
fine; pasting its contents into a hosted assistant to ask "is this a true
positive?" would breach the exact policy the local-model architecture exists to
honour.

Verdicts and filenames can be shared. Contents cannot.

### Q18. Still open from the repo's own decision log
- **D5** Where the PII mapping store lives, who reads it, encryption at rest
  [Brent West] — blocks stage 04 and freezing the schema
- **D6** Read access to the Archives network share [Joanne → Infrastructure]
- **D7** What Tracy Popp's preservation processing produces [Joanne → Tracy] —
  may *remove* work rather than add it; highest-value unanswered item
- **D9** Metadata standard for output
- **D11** Labelled sample, 50 files, two archivists independently — prerequisite
  for any scoring or sensitivity accuracy work
- **D13** How item-level description attaches to a folder-level finding aid

---

## 7. Smaller items, recorded so they are not rediscovered

| # | Item | Note |
|---|---|---|
| 1 | `rules.base.ext()` compares `row["extension"]` verbatim but normalises its own arguments | Convention is lowercase, no dot. A dotted value makes every extension rule match nothing, silently. Worth a schema-level assertion rather than a docstring. |
| 2 | `validate.py` does `from manifest import ...`; `test_rules.py` does `from schema.rules import ...` | Both assume the repo layout `src/schema/`. They do not import under `workbench.schema.*`. Fixing means diverging from the authoritative copy, so a `sys.path` shim is preferable to an edit. |
| 3 | `src/schema/delete.txt` | A 2-byte scratch file containing `x`, in the schema directory of a project whose first ground rule is "not keep/archive/delete". Upstream, so remove it there. |
| 4 | File count: crawl found 901 in `hart_correspondence`; sampling manifest accounts for 899 | Likely `_extraction_notes.txt` plus one sibling. That notes file records the 50% correspondence over-weighting and should be carried as provenance, not crawled as content. |
| 5 | §4 records `hanratty_computer` at 481 files; the sampling manifest records 483 copied | Settle with `find data/sample_1k/hanratty_computer -type f \| wc -l`. Matters because `file_uid` is accession-scoped, so a file under the wrong accession is keyed against the wrong intake form. |
| 6 | Near-duplicate detection is pairwise | Correct at 990 images, O(n²) at 12,125. Wants BK-tree bucketing — a data-structure change, not a threshold change. |
| 7 | The 17-vs-79-bit dhash separation has not been re-confirmed | Threshold 18 is taken from the handoff. Confirm against the known duplicate pair before trusting it. |
| 8 | The old review UI encodes `closed` as an access value | Removed in v1.1; the Archives uses two access levels. It also has no `restricted_review` state and no reviewer identity or decision log. Design reference, not a codebase. |

---

## 8. The one-line version

**Q1 is the only question standing between the prototype and its most
interesting run.** Everything else can be answered after the demo exists.
