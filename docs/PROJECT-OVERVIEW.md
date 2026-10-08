# RIMS project overview

Prepared 6 October 2026 from repository source, local tests and the project
coordination evidence supplied by Tayler. Reported implementation and observed
tool demonstrations are distinguished from deployment and acceptance evidence.

RIMS is an archival appraisal, description and review project for born-digital
collections at the University of Illinois System. Its purpose is to help
archivists understand a large transfer, identify material that may have enduring
value, describe it, recognize sensitive information and make traceable decisions
about access and retention. RIMS supports professional judgement; it does not
automatically delete records or replace the institution's preservation system.

Tayler is leading product development, engineering and integration while
overseeing the validation program. Gauri is responsible for reproducible
experiments and evaluation evidence. Archivists and institutional owners decide
appraisal policy, acceptable access, protected-data storage and infrastructure
approval. The project brings those responsibilities together without treating
an engineering implementation as policy approval.

See [People and stakeholders](STAKEHOLDERS.md) for the full participant list, titles and responsibility boundaries.

## GitHub as the shared project workspace

The [RIMS repository](https://github.com/terbe2022/RIMS-Archival-Project-) connects
the source code, architecture, notebooks, experimental protocols and project
documentation. GitHub Issues and the Project board hold actionable work;
branches and pull requests make changes reviewable. Engineering and validation
use distinct task branches so experimental work can inform the product without
silently changing operational behavior.

Documentation reconciliation has prepared a current handoff, project status,
decision register and validation plan, preserving historical sources and noting
conflicts rather than presenting every older assertion as current fact. GitHub
is also the handoff between Gauri's Colab experiments and Tayler's engineering:
versioned synthetic cases, notebooks and reviewed result reports provide the
evidence needed to reproduce a failure or assess a proposed improvement.

Real accession material, private manifests, mapping vaults and credentials stay
on approved University infrastructure. The public repository contains selected
source and reviewed documentation; it is not a copy of the live pipeline's
data or operational state.

## The prototype and product design

The project builds on three earlier proofs of concept: email processing, search
across different file types, and image description and sensitivity assessment.
Their lessons have informed a broader archival triage pipeline and an
accession-workbench interface for reviewing its outputs.

Inspected source covers inventory and file identification, duplicate and
appraisal-rule handling, format-based routing and extraction, descriptions,
sensitivity and identifier detection, pseudonymization, metadata and ranking.
The workbench design connects those results to explanations and reviewer
decisions. Historical reports describe runs over real collections, but the
current server deployment has not been independently reverified in this work.

The central design principles are explicit: sensitivity takes precedence over
ranking; association-based retention must remain visible; machine proposals
remain distinguishable from human decisions; and description models do not
receive the appraisal criteria they will later be evaluated against. Reviewed
release versions should be stored artifacts with provenance. Completing that
release workflow is still engineering work, rather than an already established
capability of the prototype.

The intended product outcome is a dependable internal AITS workflow built from
the existing prototype: intake, processing, review, persistent decisions and
reviewed export. Synthetic checks support development; operational acceptance
also requires approved identity, storage, deployment and archival policy.

## The shared Teams program-manager agent

Tayler has created and published a RIMS Program Manager in Copilot Studio and
opened it in Teams. Supplied demonstrations show GitHub issue retrieval and
retrieval of updates from the selected chat with Gauri. Gauri is listed as an
authorized user. She reports granting GitHub and Teams connection permissions,
but the supplied launch link fails for her; joint access remains unresolved.

The agent is intended to connect day-to-day chat coordination to the repository.
It separates reported progress, decisions, suggestions, blockers and questions;
links relevant evidence to existing issues; and prepares changes for review.
It should leave unknown owners, dates and approvals unset and should not mark
work complete without acceptance evidence. Its role spans engineering and
validation coordination, while GitHub remains the work record.

The desired workflow is to read updates from the designated conversation and
apply an exact reviewed update when Tayler or Gauri explicitly requests it.
Selected-chat reading has been demonstrated on request. Continuous listening,
durable message checkpoints, duplicate prevention and approved GitHub write
execution have not yet been verified. Publishing an agent and giving it read
tools do not, by themselves, establish those capabilities. The existing chat
and the separate agent conversation are also distinct Teams surfaces.

## Validation led by Tayler and carried out by Gauri

The prepared validation workspace gives Gauri a starting guide, Colab notebook,
synthetic fixtures, a repaired evaluation harness, experiment and result
templates, grading guidance and proposed agent roles. It is designed to let her
run reproducible experiments on a University computer without assuming she can
install a local model stack. Colab receives synthetic material only.

The first proposed experiment is a small Qwen text-model smoke test followed by
the same fixed-case evaluation loop. It checks whether notebook execution,
structured output, abstention and result capture work together. Broader model
comparisons and context ablation then test whether descriptions are accurate,
specific, appropriately restrained and supported by the source.

Tayler has directed the use of frontier-model judges for synthetic description
quality. That judging workflow is specified, but paid API access, funding and
execution remain pending. Neither the grading instructions nor a passing harness
test establishes measured model quality. Future validation of appraisal policy
and real archival decisions needs an appropriate institutionally approved
reference set and acceptance process.

Gauri's findings should become concrete engineering evidence: the synthetic
case, actual model and settings, expected and observed behavior, saved outputs
and a reproducible failure. Tayler can then connect that evidence to a scoped
fix and reviewable pull request. The proposed planning, coding, execution,
grading and analysis roles are workflow definitions, not proof that a fleet of
autonomous agents is already running.

## Current engineering progress and next outcome

The downloaded Python source snapshot matched the existing repository after
normalizing line endings. The useful work was therefore repairing defects and
reconciling behavior, rather than copying those files over the repository.

The [pipeline repair pull request](https://github.com/terbe2022/RIMS-Archival-Project-/pull/79)
fixes script imports and a broken vision prompt, preserves association evidence,
requires pseudonymized text by default, improves single-process decision audit
history, protects logs from static serving, and tightens public demonstration
exports and sync checks. Thirteen synthetic regression tests and twelve existing
appraisal-rule checks passed locally. The recovered validation harness separately
passed eight checks. These results establish the tested behavior, not production
readiness or successful model experiments.

The next outcome is to integrate reviewed changes, confirm Gauri can retrieve
and run the synthetic workspace, verify the Teams access and update workflow,
and test the actual internal prototype from intake to reviewed export on approved
infrastructure. Authentication, durable multi-user storage, release artifacts,
destination contracts and the precise deployed UI version remain material
dependencies. The repair branch has not been deployed to the live server.

Taken together, the project now has a connected foundation for product work:
an archival prototype, a GitHub collaboration and evidence workflow, a published
Teams coordination pilot, and a structured validation program. Tayler's work is
bringing those pieces into a dependable operational product, with Gauri's
experiments supplying evidence for engineering decisions.
