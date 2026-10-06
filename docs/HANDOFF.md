# RIMS handoff

Last edited: 2026-10-06. Last source/code review: 2026-10-06. Last server verification: not performed in this reconciliation.
Status: reconciled documentation; current server verification remains outstanding.

## Purpose and boundaries

RIMS supplies appraisal and description before preservation. Medusa and successor systems own preservation packaging, fixity and OAIS functions. Digital Library supplies access and ArchivesSpace supplies catalogue/finding-aid integration; their final delivery contracts remain unresolved.

The live AITS pipeline is separate from its sanitized Git clone and from the permanent local development clone. GitHub carries reviewed code, documentation and synthetic validation material. It is not a backup of live processing state. Real accession content, identifying filenames/paths, mapping vaults, sensitive manifests, credentials and runtime outputs stay on approved University infrastructure. Synthetic fixtures are the cloud evaluation route; no new cloud permission is established here.

Read root AGENTS.md first and validation/AGENTS.md for evaluation work. These documents govern agent actions. Historical procedures and this handoff do not authorize service changes, pipeline runs, deployment, deletion or synchronization.

## Pipeline architecture

The implementation spans intake/identity, inventory/hash/format detection,
structural exclusion and appraisal, lane routing/extraction, identifier scanning
and pseudonymization, description/metadata/relevance, then review/search/export.
Historical stage numbers and names vary; use the script/module and schema field
as the execution contract rather than assuming every document's stage numbering
matches. `scripts/run_cpu_pass.py` orchestrates the CPU stages;
`scripts/run_all_lanes.py` generates model descriptions; `src/schema` defines
manifest rules. Inputs are approved University accession files and intake forms;
outputs include manifests, derivatives, model JSONL and review payloads, all
restricted unless a separately reviewed public sanitization permits publication.

Inventory preserves one row per path and provenance. Content signatures route formats; extraction supplies text; identifier detection and pseudonymization prepare controlled derivatives. Metadata and descriptions support ranking and review. Search indexes extracted text directly rather than a centrality summary. Description inputs must exclude intake valuable/exclude criteria; ranking evaluates evidence against those criteria separately.

Sensitivity outranks rule match, which outranks content evidence, which outranks proximity evidence. Do not average these signals. Keep retained_by_association explicit. Machine proposals remain distinct from reviewed human decisions. Nothing is autonomously deleted. Stored reviewed derivatives, rather than regeneration at publication, are the release invariant; actual release implementation needs verification.

Manifest/schema code lives under src/schema; application code under src/workbench. Review UI, scripts and historical POCs are separate parts of the repository. Historical HTML publishing copies are deliberate; establish source/publishing relationships before editing them.

## Development and collaboration

Tayler owns engineering: pipeline and UI fixes, integrations, deployment design and dependency coordination. Gauri owns model comparison, context ablation and gold-set/pipeline evaluation. Gauri's experiments must not change production behavior as a side effect.

Use tayler/*, gauri/* or setup/* branches as appropriate, then PR to main. Show the relevant diff and validation before committing. Keep code-package changes separate from documentation reconciliation. GitHub Issues/Project owns actionable work, assignments, dependencies and dates; the four maintained documents explain orientation, status, decisions and validation. Do not maintain parallel TASKS or CALENDAR lists.

## Operational lessons requiring verification

Historical folder association promotes a folder with at least three files when
60% or more rank medium/high; low-ranked neighbors remain explicitly associated.
This is a historical implementation claim, not newly ratified policy or a fresh
server test. Test the threshold and boundary cases in pipeline validation.

`scripts/decision_server.py` historically stores an append-only log with
supersession links. Plain static serving falls back to in-memory decisions with
a warning. This does not establish authenticated identity or durable multi-user
storage. Simulated reviewer decisions remain unreviewed; a typed name alone is
not authentication.

The September handoff reports project Ollama on loopback port 11435 with a four-hour keep-alive and sequential model lanes on one GPU. These are historical observations, not verified current settings or instructions to change a service. Reported performance/failure figures are not renewed measurements.

The handoff warns that re-ingest can overwrite exported decisions. Preserve and verify decision export before any separately authorized re-ingest. Do not execute archived demo cleanup commands: broad process termination and directory deletion require a concrete reviewed target and separate authorization.

The August decision D17 forbids accessions without a record-series number; September describes provisional IDs. This conflict remains unresolved. Do not infer a policy reversal from the fact that a historical run occurred.

## Provenance and remaining closure

Restricted operational handoff location: PENDING APPROVED UNIVERSITY LOCATION

The project owner has explicitly prohibited copying, moving, uploading or
publishing the restricted handoff until that destination is approved. Brent West
is the governance contact to confirm classification and suitable access/storage;
Joanne Kaczmarek is the contact if an Archives records location is appropriate.
This is related to historical D5 mapping-store governance, but approval for one
artifact must not be inferred to cover another. Box, the Archives share and the
shared server account are candidates only, not approved destinations for this
record. Pending custody does not block public-safe documentation integration.

Authorized operators should ask the project owner for the approved restricted
record by title/date: September 29, 2026 RIMS operational handoff. The restricted
copy preserves accession identities, flagged-file references and run artifacts.
Do not expose its sensitive path or contents in public issue bodies. A pending
location does not authorize upload to a convenient cloud/document service.

## Operational templates and prerequisites

These templates document the current repository parsers; they were not executed.
Run only in an approved University environment after checking the deployed code,
dependencies, intake identity and output targets, preserving decision exports,
and obtaining approval for the specific production/model operation. Placeholder
values are not literal paths to run. Resolve provisional identity policy first;
the historical --provisional example is not an approved default.

```bash
python3 scripts/run_cpu_pass.py --data <approved-source> --intake <approved-intake> --out runs/<run-id>
python3 scripts/run_all_lanes.py --manifest runs/<run-id>/manifest.parquet --out runs/<run-id> --redacted-root runs/<run-id>/redacted --url http://127.0.0.1:11435
python3 scripts/export_prototype.py runs/<run-id>/manifest.parquet --intake <approved-intake> --out demo/<run-id>
python3 scripts/review_packet.py export demo/<run-id>/prototype-data.json --accession <accession-id> --out review/<packet>.json
python3 scripts/review_packet.py ingest demo/<run-id>/prototype-data.json --decisions review/<returned-decisions>.json --reviewer <authorized-reviewer>
python3 scripts/decision_server.py --payload demo/<run-id> --port <approved-port>
```

Model lanes historically run sequentially on one GPU. Check redacted inputs;
policy alone does not prove each run used them. After descriptions exist, verify
the documented rescore/merge path before trusting relevance results. Payload
regeneration via export_prototype is different from review_packet export, which
packages review material. Regenerating the payload after ingest can discard
decisions: preserve them first, regenerate before ingest, and verify the result.

The project owner confirms the deployed server exporter supports --thumbs while
the reviewed repository exporter does not. Treat this as source/deployment drift
requiring a separate comparison/reconciliation task. Do not append --thumbs to
the repository command above or assume either copy is fully authoritative.

Public sync runs from the live pipeline directory toward the sanitized server
Git clone, not from GitHub toward the live pipeline:

```bash
python3 scripts/tidy_server.py --dry-run
python3 scripts/sync_to_repo.py --repo ~/RIMS-Archival-Project- --public --dry-run
```

Review the proposed file list and public content before authorizing a real sync.
Current sync omits notebooks, validation/ and nested documentation. Content
checks are limited, and dry-run only prints the public sanitizer command; it
does not execute or validate the resulting public payload. Do not bypass checks
with --force. Stale server docs/*.md can overwrite maintained clone documents.
Agree file ownership/source direction before real sync, review the final diff,
and stage explicit reviewed paths on a task branch instead of blindly git add -A.

Deployment is a separate Git-reviewed, approved transfer into operational state,
with preservation/rollback verification. No current deployment mechanism is
established here. Do not treat pulling the sanitized clone or running public sync
as deploying the live pipeline. Service restarts, long GPU jobs, live runs,
cleanup, publication, authentication changes and disposal require their own
authorization. Never request or automate passwords or create SSH keys as a
side effect of this documentation workflow.

Sources: root and nested agent rules; docs/design/decisions.md; docs/PROJECT-STATUS.md; docs/work-tracking.md; September 29 handoff; September 11 meeting brief; October 6 decisions and subsequent corrections; recovered validation package. Historical originals remain outside this proposed public bundle because they contain accession-specific identifiers and unverified assertions.

This public orientation is a derivative, not a replacement for the full operational handoff. Preserve the unchanged September original in an access-controlled, approved University location outside public Git. The recovered local copy is not evidence that its storage location has been approved or that the University archive step is complete. Accession identities, flagged-file examples, exact run artifacts and diagnostic details belong in that restricted source. An approved operator needs access to it when reproducing or investigating those runs. General infrastructure paths already published in root AGENTS.md are distinct from identifying accession paths; the public document may reference those established locations.

The lost architecture-and-deployment document was not recovered. Reconstruct only from evidence, leaving hosting, cloud-GPU governance, authentication, durable review storage and destination contracts open. No completed evaluation results or labelled gold set were recovered. Current server capability remains unverified. Repository-only cutover requires integration review and a new-conversation orientation check.
