# Synthetic labelled accessions for the Archival Accession Processing Tool

Fully synthetic test accessions for the RIMS archival pipeline. Each is a realistic folder
you point the pipeline at, with an intake form and a ground-truth label for every file,
so a run can be **scored** instead of eyeballed.

> **Everything here is invented.** People, offices, sites, grant numbers, emails (`*.example.*`),
> phone numbers (555-01xx), SSNs (900-series, never issued), student IDs, salaries, passwords
> and API keys are fake.

**Never give `labels/` to the pipeline under test.** Labels are the answer key.

## The test sets

| Intake form | Folder | Files | What it tests |
|---|---|---|---|
| `ACC-SYN-2026-001` | `corpus/Achterberg_Desktop` | 228 (+23 inside containers), ~123 MB | Personal papers: a retired entomologist's whole desktop. Every lane and file type, edge cases, large files, sensitive locations. |
| `ACC-SYN-2026-001-B` | the **same** folder | same 228 | A second form (department teaching, mentoring, service and outreach history). 149 files change relevance. Checks that relevance follows the form, not the file. |
| `ACC-SYN-2026-002` | `corpus/ADAP_Office_Share` | 143 (+12 inside a ZIP), ~5 MB | Administrative records: an associate dean's office shared drive. Covers final vs superseded drafts, committee minutes, retention-eligible transactions, heavy duplication, sync conflicts, personnel and FERPA restrictions. |

### Relevance distribution (top-level files)

| | high | moderate | low | none |
|---|---|---|---|---|
| 001 (research form) | 118 | 34 | 25 | 51 |
| 001-B (teaching/service form) | 35 | 15 | 129 | 49 |
| 002 (administrative) | 85 | 16 | 16 | 26 |

## Repo layout

| Path | Contents |
|---|---|
| `intake/` | The three intake forms, in the exact `IntakeForm` schema from `src/workbench/intake.py` |
| `corpus/` | The folders to process |
| `labels/ACC-SYN-2026-001/` | `ground_truth.csv/.jsonl`, `folder_labels.csv`, `summary_stats.json`, plus `ground_truth_formB.csv` and `summary_stats_formB.json` for the second form |
| `labels/ACC-SYN-2026-002/` | `ground_truth.csv/.jsonl`, `folder_labels.csv`, `summary_stats.json` |
| `labels/LABEL_SCHEMA.md` | Field definitions and the high/moderate/low/none definitions |
| `generator/` | Deterministic generators (`build.py` builds everything; `make_large_files.py` writes multi-GB stress files on demand) |
| `docs/PIPELINE_DESIGN_NOTES.md` | When the intake form should touch the pipeline, plus the two-form and three-configuration tests |

Every label row has the following fields:

- relevance and the intake clause that decides it
- sensitivity
- expected lane and action (appraise, exclude as a system file or duplicate, review a near-duplicate, expand a container, route to a person, restrict)
- reference title, summary and keywords
- difficulty: `obvious`, `subtle` (needs content, not the filename) or `ambiguous` (reasonable archivists could disagree)
- edge-case tags

## ACC-SYN-2026-001: Achterberg Pollinator Ecology Lab desktop

### Scenario

Professor Miriam K. Achterberg retired in 2024. Her lab ran the **Prairie Bee Survey** (2016–2022): wild bees on nine restored prairies of different ages plus one never-plowed remnant on a private farm. The finding is actually in the generated data: richness recovers in about 10 years, ground-nesting specialists lag, and bare ground predicts their recovery. The remnant hosts the endangered rusty patched bumble bee, so its location is sensitive throughout.

### Coverage

About 70 extensions across every lane. Highlights:

- **Email:**
  - 38 `.eml` files plus a 12-message `.mbox`
  - attachments
  - a forwarded chain to split into messages
  - HTML-only spam and phishing
  - an ISO-8859-1 German message
- **Office files and text:**
  - modern Office formats: DOCX, XLSX and PPTX
  - legacy Office formats: DOC, XLS and PPT
  - other text formats: ODT, RTF, LaTeX, BibTeX, RIS, HTML, MHTML, vCard, iCalendar
  - text-encoding cases: Windows-1252 and UTF-16
- **PDF:**
  - mixed text, charts and tables
  - image-only scans needing OCR (handwritten notebook, a form containing an SSN)
  - an encrypted PDF
  - a truncated PDF
  - annotated reprints
- **Images:**
  - JPEG with EXIF date and GPS
  - near-duplicate bursts
  - TIFF masters with derivatives
  - a multi-page TIFF with no extension
  - a 45 MB panorama
  - GIF, BMP, EPS, SVG, WebP and transparent PNG
  - text-in-image cases: a screenshot and a whiteboard photo
- **Audio and video:**
  - speech recordings for transcription: an oral-history WAV and its MP3, an M4A voice memo, a voicemail
  - a narrated MP4
  - a silent MOV
  - a 3-minute, mostly silent recording
  - a WebM
- **Data and code:**
  - CSV (including a 47 MB file), Parquet, SQLite, HDF5, MATLAB `.mat`, NumPy `.npy`, FASTA, EML XML metadata
  - GIS: GeoJSON, a shapefile set, KML, GPX
  - code: R, R Markdown, Python, SQL, Jupyter, YAML, a `.env` file with fake credentials, a `.pyc` cache file
- **Containers:**
  - ZIP
  - a tar.gz containing a nested ZIP, a symlink and a Windows-illegal filename
  - a password-protected ZIP
  - 7z and gz
  - a compression-bomb probe
- **Junk and trick files:**
  - OS files: `.DS_Store`, `Thumbs.db`, `desktop.ini`
  - lock files, installers and shortcuts
  - zero-byte files
  - mangled, missing or misleading extensions
  - 14-level nesting
  - unicode and over-long filenames

## ACC-SYN-2026-001-B: same desktop, different purpose

The department, not the Archives, appraises the same transfer for its history project. Teaching, mentoring, lab life, service, outreach and career records become valuable. The research record goes to the research accession, so most of it becomes low.

Examples:

- Syllabi and lectures go up: moderate/low → high.
- The confidential promotion review she wrote goes low → high, as service (still restricted).
- Raw survey data and analysis code go high → low.

Sensitivity, lane, action and reference descriptions are unchanged: only relevance depends on the form.

## ACC-SYN-2026-002: Associate Dean for Academic Programs office share

The fictional Office of the Associate Dean for Academic Programs (College of Agricultural and Environmental Sciences, 2012–2023) was merged into another office in 2024, and its shared drive went to the Archives.

What it contains, and what each part tests:

- **Policy versions:** an academic integrity policy series in which v2 is a significant change (high) and v3 is wording only (low, superseded). An approved final and a 2021 revision, a OneDrive conflict copy with a one-word difference, a legacy `.doc` policy, and a website copy.
- **Committee records:** Curriculum Committee agendas and minutes for 2014–2023 (some only as signed scans), with approved and rejected proposals, including a rejected cannabis course. A ZIP duplicates the 2014–2016 records.
- **Planning and reporting:** a program review (self-study with charts, external report, response) and accreditation records (narrative, evidence index, a scanned TIFF letter). The strategic plan comes with five drafts (two significant), the final, town-hall slides, a town-hall recording with speech, aggregated survey results, and restricted raw responses with names. Annual reports run 2013–2022.
- **COVID-19 response:** faculty FAQ, course modality tracker, readiness survey with chart, a Teams chat export mixing key decisions with chatter, and a hand-sanitizer purchase order that is none even inside a high folder.
- **Data:** aggregated enrollment and outcomes (high). A student-level extract with IDs (FERPA, low). A Tableau definition, a legacy `.xls` and a "Copy of Copy of" duplicate.
- **Restricted and routine:**
  - personnel: search CVs, scoring, offer letter, salaries, a grievance
  - student petitions and integrity cases
  - purchase orders, travel vouchers, room bookings and catering past retention (tag `retention_eligible`)
  - blank templates and letterhead
- **Staff folders:** duplicate policies, a personal resume and vacation photo, and a coordinator's notes recording a 5–3 vote split that the official minutes omit (ambiguous).

## Using it

```bash
# rebuild everything (needs: reportlab, python-docx, python-pptx, openpyxl, matplotlib, pillow,
# numpy, h5py, scipy, pyarrow, pyshp, nbformat; libreoffice, ffmpeg, espeak-ng, zip, 7z)
python3 generator/build.py            # or: build.py 001 / build.py 002

# optional multi-GB stress files inside ACC-SYN-2026-001 (git-ignored)
python3 generator/make_large_files.py --size-gb 2
```

To run the pipeline, point `source_folder` at the corpus folder and submit the matching intake JSON. To score a run, join the manifest to the label CSV on the corpus-relative path and compare:

- relevance (confusion matrix by `difficulty`)
- sensitivity recall
- `expected_action` and `lane`
- titles and summaries against the reference fields

For 001 versus 001-B, also check that descriptions stay the same while relevance changes (see the design notes).

**Gaps not generated** (no writer available): `.pst`, `.msg`, `.mdb`, camera RAW, HEIC, CAD and point clouds. Images are procedural illustrations, not photographs, and the speech is synthesized.

**Git note:** `.gitattributes` keeps corpus bytes exact (no line-ending conversion). Clone on Linux, macOS or WSL.
