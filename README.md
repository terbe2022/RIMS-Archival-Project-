# RIMS Archival Project

RIMS is a prototype for supporting archival appraisal and description. It inventories files, records appraisal and sensitivity decisions, routes extraction and model work, and prepares metadata for human review. Human institutional owners decide policy, access, storage and release. Machine output does not itself authorize disposal or publication.

Tayler Erbe leads engineering, integration and validation oversight. Gauri Bhasin leads validation experiments and results analysis. GitHub contains the source, project documents and actionable issues. A shared Teams program-manager agent assists coordination from the designated project chat.

## Start here

- [Project overview](docs/PROJECT-OVERVIEW.md): purpose, components and responsibilities.
- [Documentation map](docs/README.md): current guidance and supporting history.
- [Current status](docs/PROJECT-STATUS.md): demonstrated work and outstanding verification.
- [Engineering handoff](docs/HANDOFF.md): source map, safety boundaries and integration status.
- [Validation start](validation/START-HERE.md): Gauri's synthetic-first workflow.
- [Teams coordination](docs/TEAMS-PROGRAM-MANAGER.md): chat updates, reviewed proposals and current limits.

## Data and prototype inputs

Use [Data and prototype guide](docs/DATA-AND-PROTOTYPES.md) to choose the correct input. [Private RIMS-data](https://github.com/terbe2022/RIMS-data) contains both the recorded metadata snapshot and a separate raw-file release for model validation. The raw archive is not included in a Git clone. Historical POC corpora and earlier screen-specific exports are not assumed to be included.

## Current scope

The repository contains the pipeline prototype, appraisal rules, manifest schema, review interface and earlier proofs of concept. The first validation loop uses synthetic examples and Qwen in Colab, with results captured through GitHub review. Paid frontier judging is a later step subject to access and funding.

Documentation is consolidated here. Pipeline repairs in [PR #79](https://github.com/terbe2022/RIMS-Archival-Project-/pull/79) and the executable validation kit in [PR #80](https://github.com/terbe2022/RIMS-Archival-Project-/pull/80) require their own code review and integration. Their publication is not proof of deployment or completed model experiments.

Keep real accession records, private operational data, credentials and restricted transfer material out of public GitHub and hosted model tools. Colab validation uses synthetic fixtures only. The project manager proposes changes for review; autonomous chat monitoring and GitHub writes have not been verified.

## Repository layout

`src/` and `scripts/` contain pipeline code and entry points; `rules/` contains appraisal rules; `docs/` contains active guidance and historical sources; `validation/` contains experiment guidance; `poc/` preserves earlier experiments. GitHub Issues and the actual Project board hold actionable work, rather than parallel Markdown task lists.

Python dependencies in `requirements.txt` specify version constraints; they are not a fully pinned reproducibility lock. Record the installed environment and exact commit for each experiment.
