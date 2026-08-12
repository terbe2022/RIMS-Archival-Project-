# Task — Evaluate Existing Software for the First-Pass Layer

> **Update, 12 Aug 2026 — add BitCurator, and drop two.**
> Answer 4.1: **BitCurator is already in use** at the Archives, administered by Tracy Popp. It
> bundles format identification and PII scanning, both of which we planned to build. Find out
> which components are actually running and what they emit **before** scoring anything else —
> this may remove work rather than add it.
> **DROID:** Joanne was unsure whether it runs. Ask Tracy, not Joanne.
> **Drop Preservica and Archivematica** from the evaluation — neither is licensed or run.
> Note also that the scale target dropped from millions of files to 100–10,000 per accession
> (answer 1.7), so the Tika failure-mode risk is much smaller than framed below — though still
> the most useful question on the list.
> See [`../docs/stakeholders/answers-2026-08.md`](../docs/stakeholders/answers-2026-08.md).


**Assigned to:** Gauri Bhasin
**From:** Tayler Erbe
**Target:** Week 2, recommendation by end of Week 3

---

## What I need from you

Before we build a first-pass layer that walks a drive and identifies what is on it, I want to
know how much of that we can get from software that already exists. Some of these tools are
open source and we can install them today. Some are commercial and would need a purchase or a
licence the University may or may not already hold. A few may already be running somewhere in
the Library and we simply don't know about it.

The deliverable is a recommendation: which tools we adopt, which we skip, and what is left
for us to build. Back it with the scoring below rather than an impression.

We are not trying to find one tool that does everything. We are trying to avoid rebuilding
things that already work.

---

## The shortlist, ranked

I've ranked these by how likely they are to be free, easy to stand up now, and immediately
useful for the first-pass layer. Work down the list in this order — the first four are where
I expect most of the value.

### Tier 1 — free, open source, install today, directly useful

**1. Siegfried**
Command-line format identification against the PRONOM registry. Fast — thousands of files a
second. JSON and CSV output. This is my expected primary tool for stage 01.
Licence: Apache 2.0. Install: single binary, no dependencies.

**2. Apache Tika**
Text and metadata extraction across roughly 1,400 formats behind one interface. Runs as a
server; you PUT a file and get text and metadata back. This is the tool that would let us
retire the Windows COM code in the file-search POC, which currently cannot run on Colab or on
our Linux server.
Licence: Apache 2.0. Install: single JAR, needs Java.

**3. ExifTool**
Embedded metadata for images, audio, video, PDF and Office. Native IPTC and XMP support,
which is exactly the standard we've been asked to target.
Licence: Perl Artistic / GPL. Install: single Perl script or package manager.

**4. DROID**
Same PRONOM signatures as Siegfried, with a GUI and built-in reporting. Slower and less
scriptable, but archivists know it by name and its reports are in a format they already read.
My expectation is we use Siegfried inside the pipeline and DROID when we need output a person
in the Archives will look at directly.
Licence: BSD. Free — confirm this in your evaluation, but I'm confident it is.

### Tier 2 — free, more setup, high value if they fit

**5. NSRL RDS hashsets**
NIST publishes hashes of known operating system and application files. A straight lookup
against our SHA-256 column discards system noise without opening anything. Not software so
much as a dataset, but it belongs in this evaluation because it could remove a large fraction
of a drive for free.
Cost: free download. The full set is large — check the size and whether the minimal set is
sufficient for our purpose.

**6. BitCurator**
Digital forensics toolkit built specifically for born-digital archival collections. Disk
imaging, metadata extraction, recovery of deleted files, PII scanning via bulk_extractor.
It is aimed at exactly our scenario — a drive arrives from a former employee and nobody knows
what is on it.
Licence: open source. Setup: distributed as a Linux environment or as installable packages;
check which is realistic for us.

**7. Docling**
Converts PDFs to structured markdown with layout, tables and reading order preserved. Far
cheaper than running a vision model over page images, which matters because a lot of what is
on these drives will be scanned documents.
Licence: MIT. Install: pip.

### Tier 3 — free but larger commitment, evaluate for fit not immediate adoption

**8. ePADD**
Stanford's email appraisal, processing and discovery tool. Directly overlaps the email work
we've already done. The real question is not whether it works but whether we adopt it as the
delivery interface for email and feed it, or keep our own lane.
Licence: open source (Apache 2.0).

**9. Archivematica**
Full OAIS preservation workflow — ingest, normalisation, metadata, AIP and DIP packaging.
Software is free under AGPL; most institutions pay for hosting or support rather than a
licence. My view is that we should not be building preservation packaging ourselves, so if
the Library runs this or would consider it, our pipeline should feed it and stop there.
Licence: AGPL. Optional paid support.

### Not recommended for evaluation right now

**Preservica** — commercial, enterprise licensing. Worth a single question to Joanne about
whether the University already holds a licence, because if it does that changes stage 05 and
06 significantly. But don't spend evaluation time on it unless the answer is yes.

**Copilot / Azure AI / any hosted API** — ruled out for processing archive content. These
drives contain personal email, medical and tax records, student records and unreviewed PII.
Sending that content to a hosted service is not something we can justify, and I don't want us
designing around it. See the note in the kickoff agenda.

---

## Evaluation criteria

Score each tool 1–5 on each criterion. Write one sentence of evidence per score — a score
without a reason isn't useful to me.

| # | Criterion | What a 5 looks like | What a 1 looks like |
|---|---|---|---|
| C1 | **Cost** | Free, open source, no licence needed | Commercial licence we don't hold |
| C2 | **Install effort** | Single binary or pip install, working in under an hour | Requires a dedicated server, database, or admin approval |
| C3 | **Runs where we need it** | Works on Windows, Linux and Colab | Windows-only, or needs a GUI |
| C4 | **Throughput** | Thousands of files/second | Slower than writing it ourselves |
| C5 | **Output quality** | Structured, machine-readable, stable schema | GUI-only, or output we'd have to scrape |
| C6 | **Pipeline fit** | Clean handoff — we can join its output to the manifest on a key | Assumes it owns the whole workflow |
| C7 | **Coverage** | Handles the format range we actually see on these drives | Narrow, or misses the formats we care about |
| C8 | **Maintenance** | Actively maintained, good docs, real user base | Abandoned, undocumented |

**Weighting:** C1, C2 and C6 matter most right now, because we need something working quickly
that plugs into what we're building. C4 matters more later, at scale.

---

## Scoring sheet

Copy this table per tool.

```
Tool:
Version tested:
Licence:
Cost:
Install time (actual):
Platform tested on:

C1 Cost            ___/5   Evidence:
C2 Install effort  ___/5   Evidence:
C3 Portability     ___/5   Evidence:
C4 Throughput      ___/5   Evidence:
C5 Output quality  ___/5   Evidence:
C6 Pipeline fit    ___/5   Evidence:
C7 Coverage        ___/5   Evidence:
C8 Maintenance     ___/5   Evidence:

TOTAL: ___/40

What it produces (paste a real sample of its output):

Where our code would take over:

What it does NOT do that we still have to build:

Recommendation:  Adopt  /  Adopt with reservations  /  Skip
Reason:
```

---

## How to actually test them

Use the pilot corpus once I have it assembled. Until then, build yourself a deliberately
nasty test folder — 50 to 100 files including:

- a Word document renamed to `.d1`
- a TIFF with no extension at all
- a zero-byte file
- a password-protected PDF
- a file with a non-English filename
- a nested zip containing a zip
- an old `.doc` (not `.docx`) and an old `.xls`
- a scanned PDF with no text layer
- a spreadsheet with several sheets
- a very large file (500 MB+) to check throughput claims

That set is closer to what a real researcher drive looks like than anything clean, and it
will break tools in informative ways. The mangled extensions in the file-search POC —
`.d1`, `.career2`, `net3852448d`, `00361-00850` — are the exact case magic-byte
identification is supposed to solve, so test that specifically.

---

## Specific questions I want answered

1. Does Siegfried correctly identify our mangled-extension files? What is its actual
   throughput on a folder of 10,000 files?
2. Can Tika replace the `win32com` code for `.doc`, `.xls` and `.ppt`? Compare its output
   against the POC's output on the same files — is it as good, better, or worse?
3. Is DROID genuinely free for our use, with no institutional licence needed?
4. How big is the NSRL RDS download, and how much of a typical folder does it actually
   remove? Is the minimal set enough?
5. Does BitCurator install in a form we can realistically use, or does it assume a dedicated
   forensic workstation?
6. What does Tika do when it fails? Does it hang, crash, or return an error we can catch?
   This matters more than its success rate — a hang on file 40,000 of 200,000 is worse than
   a clean failure.
7. For each Tier 1 tool: what does its output look like as a table we could join to the
   manifest? Paste a real sample.

---

## Deliverable

A short write-up in the repo at `docs/software-evaluation-results.md` containing:

- the scoring sheets
- a ranked recommendation
- for each adopted tool, the exact handoff point — what it produces and what we consume
- the revised build list: what is genuinely left for us to write
- anything that surprised you

Don't over-polish it. I would rather have honest scores and a rough write-up than a tidy
document that hides where a tool disappointed you.

---

## Related

- `docs/superseded/2026-08-07-kickoff-agenda.md` — software availability table and the licensing questions for Joanne and Brent
- `docs/design/pipeline-design.md` — stages 01 and 03, where these tools would sit
- `docs/design/manifest-schema.md` — the manifest these tools' output has to join onto
