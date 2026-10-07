# Engineering handoff

Reviewed October 7, 2026. Use the [status snapshot](PROJECT-STATUS.md) and [decisions](DECISIONS.md) alongside this source map.

## Source map

- `src/schema/manifest.py`: executable manifest contract.
- `src/context.py`: selected accession-context construction and provenance.
- `rules/` and the pipeline rule checks: deterministic appraisal rules.
- `scripts/`: inventory, extraction, description and pipeline entry points.
- `docs/accession-workbench.html`: prototype human-review interface.
- Earlier `poc/` folders: historical experiments, not the current deployment contract.

Inventory and manifest records connect upstream files to extraction, appraisal and description. Sensitivity and institutional rules take precedence over generated description. Explicit association evidence is distinct from proximity inference. A missing association is not an established negative. Human review governs disposition and release.

## Integration and verification

[PR #79](https://github.com/terbe2022/RIMS-Archival-Project-/pull/79) contains source-bootstrap, prompt-syntax, pseudonymization, pipeline failure handling, nullable association, decision-log and public-export repairs. The repaired branch passed 13 regression checks and 12 rule checks. These are local source checks, not a deployed-server receipt. The review service remains a prototype; authentication, concurrency and institutional release controls require separate acceptance.

Do not equate the GitHub clone with the live pipeline workspace. Synchronize only selected reviewed source; public export requires explicit classification and safe fields. Restricted server-transfer originals require approved institutional custody and must not be committed. Actual server environment, UI behavior and operational configuration still need controlled verification.

## Responsibilities

Tayler owns engineering and integration and oversees validation. Gauri owns validation experiments and analysis. Institutional owners decide appraisal policy, storage and infrastructure approval. The program-manager role coordinates evidence and proposals; its authority does not include deployment, credentials or independent code changes.

Use synthetic fixtures for hosted validation. Record exact commit, environment, model identifier, inputs and outputs. Follow [validation onboarding](../validation/START-HERE.md). Executable files remain in PR #80 until separately integrated.
