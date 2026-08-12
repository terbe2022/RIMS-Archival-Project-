# Google Colab — What Lives There and How It Connects

---

## The rule

**Code lives in `src/` in the repo. Notebooks import it and explain it.**

Notebooks are bad at being libraries — you can't diff them usefully, you can't import from
them, and the same function ends up copy-pasted into four of them and then quietly drifts
apart. They are excellent at two things: teaching, and driving a GPU.

So every notebook follows the same shape:

```python
!git clone https://github.com/terbe2022/RIMS-Archival-Project-.git
%cd RIMS-Archival-Project-
!pip install -q -r src/requirements-box.txt

from src.box_inventory import crawl, client_from_env    # the real code
```

The markdown cells do the teaching. The code cells call the module. When we fix a bug in
`src/`, every notebook picks it up on the next clone — nothing to update in five places.

This matters more than it sounds for the handover: what Gauri learns from is the same code
that runs in production, not a parallel notebook version that works differently.

---

## Where each kind of work runs

| Work | Where | Why |
|---|---|---|
| Filesystem walk, hashing, format ID | Gauri's laptop | Pure CPU, and her i7 is good at it |
| Box inventory | Either | API-bound, not compute-bound |
| Triage scoring, embeddings | Laptop for dev, Colab for volume | MiniLM on CPU is fine at small scale |
| Prompt development | Laptop, 20–50 items | Iteration speed matters more than throughput |
| Vision model batches | **Colab T4** | Needs CUDA |
| Large-batch summarization | **Colab T4**, then L4 | Needs CUDA |
| Full-scale production runs | **L4 server** | 24 GB, vLLM, no session limits |

Colab's job is the middle ground: work that needs a GPU but doesn't need the L4, and anything
Gauri needs to run while her server access is pending.

---

## Connecting Colab to GitHub

### Opening notebooks from the repo

File → Open notebook → **GitHub** tab → authorize → search `terbe2022/RIMS-Archival-Project-`
→ pick a branch → open any `.ipynb`.

### Saving back to the repo

File → **Save a copy in GitHub**. It asks for repo, branch, path and a commit message, and
commits directly. Two habits worth forming:

- **Commit to a branch, not `main`.** Something like `gauri/stage-0`, then open a pull request.
  That gives Tayler a review loop and keeps `main` clean.
- **Clear outputs before saving.** Edit → Clear all outputs. Notebook outputs bloat the repo,
  and one of our POC notebooks was 377 MB because nobody did this. They also leak data —
  a printed DataFrame of email content lands in a public repo permanently.

### Open in Colab badges

Add this at the top of each notebook so anyone can launch it in one click:

```markdown
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/terbe2022/RIMS-Archival-Project-/blob/main/notebooks/00_environment_check.ipynb)
```

The repo is public, so `git clone` works with no token. If it ever goes private, cloning needs
a personal access token stored in Colab Secrets — see below.

---

## Secrets — do not put credentials in notebooks

Colab has a secrets manager: the **key icon** in the left sidebar. Add a secret, toggle
notebook access, then:

```python
from google.colab import userdata
token = userdata.get('BOX_DEVELOPER_TOKEN')
```

Secrets are per-Google-account and never appear in the notebook file, so they survive a
"Save a copy in GitHub" without leaking.

**Never** paste a Box token or client secret into a cell. It ends up in the notebook JSON, and
if that gets committed it is in the public repo history permanently — and rotating the
credential is then the only real fix.

---

## Things Colab will do to you

**The filesystem is ephemeral.** Everything under `/content` disappears when the runtime
recycles — on disconnect, on idle timeout, and always within about 12 hours. Anything you want
to keep goes to Drive or back to Box.

```python
from google.colab import drive
drive.mount('/content/drive')
OUT = '/content/drive/MyDrive/rims/manifest'
```

**Sessions end mid-job.** Free tier disconnects on idle and can be reclaimed at any time. Any
batch job needs checkpointing — write results incrementally and make re-runs resume rather
than restart. `box_inventory.py` already does this; anything new should too.

**GPU is not guaranteed.** Free tier gives a T4 when one is available. Runtime → Change runtime
type → T4 GPU. Check what you actually got before assuming:

```python
!nvidia-smi
```

**Reinstalling takes minutes every session.** Keep the install cell fast and pinned. Big model
downloads are worth caching to Drive rather than re-pulling each time.

---

## Ollama in Colab

Useful for comparing models on GPU without touching the L4. It needs to run as a background
server, since Colab has no service manager:

```python
!curl -fsSL https://ollama.com/install.sh | sh
import subprocess, time
subprocess.Popen(['ollama', 'serve'])
time.sleep(5)
!ollama pull qwen2.5-vl:7b
```

Then use the HTTP API on `localhost:11434` — same interface Gauri uses locally, so prompts
developed on her laptop run unchanged here, just faster.

---

## The notebook series

| # | Notebook | Purpose | Runs on |
|---|---|---|---|
| 00 | `environment_check` | Clone, install, verify GPU and Box connection | Anywhere |
| 01 | `box_inventory` | Crawl Box into a manifest, explain each field | Anywhere |
| 02 | `triage_free_filters` | Duplicates, junk, NSRL. Measure the reduction | Laptop |
| 03 | `smart_text_peek` | Structured sampling, compare against flat first-2KB | Laptop |
| 04 | `embeddings_and_scoring` | Embed, score, folder-context weighting | Colab for volume |
| 05 | `model_comparison_text` | Three text models, same 20 documents | Colab T4 |
| 06 | `model_comparison_vision` | Three vision models, same 20 images | Colab T4 |
| 07 | `archive_expansion` | Real archives from the accession | Laptop |

Build them in order. Each one should end with numbers posted to its GitHub issue — that is
where the record of what we learned actually lives.

---

## Sharing

Gauri's Colab account is `gbhasin2@illinois.edu`. Notebooks opened from the public repo need
no sharing at all — she opens the GitHub URL and gets her own copy. Only share a Colab link
directly when you want to work in the *same* live session.

Do not share notebooks containing accession data. The repo notebooks should always be clean of
real content; sample data comes from Box at runtime.
