# Archival Accession Processing Tool — Agent Instructions

## Purpose
The Archival Accession Processing Tool is the appraisal and description layer for archival transfers. It decides what may be worth keeping, describes material, detects sensitive/personal information, and ranks evidence against archivist-authored criteria. It is not a preservation system; packaging, fixity, and OAIS preservation belong to Medusa.

The tool was brought to Tayler by University Archivist Joanne Kaczmarek. Records and Information Management Services (RIMS) is the supporting service context, not the product name. Preserve repository URLs and technical identifiers.

## Authoritative locations
- GitHub: terbe2022/RIMS-Archival-Project-
- AITS host: urbadvanalytics1.admin.uillinois.edu
- Live pipeline: /var/advanalytics/datashare/Admin-pipeline/pipelines/archivist_triage_tool/
- Sanitised Git clone on server: ~/RIMS-Archival-Project-
- Local developer clone should be a normal Git clone, not a temporary Codex workspace.

The live pipeline and Git clone are intentionally separate. Do not turn the 1.6 GB live pipeline directory into a Git repository.

## Data boundary — mandatory
Real accession content stays on approved University infrastructure. Never copy real archival/accession content, PII vaults, manifests containing sensitive material, credentials, secrets, private keys, tokens, runtime outputs, or other protected data into public GitHub, Colab, prompts, or unapproved cloud services.

GitHub synchronisation is allow-list based. Do not replace it with a deny-list. Inspect the dry run before a real sync.

Never request, expose, store, paste, or automate a user's password. Do not weaken SSH host verification.

## Architectural invariants
Do not quietly reverse these decisions:
1. Sensitivity outranks ranking.
2. Nothing is automatically deleted. The lowest selection outcome remains subject to human review/disposal.
3. Intake form valuable/exclude fields do not reach the description model; ranking evaluates descriptions against them separately.
4. Decision precedence is sensitivity -> rule match -> content evidence -> proximity evidence; signals are not averaged.
5. retained_by_association must remain explicit and explained.
6. Release versions are stored as reviewed artefacts rather than regenerated at publication time.
7. Machine proposals remain visibly distinct from human judgements and are stamped unreviewed until reviewed.
8. Auditability is preferred over throughput at this project's scale.

## Collaboration
main is the integration branch. Do not perform feature development directly on main.

Use short-lived task branches:
- tayler/<task> for engineering/product work
- gauri/<task> for validation/evaluation work
- setup/<task> for repository/workflow infrastructure

Use pull requests to merge into main. Before committing, show the relevant diff and test results. Do not push or merge when the user has asked only for inspection.

Agents must avoid overlapping edits. Before beginning a task, inspect current branch/status and open work.

## Server operations
Treat the live pipeline as operational state, not a disposable checkout. Prefer Git-controlled development and deliberate deployment/sync.

Routine public sync is designed around:
  python3 scripts/tidy_server.py --dry-run
  python3 scripts/sync_to_repo.py --repo ~/RIMS-Archival-Project- --public --dry-run

A real sync occurs only after reviewing the dry run. Do not run destructive cleanup, reset, deployment, long GPU jobs, or production-affecting commands without explicit approval.

Ollama's project-specific service has historically been run on 127.0.0.1:11435 with keep-alive because the system service selected CPU. Verify current state before relying on this; do not restart services or change system configuration without authorization.

## Current validation boundary
No real accession content goes into Colab. Validation intended for external/cloud execution uses synthetic fixtures reproducing relevant failure modes.

Gauri owns the validation/evaluation lane. Read validation/AGENTS.md before changing files under validation/.

## Human/policy dependencies
Do not present system accuracy as established until appraisal rules are ratified and a labelled gold set exists. Some decisions belong to archivists, system administrators, privacy/data-governance staff, or downstream system owners rather than engineering agents.

## Working rule for agents
Read this file and the nearest nested AGENTS.md before acting. Inspect before editing. Make the smallest coherent change. Preserve provenance and auditability. Test the behavior actually changed. State uncertainty rather than inventing missing project facts.
