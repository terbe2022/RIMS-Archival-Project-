"""
context.py — turn an intake form into prompt context, once per accession.

One function, used by every lane that calls a model: image description, document
summarisation, email summarisation. They should all see the same collection
context, or two lanes will describe the same accession from different premises.

The important thing this does is what it REFUSES to include.

`valuable` and `exclude` are excluded by construction, not by convention. Those
fields say what the archivist considers worth keeping, and they are what
relevance.py scores against. If they also reached the prompt, a model would
describe an ambiguous document in the vocabulary of the retention criteria, and
that description would then score highly against those same criteria — because
the prompt supplied the words, not because the document warranted them. The
score would be measuring the prompt.

So the allowed set is a whitelist, and adding to it is a decision someone has to
make deliberately. A blacklist would let a renamed field through silently.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

CONTEXT_VERSION = "ctx-0.1.0"

# Descriptive only: what this collection IS. Never what it is worth.
ALLOWED = ("source", "owner", "role", "scope", "research", "bio")

# Named so a future reader knows the omission was deliberate.
WITHHELD = ("valuable", "exclude")

# `access` reaches only the sensitivity pass, never the description pass.
SENSITIVITY_ONLY = ("access",)

_LABEL = {
    "source": "How the material arrived",
    "owner": "Whose collection this is",
    "role": "Their role",
    "scope": "What the collection covers",
    "research": "Subject area",
    "bio": "Background",
}

_MAX_FIELD = 700


def _clean(text) -> str:
    """
    Strip the archivist's working notes out of prose meant for a model.

    Intake forms carry instructions to colleagues — VERIFY, UNRESOLVED,
    PROVISIONAL — which are addressed to a person and would be read by a model
    as statements about the material.
    """
    if not text:
        return ""
    s = " ".join(str(text).split())
    s = re.sub(r"\b(VERIFY|UNRESOLVED|PROVISIONAL)\b[:.]?\s*", "", s)
    if len(s) > _MAX_FIELD:
        s = s[:_MAX_FIELD].rsplit(" ", 1)[0] + "…"
    return s.strip()


def form_hash(form: dict) -> str:
    """
    Identity of the form that produced a result.

    Recorded on every model output, because the intended way to correct a bad
    result is to edit the form and re-run — and that only works if you can tell
    which rows were produced by the old version. Without it, one edited sentence
    means re-running everything.
    """
    payload = json.dumps({k: form.get(k) for k in sorted(form)}, sort_keys=True,
                         default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def build(form: dict, *, sensitivity: bool = False) -> str:
    """
    The context block prepended to a model call for this accession.

    Returns "" when the form has no usable descriptive content — which is the
    ACC-2026-020 case. An empty block is the correct output there: nobody has
    said what those images are, so there is nothing to condition on, and the
    descriptions will be generic. That should be visible rather than papered
    over with a vague sentence that reads like context and is not.
    """
    parts = []
    for field in ALLOWED:
        raw = str(form.get(field) or "").strip()
        # Test the RAW value. _clean() strips the UNRESOLVED marker, so testing
        # the cleaned string never fires and a field explicitly marked unknown
        # gets passed to the model as though it were knowledge. On
        # ACC-2026-020 that meant telling a describer "Whose collection this
        # is: nothing in the delivery names a creator" — the absence of an
        # answer, formatted as an answer.
        if not raw or raw.upper().startswith(("UNRESOLVED", "NONE", "N/A", "TBD")):
            continue
        value = _clean(raw)
        if not value:
            continue
        parts.append(f"{_LABEL[field]}: {value}")

    if sensitivity:
        access = _clean(form.get("access"))
        if access:
            parts.append(f"Access conditions the archivist has specified: {access}")

    if not parts:
        return ""

    return ("Collection context. This material comes from a single archival "
            "accession, described by an archivist as follows.\n\n"
            + "\n".join(parts)
            + "\n\nUse this to understand what you are looking at. Describe only "
              "what is actually present in the item; do not assume the item "
              "contains something merely because the collection does.\n")


def describe_usage(form: dict) -> dict:
    """What was included, what was withheld, and why. For the run report."""
    included = [f for f in ALLOWED
                if str(form.get(f) or "").strip()
                and not str(form.get(f)).strip().upper().startswith(
                    ("UNRESOLVED", "NONE", "N/A", "TBD"))]
    return {
        "context_version": CONTEXT_VERSION,
        "form_hash": form_hash(form),
        "fields_included": included,
        "fields_withheld": [f for f in WITHHELD if form.get(f)],
        "withheld_reason": ("valuable/exclude are scoring criteria. Including "
                            "them in a description prompt would make the model "
                            "produce text that matches the criteria, and the "
                            "score would then measure the prompt rather than "
                            "the file."),
        "context_empty": not included,
    }
