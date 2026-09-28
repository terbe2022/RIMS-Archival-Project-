"""
lanes.py — decide which downstream process each file belongs to, and whether
that process is currently fit to receive it.

Two separate questions, deliberately kept apart:

    route()    which lane does this file belong to?
    dispatch() is the handler for that lane ready to run?

Routing is on verified format first and extension second. POC 2 routed on
extension alone and met `.d1`, `.career2`, `.toc`, `net3852448d` and
`00361-00850` in one corpus, none of which are real formats. Stage 01 already
identifies by content signature, so the PUID is the primary key and the
extension is a fallback for files stage 01 could not type.

Unhandled formats route to human attention rather than failing. That is POC 2's
own conclusion: specialist and scientific formats are the tail, not the body,
and a pipeline that errors on the tail stops on material nobody needed it to
understand.

The readiness gates exist because two of the three POCs have defects their own
READMEs say must be fixed before a real accession. A router that dispatched
anyway would produce output that looks like a successful run — masked email
with unstable placeholders reads as correctly redacted, and it is not.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .schema import manifest as M

ROUTER_VERSION = "lanes-0.1.0"

# ------------------------------------------------------------- routing ----
# PUID is authoritative. See stage01._MAGIC for what produces these.
_PUID_LANE = {
    "fmt/14": "document",       # PDF
    "fmt/111": "document",      # OLE2 — refined below by extension
    "fmt/355": "document",      # RTF
    "fmt/43": "image", "fmt/11": "image", "fmt/353": "image",
    "fmt/3": "image", "fmt/4": "image",
    "fmt/199": "av",
    "fmt/203": "av",
    "fmt/6": "av",
    "fmt/161": "tabular",       # Access
    "fmt/729": "tabular",       # SQLite
    "fmt/189": "archive",       # ZIP container — may be docx/xlsx, refined below
    "fmt/411": "archive", "x-fmt/266": "archive", "fmt/267": "archive",
    "fmt/688": "code", "fmt/899": "code",
}

_EXT_LANE = {
    # email — the Archives confirmed these arrive loose among everything else
    "eml": "email", "msg": "email", "pst": "email", "ost": "email",
    "mbox": "email", "mbx": "email",
    # document
    "doc": "document", "docx": "document", "pdf": "document", "txt": "document",
    "rtf": "document", "odt": "document", "wpd": "document", "tex": "document",
    "ppt": "document", "pptx": "document", "html": "document", "htm": "document",
    # tabular
    "xls": "tabular", "xlsx": "tabular", "csv": "tabular", "tsv": "tabular",
    "mdb": "tabular", "accdb": "tabular", "db": "tabular", "dbf": "tabular",
    # image
    "jpg": "image", "jpeg": "image", "tif": "image", "tiff": "image",
    "png": "image", "gif": "image", "bmp": "image", "heic": "image",
    # av
    "mov": "av", "mp4": "av", "avi": "av", "mkv": "av", "wmv": "av",
    "mp3": "av", "wav": "av", "m4a": "av", "flac": "av",
    # code
    "py": "code", "c": "code", "f": "code", "f90": "code", "m": "code",
    "r": "code", "sh": "code", "java": "code", "js": "code",
    # archive
    "zip": "archive", "tar": "archive", "gz": "archive", "rar": "archive",
    "7z": "archive", "iso": "archive",
    # scientific — the tail. Routed, not extracted.
    "fits": "scientific", "nc": "scientific", "hdf": "scientific",
    "h5": "scientific", "mat": "scientific", "sav": "scientific",
    "dta": "scientific", "spss": "scientific", "cdf": "scientific",
}

# OLE2 and ZIP are containers; the extension tells us which application wrote them.
_CONTAINER_REFINE = {
    "fmt/111": {"xls": "tabular", "ppt": "document", "doc": "document",
                "msg": "email", "db": "tabular"},
    "fmt/189": {"xlsx": "tabular", "docx": "document", "pptx": "document",
                "odt": "document", "ods": "tabular", "epub": "document"},
}


@dataclass
class Routing:
    lane: str | None
    method: str          # puid | puid+ext | extension | unroutable
    confidence: str      # high | medium | none
    note: str | None = None


def route(row: dict) -> Routing:
    """
    Assign one file to a lane.

    Returns lane=None for anything we cannot type. That is a real outcome, not
    an error: it means a person should look, and it is counted and reported
    rather than swallowed.
    """
    puid = row.get("s01_puid")
    ext = (row.get("extension") or "").lower().lstrip(".")

    if puid in _CONTAINER_REFINE:
        refined = _CONTAINER_REFINE[puid].get(ext)
        if refined:
            return Routing(refined, "puid+ext", "high")
        # Container identified, application unknown. OLE2 with no extension is
        # the Hanratty case: 38 files that are pre-2007 Word by signature.
        base = _PUID_LANE.get(puid)
        return Routing(base, "puid", "medium",
                       f"container {puid} with extension {ext!r}; "
                       f"lane inferred from container type only")

    if puid and puid in _PUID_LANE:
        lane = _PUID_LANE[puid]
        if ext and _EXT_LANE.get(ext) and _EXT_LANE[ext] != lane:
            # Signature and extension disagree. Trust the signature, record both.
            return Routing(lane, "puid", "medium",
                           f"extension {ext!r} suggests {_EXT_LANE[ext]}, "
                           f"signature says {lane}; signature wins")
        return Routing(lane, "puid", "high")

    if ext in _EXT_LANE:
        return Routing(_EXT_LANE[ext], "extension", "medium",
                       "no verified format; routed on extension alone")

    return Routing(None, "unroutable", "none",
                   f"no signature match and extension {ext!r} is not a known "
                   f"format; routed to human attention")


# ----------------------------------------------------------- readiness ----
@dataclass
class Handler:
    """A downstream process, and an honest account of whether it can run."""
    lane: str
    name: str
    source: str
    ready: bool
    blockers: list[str] = field(default_factory=list)
    needs_gpu: bool = False


HANDLERS = {
    "email": Handler(
        lane="email", name="email lane", source="poc/01-email-processing",
        ready=False, needs_gpu=True,
        blockers=[
            "POC 1 defect 7: PII placeholders are not stable across documents. "
            "Numbering restarts per row, so <PERSON1> means a different person "
            "in every message. Masked output looks correct and is not.",
            "POC 1 defect 1: header regex assumes a fixed field order and "
            "returns None for every field when it does not match.",
            "POC 1 defect 2: thread splitting matches the English delimiter "
            "only. The strongest thing in the POC is thread decomposition, and "
            "it silently under-recovers on anything else.",
            "POC 1 defect 4: 34.8 s/row came from subprocess against the "
            "Ollama CLI, which reloads weights per call. Use the HTTP API.",
        ]),
    "document": Handler(
        lane="document", name="document lane", source="poc/02-file-smart-search",
        ready=False, needs_gpu=True,
        blockers=[
            "POC 2 defect 1: .doc/.xls/.ppt extraction drives Microsoft Office "
            "through win32com. It cannot run on RHEL and cannot be "
            "parallelised. Replacement is a prerequisite, not a cleanup.",
            "POC 2 defect 3: MiniLM truncates at 256 tokens silently. It was "
            "embedding short summaries, so this never surfaced.",
        ]),
    "image": Handler(
        lane="image", name="image lane", source="poc/03-image-classification",
        ready=False, needs_gpu=True,
        blockers=[
            "GPU held by the legislation pipeline (D15). Description needs a "
            "vision model.",
            "POC 3 issue 1: 73% of flags were ambiguous. That is a "
            "specification problem — the criteria were never defined precisely "
            "enough for anyone to be consistent — so a labelled gold set (D11) "
            "is a prerequisite for scoring, not a follow-up.",
        ]),
    "tabular": Handler("tabular", "tabular lane", "not built", ready=False,
                       blockers=["No handler. POC 2 never implemented .mdb/.db."]),
    "av": Handler("av", "audio/video lane", "not built", ready=False,
                  blockers=["No handler. POC 2 never implemented .mov or video."]),
    "scientific": Handler("scientific", "scientific lane", "route only", ready=False,
                          blockers=["Deliberately route-only. The tail, not the body."]),
    "code": Handler("code", "code lane", "not built", ready=False, blockers=["No handler."]),
    "archive": Handler("archive", "archive lane", "not built", ready=False,
                       blockers=[f"No handler. Nested extraction capped at "
                                 f"MAX_ARCHIVE_DEPTH={M.MAX_ARCHIVE_DEPTH}."]),
}


def plan(rows: list[dict], accession: dict) -> dict:
    """
    Route every row and report what would happen, without running anything.

    This is the piece worth having before the GPU frees: it answers "what is
    actually in this accession, which processes would it need, and which of
    those can run today" from the manifest alone.
    """
    counts: dict[str, int] = {}
    unroutable: list[str] = []
    by_method: dict[str, int] = {}
    notes: list[str] = []

    for r in rows:
        rt = route(r)
        r["s03_lane"] = rt.lane
        r["s03_extractor"] = f"{ROUTER_VERSION}:{rt.method}"
        key = rt.lane or "(unroutable)"
        counts[key] = counts.get(key, 0) + 1
        by_method[rt.method] = by_method.get(rt.method, 0) + 1
        if rt.lane is None:
            unroutable.append(r.get("path_norm") or r.get("filename") or "?")
        if rt.note and len(notes) < 40:
            notes.append(f"{r.get('filename')}: {rt.note}")

    # Only lanes the accession actually said it expects. process_classes in the
    # intake form is a declaration; a lane appearing that the form did not
    # declare is worth surfacing rather than quietly handling.
    declared = set(accession.get("_process_classes") or [])
    lane_for_class = {"images": "image", "email": "email", "documents": "document",
                      "media": "av", "other": None}
    declared_lanes = {lane_for_class.get(c) for c in declared} - {None}
    present = {k for k in counts if k != "(unroutable)"}
    undeclared = sorted(present - declared_lanes) if declared_lanes else []

    return {
        "router_version": ROUTER_VERSION,
        "by_lane": dict(sorted(counts.items(), key=lambda kv: -kv[1])),
        "by_method": by_method,
        "unroutable_count": len(unroutable),
        "unroutable_sample": unroutable[:20],
        "undeclared_lanes": undeclared,
        "handlers": {
            lane: {"ready": HANDLERS[lane].ready,
                   "source": HANDLERS[lane].source,
                   "needs_gpu": HANDLERS[lane].needs_gpu,
                   "blockers": HANDLERS[lane].blockers}
            for lane in sorted(present) if lane in HANDLERS
        },
        "routing_notes": notes,
    }
