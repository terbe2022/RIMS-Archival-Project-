"""
extract.py — text extraction for the document and tabular lanes. Pure Python.

This replaces POC 2's `win32com.client` extraction, which drove a real
Microsoft Office install to read `.doc`, `.xls` and `.ppt`. Its README calls
that defect 1 and a prerequisite rather than a cleanup, for three reasons: it
cannot run on RHEL at all, it cannot be parallelised safely, and it hangs on
malformed files. A pipeline that hangs on malformed input is worse than one
that fails on it, because a hang in a batch of 150,000 files looks like
progress.

Nothing here shells out to an application. `.doc` and `.ppt` are parsed from
their OLE2 streams directly; `.xls` goes through xlrd, which is pure Python and
still supports the legacy BIFF format that modern openpyxl rejects.

Why this matters beyond format coverage: the relevance scorer currently has
almost no content evidence to work with, so nearly every file in a folder like
`Consulting/conoco` comes back flagged `retained_by_association` — kept because
of its neighbours rather than understood. That flag is correct given what the
pipeline knows, but it is meant to be the exception. Extraction is what turns
most of those into files we actually understand, and it needs no GPU.

Every extractor returns an ExtractResult rather than raising, so one unreadable
file cannot stop a run. Failures are recorded in s03_status and s03_error and
counted, which is the same posture as stage 01's format identification.
"""
from __future__ import annotations

import re
import struct
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

EXTRACTOR_VERSION = "extract-0.1.0"
MAX_TEXT = 2_000_000          # 2 MB of text per file; beyond this we truncate
SAMPLE_CHARS = 1500


@dataclass
class ExtractResult:
    text: str = ""
    method: str = "none"
    status: str = "ok"                 # ok | empty | partial | failed | skipped
    error: str | None = None
    page_count: int | None = None
    needs_ocr: bool = False
    notes: list[str] = field(default_factory=list)

    @property
    def sample(self) -> str:
        return re.sub(r"\s+", " ", self.text[:SAMPLE_CHARS]).strip()


def _strip_surrogates(text: str) -> str:
    r"""
    Remove lone surrogates.

    Bytes that are not valid UTF-8 — in a filename or inside a file — come back
    from Python surrogate-escaped as \udcXX. Nothing downstream can encode
    them: not parquet, not a text file, not JSON. They have to be dealt with at
    the point text enters the pipeline rather than at each place it leaves,
    because otherwise every writer needs the same guard and the one that gets
    forgotten is the one that crashes a run.
    """
    if not text:
        return text
    return text.encode("utf-8", "replace").decode("utf-8")


def _clean(text: str) -> str:
    """Collapse control characters and runaway whitespace, keep paragraphs."""
    text = _strip_surrogates(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x0b", "\n")
    text = re.sub(r"[\x00-\x08\x0e-\x1f\x7f]", " ", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ------------------------------------------------------- Word 97 (.doc) ----
def extract_doc(path: str | Path) -> ExtractResult:
    """
    Word 97-2003 binary format, read from the OLE2 streams.

    The text is not stored contiguously. The FIB in the WordDocument stream
    points at a Clx in one of two table streams, and the piece table inside it
    maps character positions to file offsets. Each piece is either CP-1252
    single-byte or UTF-16LE, distinguished by bit 30 of its offset field.

    Reading fcMin..fcMac instead, which is the common shortcut, returns the
    text plus deleted fragments, field codes and formatting residue, in
    document order only by accident. For appraisal that residue is worse than
    nothing: it feeds the relevance scorer text the document does not contain.
    """
    try:
        import olefile
    except ImportError:
        return ExtractResult(status="failed", method="doc",
                             error="olefile not installed")
    try:
        if not olefile.isOleFile(str(path)):
            return ExtractResult(status="failed", method="doc",
                                 error="not an OLE2 compound file")
        ole = olefile.OleFileIO(str(path))
        try:
            if not ole.exists("WordDocument"):
                return ExtractResult(status="failed", method="doc",
                                     error="no WordDocument stream; OLE2 but not Word")
            wd = ole.openstream("WordDocument").read()

            # FIB base: fComplex etc. live in the flags at 0x000A.
            flags = struct.unpack_from("<H", wd, 0x000A)[0]
            table_name = "1Table" if (flags & 0x0200) else "0Table"
            if not ole.exists(table_name):
                # Word 6/95 has no table stream. Fall back to the contiguous
                # span, and say so rather than pretending it is equivalent.
                fc_min, fc_mac = struct.unpack_from("<ll", wd, 0x0018)
                raw = wd[fc_min:fc_mac].decode("cp1252", errors="replace")
                return ExtractResult(_clean(raw), "doc:fcMin-fcMac", "partial",
                                     notes=["no table stream (Word 6/95); text may "
                                            "include deleted fragments and field codes"])

            table = ole.openstream(table_name).read()
            fc_clx, lcb_clx = struct.unpack_from("<ll", wd, 0x01A2)
            clx = table[fc_clx:fc_clx + lcb_clx]

            # Walk the Clx: 0x01 blocks are Prc (skip), 0x02 introduces the Pcdt.
            i = 0
            pcdt = None
            while i < len(clx):
                if clx[i] == 0x01:
                    cb = struct.unpack_from("<h", clx, i + 1)[0]
                    i += 3 + cb
                elif clx[i] == 0x02:
                    lcb = struct.unpack_from("<L", clx, i + 1)[0]
                    pcdt = clx[i + 5:i + 5 + lcb]
                    break
                else:
                    break
            if not pcdt:
                return ExtractResult(status="failed", method="doc",
                                     error="no piece table found in Clx")

            n = (len(pcdt) - 4) // 12
            cps = [struct.unpack_from("<L", pcdt, 4 * k)[0] for k in range(n + 1)]
            out = []
            for k in range(n):
                pcd = 4 * (n + 1) + 8 * k
                fc = struct.unpack_from("<L", pcdt, pcd + 2)[0]
                compressed = bool(fc & 0x40000000)
                off = fc & 0x3FFFFFFF
                length = cps[k + 1] - cps[k]
                if compressed:
                    chunk = wd[off // 2: off // 2 + length]
                    out.append(chunk.decode("cp1252", errors="replace"))
                else:
                    chunk = wd[off: off + length * 2]
                    out.append(chunk.decode("utf-16-le", errors="replace"))
            text = _clean("".join(out))
            if not text:
                return ExtractResult(method="doc:piecetable", status="empty")
            return ExtractResult(text[:MAX_TEXT], "doc:piecetable")
        finally:
            ole.close()
    except Exception as exc:
        return ExtractResult(status="failed", method="doc",
                             error=f"{type(exc).__name__}: {exc}")


# ------------------------------------------------------ Excel 97 (.xls) ----
def extract_xls(path: str | Path) -> ExtractResult:
    """Legacy BIFF via xlrd. openpyxl raises InvalidFileException on these."""
    try:
        import xlrd
    except ImportError:
        return ExtractResult(status="failed", method="xls",
                             error="xlrd not installed")
    try:
        book = xlrd.open_workbook(str(path), on_demand=True)
        parts = []
        for name in book.sheet_names():
            sh = book.sheet_by_name(name)
            parts.append(f"## Sheet: {name}")
            for r in range(min(sh.nrows, 5000)):
                vals = [str(v) for v in sh.row_values(r) if v not in ("", None)]
                if vals:
                    parts.append("\t".join(vals))
            book.unload_sheet(name)
        return ExtractResult(_clean("\n".join(parts))[:MAX_TEXT], "xls:xlrd",
                             page_count=book.nsheets)
    except Exception as exc:
        return ExtractResult(status="failed", method="xls",
                             error=f"{type(exc).__name__}: {exc}")


# -------------------------------------------------- PowerPoint 97 (.ppt) ---
_PPT_BOILERPLATE = re.compile(
    r"^(click to (edit|add)\b|"
    r"(second|third|fourth|fifth|sixth|seventh)\s+(outline\s+)?level$|"
    r"master (title|text) style)", re.IGNORECASE)
_PPT_TEXTBYTES = 0x0FA8
_PPT_TEXTCHARS = 0x0FA0


def extract_ppt(path: str | Path) -> ExtractResult:
    """
    PowerPoint 97-2003. Walks the record tree in the PowerPoint Document
    stream and collects TextBytesAtom (CP-1252) and TextCharsAtom (UTF-16LE).
    """
    try:
        import olefile
    except ImportError:
        return ExtractResult(status="failed", method="ppt",
                             error="olefile not installed")
    try:
        ole = olefile.OleFileIO(str(path))
        try:
            stream = next((s for s in ("PowerPoint Document", "PP97_DUALSTORAGE")
                           if ole.exists(s)), None)
            if stream is None:
                return ExtractResult(status="failed", method="ppt",
                                     error="no PowerPoint Document stream")
            data = ole.openstream(stream).read()
        finally:
            ole.close()

        out, i = [], 0
        while i + 8 <= len(data):
            ver_inst, rtype, rlen = struct.unpack_from("<HHL", data, i)
            # Low nibble is recVer. 0xF means this is a CONTAINER whose body is
            # itself a sequence of records, so we step past the 8-byte header
            # and descend. Skipping recLen instead walks straight over every
            # nested TextAtom, which is why a naive walk returns nothing.
            if (ver_inst & 0x000F) == 0x000F:
                i += 8
                continue
            body = data[i + 8: i + 8 + rlen]
            if rtype == _PPT_TEXTBYTES:
                out.append(body.decode("cp1252", errors="replace"))
            elif rtype == _PPT_TEXTCHARS:
                out.append(body.decode("utf-16-le", errors="replace"))
            i += 8 + rlen
            if rlen == 0 and (ver_inst & 0x000F) != 0x000F:
                continue
        text = _clean("\n".join(p for p in out if p.strip()))
        # Masters and layouts carry the same TextAtoms as real slides, so a
        # record walk collects "Click to edit Master title style" once per
        # layout. Left in, it dominates s03_text_sample and feeds the relevance
        # scorer boilerplate that appears in every deck ever made, which would
        # make unrelated presentations look similar to each other.
        kept, dropped = [], 0
        for line in text.split("\n"):
            s = line.strip()
            if not s or s in {"*"} or _PPT_BOILERPLATE.match(s):
                dropped += 1
                continue
            kept.append(s)
        text = _clean("\n".join(kept))
        notes = ([f"dropped {dropped} master/layout placeholder lines"]
                 if dropped else [])
        return ExtractResult(text[:MAX_TEXT], "ppt:atoms",
                             status="ok" if text else "empty", notes=notes)
    except Exception as exc:
        return ExtractResult(status="failed", method="ppt",
                             error=f"{type(exc).__name__}: {exc}")


# ---------------------------------------------------------- modern OOXML ---
def extract_docx(path: str | Path) -> ExtractResult:
    try:
        import docx
        d = docx.Document(str(path))
        parts = [p.text for p in d.paragraphs]
        for t in d.tables:
            for row in t.rows:
                parts.append("\t".join(c.text for c in row.cells))
        return ExtractResult(_clean("\n".join(parts))[:MAX_TEXT], "docx:python-docx")
    except Exception as exc:
        return ExtractResult(status="failed", method="docx",
                             error=f"{type(exc).__name__}: {exc}")


def extract_xlsx(path: str | Path) -> ExtractResult:
    try:
        from openpyxl import load_workbook
        wb = load_workbook(str(path), read_only=True, data_only=True)
        parts = []
        for ws in wb.worksheets:
            parts.append(f"## Sheet: {ws.title}")
            for row in ws.iter_rows(max_row=5000, values_only=True):
                vals = [str(v) for v in row if v is not None]
                if vals:
                    parts.append("\t".join(vals))
        n = len(wb.worksheets)
        wb.close()
        return ExtractResult(_clean("\n".join(parts))[:MAX_TEXT], "xlsx:openpyxl",
                             page_count=n)
    except Exception as exc:
        return ExtractResult(status="failed", method="xlsx",
                             error=f"{type(exc).__name__}: {exc}")


def extract_pptx(path: str | Path) -> ExtractResult:
    try:
        from pptx import Presentation
        pres = Presentation(str(path))
        parts = []
        for i, slide in enumerate(pres.slides, 1):
            parts.append(f"## Slide {i}")
            for shape in slide.shapes:
                if shape.has_text_frame:
                    parts.append(shape.text_frame.text)
        return ExtractResult(_clean("\n".join(parts))[:MAX_TEXT], "pptx:python-pptx",
                             page_count=len(pres.slides))
    except Exception as exc:
        return ExtractResult(status="failed", method="pptx",
                             error=f"{type(exc).__name__}: {exc}")


# ----------------------------------------------------------------- PDF -----
def extract_pdf(path: str | Path) -> ExtractResult:
    """
    Text layer only. A PDF with no text layer is a scan; it is flagged
    needs_ocr rather than returned as an empty document, because 'no text' and
    'text we have not read yet' are different facts about an accession.
    """
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        pages = len(reader.pages)
        parts = [(p.extract_text() or "") for p in reader.pages[:500]]
        text = _clean("\n".join(parts))
        if len(text) < 20 * max(1, min(pages, 500)) ** 0.5:
            return ExtractResult(text, "pdf:pypdf", "partial", page_count=pages,
                                 needs_ocr=True,
                                 notes=["little or no text layer; likely a scan"])
        return ExtractResult(text[:MAX_TEXT], "pdf:pypdf", page_count=pages)
    except Exception as exc:
        return ExtractResult(status="failed", method="pdf",
                             error=f"{type(exc).__name__}: {exc}")


# ------------------------------------------------------------ text-ish -----
def extract_rtf(path: str | Path) -> ExtractResult:
    try:
        from striprtf.striprtf import rtf_to_text
        raw = Path(path).read_text(encoding="cp1252", errors="replace")
        return ExtractResult(_clean(rtf_to_text(raw))[:MAX_TEXT], "rtf:striprtf")
    except Exception as exc:
        return ExtractResult(status="failed", method="rtf",
                             error=f"{type(exc).__name__}: {exc}")


def extract_text(path: str | Path) -> ExtractResult:
    """Plain text, CSV, HTML. Encoding sniffed, never assumed to be UTF-8."""
    try:
        raw = Path(path).read_bytes()[:MAX_TEXT]
        # UTF-8 strict first. chardet on a short file guesses badly and will
        # happily return utf-8 for cp1252 bytes, which silently turns every
        # accented character into a replacement mark. Legacy archival material
        # is full of cp1252, so a wrong guess here corrupts names.
        text = enc = None
        try:
            text = raw.decode("utf-8")
            enc = "utf-8"
        except UnicodeDecodeError:
            try:
                import chardet
                guess = chardet.detect(raw[:100_000])
                if guess.get("encoding") and (guess.get("confidence") or 0) > 0.8:
                    enc = guess["encoding"]
                    text = raw.decode(enc, errors="strict")
            except (ImportError, UnicodeDecodeError, LookupError):
                text = None
            if text is None:
                enc = "cp1252"
                text = raw.decode("cp1252", errors="replace")
        if Path(path).suffix.lower() in (".html", ".htm"):
            text = re.sub(r"(?is)<(script|style).*?</\1>", " ", text)
            text = re.sub(r"(?s)<[^>]+>", " ", text)
        return ExtractResult(_clean(text), f"text:{enc}")
    except Exception as exc:
        return ExtractResult(status="failed", method="text",
                             error=f"{type(exc).__name__}: {exc}")


# ---------------------------------------------------------- the router -----
# Keyed on the PUID stage 01 established, with extension only as a tiebreak
# inside container formats. POC 2 routed on extension alone and met `.d1`,
# `.career2` and `net3852448d` in one corpus.
_BY_EXT = {
    "doc": extract_doc, "xls": extract_xls, "ppt": extract_ppt,
    "docx": extract_docx, "xlsx": extract_xlsx, "pptx": extract_pptx,
    "pdf": extract_pdf, "rtf": extract_rtf,
    "txt": extract_text, "csv": extract_text, "tsv": extract_text,
    "html": extract_text, "htm": extract_text, "log": extract_text,
    "md": extract_text, "tex": extract_text,
}

_OLE2_SNIFF = (
    ("WordDocument", extract_doc),
    ("Workbook", extract_xls),
    ("Book", extract_xls),
    ("PowerPoint Document", extract_ppt),
)


def _sniff_ole2(path: str | Path):
    """
    An extensionless OLE2 file does not say which application wrote it. The
    stream names do. This is the Hanratty case: 38 files with no extension,
    typed as OLE2 by signature in stage 01 but not yet as Word.
    """
    try:
        import olefile
        ole = olefile.OleFileIO(str(path))
        try:
            names = {n[0] for n in ole.listdir()}
        finally:
            ole.close()
        for stream, fn in _OLE2_SNIFF:
            if stream in names:
                return fn
    except Exception:
        pass
    return None


def extract(row: dict) -> dict:
    """
    Extract one file and return the stage 03 columns.

    Takes a manifest row so it can use the PUID stage 01 already established
    rather than guessing again from the name.
    """
    t0 = time.perf_counter()
    path = row.get("path_raw")
    ext = (row.get("extension") or "").lower().lstrip(".")
    puid = row.get("s01_puid")

    fn = _BY_EXT.get(ext)
    if fn is None and puid == "fmt/111":
        fn = _sniff_ole2(path)
    if ext in ("eml", "msg", "mbox") or (puid == "fmt/278"):
        from . import mail
        return mail.read(path)
    if fn is None and puid == "fmt/14":
        fn = extract_pdf
    if fn is None and puid == "fmt/189" and zipfile.is_zipfile(str(path)):
        names = set(zipfile.ZipFile(path).namelist())
        if "word/document.xml" in names:
            fn = extract_docx
        elif "xl/workbook.xml" in names:
            fn = extract_xlsx
        elif "ppt/presentation.xml" in names:
            fn = extract_pptx

    if fn is None:
        res = ExtractResult(status="skipped", method="none",
                            error=f"no extractor for extension {ext!r} / puid {puid!r}")
    else:
        res = fn(path)

    return {
        "s03_extractor": f"{EXTRACTOR_VERSION}:{res.method}",
        "s03_text_len": len(res.text),
        "s03_text_sample": res.sample,
        "s03_page_count": res.page_count,
        "s03_needs_ocr": res.needs_ocr,
        "s03_duration_ms": int((time.perf_counter() - t0) * 1000),
        "s03_status": res.status,
        "s03_error": res.error or ("; ".join(res.notes) if res.notes else None),
        "s03_version": EXTRACTOR_VERSION,
        "_text": res.text,
    }
