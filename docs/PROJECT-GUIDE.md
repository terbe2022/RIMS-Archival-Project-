# Archival Accession Processing Tool — current guide

Updated October 13, 2026. This is the main operational entry point. [Evaluation](EVALUATION.md) defines Gauri's quality work; [Decisions](DECISIONS.md) and [Stakeholders](STAKEHOLDERS.md) retain policy and people registers. Issues and the [Project board](https://github.com/users/terbe2022/projects/1) own tasks/deadlines.

## Purpose and responsibilities

Joanne Kaczmarek brought this archivist tool to Tayler Erbe. RIMS is its supporting service context. Separate image, email and general-file proofs of concept are being integrated: accession context -> inventory/routing -> extraction -> descriptions -> separate appraisal/sensitivity -> human review -> export. Preservation is downstream.

Tayler owns ingestion, integration, deployment and outputs; Gauri owns reproducible model/QA evaluation and failure evidence. Archivists determine appraisal criteria and reference judgements. AI-assisted coding helps implement the system; it does not establish correctness. No new autonomous processing coordinator or automatic code-to-card/email monitor is verified active.

## Current evidence

| Area | Verified | Pending |
| --- | --- | --- |
| GitHub | Shared code merged; 18 local regression tests passed | Broader original-file coverage |
| Server | Deployed bed430ee68aa16fffa87ba87f46f2e12d20de3d6; 52 files, zero differences | Server tests, actual inference and controlled end-to-end run |
| Colab | Notebook prepared; synthetic stub checks passed locally | Actual GPU execution and quality comparisons |
| Website | Authenticated fuller metadata; public dataset URL checked 404 and unauthenticated backend 401 | Original binary/image previews not connected |
| Quality | Proposed protocols | Ratified criteria, human labels and measured appraisal accuracy |

The website simulates processing and stores reviews in the browser; it is not a running GPU pipeline. Older pages may describe an earlier sanitized snapshot. Use the dated evidence here.

## Where everything lives

For the sanitized current server capacity and observed software, see [Hardware](HARDWARE.md). These specifications are not a benchmark or a guarantee of available resources.

Code: [public repository](https://github.com/terbe2022/RIMS-Archival-Project-).
Data: [private repository](https://github.com/terbe2022/RIMS-data).
Prototype: [login](https://terbe2022.github.io/RIMS-Archival-Project-/login.html).
Experiments: [shared Colab notebook](https://colab.research.google.com/github/terbe2022/RIMS-Archival-Project-/blob/main/notebooks/shared-pipeline-colab.ipynb).

Server: `urbadvanalytics1.admin.uillinois.edu`. Live state: `/var/advanalytics/datashare/Admin-pipeline/pipelines/archivist_triage_tool`. Fresh source: `~/archival-pipeline-2026-10-13`. Old `~/RIMS-Archival-Project-` predates history cleanup: do not pull/push/deploy from it. Do not initialize Git in the live directory.

Authenticate through your own approved account; no passwords/tokens in docs, notebooks or clone URLs. A separate terminal's SSH session is not inherited by Codex. Gauri's accepted private-repo access does not establish server authorization. Prototype password is distributed separately through PEAR; email allowlisting is not configured.

## Data distinctions

| Source | Purpose and limits |
| --- | --- |
| Private raw release `raw-sample-2026-10-08` | 2,375 original sample files for approved source-based validation; not every historical POC corpus |
| Private `data/original-prototype-data.json.gz`, manifest, `load_original.py` | 2,375 fuller metadata records, four jobs, 1,052 extracted-text entries; prior outputs are not reference answers |
| Older private `data/prototype-data.json.gz` | Sanitized metadata; cannot validate absent original contents |
| Server `data/sample_1k` | Raw mixed files, email and scans; directory name does not imply exactly 1,000 files |
| Server `intake/`, `review/`, `runs/`, `state/` | Context, decisions, runtime outputs and state; protected, no blanket public copy |
| Synthetic fixtures/notebook | Cloud-executable smoke/comparison material; not original-file appraisal evidence |

Verify source hashes and raw-to-record mapping before evaluation; equal counts are not proof. Prefer Linux/WSL extraction for Windows-incompatible source names. Extracted text is not original binaries; website preview references are not currently connected assets.

## Shared workflow and next checks

Codex edits local source; task branches/PRs integrate through GitHub main; server and Colab use recorded reviewed commits. Same code SHA does not guarantee environment or data parity. Colab runs synthetic experiments; direct Codex-to-Colab runtime control is not configured. Use `tayler/*`, `gauri/*`, `setup/*` branches and meaningful tests.

Read root/validation AGENTS.md. Original accession content cannot enter public Git, Colab or unapproved prompts/services. Private hosting approval does not extend this permission. Sensitivity outranks ranking, no automatic deletion, keep valuable/exclude criteria out of description prompts, appraise separately, preserve retained_by_association and human-review provenance.

Run from the fresh checkout:

```bash
cd ~/archival-pipeline-2026-10-13
python3 scripts/deploy_code.py --live /var/advanalytics/datashare/Admin-pipeline/pipelines/archivist_triage_tool --verify
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Server test output has not been received. Earlier audit: python-pptx absent, Ollama on 11434/vLLM on 8000 responsive, historical 11435 unavailable; recheck before use. Do not restart services or replace system dependencies indiscriminately. Next run three synthetic inference requests, review row errors, then plan an isolated end-to-end sample without overwriting prior decisions.

Deployment uses scripts/deploy_code.py dry-run -> reviewed apply -> verify, with backups. Current rollback journal is under `_code_backups/20261013T174202596674Z-bed430ee68/journal.json` in the live directory. Legacy workbench/ remains; inspect launchers for old imports.

Gauri returns protocol/results/defects; archivists adjudicate labels; Tayler fixes integration through PRs; Gauri retests. The larger recovered harness remains separate pending integration. The shared notebook does not imply every historical experiment merged.

Specialist references: [architecture](design/pipeline-design.md), [manifest](design/manifest-schema.md), [accession context](ai-and-the-accession-form.md), [Teams controls](TEAMS-PROGRAM-MANAGER.md), [work tracking](work-tracking.md), [validation execution](../validation/START-HERE.md). [History](history/README.md) preserves provenance, not current completion.
