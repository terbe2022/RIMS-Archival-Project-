# Data and prototype guide

Updated October 8, 2026. Application code and public guidance live in [RIMS-Archival-Project-](https://github.com/terbe2022/RIMS-Archival-Project-). Selected original inputs, recorded output and the detailed inventory live in [private RIMS-data](https://github.com/terbe2022/RIMS-data). Access to the website, Teams agent and private repository are separate permissions.

## Which input belongs to which prototype?

| Interface or experiment | Required input | Availability and limits |
| --- | --- | --- |
| Accession workbench (`accession-workbench.html`) | `prototype-data.json`, with `jobs` and `records` | Private `data/prototype-data.json.gz` decompresses to this export: 2,375 metadata records, four jobs and 481 existing review decisions. It supports metadata browsing and review; it contains no original bodies, thumbnails or full-size images. |
| Prepared protected accession website | Authenticated serving of the same metadata snapshot | Private repository access does not connect the website automatically. Hosting, authentication and live data access must be verified separately. Do not publish this snapshot as a static website asset. |
| Earlier file-search workbench (`workbench.html`) | Its own `workbench-data.json` export | This export was not found in the transferred server files. The accession JSON is not a drop-in substitute. Raw files support rebuilding extraction/search experiments, but do not supply a ready-made search index. |
| Earlier review screen (`review.html`) | Its own `review-data.json` export | This export was not found in the transferred server files. Review packets and decisions are separate artifacts; the accession snapshot does not establish this screen's data contract. |
| Current pipeline/model validation | Original files from `rims-raw-sample.tar.gz` | Private release contains 2,375 sample files plus a sample manifest. Use file-type routing, extraction, OCR, vision and email processing as appropriate. These are inputs, not expected answers. |
| Historical POC 1: email | Historical email corpus and notebook intermediates | Current raw sample includes email files, but is not confirmed to be the historical POC corpus. Do not reuse historical counts as present results. |
| Historical POC 2: heterogeneous-file search | Historical Box corpus, extraction outputs and embeddings/index | Current raw sample includes mixed formats, but is not confirmed to reproduce that corpus or its search index. |
| Historical POC 3: image classification | Historical TIFF evaluation corpus | Current raw sample includes JPEG images; it is not the historical 1,000-TIFF evaluation set or full image backlog. |
| Synthetic-first onboarding/Colab notebooks | Synthetic fixtures defined by the validation kit | Separate from original archival data. Private GitHub access does not authorize uploading originals into Colab or a hosted model service. |
| Public project overview | Public documentation only | Does not require either private dataset. |

## Download the right item

1. Accept collaborator access to RIMS-data using your own GitHub account.
2. Clone RIMS-data for its scripts, metadata snapshot and documentation. Run `python scripts/load_dataset.py` to verify the metadata snapshot.
3. For original inputs, download **rims-raw-sample.tar.gz** from the [private release](https://github.com/terbe2022/RIMS-data/releases/tag/raw-sample-2026-10-08). A clone or source ZIP does not include release attachments.
4. Follow [private raw-data instructions](https://github.com/terbe2022/RIMS-data/blob/main/docs/RAW-DATA.md). Verify the checksum and extract in Linux/WSL with Python 3.12 or newer; some preserved filenames are incompatible with Windows.
5. Use the private inventory and [validation routes](https://github.com/terbe2022/RIMS-data/blob/main/docs/VALIDATION-ROUTES.md) to select a reviewed subset. Record dataset checksum, code commit, model settings and run environment.

## Keep inputs, outputs and reference answers distinct

- Raw archive: original sample inputs for rerunning processing.
- Metadata snapshot: existing descriptions, flags and saved review decisions from a prior export. Recorded output is not independently validated ground truth.
- Raw-file inventory: complete index and per-file hashes, not scoring labels. Its IDs are not yet verified joins to metadata record IDs.
- Sample manifest: 2,148 rows, fewer than the 2,375 physical sample files. It is neither a complete inventory nor an answer key.
- New experiment output: save separately from the baseline, with provenance. Keep original values and restricted results private.
- Reference answers and acceptance thresholds: still need human review and agreement before claims about model accuracy or the best model.

The matching raw-file and metadata counts do not prove a one-to-one correspondence. Email attachments can create additional processing units. This transfer is a selected server sample, not every upstream collection, historical POC corpus or operational run artifact.

## Storage and publication boundary

Keep RIMS-data and its release private. Public RIMS-Archival-Project- holds code, synthetic/public demonstration data and guidance, not this original dataset. Private data must be served through authenticated access; a private repository does not protect copies placed in public GitHub Pages assets. Original-data testing uses an approved environment. Synthetic examples remain the default for external/cloud onboarding.
