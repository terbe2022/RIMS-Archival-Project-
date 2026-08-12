# Box Integration — Access, Extraction, and Batch Processing

> **Scope note, 12 Aug 2026 — Box is pilot infrastructure, not the ingest path.**
> Real accessions live on an Archives network share, already preservation-processed
> ([answers §1.2](../stakeholders/answers-2026-08.md)). The six Box folders are hand-picked
> extracts. Everything below is still correct and still worth doing — it unblocks the first
> real measurements — but it is not how production material will reach us.


Target folder: `File_Archiving Project` — https://uofi.app.box.com/folder/318345592147

---

## The thing to get right first

The instinct is to download everything from Box and then process it. Don't.

**The Box API returns almost everything stage 00 through 02 needs without downloading a single
byte.** Every file object carries:

| Field | What it gives us |
|---|---|
| `id` | Stable identifier |
| `name`, `extension` | Filename |
| `size` | Bytes |
| `sha1` | **Box computes this for every file** — free deduplication |
| `created_at`, `modified_at` | Timestamps |
| `path_collection` | The full folder path, as a list of ancestors |
| `item_status` | Active vs trashed |

So the entire inventory, hashing, duplicate detection, and structural-junk filtering can run
against the API alone. Only the files that survive triage ever get downloaded.

On a 100,000-file folder, if triage keeps 5%, that's 5,000 downloads instead of 100,000 — and
the inventory pass takes minutes rather than hours or days.

This is the same triage-first argument from the pipeline design, and Box happens to make it
unusually easy to honour.

```
Box API (metadata only)  →  manifest  →  triage  →  download survivors  →  extract  →  enrich
        minutes                                          hours              …
```

One caveat: Box's `sha1` is not the SHA-256 we specified in the manifest schema. Use it for
Box-side deduplication and integrity checking, and compute SHA-256 locally on the files we
actually download. Record both.

---

## Part 1 — Getting API access

### What you create

1. Go to https://app.box.com/developers/console and sign in with your University account
2. **Create New App** → **Custom App**
3. Name it something identifiable — `RIMS Archival Pipeline`
4. Authentication method: **Server Authentication (Client Credentials Grant)**

CCG rather than JWT because it needs no keypair management, and this is a machine-to-machine
job with no end user to authenticate. Note that **you cannot change the auth method later**
without creating a new app, so pick deliberately.

### Scopes to enable

Configuration tab → Application Scopes:

- ✅ **Read all files and folders stored in Box** — required
- ✅ **Write all files and folders stored in Box** — only if we write results back; leave off for now
- ⬜ Manage users / groups / enterprise properties — not needed, and asking for them will slow approval

**App Access Level:** start with *App Access Only*. That is enough if we collaborate the
folder to the Service Account (see below), and it is a much easier approval conversation than
*App + Enterprise Access*.

### Getting it authorized

Server-authentication apps cannot be used until a Box admin authorizes them, and in the
current Developer Console **the Service Account does not exist until that happens** — the
App Details panel will say "Authorize above to generate it."

So the order is:

1. **Set scopes first**, under Content Actions on the Configuration tab. Save.
2. **Status panel → Submit** — "Submit app for authorization for access to the Enterprise"
3. Status changes from *Not Submitted* to awaiting approval; the Box admin gets the request
4. Admin approves under Admin Console → Apps → Custom Apps Manager → Authorize App
5. Status becomes **Authorized**
6. *Now* the **Service Account** section on the right-hand App Details panel shows the
   generated identity — something like `AutomationUser_1234567_abcdef@boxdevedu.com`
7. Collaborate the target folder to that Service Account (see below)

Scopes cannot be quietly widened later — changing them requires the admin to re-authorize, so
decide before submitting.

**What to put in the request:**

> Application: RIMS Archival Pipeline
> Requested by: Tayler Erbe, AITS
> Purpose: programmatic access to a Box folder of archival sample files, to build an automated
> appraisal and description pipeline for University Archives.
> Access is limited to folders explicitly shared with this app's Service Account.
> Sponsor: Joanne Kaczmarek, University Archivist.

Ask Joanne or Brent who the Box admin is and give them a heads-up — a named person is faster
than a queue.

### Testing before approval — developer token

You do not have to wait. The Developer Console will issue a **developer token** valid for about
60 minutes that authenticates **as you**. Since your own account already has access to the
folder, that is enough to run the inventory today:

```
BOX_DEVELOPER_TOKEN=...
BOX_ROOT_FOLDER_ID=318345592147
```

`box_check.py` and `box_inventory.py` both use it automatically when present, and fall back to
Client Credentials Grant when it is not. No Service Account, no collaboration step.

Treat it as a live credential: it grants your access while valid. Do not paste it into
documents, screenshots or commits, and revoke it from the Developer Console when finished.

### The step everyone misses (once authorized)

The Service Account is a separate machine user and **starts with access to nothing** — not
even folders you own.

1. Open the folder in Box
2. Share → Invite People → paste the Service Account email from the App Details panel
3. Permission: **Viewer** for read-only, **Editor** if writing results back

If the first API call returns an empty folder or a 404, this is almost always why.

### Credentials

Configuration tab gives you Client ID and Client Secret; General Settings gives the Enterprise
ID. You need 2FA on your Box account to view the secret.

**Never commit these.** Put them in a `.env` file, which `.gitignore` already blocks:

```
BOX_CLIENT_ID=...
BOX_CLIENT_SECRET=...
BOX_ENTERPRISE_ID=...
BOX_ROOT_FOLDER_ID=318345592147
```

---

## Part 2 — Rate limits and batching

Box's general API limit is around 1,000 requests per minute per user, with uploads and
downloads governed separately. The practical design consequences:

**Ask for the fields you need in one call.** `get_folder_items` accepts a `fields` parameter.
Requesting `id,name,size,sha1,...` up front avoids a second call per file, which is the
difference between one request per 1,000 files and one per file.

**Use marker-based pagination, not offset.** Offset pagination degrades badly past a few
thousand items and can skip or repeat entries if the folder changes mid-crawl. Marker
pagination is stable.

**Handle 429 properly.** Box returns `Retry-After` in seconds. Honour it rather than using a
fixed sleep, and back off exponentially on repeated 429s.

**Keep download concurrency modest.** Four to eight concurrent downloads is a reasonable
starting point. More will trip rate limits and gain nothing, since the bottleneck is usually
bandwidth.

**Checkpoint constantly.** A crawl of a large folder will be interrupted — network, token
expiry, someone's laptop sleeping. Write the manifest incrementally and record the last marker
so a restart resumes rather than starting over.

---

## Part 3 — Zip files

Box has an API that *creates* zips for download. It does not extract them. Anything compressed
has to come down and be expanded locally.

The approach:

1. Inventory pass flags archives by extension and magic bytes — `.zip`, `.gz`, `.tar`, `.7z`,
   `.rar`, `.iso`
2. Archives are downloaded and expanded to scratch
3. Every file inside gets its own manifest row, with `parent_archive_id` pointing at the
   container and a `virtual_path` of the form `container.zip!/inner/path.pdf`
4. Nested archives recurse, up to a depth limit

**Guards that matter at this scale:**

| Risk | Guard |
|---|---|
| Zip bomb | Cap total expanded size and the expansion ratio; abort and flag if exceeded |
| Path traversal (`../../etc/passwd`) | Reject any member whose resolved path escapes the extraction root |
| Infinite nesting | Depth limit — 3 is generous |
| Password-protected | Detect, do not attempt to crack, flag for human review |
| Corrupt archive | Catch and record as a manifest status, don't crash the batch |

These aren't theoretical on drives of unknown provenance.

---

## Part 4 — What to build, in order

| # | Component | Purpose |
|---|---|---|
| 1 | `box_inventory.py` | Crawl the folder tree via API, metadata only, write the manifest |
| 2 | Triage (stages 02) | Run on the manifest — no downloads needed |
| 3 | `box_fetch.py` | Download only the selected files, with retry and resume |
| 4 | Archive expander | Expand downloaded archives, add child rows |
| 5 | Extraction and enrichment | The existing pipeline stages |

Steps 1 and 3 are in `src/`. They are written to run against the pilot folder first, then scale.

---

## Part 5 — Open questions

- Who is the University's Box admin, and what is their turnaround on app authorization?
- Is there a storage quota on the folder, and do we have headroom if we write results back?
- Does Box Governance apply retention or legal hold to this content? That would constrain what
  we may do with it.
- What is the actual file count and total size of folder 318345592147? The inventory pass
  answers this on its first run, and it is the number the throughput model needs.

---

## Reference

- Box Developer Console — https://app.box.com/developers/console
- Client Credentials Grant setup — https://developer.box.com/guides/authentication/client-credentials/client-credentials-setup
- Authorization guide — https://developer.box.com/guides/authorization/
- Python SDK (`box-sdk-gen`) — https://github.com/box/box-python-sdk-gen
- Rate limits — https://developer.box.com/guides/api-calls/permissions-and-errors/rate-limits/

Box changes its console and SDKs periodically — check the current docs before assuming any of
the above is still exact.
