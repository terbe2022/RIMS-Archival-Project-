#!/usr/bin/env bash
# Creates the seed issues. Run AFTER setup-labels.sh and setup-milestones.sh.
# Requires the GitHub CLI:  https://cli.github.com/   then:  gh auth login
set -u
REPO="terbe2022/RIMS-Archival-Project-"

gh issue create --repo "$REPO" --title 'Fill in the manifest schema worksheet' --label 'stage:01-inventory,type:decision,blocker' --milestone 'M1 - Foundations' --body 'One row per file, columns added by each stage. Every other stage depends on this contract, and nothing has been designed yet.

Work through the worksheet together — about 30 questions across 7 sections: keys and identity, storage format, which stage owns which column, nulls and failure states, versioning, how layered decisions get recorded.

Two things to get right:
- **"Not yet processed" vs "processed, found nothing"** must be distinguishable, or resumability breaks.
- **Column ownership per stage.** No stage writes a column another stage owns. That is what makes the components assemblable.

Commit partial answers rather than waiting for completeness. A half-filled worksheet with a named blocker beats an empty one.

Worksheet: https://github.com/terbe2022/RIMS-Archival-Project-/blob/main/worksheets/W1_manifest_schema_worksheet.md'

gh issue create --repo "$REPO" --title 'Get remote access to a real drive — or a directory listing of one' --label 'stage:00-source,type:question,blocker,needs:infra' --milestone 'M1 - Foundations' --body 'Everything built so far has run on small samples pulled through Box, which hides every problem that shows up at drive scale. Our throughput estimates are guesses because of it.

**The cheap version of this ask:** a directory listing of one representative drive. It gives file counts and format mix, which are the two variables that dominate processing time, and it costs nothing to produce even before full access is sorted out. Ask for this first.

Options and the questions for Privacy and Infrastructure are in the assessment worksheet.

Worksheet: https://github.com/terbe2022/RIMS-Archival-Project-/blob/main/worksheets/W3_storage_and_ingest_assessment.md'

gh issue create --repo "$REPO" --title 'Request the appraisal policy and a 300–500 file gold set' --label 'stage:02-triage,type:question,blocker,needs:joanne,needs:bethany' --milestone 'M1 - Foundations' --body 'Without a written definition of what "important" means, triage cannot be built or measured.

The image POC is the argument for why this matters: of 79 flagged images, 13 were clearly correct, 8 clearly wrong, and **58 (73%) were ambiguous**. That is not a model failure — it is what happens when criteria were never defined precisely enough for anyone, human or machine, to be consistent.

Frame the ask as a specification, not a favour. The gold set is simultaneously the spec and the way we measure whether triage works.

Questions: https://github.com/terbe2022/RIMS-Archival-Project-/blob/main/worksheets/W4_questions_by_stakeholder.md'

gh issue create --repo "$REPO" --title 'Check the ZBook for a discrete NVIDIA GPU' --label 'type:setup,good-first-issue' --milestone 'M1 - Foundations' --body 'Device Manager → Display adapters. Task Manager lists GPUs separately as "GPU 0" and "GPU 1" and it is easy to report only the first.

HP ships the ZBook Power G9 in configurations both with and without an RTX A1000/A2000. If there is a card, the model plan changes — CUDA becomes available and small quantised vision models become practical.

If NVIDIA appears, run `nvidia-smi` and post the output here.

Setup guide: https://github.com/terbe2022/RIMS-Archival-Project-/blob/main/docs/onboarding-and-setup.md'

gh issue create --repo "$REPO" --title 'Set up the Python environment and pull the three models' --label 'type:setup' --milestone 'M1 - Foundations' --body 'Project venv (not base Anaconda), install the stack, freeze `requirements.txt`.

Models — this is the full list, about 5 GB total:
- `llama3.2:3b` — text workhorse
- `moondream` — vision, built for constrained hardware
- `nomic-embed-text` — embeddings with 8K context

**Use the Ollama HTTP API, not the CLI.** The CLI reloads model weights on every call, which is why POC 1 measured 34.8 sec/row. Do not copy that pattern from the old notebooks.

Setup guide: https://github.com/terbe2022/RIMS-Archival-Project-/blob/main/docs/onboarding-and-setup.md'

gh issue create --repo "$REPO" --title 'Install Siegfried and ExifTool, confirm both run' --label 'stage:01-inventory,type:setup' --milestone 'M1 - Foundations' --body 'Magic-byte format identification is what resolves the mangled extensions POC 2 had to skip — `.d1`, `.career2`, `net3852448d`, `00361-00850`. Almost all of those are ordinary formats with broken names.

Test specifically: rename a `.docx` to `.d1` and confirm Siegfried still identifies it correctly.

Evaluation task: https://github.com/terbe2022/RIMS-Archival-Project-/blob/main/worksheets/W2_software_evaluation_task.md'

gh issue create --repo "$REPO" --title 'Run the five-part environment smoke test' --label 'type:setup,good-first-issue' --milestone 'M1 - Foundations' --body 'Before building anything, confirm each piece works:

1. Embed 100 strings with `nomic-embed-text`, record the timing — it is your baseline
2. One prompt to `llama3.2:3b` via the HTTP API
3. One image to `moondream`
4. Siegfried over a folder, JSON out
5. Read a `.docx` with python-docx and a `.pdf` with pypdf

Post the numbers here. If any fail, say so before working around it.'

gh issue create --repo "$REPO" --title 'Evaluate existing archival software' --label 'type:research' --milestone 'M1 - Foundations' --body 'Score the shortlist against the 8 criteria. Tier 1 first — Siegfried, Tika, ExifTool, DROID — that is where most of the value is.

Key questions to answer:
- Can Tika replace the `win32com` code for `.doc`/`.xls`/`.ppt`? Compare output on the same files.
- Is DROID genuinely free with no institutional licence?
- How big is the NSRL RDS download and how much does it actually remove?
- **What does Tika do when it fails** — hang, crash, or catchable error? This matters more than its success rate. A hang on file 40,000 of 200,000 is worse than a clean failure.

Deliverable: `docs/software-evaluation-results.md`

Task: https://github.com/terbe2022/RIMS-Archival-Project-/blob/main/worksheets/W2_software_evaluation_task.md'

gh issue create --repo "$REPO" --title 'Ask which archival software the University already licenses' --label 'type:question,needs:joanne,needs:brent' --milestone 'M1 - Foundations' --body 'Preservica, Archivematica, DROID, ePADD. If any are already running, parts of stages 05 and 06 shrink significantly.

The strategic point to make: **we should not be building a preservation system.** Archivematica and Preservica already do that. What does not exist is appraisal and description at this scale. That is our contribution and everything else should be borrowed.

Questions: https://github.com/terbe2022/RIMS-Archival-Project-/blob/main/worksheets/W4_questions_by_stakeholder.md'

gh issue create --repo "$REPO" --title 'Take storage and privacy questions to Data Privacy and Governance' --label 'type:question,needs:privacy' --milestone 'M1 - Foundations' --body 'Get in writing that local open-weight processing on university hardware is acceptable, and that hosted AI services are excluded for this content.

These drives will hold personal email, unreviewed PII, medical and tax records, and FERPA-covered student records. I am designing as if hosted services are off the table — this closes that question rather than leaving the architecture depending on an approval we are unlikely to get.

Worksheet: https://github.com/terbe2022/RIMS-Archival-Project-/blob/main/worksheets/W3_storage_and_ingest_assessment.md'

gh issue create --repo "$REPO" --title 'Assemble the pilot corpus — 500 to 2,000 mixed files' --label 'stage:00-source,type:build' --milestone 'M1 - Foundations' --body 'Small enough to iterate on, varied enough to break things. Also the pool the gold-standard labelling set comes from.

Include the awkward cases deliberately: a Word doc renamed to `.d1`, a TIFF with no extension, a zero-byte file, a password-protected PDF, a non-English filename, a nested zip, an old `.doc` and `.xls`, a scanned PDF with no text layer, a multi-sheet spreadsheet, and something over 500 MB.'

gh issue create --repo "$REPO" --title 'Set up the Box project folder structure' --label 'stage:00-source,type:setup' --milestone 'M1 - Foundations' --body 'Somewhere for Joanne'\''s team to work, and for anything too large or sensitive to commit.

Structure proposed in the upload guide: `01-Data/`, `02-Documents/`, `03-Working/`.

Rule: **if it contains data it goes in Box; if it describes or produces data it goes in GitHub.**

Post the share links here when done — they need wiring into the scope document.'

gh issue create --repo "$REPO" --title 'Build Stage 0 — filesystem walk to manifest' --label 'stage:01-inventory,type:build' --milestone 'M2 - First pass working' --body 'Walk the tree recording path, filename, extension, size, created, modified, accessed, depth. Open nothing.

**Target: 10,000 files inventoried in under a minute.** Parallelise across the P-cores.

Preserve the full original path verbatim — it is the primary key and how provenance is proved.

Heavily annotated notebook: a markdown cell before each code cell explaining what and why. No hardcoded paths.

Depends on: manifest schema'

gh issue create --repo "$REPO" --title 'Build Stage 1 — SHA-256 and Siegfried format ID' --label 'stage:01-inventory,type:build' --milestone 'M2 - First pass working' --body 'Hash every file, run Siegfried over the tree, join both onto the manifest on path.

Hashing is cheap and buys deduplication, integrity checking, and NSRL hashset lookups.

Open question worth deciding here: whole-file hash, or head+tail+size for very large media? Whole-file is cleaner; head+tail is much faster on multi-gigabyte video.

Depends on: Stage 0'

gh issue create --repo "$REPO" --title 'Build Stage 2a — duplicate detection and structural filters' --label 'stage:02-triage,type:build' --milestone 'M2 - First pass working' --body 'Free exclusions with no content analysis: exact duplicates by hash, NSRL known files, zero-byte, `~$` lock files, `.DS_Store`, `Thumbs.db`, caches, `node_modules`, `.git` internals.

**Report the reduction percentage.** That number is the argument for the whole architecture and I want it measured rather than assumed. Current working guess is 40–70% but nothing has been measured.

Nothing is deleted — decisions are written to the manifest as Layer 0.

Depends on: Stage 1'

gh issue create --repo "$REPO" --title 'Design and test the smart text peek' --label 'stage:02-triage,type:research' --milestone 'M2 - First pass working' --body 'A flat first-2KB is not enough — documents opening with letterhead, cover pages, or blank scanned pages all look identical in their first 2KB, and on institutional material that is a lot of everything.

Approach: ~6KB budget sampled structurally — head after skipping front matter, tail (conclusions and signatures are often the most identifying part), three strided middle samples, plus headings and TOC entries.

Two refinements to test:
- Extract keywords from the peek and embed those, not raw text. Boilerplate dominates otherwise.
- Escalation ladder rather than a fixed budget — most files resolve at tier 1.

Design: https://github.com/terbe2022/RIMS-Archival-Project-/blob/main/docs/pipeline-design.md'

gh issue create --repo "$REPO" --title 'Re-benchmark summarisation: Ollama CLI vs Ollama serve vs vLLM' --label 'stage:04-enrichment,type:research' --milestone 'M3 - Enrichment' --body 'POC 1 measured 34.8 sec/row via `subprocess.run()` against the Ollama CLI, which reloads model weights every call. That is an implementation artefact, not a model limit.

The image pipeline went 22.2 hrs → 3.7 hrs on the same L4 by migrating to vLLM — 6.22×, of which 3.6× was purely the serving stack. Expect something comparable here.

Re-benchmark before any hardware or model decision is made.

Prior work: https://taylererbe.com/archival-image-throughput-evaluation.html'

gh issue create --repo "$REPO" --title 'Port Office extraction off win32com to Tika + LibreOffice' --label 'stage:03-extraction,type:build' --milestone 'M3 - Enrichment' --body 'POC 2 uses `win32com.client` to drive actual Word, Excel and PowerPoint. It will not run in Colab, will not run on the Linux server with the L4, cannot be parallelised safely, and hangs on malformed files.

This is a prerequisite for the unified pipeline, not a cleanup task.

Verify output parity against POC 2 on the same sample files before switching over.

POC 2 defects: https://github.com/terbe2022/RIMS-Archival-Project-/blob/main/poc/02-file-smart-search/'

gh issue create --repo "$REPO" --title 'Compare three text models on the same 20 documents' --label 'stage:04-enrichment,type:research' --milestone 'M3 - Enrichment' --body 'Same documents, same prompt, compare output quality and speed. Record the numbers here.

Note for metadata work: more detail is not better. A larger model writes more fluent prose but invents plausible creators and dates more confidently. For Dublin Core fields we want extraction, not generation — small model, constrained schema, required to emit `null` rather than guess.'

gh issue create --repo "$REPO" --title 'Compare three vision models on the same 20 images' --label 'stage:04-enrichment,type:research' --milestone 'M3 - Enrichment' --body 'Same images, same prompt. Include `moondream` as the local baseline.

Carry forward from POC 3: LLaVA produced rationales that correctly described racialised content while returning `offensive: false`. The description was right, the judgment was wrong. **Keep description and classification as separate, independently auditable steps** — that is what made the semantic method work and it was ~200× faster.'

gh issue create --repo "$REPO" --title 'Decide: adopt ePADD for email, or keep our own lane' --label 'stage:04-enrichment,type:decision,needs:brent' --milestone 'M3 - Enrichment' --body 'A genuine build-versus-adopt fork. ePADD is Stanford'\''s email appraisal, redaction and discovery tool for archives, and it directly overlaps POC 1.

Either it becomes the delivery interface for the email portion and we feed it, or we keep our own lane. Worth deciding rather than drifting.

Ask Brent what RIMS has been using for email archiving and e-discovery before deciding.'

gh issue create --repo "$REPO" --title 'Agree human oversight thresholds' --label 'stage:02-triage,type:decision,needs:joanne,needs:brent' --milestone 'M2 - First pass working' --body 'Proposed starting position — negotiate, do not impose:

| Situation | Oversight |
|---|---|
| Anything flagged sensitive | 100% human review, always |
| Layer 1 exclusions, first drive | 100% review — first drive is calibration |
| Layer 1 exclusions, later drives | Stratified 5–10% plus the borderline band |
| Auto-promoted files | Stratified audit 5–10% |
| Deletion of anything | Explicit human approval, batch level, recorded |

**Establish review capacity first.** Thresholds set without knowing how many items per week the team can actually review produce a queue nobody works through.'

gh issue create --repo "$REPO" --title 'Build the throughput model and sizing calculator' --label 'stage:07-scale,type:build' --milestone 'M5 - Scale' --body 'Instrument every stage to record per-file and per-batch timing. Benchmark on a representative sample, not a convenient one — format mix drives cost more than file count does.

Deliverable: given file count and format mix, a defensible wall-clock estimate, plus a recommended processing order across the drive queue so the Archives can schedule.

Blocked until a real drive or at least a directory listing exists — format mix and triage retention rate are the two dominant variables and both are currently guesses.'

echo "Created 23 issues."