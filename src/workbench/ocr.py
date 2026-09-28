"""
ocr.py — read the scans.

A 1994 letter that was scanned rather than typed has no text layer. Extraction
returns an empty string, the file ranks on its filename alone, and the pipeline
reports it as "not read" — which is honest but useless. In this corpus that is
not an edge case: the Hart accession's forty-four 1994 administrative PDFs are
scans, and the estimator flags six more in Hanratty.

Deliberately a separate stage, not part of extraction
----------------------------------------------------
OCR is slow, it is lossy, and its output is a different KIND of evidence from a
text layer. A PDF's own text is what the author wrote; OCR output is a machine's
reading of a picture of what the author wrote. Those should not be silently
mixed in one column, so `s03_text_source` records which one produced the text
and every OCR'd row can be found and re-done when a better engine arrives.

Confidence is kept, not discarded
---------------------------------
Tesseract reports a per-word confidence. A page that OCRs at 42% mean confidence
is not a page that was read; it is a page that was guessed at. Pages below the
floor are recorded as attempted-and-failed rather than returned as text, because
low-confidence OCR poured into a search index is worse than an empty field — it
is findable noise that looks like content.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

STAGE_VERSION = "ocr-0.1.0"

# Below this mean word confidence the text is not trustworthy enough to index.
CONFIDENCE_FLOOR = 55.0

# Pages beyond this are sampled rather than read in full. A 300-page scanned
# report does not need every page to be appraised; it needs enough to know what
# it is.
MAX_PAGES = 12

_WS = re.compile(r"[ \t]+")


def available() -> dict:
    """
    What is usable here. Two independent paths, and neither needs root.

    tesseract + pdftoppm is the better OCR when a sysadmin can install it:
    faster, cheaper, and it reports a real per-word confidence.

    pypdfium2 + a vision model needs nothing but a pip wheel and the GPU that
    is already serving descriptions. It is slower per page and it cannot give a
    calibrated confidence — a language model's "I am sure" is not Tesseract's
    word-level score and must not be recorded as though it were. But it reads
    the scans, and on this host it is the path that exists.
    """
    have = {
        "tesseract": shutil.which("tesseract") is not None,
        "pdftoppm": shutil.which("pdftoppm") is not None,
        "ocrmypdf": shutil.which("ocrmypdf") is not None,
        "pypdfium2": False,
    }
    try:
        import pypdfium2  # noqa: F401
        have["pypdfium2"] = True
    except ImportError:
        pass
    have["any"] = have["tesseract"] or have["pypdfium2"]
    return have


# What the model is asked for. Deliberately not "describe this page" — a
# description of a letter is not the letter, and the whole point is to recover
# the text so it can be searched and scored as the file's own content.
VLM_PROMPT = (
    "Transcribe all text visible in this image, exactly as it appears. "
    "Preserve line breaks, letterheads, dates, addresses and signatures. "
    "Do not summarise, do not describe the image, do not add commentary. "
    "If the page contains no legible text, reply with exactly: NO_TEXT")


def _rasterise(pdf: Path, max_pages: int, scale: float = 2.0) -> list:
    """PDF pages to PNG bytes, with no system dependency."""
    import io

    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(pdf))
    pages = []
    for i in range(min(len(doc), max_pages)):
        bitmap = doc[i].render(scale=scale, grayscale=True)
        buf = io.BytesIO()
        bitmap.to_pil().save(buf, format="PNG")
        pages.append(buf.getvalue())
    return pages


def _vlm_page(png: bytes, url: str, model: str, timeout: int) -> str:
    import base64

    import requests
    r = requests.post(f"{url}/api/generate", timeout=timeout, json={
        "model": model, "prompt": VLM_PROMPT, "stream": False,
        "images": [base64.b64encode(png).decode()],
        "options": {"temperature": 0, "num_predict": 1200}})
    r.raise_for_status()
    text = (r.json().get("response") or "").strip()
    return "" if text.upper().startswith("NO_TEXT") else text


def needs_ocr(row: dict, min_chars: int = 120) -> bool:
    """
    A file worth OCR'ing: an image or a document that produced no usable text.

    Deliberately conservative. A PDF with a thin text layer — a cover page of
    real text over scanned body pages — still reads as "has text" and will be
    missed. Catching those needs a page-level check, which is a later problem.
    """
    if row.get("layer") == 0:
        return False
    lane = row.get("s03_lane")
    if lane not in ("document", "image"):
        return False
    return (row.get("s03_text_len") or 0) < min_chars


def _tesseract(image: Path, lang: str = "eng") -> tuple[str, float]:
    """Return (text, mean word confidence). Uses TSV so confidence survives."""
    out = subprocess.run(
        ["tesseract", str(image), "stdout", "-l", lang, "tsv"],
        capture_output=True, text=True, timeout=180)
    if out.returncode != 0:
        return "", 0.0

    words, confs = [], []
    for line in out.stdout.splitlines()[1:]:
        parts = line.split("\t")
        if len(parts) < 12:
            continue
        conf, text = parts[10], parts[11]
        if text.strip():
            words.append(text)
            try:
                c = float(conf)
                if c >= 0:
                    confs.append(c)
            except ValueError:
                pass
    text = _WS.sub(" ", " ".join(words)).strip()
    return text, (sum(confs) / len(confs) if confs else 0.0)


def ocr_file_vlm(path: str | Path, url: str = "http://127.0.0.1:11435",
                 model: str = "llava-llama3", max_pages: int = MAX_PAGES,
                 timeout: int = 300) -> dict:
    """
    Read a scan with the vision model rather than Tesseract.

    `confidence` is deliberately None, not a number. Tesseract measures how
    sure it is per word; a language model asked to transcribe returns no such
    measure, and inventing one would put a figure in a column that other code
    compares against a threshold. A missing confidence is a fact; a fabricated
    one is a bug waiting to be trusted.
    """
    p = Path(path)
    out = {"text": "", "confidence": None, "pages": 0,
           "engine": f"vlm:{model}", "version": STAGE_VERSION, "error": None}
    if not p.exists():
        out["error"] = "file not found"
        return out
    if not available()["pypdfium2"]:
        out["error"] = "pypdfium2 not installed"
        return out

    try:
        is_pdf = p.suffix.lower() == ".pdf" or p.read_bytes()[:5] == b"%PDF-"
        pages = _rasterise(p, max_pages) if is_pdf else [p.read_bytes()]
        out["pages"] = len(pages)
        texts = []
        for png in pages:
            t = _vlm_page(png, url, model, timeout)
            if t:
                texts.append(t)
        out["text"] = "\n\n".join(texts)
        if not out["text"]:
            out["error"] = "model reported no legible text"
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def ocr_file(path: str | Path, lang: str = "eng",
             max_pages: int = MAX_PAGES) -> dict:
    """
    OCR one file. Returns text, confidence, page count, and why if it failed.

    Never raises. A file that cannot be read is a result, not an error — the
    manifest has a column for "attempted and failed" and that is more useful
    than a traceback halfway through an accession.
    """
    p = Path(path)
    result = {"text": "", "confidence": 0.0, "pages": 0,
              "engine": "tesseract", "version": STAGE_VERSION, "error": None}

    if not p.exists():
        result["error"] = "file not found"
        return result
    have = available()
    if not have["tesseract"]:
        result["error"] = "tesseract not installed"
        return result

    try:
        if p.suffix.lower() == ".pdf" or p.read_bytes()[:5] == b"%PDF-":
            if not have["pdftoppm"]:
                result["error"] = "pdftoppm not installed; cannot rasterise PDF"
                return result
            with tempfile.TemporaryDirectory() as td:
                subprocess.run(
                    ["pdftoppm", "-r", "200", "-gray", "-f", "1",
                     "-l", str(max_pages), "-png", str(p), f"{td}/pg"],
                    capture_output=True, timeout=600)
                pages = sorted(Path(td).glob("pg*.png"))
                result["pages"] = len(pages)
                texts, confs = [], []
                for page in pages:
                    t, c = _tesseract(page, lang)
                    if t:
                        texts.append(t)
                        confs.append(c)
                result["text"] = "\n\n".join(texts)
                result["confidence"] = round(
                    sum(confs) / len(confs), 1) if confs else 0.0
        else:
            t, c = _tesseract(p, lang)
            result["text"], result["confidence"], result["pages"] = t, round(c, 1), 1
    except subprocess.TimeoutExpired:
        result["error"] = "timed out"
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    if result["text"] and result["confidence"] < CONFIDENCE_FLOOR:
        # Kept in the record, kept out of the text column. A reviewer can see
        # that OCR was tried and what it thought, without the guess becoming
        # searchable content.
        result["error"] = (f"mean confidence {result['confidence']}% is below "
                           f"the {CONFIDENCE_FLOOR}% floor — read as a guess, "
                           f"not as text")
        result["rejected_text"] = result["text"][:500]
        result["text"] = ""
    return result


def apply(row: dict, out: dict) -> dict:
    """
    Merge an OCR result into a manifest row.

    `s03_text_source` is the point of this function: a later reader must be
    able to tell a text layer from a machine's reading of a picture.
    """
    if out.get("text"):
        row["s03_text_sample"] = out["text"][:8000]
        row["s03_text_len"] = len(out["text"])
        row["s03_status"] = "ok"
        # Which engine read it, not just that something did. A transcription by
        # a language model and a Tesseract pass are different evidence and a
        # later reader has to be able to tell them apart.
        row["s03_text_source"] = ("ocr_vlm" if str(out.get("engine", "")).startswith("vlm")
                                  else "ocr")
        row["s03_ocr_engine"] = out.get("engine")
        row["s03_ocr_confidence"] = out["confidence"]
        row["s03_ocr_pages"] = out["pages"]
        row["s03_needs_ocr"] = False
    else:
        row["s03_needs_ocr"] = True
        row["s03_text_source"] = "ocr_failed"
        row["s03_ocr_confidence"] = out.get("confidence", 0.0)
        row["s03_error"] = out.get("error") or "no text recovered"
    return row
