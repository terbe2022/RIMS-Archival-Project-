> Historical source preserved during the October 7, 2026 documentation reconciliation. Descriptions, schedules and approvals below are dated evidence, not current operating instructions. See the [current documentation map](../../README.md).

> Recovered September validation source, transferred October 6, 2026. Original body preserved for provenance; read validation/PLAN.md and validation/RECOVERY.md for current review limits. Not evidence of completed experiments.

> Synthetic fixtures reproduce observed failure modes and are useful for screening. Passing them does not guarantee real-corpus performance. Historical model/licence and speed claims require verification before selection. No named model is newly recommended here.

# Model validation — brief

**Owner:** Gauri Bhasin
**Purpose:** establish which open-weight model should generate metadata for the
archival pipeline, with evidence rather than preference.

---

## Why this is worth doing

The pipeline generates a title, description and subject terms for every file it
can read, and ranks everything against the archivist's own appraisal criteria.
All of that rests on a model nobody has measured. Every claim the project makes
about description quality is currently an assumption.

This work turns that into a number. It is also the thing that makes the rest of
the project defensible: the first question a governance reviewer asks is "how do
you know it works", and at the moment the honest answer is that we don't.

---

## The rule that shapes everything

**No real accession content goes into Google Colab.**

Colab runs on Google's infrastructure. The corpus contains personal email,
unreviewed identifiers, medical and tax records, and FERPA-covered student
records. Local open-weight models on university hardware is not a preference —
it is the reason the architecture exists, and it is what was promised to the
Archives and to the Privacy Office.

So the notebook uses a **synthetic corpus** that reproduces the real one's
failure modes without its content. Mangled Latin-1 encodings, extensions that
are not formats, 1993 campus BSMTP mail that crashed the real parser,
extractions that returned only a quoted reply chain, OCR mush, blank pages, and
a ZIP+4 postal code that must not be read as a social security number. The
names and subjects are invented; every shape is a defect that actually
occurred.

A model that handles those will handle the real thing. The confirming run
against real material happens on the server, at the end, on one or two
candidates.

---

## What to establish

Four questions, none of which needs labelled data. That is the point — you can
start immediately rather than waiting on archivists.

### 1. Does it hold a schema?
Parseable JSON with the required keys, every call, unattended. Below about 95%
needs constrained decoding or a repair pass. Usually fixable and not a verdict
on the model, but it has to be known.

### 2. Does it know when it cannot answer?
**The one that matters most.** Given a blank page, a truncated extraction or a
quoted reply chain, does it decline or invent? A model that describes an empty
file as "a letter regarding administrative matters" fails invisibly: the output
looks like description, reaches the manifest, and ends up in a finding aid a
researcher trusts.

Measured by degrading real inputs, so the correct answer is known without
anyone labelling anything.

### 3. Is it consistent?
Same input, same answer, at greedy decoding. Two different answers is a serious
finding — a model that contradicts itself cannot be audited, and auditability
is the property this project is selling.

### 4. What does it cost?
Seconds per file, and hours for 150,000 — the whole personal-papers backlog.
Remember that a slow result may be a serving problem: this project measured
6.22× from moving Ollama to vLLM on identical hardware.

### Then, and only then: is the description any good?
Needs a person. The four measures above narrow eight candidates to two or
three first, so grading time is spent well. Use
`docs/description-grading-rubric.md`, grade blind, score the four dimensions
separately and never average them.

---

## What you have

| | |
|---|---|
| `notebooks/colab-model-evaluation.ipynb` | Run this. Colab, free tier, T4 |
| `src/workbench/fixtures.py` | The synthetic corpus, ~54 files |
| `src/workbench/evaluate.py` | The harness and the scoring |
| `docs/description-grading-rubric.md` | For the human grading pass |
| `src/workbench/context.py` | How the intake form conditions the prompt |
| `src/workbench/relevance.py` | How ranking works, if you want the whole picture |

Candidates worth comparing, all runnable on a free T4 at 4-bit:

- `Qwen/Qwen2.5-7B-Instruct` — Apache 2.0
- `meta-llama/Llama-3.1-8B-Instruct` — Llama licence, has use restrictions
- `mistralai/Mistral-7B-Instruct-v0.3` — Apache 2.0
- `microsoft/Phi-3.5-mini-instruct` — MIT, 3.8B, is smaller enough?

Note the licences in your write-up. For a university deployment, a model with
use restrictions is a different proposition from one without, and that belongs
in the recommendation rather than a footnote.

---

## What to hand back

One page:

1. The comparison table, unedited.
2. Every disqualifying finding, **quoting the actual output**. An invented name,
   a fabricated date, a confident description of a blank page. One clear
   instance is enough — you do not need a rate to report a kind of failure.
3. A recommendation, a runner-up, and the condition that would change your mind.
4. Licence notes.
5. What you could not measure. Whether descriptions are *useful to an
   archivist* is a different question from whether they are correct, and it
   needs an archivist. Say so rather than letting the numbers imply it.
6. Your sample: how many cases, of what kinds. A result without its sample is
   not reproducible.

---

## Things that would be easy to get wrong

**Improving the prompt mid-run.** You are measuring models. Change the prompt
and the model at once and you learn nothing about either. Get a baseline first;
then changing one thing at a time is exactly the right next experiment.

**Averaging the rubric dimensions.** A description can be accurate and useless,
or fluent and wrong. A single score hides precisely the failure you are looking
for.

**Treating a high score as a verdict.** These are 54 synthetic files. They are
built from real defects, but they are not the corpus. The result narrows the
field; it does not settle it.

**Rewarding the wrong behaviour.** I made this mistake writing the harness: I
was counting "required keys present" across all cases, which penalised a model
for correctly declining a blank page — declining means no title. That metric
would have selected *for* the overconfident model. Watch for it in anything you
add.

---

## Experiments worth doing if there is time

**Does the intake form actually help?** The pipeline prefixes a collection
context block to every prompt — source, owner, role, scope, research area.
Nobody has tested whether it improves description quality. Same files, same
model, with and without. This is a load-bearing assumption in the whole design
and it is unverified. Arguably the highest-value thing in this document.

**Is a small model enough for triage?** Triage is a coarse decision. If
Phi-3.5-mini at 3.8B is adequate for the volume tier even though it is weaker
at description, the cost model changes substantially.

**Where does quantisation start to hurt?** 4-bit against 8-bit, same model,
same cases. The expectation is that JSON adherence degrades before prose does.
Worth confirming, because here JSON adherence is what matters.
