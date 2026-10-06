# RIMS — Current Project Status

This document captures working status and priorities. It is expected to change more frequently than AGENTS.md.

## Working system
A working pipeline has run against 2,375 real files across three accessions with a review interface. CPU processing covers crawl/hash, content-signature format identification, exclusions, appraisal rules, seven-lane routing, text extraction, identifier detection, Dublin Core metadata, and evidence-based ranking. Description and two-tier redaction are implemented.

## Engineering work that can proceed
- Fix Publish & export buttons.
- Correct the Search dataset filter: a public/discovery view should not default to undecided material.
- Re-run image sensitivity/classification through the evidence gate; legacy image flags predate the gate.
- Build useful folder- and collection-level synthesis beyond counts/subject terms.
- Port email threading from POC 1.

## Engineering blocked by dependencies
- OCR: host lacks Tesseract; sysadmin assistance is required. Vision fallback has not been adequate.
- Semantic search UI: offline TF-IDF/SVD fallback exists; MiniLM/model availability on the host remains a dependency.
- Click-through to originals: requires a hosting/serving decision.
- Write-back to Medusa, ArchivesSpace, and Digital Library: handoff contract is undecided.
- Production authentication/identity and durable multi-user decision storage remain unresolved.

## Validation / policy gap
The appraisal rules have not yet been ratified by Archives, and there is no labelled gold set. Therefore accuracy claims are not yet established.

Proposed gold-set exercise: 50 files, independently labelled by two archivists, with inter-rater agreement measured.

## Immediate validation program
1. Model comparison on synthetic fixtures.
2. Context-block ablation: same files/model with and without intake context.
3. Gold-set and end-to-end pipeline validation, including ranking, retained_by_association, folder threshold behavior, sensitivity/identifier detection, false positives, and false negatives.

## Important known lessons
Past defects included ZIP+4 being interpreted as SSN-like data, descriptions being merged after scoring, contradictory rationale fields, dead UI handlers, undefined flag rendering, hidden decision controls, misleading release-version comparison, and unsupported image sensitivity claims. Validation should test artifacts and behavior, not only aggregate counts.

A particularly important evidence-gate lesson: sensitivity claims should contain locatable/checkable evidence rather than an unfalsifiable label.
