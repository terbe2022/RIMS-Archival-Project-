# Working with the Box Sample Data

> **Scope note, 12 Aug 2026 — Box is pilot infrastructure, not the ingest path.**
> Real accessions live on an Archives network share, already preservation-processed
> ([answers §1.2](../stakeholders/answers-2026-08.md)). The six Box folders are hand-picked
> extracts. Everything below is still correct and still worth doing — it unblocks the first
> real measurements — but it is not how production material will reach us.


**Gauri — this covers getting into Box, what's actually in there, and what to run first.**
From Tayler.

---

## Getting access

Two separate things, and you need both.

### 1. Access to the folder itself

I'll add `gbhasin2@illinois.edu` as a collaborator on the project folder with Viewer
permission. You'll get an email. Once that's done you can browse it in the Box web interface
like any other shared folder:

https://uofi.app.box.com/folder/318345592147

Browse it before writing any code. Ten minutes clicking around will tell you more about the
shape of this problem than the design doc does.

### 2. Your own API token

To read Box programmatically you need a token. **I'm not going to give you mine**, and you
shouldn't accept it if I offer — a developer token authenticates as the person who generated
it, with their full Box access across the whole University account. Yours needs to be yours,
so it can be revoked independently and so the audit log shows who actually did what.

I'll add you as a collaborator on the Box app (`File_Archiving_Box_Storage`) in the Developer
Console. Then:

1. Go to https://app.box.com/developers/console
2. Open `File_Archiving_Box_Storage`
3. Find the **Developer Token** section and click **Generate**
4. Copy it

**It expires after about 60 minutes.** That's deliberate on Box's part. When a script stops
working with an auth error, that's usually all it is — generate a fresh one and carry on.

Longer term we'll use a Service Account instead, which doesn't expire, but that's waiting on
approval from the University's Box admin. The token gets you working today, and the code
handles both paths so nothing changes when we switch.

### What to do with the token

Create a file called `.env` in your project folder — same directory as `src/`:

```
BOX_DEVELOPER_TOKEN=paste_your_token_here
BOX_ROOT_FOLDER_ID=318353711369
```

That's it. The scripts read it automatically.

**Never put the token anywhere else.** Not in a notebook cell, not in a `.py` file, not in a
Slack message. `.gitignore` already blocks `.env`, but that only protects you if the token is
in `.env` and nowhere else. If one ever ends up in a commit, tell me — we rotate it, we don't
try to scrub history.

In Colab it goes in the secrets manager instead — the key icon in the left sidebar. Same rule:
never in a cell.

---

## What's actually in the folder

It isn't one dataset. It's three different kinds of test data that arrived for three different
reasons.

### Hard-drive examples — ~600 files across six folders

| Folder | Files |
|---|---|
| `Hanratty Computer 2017` | 485 |
| `Election_2016` | 75 |
| `2415001_VCResearch` | 23 |
| `2620191_MichaelHart` | 8 |
| `1513059_DonCrummey` | 8 |
| `2620267_FemTech` | 0 |

These are the ones that matter most. Each is material extracted from a real archival hard
drive — someone's actual working files. That's the closest thing we have to the problem this
whole project exists to solve.

Start with `Hanratty Computer 2017`, folder ID `318353711369`. It's the largest and it's a
single person's material, so the folder structure should carry real meaning.

Note `2620267_FemTech` has **zero files**. Not a mistake to fix — an edge case to handle. Any
crawler that assumes folders contain things will fall over on it, and empty directories are
common on real drives.

### Image classification POC — `All Scanned Images.zip`, 3.8 GB

The corpus behind POC 3. Don't download it casually — it's 3.8 GB and it'll take a while.
Useful when you get to the vision model comparison; not needed before then.

### Email archive POC — two `.download` files

`require.min.js.download` and `MathJax.js.download`, about 77 KB combined.

Worth pausing on these, because they're a perfect illustration of the problem. They're
JavaScript assets that got saved when someone did "Save Page As" in a browser. They have no
archival value whatsoever. They're exactly the kind of thing that should be filtered out at
tier 0, before anything expensive touches them.

A real accession will have thousands of these — browser caches, application data, installer
fragments. Being able to identify and discard them cheaply is most of what triage does.

---

## The caveat that matters

**These are files extracted from hard drives and copied into Box. They are not the hard
drives.**

That distinction affects what our measurements mean:

| What Box gives us | What a real drive has |
|---|---|
| Files someone chose to extract | Everything, including what nobody looked at |
| Flattened or partial folder structure | The original hierarchy, decades deep |
| Whatever survived the copy | Deleted files, slack space, system directories |
| Box's normalized metadata | Original filesystem timestamps, permissions, ACLs |
| No OS or application files | Windows directories, Program Files, caches |

So when the inventory comes back with a duplicate rate, that's the duplicate rate **of a
curated extract**, not of a drive. It's still worth measuring — it's the best data we have —
but we should label it as what it is, and expect the real numbers to look different.

The design assumes 40–70% of a drive falls out for free at tier 0. Much of that 40–70% is
operating system and application files, and **none of those are in Box**. So expect a much
lower figure here, and don't read that as the assumption being wrong.

I'm working on getting access to an actual drive. Until then, this is what we have.

---

## What to run first

Once your token is in `.env`:

```bash
pip install box-sdk-gen pandas pyarrow python-dotenv

python src/box_check.py
```

Checks credentials, SDK, authentication, folder visibility, listing, and whether `sha1` comes
back. If any step fails it names the step and the fix.

Then:

```bash
python src/box_inventory.py --folder 318353711369 --out manifest/
```

Crawls `Hanratty Computer 2017`. **Downloads nothing** — it builds the manifest from Box
metadata alone. Should take under a minute for 485 files.

Then try the other folders and compare. Six accessions from six different people is a small
sample, but it'll tell you how much they vary, which is itself useful for the triage design.

---

## Why nothing gets downloaded

Box returns `sha1`, `size`, `name`, the full folder path and timestamps in the same API call
that lists a folder. So inventory, deduplication and structural filtering can all run before a
single byte moves.

This is the central idea in the whole pipeline, and Box happens to make it easy to honour. Only
files that survive triage ever get downloaded.

One wrinkle for the manifest schema: Box gives us **SHA-1**, and our schema specifies
**SHA-256**. Use Box's sha1 for Box-side deduplication and integrity checking, and compute
SHA-256 locally on the files we actually download. Record both. Worth capturing in the schema
worksheet when we sit down with it.

---

## Things to watch

**Rate limits.** Box allows roughly 1,000 requests per minute. The crawler handles 429s by
honouring the `Retry-After` header, but if you write your own loop, don't hammer it.

**The token expiring mid-run.** The crawler checkpoints every 25 folders. Generate a fresh
token, update `.env`, re-run — it resumes rather than starting over.

**Don't commit anything from `manifest/` or `data/`.** Real filenames from real accessions
shouldn't land in a public repo. `.gitignore` covers the usual cases, but the GitHub web
uploader ignores `.gitignore` entirely, so the real protection is not dragging them in.

---

## Questions worth asking as you go

Things I don't know the answer to, and would like to:

- How much does folder structure vary between the six accessions? If they're all shaped
  differently, folder-context weighting gets harder.
- What's the oldest file in there? Old drives mean legacy formats — WordPerfect, Lotus — that
  nothing in the current pipeline handles.
- How many files have extensions that don't match their actual format? That's what Siegfried
  is for, and it tells us how much the extension-based routing in POC 2 was getting wrong.
- Are there password-protected or encrypted files? They need a human queue, not a cracking
  attempt.

Post what you find on the inventory issue. Those numbers are more useful to the project right
now than any code.
