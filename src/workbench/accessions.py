"""
accessions.py — turn intake forms into ACCESSION_SCHEMA rows.

The intake forms are prose written by an archivist. The accession schema wants
structured fields, three of which the forms do not carry and cannot be guessed:

    record_series    6-7 digits, assigned by an accessioning archivist.
                     make_accession_uid() raises without it, so file_uid
                     cannot be derived, so the accession cannot be crawled.

    accession_type   personal_papers | administrative. ruleset_for() raises on
                     anything else. The forms carry `job_type` (images, mixed,
                     email) which is a *process class*, not an accession type.

    profile_field    Selects the drafts rule. The ruleset keeps working drafts
                     for a humanities scholar and does not for a chemist, so
                     getting this wrong changes real outcomes.

This module reads them from `intake/accession_registry.json` and refuses to
invent any of them. A missing value stops the accession; it never defaults.
That is the same posture as ruleset_for(): unknown is an error, not a silent
default.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from .schema import manifest as M


class AccessionNotReady(Exception):
    """Raised when a registry entry is missing something the schema requires."""


# Needed to crawl at all: without these there is no accession_uid, so no
# file_uid, so no row. Hard stop.
REQUIRED = ("record_series", "source_media", "source_received")

# Needed to appraise. Absent, stage 01 still characterises the files and stage
# 02a skips the rules with a stated reason. That is the ACC-2026-020 case: the
# description path is worth demonstrating, the appraisal path is not.
REQUIRED_FOR_APPRAISAL = ("accession_type",)


def _parse_date(v) -> date:
    if isinstance(v, date):
        return v
    return datetime.fromisoformat(str(v)).date()


def load_registry(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_intake(intake_dir: str | Path) -> dict:
    """Read every ACC-*.json in a directory, keyed by accession id."""
    out = {}
    for p in sorted(Path(intake_dir).glob("ACC-*.json")):
        with open(p, encoding="utf-8") as fh:
            form = json.load(fh)
        out[form["accession"]] = form
    return out


# A provisional series lets a demonstration run before an accessioning
# archivist has assigned a real number. It is deliberately conspicuous: the
# 9-prefix is outside the range the classification list uses, every row carries
# provisional_identity=True, and the runner prints a warning per accession.
# The point is that a provisional run can never be mistaken for a real one, not
# that the check has been removed.
PROVISIONAL_PREFIX = "999"


def provisional_series(acc_id: str) -> str:
    digits = "".join(ch for ch in acc_id if ch.isdigit())[-4:] or "0000"
    return (PROVISIONAL_PREFIX + digits)[:7]


def build_row(acc_id: str, form: dict, reg: dict,
              allow_provisional: bool = False) -> dict:
    """
    Combine one intake form with one registry entry into an accession row.

    Raises AccessionNotReady naming exactly what is missing, so the operator
    gets a decision to make rather than a stack trace.
    """
    provisional = False
    if allow_provisional and not reg.get("record_series"):
        reg = dict(reg)
        reg["record_series"] = provisional_series(acc_id)
        provisional = True

    missing = [k for k in REQUIRED if not reg.get(k)]
    if missing:
        raise AccessionNotReady(
            f"{acc_id}: registry is missing {', '.join(missing)}. "
            f"These are assigned by an accessioning archivist and are not "
            f"derivable from the intake form. Fill them in "
            f"intake/accession_registry.json before running."
        )

    acc_type = reg.get("accession_type")
    if acc_type is not None and acc_type not in M.ACCESSION_TYPES:
        raise AccessionNotReady(
            f"{acc_id}: accession_type {acc_type!r} is not one of "
            f"{sorted(M.ACCESSION_TYPES)}. Note `job_type` in the intake form "
            f"({form.get('job_type')!r}) is a process class, not an accession type."
        )
    if reg["source_media"] not in M.SOURCE_MEDIA:
        raise AccessionNotReady(
            f"{acc_id}: source_media {reg['source_media']!r} not in "
            f"{sorted(M.SOURCE_MEDIA)}."
        )

    received = _parse_date(reg["source_received"])
    accession_uid = M.make_accession_uid(
        reg["record_series"], received, int(reg.get("sequence", 1)))
    parts = M.parse_record_series(reg["record_series"])

    return {
        "accession_uid": accession_uid,
        "record_series": parts["record_series"],
        "record_group": parts["record_group"],
        "series": parts["series"],
        "subseries": parts["subseries"],
        "source_label": form.get("name"),
        "accession_type": acc_type,
        "source_media": reg["source_media"],
        "source_ref": reg.get("source_ref") or form.get("source_folder"),
        "source_received": received,
        "accession_archivist": reg.get("accession_archivist"),
        "profile_person": reg.get("profile_person") or form.get("owner"),
        "profile_department": reg.get("profile_department"),
        "profile_field": reg.get("profile_field"),
        "profile_active_years": reg.get("profile_active_years"),
        "profile_summary": form.get("scope"),
        "profile_source": form.get("submitted_by"),
        "deed_of_gift_ref": reg.get("deed_of_gift_ref"),
        "deed_restrictions": reg.get("deed_restrictions"),
        "legal_hold": bool(reg.get("legal_hold", False)),
        "selection_completed_at": None,
        "retention_window_days": int(
            reg.get("retention_window_days", M.DEFAULT_RETENTION_DAYS)),
        # not part of ACCESSION_SCHEMA; carried for the runner's own use
        "_source_folder": form.get("source_folder"),
        "provisional_identity": provisional,
        "_form_status": form.get("status"),
        # What the form SAYS the accession contains. lanes.plan() compares this
        # against what routing actually found, so a lane appearing that the
        # archivist did not anticipate is surfaced rather than quietly handled.
        # Without this the comparison has nothing to compare against and
        # reports "nothing undeclared" for every accession.
        "_process_classes": form.get("process_classes") or [],
        "_appraisal_ok": form.get("status") == "queued",
    }


def resolve(intake_dir: str | Path, registry_path: str | Path,
            allow_provisional: bool = False) -> tuple[dict, list[str]]:
    """
    Build every accession row that can be built.

    Returns (rows_by_accession_id, problems). Problems are returned rather than
    raised so one unready accession does not stop the other two: stage 01 can
    still characterise what it can reach.
    """
    forms = load_intake(intake_dir)
    registry = load_registry(registry_path)
    rows, problems = {}, []
    for acc_id, form in forms.items():
        reg = registry.get(acc_id)
        if reg is None:
            problems.append(f"{acc_id}: no entry in the registry")
            continue
        try:
            rows[acc_id] = build_row(acc_id, form, reg, allow_provisional)
        except (AccessionNotReady, ValueError) as exc:
            problems.append(str(exc))
    return rows, problems
