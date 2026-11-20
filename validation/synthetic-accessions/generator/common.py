"""
Shared registry and scenario constants for the synthetic accession.

Every builder writes a file through `reg.add(...)`, which records the ground-truth
label alongside the path. Nothing in this corpus is real: people, sites, grant
numbers, identifiers, SSNs (900-series, never issued), phone numbers (555-01xx)
and email domains (*.example.*) are invented.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
from dataclasses import dataclass, field, asdict
from pathlib import Path

SEED = 20261113
random.seed(SEED)

REPO = Path(__file__).resolve().parents[1]
CORPUS = REPO / "corpus"
ROOT_NAME = "Achterberg_Desktop"
ROOT = CORPUS / ROOT_NAME
LABELS = REPO / "labels"
ACCESSION = "ACC-SYN-2026-001"

# --------------------------------------------------------------------------
# Scenario: all fictional
# --------------------------------------------------------------------------
DONOR = "Miriam K. Achterberg"
DONOR_EMAIL = "machterberg@illinois.example.edu"
DEPT = "Department of Entomology"
LAB = "Achterberg Pollinator Ecology Lab"
GRANT = "NSF DEB-1900417"
GRANT_TITLE = ("Collaborative Research: Recovery trajectories of native bee "
               "communities across a 30-year chronosequence of restored tallgrass prairie")

PEOPLE = {
    "achterberg": ("Miriam Achterberg", DONOR_EMAIL),
    "quintero":   ("Rafael Quintero", "rquintero@stats.prairiestate.example.edu"),
    "natarajan":  ("Priya Natarajan", "pnatara2@illinois.example.edu"),
    "feld":       ("Jonah Feld", "jfeld3@illinois.example.edu"),
    "penner":     ("Doug Penner", "dpenner@illinois.example.edu"),
    "lindqvist":  ("Karen Lindqvist", "karen.lindqvist@dnr.illinois.example.gov"),
    "ritter":     ("Harold Ritter", "hjritter.farm@mailbox.example.com"),
    "okonkwo":    ("Adaeze Okonkwo", "aokonkwo@illinois.example.edu"),     # dept head
    "baptiste":   ("Celine Baptiste", "cbaptiste@xerces-like.example.org"),
    "deptadmin":  ("Entomology Office", "ento-office@illinois.example.edu"),
    "tom":        ("Tom Achterberg", "tom.achterberg@mailbox.example.com"),  # spouse
    "editor":     ("Journal of Pollination Ecology Editorial Office", "jpe-editorial@journals.example.org"),
    "it":         ("Campus IT Help Desk", "help@techservices.illinois.example.edu"),
    "vendor":     ("BugSupply Co.", "deals@bugsupply.example.com"),
    "reporter":   ("Lena Ortiz", "lortiz@champaigncourier.example.com"),
}

SITES = [
    # code, name, county, restored_year, lat, lon, ownership
    ("SBP", "Sangamon Bend Prairie",      "Piatt",     1992, 40.0712, -88.6431, "state"),
    ("KRR", "Kickapoo Ridge Restoration", "Vermilion", 1998, 40.1489, -87.7402, "state"),
    ("HCP", "Hollis Creek Prairie",       "Champaign", 2003, 40.2511, -88.1903, "university"),
    ("MLP", "Meadowlark Prairie",         "Champaign", 2008, 40.0398, -88.3127, "county"),
    ("OTW", "Old Tile Works Prairie",     "Douglas",   2011, 39.8102, -88.2785, "county"),
    ("BRF", "Ritter Farm Remnant",        "Ford",      1900, 40.5521, -88.0164, "private"),  # remnant, sensitive
    ("WCR", "Willow Creek Restoration",   "Macon",     2014, 39.8925, -88.8213, "state"),
    ("PEN", "Pennant Hill Prairie",       "Coles",     2016, 39.4630, -88.1702, "private"),
    ("CRB", "Cardinal Bluff Planting",    "Champaign", 2018, 40.1802, -88.0910, "university"),
    ("LAF", "Lafayette Road Planting",    "Champaign", 2019, 40.0601, -88.2410, "university"),
]

BEE_TAXA = [
    "Bombus impatiens", "Bombus griseocollis", "Bombus bimaculatus", "Bombus auricomus",
    "Bombus pensylvanicus", "Bombus affinis", "Agapostemon virescens", "Augochlora pura",
    "Augochlorella aurata", "Halictus ligatus", "Lasioglossum pilosum", "Lasioglossum versatum",
    "Melissodes bimaculatus", "Melissodes trinodis", "Ceratina calcarata", "Ceratina dupla",
    "Andrena commoda", "Andrena carlini", "Megachile brevis", "Megachile mendica",
    "Hylaeus affinis", "Calliopsis andreniformis", "Svastra obliqua", "Xylocopa virginica",
    "Apis mellifera", "Nomada articulata", "Triepeolus lunatus", "Coelioxys octodentata",
]

# --------------------------------------------------------------------------
# Label vocabulary
# --------------------------------------------------------------------------
RELEVANCE = ("high", "moderate", "low", "none")
SENSITIVITY = ("none", "pii_contact", "pii_ssn", "ferpa_student", "hr_personnel",
               "medical", "financial_personal", "confidential_peer_review",
               "sensitive_location", "credentials", "minor_child")
LANES = ("document", "tabular", "image", "av", "email", "code", "scientific",
         "geospatial", "database", "archive", "system", "unknown")
ACTIONS = ("appraise", "exclude_system_file", "exclude_duplicate", "review_near_duplicate",
           "route_human_unidentified", "route_human_encrypted", "route_human_corrupt",
           "expand_container", "restrict_sensitive")


@dataclass
class Label:
    path: str                      # relative to corpus/
    relevance: str
    relevance_rationale: str       # which intake clause decides it, in words
    sensitivity: list[str]
    lane: str
    expected_action: str
    gt_title: str
    gt_summary: str
    gt_keywords: list[str]
    tags: list[str] = field(default_factory=list)
    true_format: str = ""          # what the bytes actually are
    nominal_date: str = ""         # the date the material belongs to
    container: str = ""            # archive this member lives inside, if any
    duplicate_of: str = ""
    difficulty: str = "obvious"    # obvious | subtle | ambiguous
    # filled at finalise
    size_bytes: int = 0
    sha256: str = ""
    extension: str = ""


class Registry:
    def __init__(self, root_name: str = ROOT_NAME):
        self.root_name = root_name
        self.root = CORPUS / root_name
        self.labels: dict[str, Label] = {}
        self.folders: dict[str, dict] = {}

    def p(self, rel: str) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def add(self, rel: str, relevance: str, why: str, *, lane: str, title: str,
            summary: str, keywords=(), sens=("none",), action="appraise", tags=(),
            fmt="", date="", difficulty="obvious", container="", duplicate_of=""):
        assert relevance in RELEVANCE, relevance
        assert lane in LANES, lane
        assert action in ACTIONS, action
        for s in sens:
            assert s in SENSITIVITY, s
        key = f"{self.root_name}/{rel}" if not container else f"{container}::{rel}"
        self.labels[key] = Label(
            path=key, relevance=relevance, relevance_rationale=why,
            sensitivity=list(sens), lane=lane, expected_action=action,
            gt_title=title, gt_summary=summary, gt_keywords=list(keywords),
            tags=list(tags), true_format=fmt, nominal_date=date,
            container=container, duplicate_of=duplicate_of, difficulty=difficulty,
        )

    def folder(self, rel: str, relevance: str, summary: str):
        self.folders[f"{self.root_name}/{rel}".rstrip("/")] = {
            "folder": f"{self.root_name}/{rel}".rstrip("/"),
            "dominant_relevance": relevance, "gt_summary": summary}

    def finalise(self):
        for key, lab in self.labels.items():
            lab.extension = Path(key.split("::")[-1]).suffix.lower()
            if lab.container:
                continue
            f = CORPUS / key
            if not f.exists():
                raise FileNotFoundError(key)
            lab.size_bytes = f.stat().st_size
            lab.sha256 = sha256(f)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


reg = Registry()


def write_text(rel: str, text: str, encoding="utf-8") -> Path:
    path = reg.p(rel)
    path.write_text(text, encoding=encoding, newline="")
    return path


def rng(name: str) -> random.Random:
    """Independent deterministic stream per builder, so editing one builder
    does not reshuffle every other file."""
    return random.Random(f"{SEED}:{name}")
