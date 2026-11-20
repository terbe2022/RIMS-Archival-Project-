# Synthetic accessions for Gauri

This package is a byte-for-byte copy of the invented test data from `tayler-erbe/archivist-data` at commit `d7a3ed2884b15cb21bac6f3488dc21ec69412801`. It is now available in the shared project; access to Tayler's other GitHub account is unnecessary. [PROVENANCE.json](PROVENANCE.json) records all 403 source files and their hashes. The original repository remains intact.

## Start without compute

1. Read the [dataset overview](README.md) and [label definitions](labels/LABEL_SCHEMA.md).
2. Compare [research intake 001](intake/ACC-SYN-2026-001.json) with [teaching/service intake 001-B](intake/ACC-SYN-2026-001-B.json). Both describe the same 228-file [faculty desktop](corpus/Achterberg_Desktop), with different appraisal priorities.
3. Review [administrative intake 002](intake/ACC-SYN-2026-002.json) alongside its 143-file [office share](corpus/ADAP_Office_Share).
4. Select a small set of files and document the expected routing, sensitivity evidence and relevance rationale before running a model. No GPU is needed to inspect the fixtures, forms or label tables.

The [two-form comparison table](labels/ACC-SYN-2026-001/ground_truth_formB.csv) records 149 changed relevance categories. These are **machine-authored, unreviewed reference labels**, despite the upstream filenames saying `ground_truth`. They are starting hypotheses for Gauri and Joanne to review, not an approved archival gold set, retention policy or evidence of model quality. `exclude_duplicate` and other action labels never authorize automatic deletion.

## Download and use

From this GitHub branch, choose **Code → Download ZIP** for the shared repository. Alternatively, clone the shared repository and check out the exact commit recorded for the experiment. Use Linux, macOS or WSL for the complete corpus: deeply nested paths and nested archives include Windows compatibility test cases. Do not rename files or normalize line endings; these bytes are intentional test evidence.

Inside `validation/synthetic-accessions`, run `python verify_dataset.py` to verify all imported files. The prebuilt fixtures are ready to inspect; **do not run the generators just to use them**. Rebuilding needs additional tools and can change timestamps and byte hashes.

Supply **only** the selected `corpus/` folder and matching `intake/` JSON to a runner. Never provide `labels/`, reference descriptions, provenance or generator source to the model under test. Keep evaluation answers separate from model inputs. Intake `source_folder` paths are relative to this package, so resolve them from this directory when integrating a runner. This transfer does not add an end-to-end runner or establish that the current pipeline accepts every format.

Record the shared repository commit, intake filename, source-relative file paths, model revision, prompt and settings with every experiment. Keep the original reference labels unchanged; put reviewed corrections and results in a separate experiment record.

## Boundaries and test cases

- All people, identifiers, documents and credential-like strings are invented. Real accession data remains subject to the project's existing infrastructure restrictions.
- The dataset deliberately includes corrupt/encrypted files, fake phishing, executable-looking samples and a high-compression ZIP probe that expands to about 200 MB. Do not execute corpus files or recursively unpack everything. Test archive handling with size, ratio and depth limits.
- Images are procedural illustrations and speech is synthesized. There are no genuine PST or MSG fixtures; changing a text file's extension does not produce either format.
- The upstream [design notes](docs/PIPELINE_DESIGN_NOTES.md) contain proposals, not proof of implemented behavior. The comparison of forms 001/001-B holds descriptive context constant and changes appraisal criteria. Other descriptive-context changes may require regenerating descriptions.
- Downloading this package does not grant server/API access, allocate a GPU or authorize paid model calls.
