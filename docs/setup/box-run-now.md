# Run the inventory today

> **Scope note, 12 Aug 2026 — Box is pilot infrastructure, not the ingest path.**
> Real accessions live on an Archives network share, already preservation-processed
> ([answers §1.2](../stakeholders/answers-2026-08.md)). The six Box folders are hand-picked
> extracts. Everything below is still correct and still worth doing — it unblocks the first
> real measurements — but it is not how production material will reach us.


You do not need the admin. The developer token authenticates as you, and you already
have access to the folder.

## 1. Create `.env`

In your project folder, alongside `src/`. Copy `.env.example` to `.env` and paste the
token in:

```
BOX_DEVELOPER_TOKEN=<paste your real token here>
BOX_ROOT_FOLDER_ID=318353711369
```

`.gitignore` already blocks `.env`. Do not paste the token into any other file.

## 2. Install

```bash
pip install box-sdk-gen pandas pyarrow python-dotenv
```

## 3. Check the connection

```bash
python src/box_check.py
```

Expect: authenticated as you, folder name `TomHanratty` visible, first page listed,
and `sha1` present on the sample file. If any step fails it names the step and the fix.

## 4. Crawl it

```bash
python src/box_inventory.py --folder 318353711369 --out manifest/
```

Downloads nothing. Progress prints every 25 folders. If the token expires mid-run,
generate a fresh one, update `.env`, and re-run — it resumes from the checkpoint.

## What you get

`manifest/box_inventory.parquet`, one row per file, plus a summary:

- total files and gigabytes
- exact duplicate percentage (from Box's sha1 — free, no downloads)
- zero-byte files
- archives needing expansion
- the real extension distribution, top 15

**These are the numbers the whole plan has been assuming.** Post them on issue #2 —
they replace the two biggest guesses in the throughput model and tell us whether the
format-mix assumptions in the gap analysis hold up.

## Which folder

| ID | Folder | When |
|---|---|---|
| `318353711369` | TomHanratty | Now — one accession, the realistic test |
| `318345592147` | File_Archiving Project | Later — the parent, everything |

Start with TomHanratty. If it is one person's material, it is a genuine sample of what
a real accession looks like, which is exactly what has been missing.

## Then

```bash
# look at what came back
python -c "import pandas as pd; d=pd.read_parquet('manifest/box_inventory.parquet'); \
print(d.shape); print(d['extension'].value_counts().head(25))"
```

Do not run `box_fetch.py` yet — triage has not run, so there is no `selected` column and
nothing to fetch selectively. If you want to eyeball a few real files first:

```bash
python src/box_fetch.py --manifest manifest/box_inventory.parquet --dest data/raw --limit 25
```
