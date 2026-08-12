# File Type Coverage — What POC 2 Handled, What It Didn't, and How to Close the Gaps

> **Update, 12 Aug 2026 — the Archives has told us the actual format mix.**
> Answer 1.7: `.xls` `.doc` `.pdf` `.txt` `.csv` `.mov` `.jpg` `.mp4` `.eml` `.pst`.
> Five lanes cover it — document, tabular, image, av, email — and those should be built first.
> Two consequences for what follows: **`.pst` and `.eml` are inside personal-papers accessions**,
> so email is main-line rather than a later phase; and specialist scientific and geospatial
> formats are the tail rather than the body, so they should **route to human attention rather
> than fail**. Answer 8.4 confirms the disciplines are represented, but the list above is
> office-typical.
> See [`../stakeholders/answers-2026-08.md`](../stakeholders/answers-2026-08.md).


Derived from `Working_Scratch_for_Archiving_Work.ipynb`, the Box SDK notebooks, and the
progress-update document's own file-type table.

---

## 1. Handled in POC 2

| Formats | Method used | Carry forward? |
|---|---|---|
| `.pdf` (+ mangled variants `pdf1`, `pdf3`, `pd`) | PyPDF2, cleaned with `re` + `unicodedata` | Replace PyPDF2 → `pypdf` or `pdfplumber`. PyPDF2 is deprecated and weak on layout. |
| `.jpg .png .gif .tif .eps` | llava-llama3 via Ollama, batched | Yes, but swap model. `.eps` needs Ghostscript — PIL handles it poorly. |
| `.doc .docx` (+ `doc1 doc2 doc5 do`) | python-docx; win32com fallback | **Replace COM** with LibreOffice headless or Tika |
| `.xls .xlsx xls2` | win32com — sheet names, column headers, first 10 rows | **Replace COM** with `openpyxl` / `pandas` / `xlrd2`. Schema-only approach is correct. |
| `.ppt .pptx ppt1` | python-pptx; win32com fallback | **Replace COM**. Some outputs were truncated. |
| `.html .htm .mhtml .mht` | BeautifulSoup visible-text extraction | Yes. `.mhtml` needs the `email` module first to unwrap MIME. |
| `.rtf` | `striprtf` | Yes, works fine |
| `.txt` | direct read | Add encoding detection (`charset-normalizer`) — legacy drives have CP1252, Latin-1, UTF-16 |
| `.zip` | `zipfile` extraction | Yes — but add recursion depth limit and zip-bomb guard |

---

## 2. Not handled — with remediation

### Explicitly deferred in POC 2

| Format | POC 2 status | How to close it |
|---|---|---|
| `.eml`, `.mbox` | "Not fully processed due to size" | The email pipeline exists in POC 1. Integration is the work, not invention. Use `mailbox` for mbox, `email` stdlib for eml. |
| `.mdb` | Never processed | `mdbtools` (`mdb-tables`, `mdb-schema`, `mdb-export`) on Linux — no Access install needed. Extract table names + schema + row counts; that's usually enough to appraise. |
| `.db`, `.sqlite`, `.sqlite3` | Never processed | `sqlite3` stdlib. Same approach: schema, table names, row counts, sample rows. Trivially cheap. |
| `.mov` and video generally | Skipped for time | `ffmpeg` keyframe extraction (3–5 frames) → VLM description; `faster-whisper` for audio transcript. Expensive — gate behind triage. |
| `.gz` | Placeholder only | `gzip` / `tarfile`. Recurse into contents. |
| Unknown extensions (`.toc`, `.d1`, `.career2`, `.hanrttydoc`) | Filename-guessing | **Solved by magic-byte identification.** Siegfried/DROID identifies these properly. Most are ordinary formats with mangled names. |
| Batch labels (`00361-00850`, `00136-01590`) | Assumed scans, skipped | Magic bytes will resolve. Almost certainly TIFF/JPEG scan sequences → OCR lane. |
| Corrupted (`net3852448d`, `dmdelive13b254ad`) | Filename cleaning, fallback | Magic bytes; if unidentifiable, flag as `unidentified` and rely on folder-level context. |

### Never encountered — but will appear on researcher drives

This is the category the stakeholder conversation flagged (ArcGIS, 3D imaging). These drives
come from researchers across disciplines, so format diversity will be much wider than the
test corpus suggested.

**The important insight for all of these: the file header *is* the metadata.** You don't need
an LLM. Reading an HDF5 header or a shapefile's attribute schema gives you variable names,
units, coordinate system, spatial extent, and time range in milliseconds — richer and more
accurate than any generated summary. This should be a first-class lane, not a fallback.

| Category | Formats | Tooling | What to extract |
|---|---|---|---|
| **Geospatial vector** | `.shp` (+ `.dbf .shx .prj`), `.geojson`, `.gpkg`, `.kml`, `.gdb` | GDAL/OGR, `geopandas`, `fiona` | CRS, extent, geometry type, feature count, attribute schema |
| **Geospatial raster** | GeoTIFF, `.img`, `.asc`, `.nc` | GDAL, `rasterio` | CRS, extent, resolution, band count, nodata, acquisition date |
| **ArcGIS project files** | `.mxd`, `.aprx`, `.lyr` | `arcpy` (licensed) or treat as opaque + folder context | Layer names if accessible |
| **3D / mesh** | `.obj`, `.ply`, `.stl`, `.fbx`, `.dae` | `trimesh`, `Open3D` | Vertex/face count, bounding box, texture refs |
| **Point cloud** | `.las`, `.laz`, `.e57` | `laspy`, PDAL | Point count, extent, CRS, classification codes |
| **CAD** | `.dwg`, `.dxf` | `ezdxf` (dxf), ODA converter (dwg) | Layer names, entity counts, title block |
| **Scientific arrays** | `.h5`, `.hdf5`, `.nc`, `.mat`, `.npy`, `.npz` | `h5py`, `netCDF4`, `scipy.io` | Dataset names, shapes, dtypes, attributes, units |
| **Astronomy** | `.fits` | `astropy` | Header cards — instrument, target, date, exposure |
| **Statistics** | `.sav` (SPSS), `.dta` (Stata), `.rdata`, `.rds` | `pyreadstat`, `pyreadr` | Variable names, labels, value labels, N |
| **Bioinformatics** | `.fasta`, `.fastq`, `.bam`, `.vcf` | Biopython, pysam | Sequence counts, reference genome, sample IDs |
| **Notebooks / code** | `.ipynb`, `.py`, `.r`, `.m`, `.sql`, `.do` | `nbformat`, AST parsing | Markdown cells, docstrings, imports, function names |
| **LaTeX / bib** | `.tex`, `.bib`, `.bbl` | plain text + regex | Title, abstract, section headings, citations |
| **More archives** | `.7z`, `.rar`, `.tar`, `.iso`, `.dmg` | `py7zr`, `rarfile`, `tarfile`, `pycdlib` | Recurse |
| **Email, other** | `.msg`, `.pst`, `.ost`, `.olm` | `extract-msg`, `libpst`/`readpst` | Full email lane. `.pst` is very likely on faculty drives. |
| **Legacy office** | `.wpd` (WordPerfect), `.wk1`, `.123`, `.sam` | LibreOffice headless | Real risk on 20–30 year old drives |
| **Encrypted / protected** | any | detect only | Route straight to human queue — do not attempt to crack |

---

## 3. Suggested routing table structure

Rather than a chain of `if extension in [...]` blocks (which is how POC 2 grew, and why it's
hard to extend), define routing as data:

```python
# One row per format class. Adding a new format = adding a row, not editing logic.
{
  "puid": "fmt/199",              # PRONOM ID from Siegfried, not the extension
  "class": "geospatial_raster",
  "lane": "scientific",
  "extractor": "gdal_header",
  "cost_tier": 1,                 # 0=free 1=cheap 2=moderate 3=expensive
  "needs_gpu": False,
  "triage_signal": "header_only", # what Stage 3 reads
  "enrich_fn": "enrich_geotiff",
}
```

Benefits: routing keyed on verified format rather than extension; cost tier is explicit so the
scheduler can budget; adding a format is a config change; and unhandled formats fall through
to a defined default (folder-level context + technical metadata only) rather than crashing.

---

## 4. Priority order

Not everything needs building at once. Suggested sequence:

**Tier 1 — needed for any real drive**
Magic-byte identification, hashing/dedupe, plain text, PDF, Office (portable), images, email
(`.eml`/`.mbox`/`.msg`/`.pst`), archives with recursion.

**Tier 2 — high value, moderate effort**
Scientific array formats (header-only — very cheap, very informative), geospatial vector and
raster, SQLite/Access schema, notebooks and code, OCR for scanned material.

**Tier 3 — expensive or rare**
Video and audio, 3D and point cloud, CAD, legacy office formats, bioinformatics.

**Tier 4 — handle by exception**
Encrypted files, proprietary instrument formats, anything unidentifiable. These get technical
metadata plus folder context and go to a human queue. There will always be a long tail, and
the system should degrade gracefully rather than pretend to cover everything.
