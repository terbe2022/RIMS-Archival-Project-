"""
The intake form.

This is the contract between the web form and the server. The form the archivist
fills in on the page and the file the scheduled job reads are the same JSON
document, which is the only reason the two halves of this prototype can be shown
to agree. If you change a field name here, change it in web/index.html too.

A completed form is stored three times over, deliberately:
  intake/<accession>.json                     the live form, editable until lock
  runs/<run_id>/intake/<accession>.json       frozen snapshot of what was actually run
  <transformed>/<accession>/intake.json       shipped next to the output it produced

The third copy is the one that matters in five years, when someone asks why a
photograph was ranked the way it was.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

JOB_TYPES = ("images", "email", "mixed")
FILE_CLASSES = ("images", "email", "documents", "media", "other")

# (key, label, required) — label text matches the web form so the two read alike
FIELDS = [
    ("source",   "Where did this come from?",         True),
    ("owner",    "Whose material is it?",             True),
    ("role",     "Their role and dates",              False),
    ("scope",    "Scope of their work",               True),
    ("research", "Type of research or function",      False),
    ("bio",      "Background and context",            False),
    ("valuable", "What is most valuable to keep?",    True),
    ("exclude",  "What can go?",                      False),
    ("access",   "Access and sensitivity",            False),
]


@dataclass
class IntakeForm:
    accession: str
    name: str
    job_type: str = "mixed"
    source_folder: str = ""                  # Box folder id/path or local subfolder
    process_classes: list[str] = field(default_factory=lambda: list(FILE_CLASSES[:3]))
    source: str = ""
    owner: str = ""
    role: str = ""
    scope: str = ""
    research: str = ""
    bio: str = ""
    valuable: str = ""
    exclude: str = ""
    access: str = ""
    submitted_at: str = ""
    submitted_by: str = ""
    status: str = "draft"                    # draft | queued | locked | complete
    run_history: list[dict] = field(default_factory=list)
    notes: str = ""

    # -- validation ---------------------------------------------------------
    def problems(self) -> list[str]:
        out = []
        if not self.accession or not re.fullmatch(r"[A-Za-z0-9._-]+", self.accession):
            out.append("accession must be set and contain no spaces or slashes")
        if not self.name.strip():
            out.append("name is required so the accession can be found later")
        if self.job_type not in JOB_TYPES:
            out.append(f"job_type must be one of {', '.join(JOB_TYPES)}")
        if not self.source_folder.strip():
            out.append("source_folder is required — point the form at a folder")
        bad = [c for c in self.process_classes if c not in FILE_CLASSES]
        if bad:
            out.append(f"unknown file classes: {', '.join(bad)}")
        if not self.process_classes:
            out.append("select at least one file class to process")
        for key, label, required in FIELDS:
            if required and not str(getattr(self, key, "")).strip():
                out.append(f'"{label}" is required — the ranking depends on it')
        return out

    def validate(self) -> None:
        p = self.problems()
        if p:
            raise ValueError("intake form is not usable:\n  - " + "\n  - ".join(p))

    # -- the part the models actually see -----------------------------------
    def context_block(self) -> str:
        """
        Rendered once per run and prepended to every model call for the accession.
        Kept as plain prose because that is what the archivist wrote; reformatting
        it into a schema loses the hedging that tells the model when to be unsure.
        """
        lines = [
            "You are helping a university records and information management",
            "committee process a backlog accession. Everything below was written by",
            "the archivist who accepted the material. Treat it as authoritative about",
            "what matters; treat your own judgement as provisional.",
            "",
            f"Accession: {self.accession} — {self.name}",
            f"Job type: {self.job_type}",
        ]
        for key, label, _ in FIELDS:
            val = str(getattr(self, key, "")).strip()
            if val:
                lines.append(f"\n{label}\n{val}")
        lines += [
            "",
            "Two standing rules for this accession:",
            "1. You never decide the fate of a file. You describe it, flag it, rank it,",
            "   and say why. A person makes every keep, archive, and delete decision.",
            "2. When the material does not give you enough to be sure, say so through a",
            "   low confidence score rather than inventing detail. A hedge is useful;",
            "   a confident wrong title is worse than no title.",
        ]
        return "\n".join(lines)

    def priorities(self) -> list[str]:
        """Keyword handles pulled out of the retention priorities, for the no-model path."""
        text = f"{self.valuable} {self.scope} {self.research}".lower()
        words = re.findall(r"[a-z][a-z\-']{3,}", text)
        stop = {
            "this", "that", "with", "from", "have", "been", "were", "they", "their", "them",
            "what", "when", "which", "will", "would", "should", "could", "there", "these",
            "those", "than", "then", "into", "onto", "over", "under", "about", "anything",
            "everything", "something", "keep", "keeping", "retain", "retained", "worth",
            "even", "also", "only", "just", "very", "most", "more", "some", "such", "same",
            "form", "asks", "material", "files", "file", "frame", "name", "named",
        }
        seen, out = set(), []
        for w in words:
            if w in stop or w in seen:
                continue
            seen.add(w)
            out.append(w)
        return out[:60]

    def exclusions(self) -> list[str]:
        text = f"{self.exclude}".lower()
        return [w for w in re.findall(r"[a-z][a-z\-']{3,}", text)][:40]

    # -- io -----------------------------------------------------------------
    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: dict) -> "IntakeForm":
        d = dict(d or {})
        # tolerate the web form's camelCase and a couple of older field names
        alias = {
            "jobType": "job_type", "type": "job_type",
            "sourceFolder": "source_folder", "boxFolder": "source_folder",
            "folder": "source_folder", "filters": "process_classes",
            "processClasses": "process_classes",
            "submittedAt": "submitted_at", "submittedBy": "submitted_by",
            "runHistory": "run_history", "id": "accession",
        }
        for old, new in alias.items():
            if old in d and new not in d:
                d[new] = d.pop(old)
        known = {f for f in cls.__dataclass_fields__}
        extra_notes = {k: v for k, v in d.items() if k not in known}
        clean = {k: v for k, v in d.items() if k in known}
        form = cls(**clean)
        if extra_notes and not form.notes:
            form.notes = json.dumps(extra_notes, ensure_ascii=False)
        if isinstance(form.process_classes, str):
            form.process_classes = [c.strip() for c in form.process_classes.split(",") if c.strip()]
        return form

    @classmethod
    def load(cls, path: str | Path) -> "IntakeForm":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")
        return path

    def submit(self, by: str = "") -> "IntakeForm":
        self.submitted_at = datetime.now().astimezone().isoformat(timespec="seconds")
        self.submitted_by = by or self.submitted_by
        if self.status == "draft":
            self.status = "queued"
        return self


def load_all(directory: str | Path) -> list[IntakeForm]:
    d = Path(directory)
    if not d.exists():
        return []
    forms = []
    for p in sorted(d.glob("*.json")):
        try:
            forms.append(IntakeForm.load(p))
        except Exception as e:                                  # noqa: BLE001
            print(f"  ! skipping unreadable intake form {p.name}: {e}")
    return forms


def queued(directory: str | Path) -> list[IntakeForm]:
    return [f for f in load_all(directory) if f.status in ("queued", "locked")]


def slugify(text: str, limit: int = 48) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return text[:limit].strip("-") or "untitled"
