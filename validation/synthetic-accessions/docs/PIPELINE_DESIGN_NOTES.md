# When should the intake form touch the pipeline?

The design question: build the **contextual layer** first (title, description,
metadata, summary, folder context for every file) and then run AI relevance on
top of it? Or pass the intake form while the contextual layer is being built?

## Recommendation: split the form, don't choose one side

The intake form holds two kinds of fields. The project already separates them
(`docs/history/docs/ai-and-the-accession-form.md`, AGENTS.md invariant 3):

| Fields | Use while building context? | Use in the relevance pass? |
|---|---|---|
| `source`, `owner`, `role`, `scope`, `research`, `bio` (descriptive) | **Yes** | Yes |
| `valuable`, `exclude` (appraisal criteria) | **No** | **Yes**, clause by clause |
| `access` (sensitivity) | Yes, but only to choose which detectors run | It can raise the restriction level, never lower relevance |

So the pipeline should run in this order:

1. **Context layer (form-light).** Inventory, identify, extract, downsample and describe each
   file, using only the descriptive fields as background. Knowing this is an entomologist's lab
   computer turns "a line chart" into "bee species richness vs. years since restoration". It
   doesn't tell the model what to look for.
2. **Relevance layer (form-aware).** Score each description against each `valuable` / `exclude`
   clause, quote the winning clause, apply rule precedence (sensitivity → rule → content →
   proximity), and mark association-based retention explicitly.
3. **Review.** Show the archivist the rank, the deciding clause and the evidence span, sorted
   so the most confident calls in each direction are easiest to confirm in bulk.

### Why not give the criteria to the description model?

- **It marks its own homework.** Tell a describer "she values referee reports" and it will
  describe ambiguous documents as referee reports. Scoring that description against the same
  sentence then measures the prompt, not the file. In this corpus, `misc_data.xlsx`, the
  whiteboard photo and `Downloads/Achterberg_etal_2021_JPE (1).pdf` are where this would show.
- **Reuse.** The expensive work (OCR, transcription, vision, long-document summaries) is done
  once. If the archivist edits the form, only the cheap relevance pass reruns. A second form for
  the same folder (for example a teaching-history collection) reuses the whole context layer.
- **Auditability.** A description that doesn't depend on the criteria can be checked on its own
  against the file. That's the separation POC 3 showed was needed (LLaVA described correctly
  but judged wrong).

### Where the form *can* help during context building: scheduling, not wording

Use `valuable` / `exclude` to decide **how much effort** a file gets, never **what it says**. Examples:

- Spend full OCR and transcription on folders whose cheap, metadata-only score is high.
- Downsample hard in folders that look like system files or personal media.
- Run the access-driven detectors (GPS in EXIF, SSN patterns, coordinates in CSV/GPX) everywhere.

This is a triage budget. Every file still gets a description, and nothing is skipped without a record.

## Testing the choice with this corpus

Treat it as an experiment rather than a debate. Run three configurations on
`corpus/Achterberg_Desktop` with the same model and settings:

| Run | Description prompt gets | Relevance pass gets |
|---|---|---|
| A | nothing (generic) | full form |
| B | descriptive fields only (recommended) | full form |
| C | full form including valuable/exclude | full form |

Compare on `labels/ACC-SYN-2026-001/ground_truth.csv`:

- Relevance confusion matrix, reported separately for `obvious` / `subtle` / `ambiguous`.
  C should look best on `ambiguous` items. Check whether its descriptions of those items are
  still faithful to the file; inflated agreement there is the warning sign.
- False negatives on `high` (the costly error) and on `sensitivity`.
- Description accuracy against `gt_summary`, using the EVALUATION.md rubric with blind grading.
- The rationale should cite the clause named in `relevance_rationale`.

If C beats B on ambiguous files *without* losing description faithfulness, that's evidence to
revisit the rule. Until then, B is the default.

## Large files and downsampling

The corpus contains files that only work if pre-processing is size-aware:

- the 45 MB panorama TIFF
- the 47 MB datalogger CSV
- the 3-minute, mostly silent recording
- the ~1000:1 ZIP
- with `make_large_files.py`, multi-GB CSV, TIFF and MP4 files

Recommended handling:

| Content | Handling |
|---|---|
| Images | Read the header first. Downsample to the model's input size before decoding the full raster (`Image.draft` / tile reads). Keep EXIF. |
| Tables | Stream. Profile the schema, row count, ranges and a stratified sample of rows. Don't load the whole file. |
| Audio/video | Probe the duration. Sample keyframes and voice-active segments. Transcribe the speech, not the silence. |
| Archives | Check the expansion ratio and total size before extracting, with a depth limit. Record each member as its own manifest row with a parent link. |

## Folder context

`labels/ACC-SYN-2026-001/folder_labels.csv` gives reference summaries for 35 folders. A folder rollup
should combine child descriptions bottom-up (file → folder → parent).

Proximity evidence must stay visible as `retained_by_association`. The 14-level "New Folder (2)"
chain and `LabDrive_copy/instrument/` (unidentifiable binaries whose only signal is where they
sit) test that.

## The two-form test (now built)

`intake/ACC-SYN-2026-001-B.json` appraises the same folder for a department history
project covering teaching, mentoring, service and outreach.
`labels/ACC-SYN-2026-001/ground_truth_formB.csv` gives `relevance_A`, `relevance_B` and the form-B
rationale for every file. 149 of 228 files change relevance; for example, 99 go high→low and
11 go low→high.

Run the pipeline twice, once per form, and check:

1. **Descriptions don't change.** Titles and summaries should be identical, or nearly so, across
   the two runs if the description step only sees the descriptive fields. Drift means appraisal
   criteria are leaking into description.
2. **Relevance does change.** Per-file agreement with `relevance_A` in run A and with `relevance_B`
   in run B. A model that ranks the raw bee data high under both forms is ranking on the file,
   not on the form.
3. **Rationales cite the right form.** Run B's rationale should quote teaching, service or
   outreach clauses, not research ones.
