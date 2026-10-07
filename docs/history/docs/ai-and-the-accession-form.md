> Historical source preserved during the October 7, 2026 documentation reconciliation. Descriptions, schedules and approvals below are dated evidence, not current operating instructions. See the [current documentation map](../../README.md).

# Where AI is used, and how the accession form drives it

Design note, 5 September 2026.

The accession form is the only thing in this system that carries an archivist's
judgement about a specific collection. Everything else is generic. So the design
question is not *whether* the form reaches the models — it is **which fields
reach which stage, and in which direction**, because getting that wrong produces
results that look excellent and mean nothing.

---

## The trap, first

There are two completely different ways to use the form, and they must not touch
the same field.

**As context.** Put collection background into the prompt so the model
understands what it is looking at. An unlabelled diagram in a chemical
engineering research computer is a flow schematic; the same image with no
context is "a line drawing."

**As criteria.** Compare what came out against what the archivist said matters,
to decide rank.

If a field is used for both, the system marks its own homework. Tell a model
"this collection values referee reports and correspondence about drafts," and it
will describe an ambiguous document in those terms; then score that description
against the same sentence and it scores highly — because the prompt put the
words there, not because the document is a referee report. The score measures
the prompt.

**The rule that prevents it:**

| Form field | Prompt context | Scoring criteria |
|---|:--:|:--:|
| `source`, `owner`, `role`, `scope`, `research`, `bio` | **yes** | no |
| `valuable`, `exclude` | **never** | **yes** |
| `access` | yes, for sensitivity only | no — raises rank, never lowers |
| `notes`, `process_classes` | operational | no |

Descriptive fields say *what world this is*. Appraisal fields say *what we
value*. The model may know the first and must not know the second.

---

## Every place a model is used

### 1. Image description and sensitivity — `vision.py`
**Model:** LLaVA-1.5-7B on vLLM. **Status:** adapter built; production run never
executed (15 of 12,125 images done).

Produces title, description, an `offensive` boolean, one of nine categories, a
reason and a confidence.

**Form usage today:** none. The prompt is collection-agnostic.

**What should change:** prepend `scope`, `role` and `research` as a context
block. The current prompt already carries the hardest part — that an image
*containing* sensitive content differs from an image whose *subject* is a
difficult historical topic. Collection context makes descriptions specific
rather than generic: "Memorial Stadium under construction, 1923" instead of "a
stadium is being built."

For ACC-2026-020 this is exactly why the form is `draft`. Nobody has said what
those images are, so there is no context to prepend, and the descriptions will
be generic. That is a fact to state when showing it, not a defect to hide.

**What must not change:** `valuable` and `exclude` stay out of this prompt.

### 2. Document and spreadsheet summarisation — POC 2, not yet ported
**Model:** Llama via Ollama. **Status:** exists in notebooks; extraction
replaced, summarisation not ported.

**Form usage today:** none.

**What should change:** same context block. A summariser told it is reading a
fluid-dynamics researcher's working files will keep the technical specifics that
a generic summariser discards as jargon.

**Defect to fix on the way in:** POC 2's pre-truncation keeps the 250 sentences
most *typical* of the document, measured by mean cosine similarity to all other
sentences. For appraisal that is backwards — the unusual paragraph in a routine
memo is the reason to keep it, and centrality selection is precisely what
discards it. Truncate by position and structure instead, or raise the limit.

### 3. Email summarisation — POC 1, not ported
**Status:** messages are now parsed and classified on CPU (`mail.py`), but
nothing summarises them.

**Form usage when built:** context block, plus `access` for the sensitivity
pass.

**Blocker:** POC 1's placeholder numbering restarts per document. `stage04.py`
fixes that with labels stable across the whole accession, so summarisation
should run on the pseudonymised text and never on the raw.

### 4. Relevance and importance ranking — `relevance.py`
**Model:** MiniLM embeddings, or lexical matching when unavailable.
**Status:** built and running. **This is the only place the form is used today.**

Splits `valuable`, `exclude` and `access` into individual clauses, scores each
file against every clause, and quotes the winning clause as the reason.

### 5. Personal information detection — `redaction.py` + `stage04.py`
**Model:** deterministic regex, plus spaCy or Presidio for names (neither
installed).

**Form usage:** `access` should select which entity types are in scope.
ACC-2026-022's access field names quasi-identifiers explicitly and asks for
open-web release to strip them; ACC-2026-021's asks for referee reports to be
routed rather than redacted. Those are different jobs and the form already
distinguishes them.

### 6. Semantic sensitivity scoring — POC 3 Method 1, deliberately excluded
Embeds descriptions and flags on similarity to taxonomy keywords. The taxonomy
mixes `blackface` and `swastika` with `costume`, `body`, `war` and
`application`. Every photograph of people in costume matches racialized
performance. Not a threshold problem.

---

## How importance is actually decided

Not one score. Four signals with different trust levels, resolved by
precedence rather than addition:

```
  1. SENSITIVITY          rules, model flags, detected identifiers
     └─ always wins. Routes to restricted_review, never to discard.

  2. RULE MATCH           deterministic, from the confirmed ruleset
     └─ decides disposition. A model never writes s02_decision.

  3. CONTENT EVIDENCE     form clauses matched against extracted text
     └─ decides rank. This is the file understood on its own merits.

  4. PROXIMITY EVIDENCE   form clauses matched against path only
     └─ decides rank, flagged retained_by_association.
        Kept because of its neighbours, not because we understand it.
```

The separation between 3 and 4 is the piece the competitive review says nobody
else has. It is also why extraction mattered: before it, nearly everything in a
folder ranked on proximity alone.

**A model's output enters at level 3, never above it.** A description is
evidence about a file, weighed like extracted text. It cannot dispose of
anything.

---

## Two things this needs that do not exist yet

### Form versioning
Every model output must record which version of the form produced it — a hash of
the form file in `s04_prompt_version`, alongside the prompt version.

The intended correction path is "edit the form and re-run." That only works if
you can tell what is stale. When Joanne fills in ACC-2026-020's `scope`, every
description generated without it needs regenerating, and every score needs
recomputing. Without a form hash on each row, the only safe answer is to redo
everything.

### A cost gate that cannot silently skip
Description is the expensive step. At 12,125 images and 55.4 img/min that is 3.7
hours, which is affordable. At 150,000 mixed files it is not.

The gate: rank cheaply on CPU first, describe the top bands with the model,
**and describe a random sample of the bottom band as well** — because the only
way to know the cheap ranking is not systematically missing something is to
measure what it discarded. Skipping the bottom band entirely makes the cheap
score unfalsifiable.

---

## What to say about it

The form is a contract. The archivist writes what the collection is and what
matters in it; the pipeline uses the first half to understand and the second
half to rank, and never mixes them. Disagreeing with a result means editing the
form and re-running, not overruling the machine one file at a time.

That is also the honest answer to "how accurate is it." The system does not
claim to know what is valuable. It claims to apply the archivist's own stated
criteria consistently across a hundred and fifty thousand files, and to show its
reasoning on every one.
