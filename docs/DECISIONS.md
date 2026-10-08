# Archival Accession Processing Tool decision register

Last edited: 2026-10-07. Last source/code review: 2026-10-06. Last server verification: not performed in this reconciliation.
Current consolidated decision register. The August register remains at docs/design/decisions.md with a historical-source banner.

## Operating decisions carried from AGENTS.md

Sensitivity takes precedence over ranking; signals are resolved in order, not averaged. No autonomous deletion. Description models never receive valuable/exclude criteria. Association retention remains explicit. Reviewed release versions are stored artifacts. Machine proposals remain stamped unreviewed. Public sync remains allow-list based and requires dry-run review. Real protected content remains on approved University infrastructure.

## Reconciliations supported by current sources and later corrections

| Subject | Resolution | Evidence/status |
|---|---|---|
| Description order | Pseudonymized copy before summarization | Policy; historical run compliance requires logs |
| Search/truncation | Index extracted text; reject centrality-based removal of atypical evidence | Source review and October reconciliation |
| Image evaluation | Keep raw counts; no accuracy/prevalence inference | Later correction overrides October source's approximately 1% claim |
| Description/classification | Separate steps; test evidence-gated claims | Architectural direction; not measured success |
| Gauri | Validation owner, not production pipeline constructor | Root/nested agent rules |
| Notebook sync | Explicit file entries plus stripped-output validation | Implemented on PR #79 repair branch; integration and deployment pending |
| Task tracking | GitHub Issues/Project holds actionable work | Current coordination convention; actual Project fields must be retrieved |
| Documentation organization | Active project, engineering, coordination and validation guides are listed in docs/README.md; replaced material is preserved under docs/history/ | Consolidated through documentation PR #81 |

## Historical decisions preserved, not silently reopened

August D3 selected the project's email processing lane over ePADD, with possible delivery-interface reconsideration. D16 carries record_series and accession_uid separately. D18 separates accession rulesets. D19 enforces sensitivity precedence. D20 records stakeholder-approved oversight defaults; current capacity/implementation needs verification. D21 records open/restricted vocabulary; proposed three release variants must not silently redefine it. D22 permits deliberate approved disposal, never autonomous deletion. D23 rejects hosted AI for protected material. D24 chooses Parquet/DuckDB. D25 keeps one row per path. D26 replaces COM-based Office extraction.

## Unresolved decisions

- Product vocabulary for material offered back to a family rather than discarded:
  historical review raised a distinct not-accessioned outcome; no approved label
  or implemented return workflow is established.
- Server/repository exporter drift: owner confirms server --thumbs support and
  older repository parser omission. Reconcile source versions in a separate
  engineering task before declaring either the deployment source of truth.
- Restricted operational handoff home: pending approved University location.
- Restricted custody clarification from project owner: no copy/move/upload or
  publication until approval. Seek classification/storage guidance from Brent
  West and, for an Archives location, Joanne Kaczmarek. This is a dependency
  related to D5, not an inferred approval of Box/share/server storage.
- Lost deployment framing contained options, not decisions or approvals, per
  project-owner clarification. Write fresh framing against current evidence if
  needed; cloud-GPU governance remains unresolved. No old-chat recovery required.

- D17 versus provisional accession identifiers: require explicit project-owner/policy resolution.
- D5/D8: current mapping-vault and working-copy access/storage/clearing rules.
- D9/D13/D14: destination metadata, folder-level finding-aid attachment and email access.
- D10/D11/D12: review capacity, labelled reference set and retention-window confirmation.
- D6/D7/D15: current share/upstream processing/Gauri access status; historical blockers are not automatically current.
- Production identity, multi-user persistence, original-file hosting and cloud-GPU governance.
- Release-stage role enforcement and artifact requirements: recovered code is proposal only.

Later human guidance overrides an older document only where explicitly supplied. Dates, approvals, verified deployments and completed experiments must not be reconstructed from prose.
