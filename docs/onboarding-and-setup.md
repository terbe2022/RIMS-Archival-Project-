# Getting Your Machine Set Up

# Getting Your Machine Set Up

**Gauri — read this first. Everything you need to be productive in week one.**
From Tayler.

---

## Your hardware, and what it means

Thanks for the detailed specs — that's exactly what I needed. Working from what you sent:

| Component | | What it means for us |
|---|---|---|
| CPU | i7-12700H, 14 cores / 20 threads | Strong. Parsing, hashing, embeddings, multiprocessing all fine |
| GPU | Intel UHD, integrated | No CUDA — no vLLM, no GPU-accelerated inference |
| RAM | 16 GB (15.6 usable) | The real constraint. ~11 GB free after Windows |
| Storage | 954 GB NVMe | Plenty, but don't stage large sample sets locally |

One 30-second thing worth confirming, and then I'll stop asking: HP ships the ZBook Power G9
both with and without a discrete RTX A1000. Device Manager → Display adapters will say for
certain. If NVIDIA shows up there, tell me — it changes which models you can run and I'd
rather revise the plan now than have you work around a limit you don't have. If it's Intel
only, that matches what you sent and we're set.

**Here's the thing I want you to understand about your assignment.** The triage layer is
entirely CPU work — walking a filesystem, hashing, identifying formats, parsing headers,
extracting text, computing embeddings, applying scoring rules. None of it needs a GPU. And
triage is the part of this system that determines whether the whole thing is viable, because
it's what stops us running expensive models across a million files.

So you're not getting the leftover work because you don't have a GPU. You're getting the part
that matters most, and it happens to fit your machine well. The GPU-bound work — vision
models, large-batch summarization — runs on Colab or on the L4 server, and I'll handle that
until your server access comes through.

## What your machine is actually good for

Your specs: i7-12700H (6 performance cores + 8 efficiency cores, 20 threads), 16 GB RAM,
954 GB NVMe, integrated graphics.

That's a strong CPU and a tight memory budget. Windows will take about 4 GB, so plan around
roughly 11 GB of working memory.

Here's the thing I want you to understand about your assignment: **the triage layer is
entirely CPU work.** Walking a filesystem, hashing files, identifying formats, parsing
headers, extracting text, computing embeddings, applying scoring rules — none of that needs a
GPU. And triage is the part of this system that determines whether the whole thing is viable,
because it's what stops us from running expensive models across a million files.

So you're not getting the leftover work because you don't have a GPU. You're getting the part
that matters most, and it happens to fit your machine well. The GPU-bound work — vision
models, large-batch summarization — runs on Colab or on the L4 server, and I'll handle that
side until your server access comes through.

---

## Step 1 — Python environment

Don't install into your base Anaconda environment. Make a project-specific one so we can
reproduce it later and so nothing you install here breaks anything else.

```bash
# from your projects folder
python -m venv .venv
.venv\Scripts\activate          # Windows
python -m pip install --upgrade pip
```

Then install the stack:

```bash
pip install pandas pyarrow numpy tqdm python-dotenv
pip install sentence-transformers faiss-cpu
pip install pypdf pdfplumber python-docx python-pptx openpyxl
pip install beautifulsoup4 lxml striprtf charset-normalizer
pip install presidio-analyzer presidio-anonymizer
pip install python-magic-bin        # Windows binary build — not plain python-magic
python -m spacy download en_core_web_lg    # Presidio needs this
```

Freeze it when it works: `pip freeze > requirements.txt` and commit that.

A note on `python-magic`: on Windows you need `python-magic-bin`, not `python-magic`. The
plain package expects a system library that isn't there by default. This trips people up.

---

## Step 2 — Ollama and models

Install Ollama from https://ollama.com. It runs as a background service and gives you a local
API on port 11434.

**One thing I want you to do differently from how I did it in the POCs.** In the email
notebook I called Ollama through `subprocess.run()` against the CLI, once per row. That
reloads the model weights on every single call, and it's why that pipeline measured 34.8
seconds per row. Use the HTTP API against the running server instead — same model, same
hardware, dramatically faster:

```python
import requests
r = requests.post("http://localhost:11434/api/generate",
                  json={"model": "llama3.2:3b", "prompt": "...", "stream": False})
print(r.json()["response"])
```

Don't copy the `subprocess` pattern from my old notebooks. I'm leaving it in the repo as a
record of what we did, not as an example to follow.

### What to download — my final answer

I'm giving you a short list rather than a menu. There are a lot of models you *could* run;
these are the ones I want you actually using. Total footprint is about 5 GB.

```bash
ollama pull llama3.2:3b          # ~2.0 GB — your text workhorse
ollama pull moondream            # ~1.7 GB — your vision model
ollama pull nomic-embed-text     # ~275 MB — embeddings with real context length
```

**Why these three:**

**`llama3.2:3b`** — text summarization, classification, structured extraction. It matches
what the POCs used, so when you compare your output to the old results you're comparing
like with like. Fast enough on your CPU to iterate: roughly 10–20 tokens/second. Good enough
for triage adjudication, which is a coarse decision, not a nuanced one.

**`moondream`** — this is the one I want you to use for images, and it's probably not what
you'd have picked. It's a 1.8B vision model built specifically for constrained hardware. On
your machine it will actually respond in seconds rather than minutes. LLaVA-7B — what we
used in the image POC — takes 2 to 2.5 minutes per image even on the L4 under Ollama. On your
CPU it would be unusable for iteration. Moondream is a smaller, weaker model, and that's
fine, because what you're doing on your laptop is **developing and testing prompts**, not
producing final output. When a prompt works, we run it at quality on the L4.

**`nomic-embed-text`** — for embeddings. Note that `all-MiniLM-L6-v2`, which I used in the
file-search POC, truncates at 256 tokens. That was fine there because it was embedding short
summaries, but if you feed it longer text it silently cuts it off and you won't get an error.
Nomic handles 8K. Use it when embedding document text; MiniLM is still fine for short
summaries and it's faster.

### What NOT to download

You cannot run the good vision models on this machine, and trying will waste your time. Don't
pull `llava:7b`, `llava-llama3`, `qwen2.5-vl:7b`, or anything above about 4 GB. They will
technically load and then run so slowly you'll give up. I know this because I measured it on
hardware better than yours.

If you want to try a stronger vision model, use Colab's free T4 — that's what it's for.

---

## Step 3 — The archival tools

These aren't Python packages and they're the tools your software evaluation task covers.
Install at least the first two in week one:

**Siegfried** — format identification by magic bytes. Download the Windows binary from
https://www.itforarchivists.com/siegfried, put it somewhere on your PATH, then:

```bash
sf -version
sf C:\path\to\test\folder > out.json
```

**ExifTool** — https://exiftool.org, Windows executable. Rename `exiftool(-k).exe` to
`exiftool.exe` and put it on your PATH.

```bash
exiftool -json C:\path\to\image.tif
```

**Apache Tika** — needs Java. Download `tika-server-standard-*.jar` and run it as a server:

```bash
java -jar tika-server-standard-2.9.2.jar
# then PUT files to http://localhost:9998/tika
```

---

## Step 4 — Prove it works

Before you build anything, confirm each piece runs. Small script, five minutes:

1. Embed 100 short strings with `nomic-embed-text` and time it. Write the number down — it's
   your baseline for everything later.
2. Send one prompt to `llama3.2:3b` through the HTTP API and get a response back.
3. Send one image to `moondream` and get a description.
4. Run Siegfried over a folder and get JSON out.
5. Read a `.docx` with `python-docx` and a `.pdf` with `pypdf`.

If all five work, your environment is good. If any fail, tell me before you spend time
working around it.

---

## Using AI to help you set this up

You'll hit installation problems — everyone does, especially on Windows. Use Claude or
ChatGPT to work through them rather than getting stuck. Here's a prompt that will give you
useful help instead of generic answers:

> I'm setting up a local AI development environment on Windows 11. My machine is an HP ZBook
> with an Intel i7-12700H, 16 GB RAM, and Intel UHD integrated graphics — no NVIDIA GPU, no
> CUDA. I'm working in a Python 3.11 virtual environment.
>
> I'm trying to [describe exactly what you're doing]. I ran [exact command] and got [paste
> the full error, not a summary].
>
> Please help me fix this. Keep in mind I have no CUDA, so don't suggest anything requiring a
> GPU. Explain what caused the error, not just the fix — I want to understand it.

Two things that make a real difference: paste the **full** error message rather than
describing it, and always mention that you have no CUDA. Most AI answers assume a GPU and
will send you down a path that can't work on your machine.

Ask it to explain, not just to fix. You're going to own this system eventually, so
understanding why something broke is worth more than getting past it quickly.

---

## Week one checklist

**Environment**
- [ ] Check Device Manager for a discrete GPU, send me a screenshot
- [ ] Create project venv, install the Python stack, commit `requirements.txt`
- [ ] Install Ollama, pull the three models
- [ ] Install Siegfried and ExifTool, confirm both run
- [ ] Run the five-part smoke test above

**Repo**
- [ ] Confirm you can clone and push to the GitHub repo
- [ ] Read the pipeline design document end to end, write down what doesn't make sense
- [ ] Skim the three POC folders — you don't need to understand every cell yet

**Design**
- [ ] Work through the manifest schema worksheet with me. This is the week's most important
      deliverable and everything else depends on it.

**Reading**
- [ ] The two case studies on throughput — they explain why the serving stack matters more
      than the model choice, and that finding shapes the whole architecture

---

## Week two

- [ ] Build the Stage 0 notebook: walk a folder into a manifest. Target 10,000 files in under
      a minute.
- [ ] Build the Stage 1 notebook: SHA-256 plus Siegfried format ID joined onto the manifest.
- [ ] Build the Stage 2 notebook: duplicate detection and structural junk filters. Report
      what percentage of a real folder falls out at zero cost — I want that number.
- [ ] Start the software evaluation task.
- [ ] Compare `llama3.2:3b` against one other text model on the same 20 documents.

---

## How I want the notebooks written

You'll be handing these to people who aren't engineers, and you'll be reading them yourself in
six months. A markdown cell before each code cell explaining what it does **and why it's done
that way** is worth the extra effort. The email preprocessing notebook in the POC folder does
this reasonably well; the scratch notebook doesn't, and the difference is obvious when you try
to read them.

Also — no hardcoded paths like `C:\Users\terbe\Desktop\...`. My old notebooks are full of
them and it's the main reason they can't be run by anyone but me. Use a config cell at the
top or environment variables.

---

## One last thing

The components I'm handing you have known defects. The email header regex assumes a fixed
field order and returns `None` on anything else. The thread splitter only matches the English
`-----Original Message-----` delimiter, so it misses forwards and non-English mail. Presidio
tagged a US phone number as `UK_NHS`.

I'm telling you these up front on purpose. Finding and fixing them is good work and I want
you to do it. What I don't want is for them to quietly propagate into the new system because
nobody knew they were there.

If something in the old code looks wrong to you, it might be. Say so.
