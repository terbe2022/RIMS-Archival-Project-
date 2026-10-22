# Outstanding questions — October 22, 2026

This replaces the October 21 remaining-question list. The August answers remain preserved. Sources are Tayler’s supplied clarifications and the supplied October 21 Gauri/Joanne email. Earlier assistant suggestions quoted in those notes are not independent verification.

## Immediate follow-ups

- **Joanne and Gauri — walk through intake:** Use one or two representative accessions. Identify published taxonomies, local terms, examples that should and should not trigger flags, and the desired archivist action. Gauri starts with intake, then output/export; Tayler supports integration.
- **Joanne — review capacity and starting accessions:** Estimate time to review a realistic flagged queue and identify the first three or four accessions. These help plan testing; they do not block drafting the workflow.
- **Tracy Popp — show us incoming metadata:** Which tools produce it? Provide a safe example/schema, file identifiers and checks already performed. DROID remains unconfirmed. We can build our metadata independently while preserving hers.
- **Gauri, Tayler and destination owners — show us the package Medusa needs:** Draft the master table and package, then confirm required fields, hierarchy, identifiers and transfer route. Map preservation, description and discovery separately; do not assume four identical uploads.

## Questions Joanne has asked us

These are for Tayler and Gauri to answer, not another questionnaire for Joanne:

- Why compare alternatives with the original POC models? How much is driven by compute availability?
- List the specific processing tasks for documents, email and images, and explain how model outputs connect within the workflow.
- Where did the 54 synthetic fixtures come from? Show actual empty and truncated examples.
- Define processing time, efficiency, parsing, required-field validity, description-contract validity and abstention separately.
- Identify the application components consuming results, distinguish observed failures from anticipated integration problems, and show what an archivist would have to correct.
- Can published taxonomies be retrieved from a web/server source and referenced? Selection/retrieval is separate from local keywords. Implementation is unverified.

Reported Qwen results are 100% parsing, 55.3% required-field validity, 14.8% description-contract validity and 50% expected abstention. Do not collapse these into one schema metric or treat abstention failures as a verified fabrication rate. Raw ZIP verification and full factual review remain outstanding. Empty-text image-labelled fixtures do not test vision.

## File intake, review and export — intended design

These are requirements to design and test, not claims of completed functionality:

1. Inventory a source folder and its nested files, preserving structure and exact original paths. Generate the metadata this tool needs independently of upstream metadata.
2. Preserve Tracy Popp’s supplied table separately from our generated table. Join through stable file IDs, original paths and her identifiers when available. Paths alone are not globally unique. Her current metadata tool remains unconfirmed.
3. Show title, summary, model recommendation and explanation, with original inspection where supported. Filter by priority and recommendation reason; inspect and save batch decisions. Drafts, personal material and unrelated research are contextual review examples, never automatic discard rules. Sensitivity outranks ranking. Valuable/exclude appraisal criteria stay out of description prompts.
4. Require explicit Keep, Do not keep, or Defer / further review for every file before export. An unchecked file blocks export; Defer is an explicit decision.
5. Produce three disposition folders preserving hierarchy/context, plus CSV or Excel metadata containing model labels/explanations, human decisions, identifiers and original/export locations. Do not keep never executes deletion. Copy versus move remains unresolved; no source-moving operation is authorized here.
6. Box is a proposed handoff option pending capacity/access arrangements. Build destination mappings rather than assuming all systems accept the same spreadsheet or require separate uploads.

## Deferred or internal work

- **Researcher email access:** Future scope decision. Preserve open/restricted designations in current review/export. A workstation and a browser are not mutually exclusive.
- **Donor restrictions:** Optional intake fields for an agreement reference and handling instructions, carried into review/export. Keep the agreement in its existing repository. Rarity is Tayler’s recalled meeting clarification, not a new written answer from Joanne. Automatic interpretation/enforcement is undefined.
- **PII mapping and working-copy controls:** Tayler, Brent and storage owners handle location, readers, encryption and clearing rules. These remain operational dependencies, not Joanne’s immediate questions. Redaction/pseudonymization and summarization are different outputs; neither establishes storage authorization.
- **Confidentiality process:** Status unverified. Tayler/Brent should check the template and access process internally, rather than ask Joanne again without evidence it is still missing.
- **Workload:** Gather counts and format proportions during controlled inventory/performance planning. No broad software/workload questionnaire is needed to start design. Image-specific details await Tayler’s further follow-up.

## Publicly documented Library systems

Official sources checked October 22, 2026:

- [Archives Holdings Database](https://archon.library.illinois.edu/archives/): Archon collection descriptions and digital-material records. Historical ArchivesSpace wording is not proof of a migration.
- [Digital Library](https://www.library.illinois.edu/digital-strategies/digital-library/): Access to digitized and born-digital collections, including folder/file browsing; its page identifies Kumquat. [Carl Woese example](https://digital.library.illinois.edu/collections/cd535a80-4852-0133-a7fd-0050569601ca-3).
- [Medusa](https://www.library.illinois.edu/digital-strategies/medusa-digital-preservation-repository/): Preservation management with an approved-user registry. Working preservation target; exact import requirements need confirmation.
- [Digital Collections Search Gateway](https://www.library.illinois.edu/digital-strategies/digital-collections-search-gateway/): A discovery index across collections and repositories, not necessarily a fourth upload destination.

These public roles narrow the question to incoming metadata and outgoing package requirements. They do not establish Tracy’s current software or compatibility of an untested export.

[Original August answers](answers-2026-08.md) · [October 21 source review](answer-reconciliation-2026-10-21.md)
