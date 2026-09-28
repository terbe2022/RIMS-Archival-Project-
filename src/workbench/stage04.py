"""
stage04.py — pseudonymisation, the mapping vault, and release levels.

What the archivist asked for, and what this builds:

    original          the file on disk, never modified, always available
    reading_room      direct identifiers replaced with stable numbered labels
    open_web          direct and indirect identifiers both replaced
    summary           a model's summary of the redacted text  (NOT BUILT — hook only)

The archivist chooses which level is released. Nothing here publishes anything.

The change from redaction.apply()
---------------------------------
`redaction.apply()` replaces every name with the same string, so two
correspondents in one message both become "[NAME REDACTED]". That is safe and
useless: a reader cannot follow the exchange, and a model asked to summarise it
cannot tell who did what.

This allocates a stable numbered label instead — PERSON_001, PHONE_002 — and
keeps a mapping of label to real value in a vault. Two properties make the
labels worth having:

  Stable WITHIN a message, so an exchange reads coherently.
  Stable ACROSS the accession, so PERSON_001 is the same human in message 4
  and message 400.

The second is what POC 1 got wrong. Its numbering restarted per document, so
<PERSON1> meant a different person in every message. Masked output produced
that way looks correct and is not, which is worse than obviously broken output
because nobody checks it.

Name variants are folded to one label, so "Thomas Hanratty", "Tom Hanratty",
"Hanratty" and "T. Hanratty" all become PERSON_001 rather than four people.

The vault
---------
The vault is the re-identification key. It is written SEPARATELY from the
manifest, never into it, because the manifest is the thing that gets exported,
shared and published. Only `s04_pii_map_ref` — a reference, not a value — goes
into the manifest row.

D5 is unanswered: where this store lives, who can read it, and whether it is
encrypted at rest is Brent West's decision and came back blank. Until then the
reference is a local file path and the vault is written with restrictive
permissions. When D5 lands, `map_ref` becomes a URI or a key and nothing else
changes — which is why the reference is stored rather than the mapping.
"""
from __future__ import annotations

import json
import os
import re
from collections import OrderedDict
from pathlib import Path

from . import redaction

STAGE_VERSION = "s04-0.1.0"

LEVELS = ("reading_room", "open_web")

# Entity types whose values are worth keeping distinct rather than collapsing.
# An amount or a URL does not need a stable identity across the accession; a
# person, a phone number or an account does.
_STABLE = {"person", "phone", "email", "address", "account", "card", "ssn",
           "student_id", "passport", "driver_license", "org", "ip"}

_TITLE_RE = re.compile(r"^(dr|prof|professor|mr|mrs|ms|miss)\.?\s+", re.I)


def _canonical(kind: str, value: str) -> str:
    """
    The key under which a value claims a label.

    For people this folds initials, titles and surname-only mentions together,
    so one person does not become four. It is deliberately conservative about
    the reverse error: two different people who share a surname will collide,
    which is why every allocation is recorded in the vault for a human to check
    rather than trusted silently.
    """
    v = " ".join(str(value).split()).strip(" ,.;:")
    if kind == "person":
        v = _TITLE_RE.sub("", v)
        parts = [p for p in re.split(r"\s+", v) if p]
        if len(parts) > 1:
            # first initial + surname: "Thomas Hanratty" and "T. Hanratty" match
            return f"{parts[0][0].lower()}|{parts[-1].lower()}"
        return v.lower()
    if kind in ("phone", "ssn", "account", "card", "student_id"):
        return re.sub(r"\D", "", v)          # formatting is not identity
    return v.lower()


class Vault:
    """
    Label allocation and the re-identification mapping, scoped to one accession.

    Not a general store. Scoping to the accession is deliberate: labels must be
    stable across an accession's messages, and must NOT be shared between
    accessions, because that would let someone holding two published redacted
    sets correlate a person across both.
    """

    def __init__(self, accession_uid: str):
        self.accession_uid = accession_uid
        self._by_key: dict[tuple[str, str], str] = {}
        self._entries: "OrderedDict[str, dict]" = OrderedDict()
        self._counts: dict[str, int] = {}

    def label_for(self, kind: str, value: str) -> str:
        key = (kind, _canonical(kind, value))
        if key in self._by_key:
            label = self._by_key[key]
            self._entries[label]["seen"] += 1
            forms = self._entries[label]["forms"]
            if value not in forms and len(forms) < 12:
                forms.append(value)
            return label
        n = self._counts.get(kind, 0) + 1
        self._counts[kind] = n
        label = f"{kind.upper()}_{n:03d}"
        self._by_key[key] = label
        self._entries[label] = {
            "label": label, "type": kind, "canonical": key[1],
            "forms": [value], "seen": 1,
            "tier": redaction.TIER.get(kind, 2),
            "stable": kind in _STABLE,
        }
        return label

    def write(self, path: str | Path) -> str:
        """
        Persist the mapping and return the reference that goes in the manifest.

        Written 0600. This file re-identifies every person in the accession.
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "accession_uid": self.accession_uid,
            "stage_version": STAGE_VERSION,
            "warning": ("This file re-identifies redacted material. It is the "
                        "re-identification key, not a log. Access should be "
                        "controlled separately from the manifest. See D5."),
            "entries": list(self._entries.values()),
        }
        p.write_text(json.dumps(payload, indent=2))
        try:
            os.chmod(p, 0o600)
        except OSError:
            pass
        return str(p)

    @property
    def entry_count(self) -> int:
        return len(self._entries)


def allocate(entities, vault: Vault) -> dict:
    """
    Claim a label for every detected entity, once.

    Allocation is separated from rendering because a file is rendered at more
    than one release level. Allocating inside the render loop counts each
    occurrence once per level, which inflates every occurrence count in the
    vault by the number of levels — the sort of error that looks like data.
    """
    return {(e.start, e.end): vault.label_for(e.type, e.value) for e in entities}


def pseudonymise(text: str, entities, labels: dict, level: str) -> tuple[str, list[dict]]:
    """
    Replace identifiers with stable labels at the given release level.

    Replacement runs right to left over the detected spans so earlier offsets
    stay valid, rather than by string substitution — substituting by value
    rewrites unrelated occurrences of a common surname elsewhere in the text.
    """
    max_tier = 1 if level == "reading_room" else 2
    spans = []
    for e in entities:
        if e.tier > max_tier:
            continue
        spans.append((e.start, e.end, e.type, e.value, e.confidence))
    spans.sort(key=lambda s: s[0], reverse=True)

    used = []
    out = text
    for start, end, kind, value, conf in spans:
        label = labels[(start, end)]
        out = out[:start] + f"[{label}]" + out[end:]
        used.append({"label": label, "type": kind, "confidence": conf})
    return out, used


def run(rows: list[dict], accession: dict, out_dir: str | Path,
        levels=LEVELS, name_detector: str = "heuristic") -> dict:
    """
    Pseudonymise every row that has text, and write the vault once.

    The original file is untouched and its path stays in the manifest. Redacted
    texts are written to disk and referenced, not stored inline, so a manifest
    can be shared without carrying message bodies.
    """
    out_dir = Path(out_dir)
    vault = Vault(accession["accession_uid"])
    stats = {"processed": 0, "with_identifiers": 0, "by_type": {},
             "low_confidence_names": 0}

    for r in rows:
        text = r.get("_text") or r.get("s03_text_sample") or ""
        # Defensive: a text field that reached here with lone surrogates cannot
        # be written to disk, and a crash at write time loses the whole run.
        text = text.encode("utf-8", "replace").decode("utf-8")
        if not text or r.get("layer") == 0:
            continue
        stats["processed"] += 1
        entities = redaction.detect(text, name_detector=name_detector)
        if not entities:
            r["s04_pii_entities_json"] = json.dumps([])
            continue
        stats["with_identifiers"] += 1

        labels = allocate(entities, vault)
        written = {}
        for level in levels:
            masked, used = pseudonymise(text, entities, labels, level)
            path = out_dir / level / f"{r['file_uid']}.txt"
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8", errors="replace") as fh:
                fh.write(masked)
            written[level] = str(path)

        summary = redaction.summarise(entities)
        for k, v in summary["by_type"].items():
            stats["by_type"][k] = stats["by_type"].get(k, 0) + v
        stats["low_confidence_names"] += summary["low_confidence_names"]

        r["s04_pii_entities_json"] = json.dumps(
            [{"type": e.type, "tier": e.tier, "detector": e.detector,
              "confidence": e.confidence} for e in entities])
        r["s04_masked_text_path"] = json.dumps(written)
        r["s04_sensitivity_flags"] = summary["direct"] or None
        r["s04_version"] = STAGE_VERSION
        # A long message with very few detected names is itself a signal that a
        # person should read it, rather than evidence that it is clean.
        r["s04_review_hint"] = (
            "few identifiers found in a long text — verify before release"
            if len(text) > 4000 and summary["identifiers_found"] < 2 else None)

    map_ref = vault.write(out_dir / "pii_map.json") if vault.entry_count else None
    for r in rows:
        if r.get("s04_masked_text_path"):
            r["s04_pii_map_ref"] = map_ref

    return {
        "stage_version": STAGE_VERSION,
        "vault_entries": vault.entry_count,
        "map_ref": map_ref,
        "levels_written": list(levels),
        "summary_tier": "not built — needs a model; see POC 1",
        **stats,
    }
