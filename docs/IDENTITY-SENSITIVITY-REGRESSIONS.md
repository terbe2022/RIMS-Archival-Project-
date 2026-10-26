# File identity and sensitivity regression results

October 26, 2026. Synthetic component tests only; no original accession data,
model calls, server deployment or live-site changes.

Gauri reported possible wrong-file assignments, folder association leakage and
sensitivity evidence/filtering gaps. The tests reproduce those boundaries and
exercise the repairs independently of GPU availability.

## Before and after

Against main at `d16161ca613774167e7d3ca03d69c87ae2bc35f8`, the 16 new tests
produced 10 failures and four errors (missing evidence fields), with two existing
compatibility cases passing. After repair, all 16 pass. All 18 existing tests
also pass, for 34 total. Both HTML files' inline scripts compile with Node.

Run from a checkout with pandas, pyarrow, requests and Pillow installed, and
Node on PATH:

```sh
python -B -m unittest discover -s tests -p test_identity_sensitivity.py -v
python -B -m unittest discover -s tests -v
```

## Changes tested

- Image results use an explicit file UID first. Otherwise an exact source or
  accession-relative path must identify one file. Bare legacy filenames work
  only when unique. An unknown explicit UID or a wrong full path cannot fall
  back to a filename. Ambiguous matches are skipped and counted, never copied
  to every same-named file. Optional accession identity further scopes matches.
- Folder associations use accession UID plus the complete normalized parent
  path. Missing identity does not establish a shared folder. Association within
  a genuine common folder still works and retains its separate rationale.
- Vision evidence stays in the existing sensitivity JSON column. PII evidence
  retains start/end offsets relative to original extracted text, detector and
  confidence, without embedding identifier values. These offsets do not refer
  to shortened snippets, redacted text or original PDF page coordinates.
- Private review/workbench exports retain evidence. Public exports do not gain
  evidence excerpts or PII spans. The protected prototype carries complete
  sensitivity categories separately from its shortened display badges.
- Both frontend sources recognize all nine vision categories. The Pages bulk
  selection and release paths withhold flagged records; the legacy workbench
  bulk actions and release export also check sensitivity. Explicit machine
  sensitivity fields withhold even unfamiliar future category labels.

## Boundaries and migration

These tests establish component behavior, not deployed end-to-end acceptance or
archival model accuracy. PR #79 remains separate; these changes do not require
merging that older branch wholesale.

Existing misassignments or missing evidence need a controlled re-import from
preserved outputs and original metadata where available. Information already
dropped cannot be recovered from an incomplete manifest alone. New private
payload fields are evidence transport, not a completed evidence-viewer UI.

Legacy results with relocated full paths and no stable file IDs now require an
explicit identity reconciliation; the importer does not guess their new root.
Hashes and version comparison remain separate review work. No files are
deduplicated, moved or deleted by these repairs.
