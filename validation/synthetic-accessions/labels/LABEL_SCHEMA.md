# Ground-truth label schema

One record per file on disk, plus one per labelled member inside a container (mbox
message, ZIP/tar member). Files are `ground_truth.csv` (lists joined with `;`) and
`ground_truth.jsonl` (lists as arrays). Labels were written **when each file was
created, for the purpose it was created for**. They are not inferred after the fact.

| Field | Meaning |
|---|---|
| `path` | Path relative to `corpus/`. Container members use `<container path>::<member>`; nested containers chain `::`. mbox members use their `Message-ID`. |
| `relevance` | `high` / `moderate` / `low` / `none`, judged against that accession's intake form (see definitions below). For the alternate form, `ground_truth_formB.csv` has `relevance_A`, `relevance_B`, `relevance_rationale_B` and `changed`. |
| `relevance_rationale` | The intake clause (or exclusion) that decides it, in words. Use it to check that a model's explanation cites the right reason. |
| `sensitivity` | Zero or more of: `none`, `pii_contact`, `pii_ssn`, `ferpa_student`, `hr_personnel`, `medical`, `financial_personal`, `confidential_peer_review`, `sensitive_location`, `credentials`, `minor_child`. These are independent of relevance: high-value files can be sensitive. |
| `lane` | Expected processing lane: `document`, `tabular`, `image`, `av`, `email`, `code`, `scientific`, `geospatial`, `database`, `archive`, `system`, `unknown`. |
| `expected_action` | `appraise`, `exclude_system_file`, `exclude_duplicate`, `review_near_duplicate`, `expand_container`, `route_human_corrupt`, `route_human_encrypted`, `route_human_unidentified`, `restrict_sensitive`. None of these mean delete (no autonomous deletion). |
| `gt_title`, `gt_summary`, `gt_keywords` | Reference description for grading generated titles and summaries. A reference, not the only acceptable wording. |
| `tags` | Edge-case tags, e.g. `misleading_extension`, `no_extension`, `scanned_image_pdf`, `needs_ocr`, `exif_gps`, `near_duplicate`, `duplicate_exact`, `large_file`, `encrypted`, `nested_archive`, `audio_speech`, `non_utf8_encoding`, `deep_nesting`, `system_file`. |
| `true_format` | What the bytes really are (useful when the extension lies). |
| `difficulty` | `obvious`, `subtle` (needs content, not the filename), `ambiguous` (reasonable reviewers could disagree; a model should hedge). |
| `duplicate_of` | For exact duplicates, the path of the copy to keep. |
| `container` | For members, the container file's path. |
| `size_bytes`, `sha256`, `extension`, `nominal_date` | Technical facts; `nominal_date` is when the content belongs, not the file mtime (Git does not keep mtimes). |

## Relevance definitions

- **high:** squarely matches a `valuable` clause: survey data, field records, specimen images, analysis code and figures, drafts and reviews, grant documents, substantive correspondence, GIS, talks, oral history, CV.
- **moderate:** documents her career, outreach or the research context, but is not the research record itself. Examples: annotated reprints, outreach talks, a representative syllabus, service that applies her findings, logistics of her own talks, side projects at survey sites.
- **low:** falls under an `exclude` clause or is restricted with only marginal research value. Examples: unannotated on-topic reprints, run logs, routine survey logistics, confidential reviews, personnel files, travel confirmations.
- **none:** no relevance to the university-work record. Examples: system files, installers, personal or household material, spam, phishing, routine notices, and near-miss items (a bee movie script, beekeeping catalog, garden plan).

Duplicates carry the same relevance as the original. The `expected_action` of `exclude_duplicate` says what to do with them.

Relevance and access are separate decisions. A `high` file with `sensitive_location` is kept *and* restricted. Sensitivity outranks ranking: it changes release level, never reduces relevance.
