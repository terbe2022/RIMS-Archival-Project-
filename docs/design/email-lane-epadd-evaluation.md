# Email lane — build on POC 1, or adopt ePADD?

**Assessment of `emails_parsed_cleaned_PII_Extracted_v3`, 12 August 2026**
Corpus: Michael Brewer / Abbott Power Plant, 738 `.eml` files → 1,650 message rows.
Stack: Presidio (analyzer + anonymizer), Ollama/Llama, pandas, NLTK, scikit-learn.

---

## The recommendation

**Keep your own lane. Do not adopt ePADD as the processing engine.** Take one specific idea
from it, and revisit it only as a *delivery* interface if Library IT ever clears it.

That is not a close call, and it is not mainly about the Java runtime problem. It is because
**ePADD and your pipeline solve different problems**, and the problem ePADD solves is not the
one the Archives described in answer 1.2.

There is one real weakness in what you built, and it is fixable in about a day. Detail below.

---

## What the POC actually does, measured

I ran the numbers rather than taking the notebook's word for it.

| | Result |
|---|---|
| Source files | 738 `.eml` |
| Message rows produced | 1,650 |
| Thread decomposition | **Works** — quoted reply chains split into separate messages with their own headers |
| Header extraction on quoted messages | From/Sent/To/Subject recovered from the reply block, not just the envelope |
| Text extraction failures | 31 rows (2%) |
| PII entity types | Names, phones, emails, dates, SSN |
| Summaries generated | 1,598 / 1,600 (99.9%) |
| Mean summary length | 359 characters |

### The thread decomposition is the strongest thing here

738 files became 1,650 messages. One OSHA thread yields 10 rows; a hiring thread yields 11 —
each with its own sender, timestamp and subject, pulled out of the quoted `From:/Sent:/To:`
block rather than the file envelope.

That matters more than it sounds. In a real accession, a forwarded chain is often the **only**
surviving copy of the messages inside it. If you index at file level, those intermediate
messages are invisible to search — they exist only as quoted text buried in one document.
Decomposing them makes each individually findable and individually appraisable.

**ePADD does not do this.** It ingests mailboxes as messages and treats a forwarded chain as one
message. Your approach recovers roughly 2.2× more addressable units from the same corpus.

Against answer 3.2 — where Joanne named **correspondence as the single highest-value category**
in personal papers — that is not a marginal technical advantage. It is directly the thing she
said she cares most about.

### The summaries are usable but not clean

Sampled output is legible and appropriately cautious:

> A document management plan is nearing completion and will be ready for review upon the
> writer's return. The plan outlines a formal procedure for updating others on their location…

Two defects:

**13% carry model preamble** — "Here is the rewritten summary:", "Summary:" — leaking into
stored output. 215 of 1,598 rows. Cosmetic, trivially fixed with a strip-and-validate pass, but
it should never have reached a saved artefact.

**Some summaries are so abstracted they carry no information.** "The decision has been made, and
all relevant parties are informed." That is a summary of nothing. It happens because the
summariser runs on `cleaned_text` — the *masked* version — so the model is summarising a
document with the names already removed and produces "a contact," "another individual," "a
designated point of contact."

**That is an ordering bug, and it is the most consequential finding in this review.** You are
paying the full cost of running a model and getting a degraded result, because you masked before
you summarised. Summarise the original, then mask the summary. Same cost, materially better
output.

---

## The serious problem: the PII map is not a map

This is the one that has to be fixed before this touches a real accession.

`names` currently holds, per row:

```
{'<PERSON1>': 'Beth', '<PERSON2>': 'Mike', '<PERSON3>': 'Joanne Kaczmarek'}
```

Two things are wrong.

**1. It sits in the same file as the masked text.** The schema doc already flags this — the
placeholder-to-real-value dictionary stored beside the redacted content defeats the entire
purpose of redacting. Anyone with the CSV has both halves. This is exactly what `s04_pii_map_ref`
in schema v1.1 exists to prevent, and it is board item #43, still blocked on Brent.

**2. Placeholders are not stable across documents.** I checked:

| Real name | Placeholder assignments observed |
|---|---|
| Beth | `<PERSON1>` ×203, `<PERSON2>` ×29, `<PERSON3>` ×23, `<PERSON5>` ×21, `<PERSON4>` ×20 |
| Mike | `<PERSON2>` ×115, `<PERSON3>` ×97, `<PERSON4>` ×65, `<PERSON7>` ×34 … |

Numbering restarts per document, so `<PERSON1>` means a different person in every row.

The consequence: **a researcher cannot follow a person through the redacted corpus.** In an
archive, the network — who corresponded with whom, over what period — is frequently the research
object itself. Per-document numbering destroys it while still storing every real name in the
next column.

You want a corpus-stable pseudonym: the same person gets the same token everywhere, the mapping
lives in an access-controlled store, and the redacted text becomes genuinely useful rather than
merely censored. That is a strictly better outcome on both axes — safer *and* more useful.

**Fix cost:** roughly a day. Entity resolution across the corpus, assign stable IDs, write the
map to a separate store. It has to happen regardless of the ePADD decision.

### Related: entity resolution isn't happening

"Mike" (456), "Mike Brewer" (198) and "Michael K" (147) are counted as three people. They are
almost certainly one. Same for "Kelly" and "Kelly Kathrens."

Not a defect of the extraction — Presidio found the spans correctly — but nothing downstream
reconciles them. Correspondent-level analysis needs this, and stable pseudonyms need it too,
since you cannot assign a stable ID to a person you cannot identify consistently.

---

## Where ePADD genuinely beats this

Fair accounting. Three things:

**Correspondent analysis and sorting.** ePADD's central feature — group by correspondent, sort
by volume, browse a person's whole exchange. Yours has the raw material for this and does not
build it.

**Lexicon-based sensitivity screening.** ePADD ships curated term lists for archival sensitivity
review, developed by archivists over years. Yours has Presidio, which finds PII entities but does
not know what *archival sensitivity* means. Answer 3.3 names categories — HR matters, discipline
records, FMLA — that a PII scanner will not catch, because "the discipline hearing for the
groundskeeper" contains no SSN.

**It is a known quantity in the profession.** Bethany and Joanne can talk to peers who use it.
That is worth something real when a system has to be trusted by people who did not build it.

---

## Where it does not, and why that decides it

**ePADD requires a mailbox.** MBOX, IMAP, or a `.pst` it can convert. Answer 1.7 says accessions
arrive as `.pst` **and** `.eml` — and loose `.eml` files scattered through a personal drive are
the harder, more common case. That is what your parser was built for and what ePADD is worst at.

**ePADD is a separate application, not a component.** It is a desktop tool with its own store and
its own workflow. It cannot be a stage in a pipeline. Adopting it means email leaves your
pipeline at Stage 03 and comes back — or doesn't — with its own metadata model that then needs
crosswalking into your manifest.

**Answer 1.7 is decisive on this point.** Email arrives *inside* personal-papers accessions,
mixed with `.doc`, `.pdf`, `.xls` and everything else. It is not a separate corpus. Routing it to
a different application means the appraisal decision for a researcher's correspondence gets made
in a different system, with different criteria, from the appraisal decision for their papers —
when answer 3.2 says the correspondence is valuable *precisely because* it references the
research in those papers. Splitting them severs the connection that makes both worth keeping.

**And the Java runtime problem is real.** Library IT has open concerns and has not responded.
Even in the best case that is an unresolved dependency on someone else's security posture.

---

## What I would actually do

**Build on POC 1.** It handles the harder input format, it decomposes threads in a way ePADD
does not, and it stays inside the pipeline where the appraisal decision belongs.

**Steal one idea: the sensitivity lexicon.** ePADD is open source. Its term lists encode archival
judgement you would otherwise have to develop from scratch, and they map onto exactly the
categories Joanne named in answer 3.3. Read them, adapt them, credit them. That is the part
worth borrowing and it needs no installation, no Java, and no IT approval.

**Keep ePADD alive as a possible delivery interface only.** If Library IT clears it, and if
Joanne goes ahead with a reading-room workstation for email access (her email raises this), ePADD
could be the reading interface while your pipeline remains the processing engine. That is a
Stage 06 question, not a Stage 03 one, and it can be decided much later.

### Fix list before this runs on a real accession

| | Fix | Effort | Why |
|---|---|---|---|
| 1 | **Move the PII map out of the artefact** into an access-controlled store | Blocked on #43 | Currently the mask and the key ship together |
| 2 | **Corpus-stable pseudonyms** — same person, same token, everywhere | ~1 day | Makes redacted text usable; enables correspondent analysis |
| 3 | **Summarise before masking**, not after | ~1 hour | Removes the "a contact told another individual" failure mode |
| 4 | Strip model preamble, validate before storing | ~1 hour | 13% of stored summaries are contaminated |
| 5 | Entity resolution — Mike / Mike Brewer / Michael K | ~1 day | Prerequisite for 2 |
| 6 | Sensitivity lexicon beyond PII, from answer 3.3 categories | ~2 days | Presidio finds SSNs, not personnel matters |
| 7 | Correspondent-level views | ~2 days | The one ePADD feature genuinely worth matching |
| 8 | Investigate the 31 extraction failures (2%) | ~2 hours | Small, but find out whether it's a format class |

Items 3 and 4 are same-day. Items 1 and 2 are the ones that matter, and 1 is not blocked on
engineering — it is blocked on Brent.

### The honest framing for #63

The decision is being made on **architectural fit**, not on capability, and the write-up should
say so. ePADD is a good tool aimed at a workflow the Archives does not have: a curated mailbox
handed over as a unit. What the Archives actually has, per answer 1.2, is 49 mixed accessions on
a network drive with email scattered through them. That is your pipeline's case, not ePADD's.

The Java runtime issue is a real constraint and worth recording, but it should be the second
reason listed, not the first. If it were the first, the decision would look like it went our way
by luck.
