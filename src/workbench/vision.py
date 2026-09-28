"""
vision.py — the image lane. Puts existing image-classification work into the
manifest instead of alongside it.

This does not reimplement the image pipeline. `archival_image_processing`
already has the parts that took real effort: a nine-category taxonomy covering
NAGPRA, HIPAA and FERPA, a prompt refined through a 1,200-call experiment, a
measured backend comparison, and a labelling guide precise enough to produce a
gold set. What it does not have is a route into the manifest, so its results sit
in `outputs.jsonl` files rather than in the same table as everything else.

Two entry points:

    ingest_jsonl()  read an existing run's outputs and merge them into manifest
                    rows. No GPU, no re-processing. Use this for work already
                    done.

    describe()      call a VLM for rows that have no description yet. Needs the
                    GPU. Checkpoints per batch, because the card is shared and
                    may go away mid-run.

On the flag itself
------------------
The prompt's central distinction is between an image that CONTAINS sensitive
content and an image whose SUBJECT is a difficult historical topic. A photograph
of a protest against a war is not violent content. That distinction is the
reason the flag is usable on archival material at all, and it is preserved here
rather than re-derived.

`offensive` is never written to s02_decision. It routes to restricted_review
through the same precedence rule as every other sensitivity signal, so an image
flagged by a model lands in a supervising archivist's queue and nowhere else.

On Method 1
-----------
The semantic-similarity method is deliberately NOT wired in. It embeds the
generated description and flags on cosine similarity against individual
taxonomy keywords, and the taxonomy mixes highly specific terms — blackface,
swastika, chief illiniwek — with extremely generic ones: costume, body, war,
application, confidential. Any photograph of people in costume matches
historical racialized performance; any battlefield photograph matches violence.
That is the mechanism behind the 73% ambiguous rate, and it is a taxonomy
problem rather than a threshold problem. Method 2's combined prompt gives a
category, a reason and a confidence, and was measured at 100% field validity.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

VISION_VERSION = "vision-0.1.0"

# The nine categories. Names must match the prompt exactly — it instructs the
# model never to invent new ones, and a renamed category here would silently
# drop every match.
CATEGORIES = (
    "historical racialized performance", "human remains",
    "native american imagery", "nudity/sexual content",
    "violence/graphic content", "hate symbols", "medical/health records",
    "student/pii records", "other sensitive categories",
)


def _norm_category(value) -> str | None:
    if not value:
        return None
    v = str(value).strip().strip(".").lower()
    if v in ("none", "n/a", "null", "false", ""):
        return None
    for c in CATEGORIES:
        if v == c or v.startswith(c[:18]):
            return c
    return f"unrecognised:{v[:40]}"


# Invalid JSON escapes. LLaVA writes markdown habits into its JSON —
# "offense\\_category" with an escaped underscore — and \\_ is not a legal JSON
# escape, so json.loads rejects the whole record over one character.
#
# Measured across the existing runs, on the 1,725 calls that intended JSON:
# 86.0% parse strictly, 13.1% are recovered by this repair, and 0.9% remain
# broken — those are responses truncated at a token limit mid-description.
# One call in eight is worth recovering, because the original parser returns
# PARSE_ERROR for them and a PARSE_ERROR is indistinguishable from an image
# the model had nothing to say about.
_BAD_ESCAPE = re.compile(r'\\(?!["\\\\/bfnrtu])')


def repair_json(text: str) -> str:
    """Remove backslashes that are not valid JSON escape introducers."""
    return _BAD_ESCAPE.sub("", text)


def parse_output(raw) -> dict:
    """
    Read one model response.

    The measured failure mode is titles exceeding the length bound (3 of 150 in
    the variant C run), not malformed JSON. A long title is a truncation
    problem, not a reason to discard a good description, so it is trimmed and
    the trim is recorded.
    """
    if isinstance(raw, dict):
        d = raw
    else:
        text = str(raw or "").strip()
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
        d = None
        for candidate in (text, repair_json(text)):
            try:
                d = json.loads(candidate)
                break
            except json.JSONDecodeError:
                continue
        if d is None:
            m = re.search(r"\{.*\}", text, re.S)
            if not m:
                return {"_error": "no JSON object in model output"}
            for candidate in (m.group(0), repair_json(m.group(0))):
                try:
                    d = json.loads(candidate)
                    break
                except json.JSONDecodeError as exc:
                    err = exc
            if d is None:
                return {"_error": f"unparseable JSON: {err}"}

    title = str(d.get("title") or "").strip()
    notes = []
    if len(title) > 100:
        title = title[:97].rstrip() + "…"
        notes.append("title truncated to 100 characters")

    offensive = d.get("offensive")
    if isinstance(offensive, str):
        offensive = offensive.strip().lower() in ("true", "yes", "1")

    category = _norm_category(d.get("offense_category"))
    # A flag must name what was seen and where. A model asserting "there is a
    # swastika" in a photograph of a football crowd is not making a judgement
    # call — it is hallucinating an object, and the tell is that it cannot
    # point at one. Requiring locating evidence turns an unfalsifiable claim
    # into a checkable one, and an unevidenced flag is downgraded rather than
    # dropped, because the model may still have seen something real.
    evidence = str(d.get("offense_evidence") or d.get("offense_reason") or "").strip()
    # The test is whether the evidence LOCATES the thing. A person who has
    # actually seen an object in a photograph says where it is — on a banner,
    # in the upper left, worn by a figure in the foreground. A model that has
    # invented one can only assert that it is present, because there is no
    # position to give. "due to the presence of a swastika symbol" is eleven
    # words and locates nothing.
    WHERE = ("left", "right", "upper", "lower", "top", "bottom", "centre",
             "center", "corner", "background", "foreground", "behind", "above",
             "below", "worn", "held", "banner", "sign", "wall", "flag", "board",
             "uniform", "sleeve", "armband", "wall of", "edge of", "middle")
    ev = evidence.lower()
    located = bool(evidence) and any(w in ev for w in WHERE)
    if offensive and not located:
        notes.append("flagged offensive without locating evidence — downgraded "
                     "to a description note; a person should still look")
        offensive = False
        category = None

    if offensive and not category:
        # Flagged with no category is not a usable flag: an archivist cannot
        # act on it and it cannot be counted. Recorded as a parse note so the
        # rate is visible rather than silently coerced.
        notes.append("flagged offensive with no category given")
    if category and not offensive:
        notes.append("category given without the offensive flag set")

    # Text descriptions carry three keys images do not. `readable` is the
    # important one: a model reporting that an extraction is unusable is giving
    # a correct answer, and discarding it would leave the file looking merely
    # undescribed rather than known-undescribable.
    readable = d.get("readable")
    if isinstance(readable, str):
        readable = readable.strip().lower() not in ("false", "no", "0")
    subjects = d.get("subjects")
    if isinstance(subjects, str):
        subjects = [s.strip() for s in subjects.split(",") if s.strip()]

    return {
        "title": title or None,
        "description": (str(d.get("description") or "").strip() or None),
        "subjects": subjects if isinstance(subjects, list) else None,
        "genre": (str(d.get("genre") or "").strip().lower() or None),
        "readable": True if readable is None else bool(readable),
        "offensive": bool(offensive),
        "offense_evidence": evidence or None,
        "category": category,
        "reason": (str(d.get("offense_reason") or "").strip() or None),
        "confidence": d.get("confidence"),
        "_notes": notes,
    }


def to_manifest(parsed: dict, model: str | None = None,
                prompt_version: str = "combined-c-v4") -> dict:
    """Map one parsed response onto manifest columns."""
    row = {
        "s04_description": parsed.get("description"),
        "s04_summary": parsed.get("title"),
        "dc_title": parsed.get("title"),
        "s04_doc_type": parsed.get("genre") or "image",
        "s04_model": model,
        "s04_prompt_version": prompt_version,
        "s04_version": VISION_VERSION,
    }
    if parsed.get("offensive") and parsed.get("category"):
        row["s04_sensitivity_flags"] = [parsed["category"]]
        row["s04_sensitivity_scores_json"] = json.dumps({
            "category": parsed["category"],
            "reason": parsed.get("reason"),
            "confidence": parsed.get("confidence"),
            "source": "vlm-combined-prompt",
        })
    if parsed.get("subjects"):
        row["dc_subject"] = "; ".join(str(x) for x in parsed["subjects"][:8])
    if parsed.get("readable") is False:
        # Recorded as a fact about the file, not as a failure of the run. The
        # description explains why, and the title stays empty rather than being
        # filled with something invented.
        row["s04_error"] = ("model reports the extracted text does not support "
                            "a description")
        row["dc_title"] = None
        row["s04_summary"] = None

    notes = parsed.get("_notes") or []
    if parsed.get("_error"):
        row["s04_error"] = parsed["_error"]
    elif notes:
        row["s04_error"] = "; ".join(notes)
    return row


def ingest_jsonl(rows: list[dict], jsonl_path: str | Path,
                 model: str | None = None) -> dict:
    """
    Merge an existing image-classification run into manifest rows.

    Matches on filename rather than full path, because the image pipeline ran
    against its own directory layout and the manifest holds accession-relative
    paths. Filenames in this corpus are sequential and unique, so this is safe
    here; it would not be in a corpus with repeated names across folders, and
    the collision count is reported so that assumption stays visible.
    """
    by_name: dict[str, list[dict]] = {}
    for r in rows:
        by_name.setdefault(Path(r.get("filename") or "").name, []).append(r)

    matched = unmatched = flagged = errors = 0
    collisions = sum(1 for v in by_name.values() if len(v) > 1)
    categories: dict[str, int] = {}
    warmups = 0

    with open(jsonl_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                errors += 1
                continue
            # Benchmark runs include warm-up calls whose results are real but
            # were made to prime the server. Counting them would double-count.
            if rec.get("is_warmup"):
                warmups += 1
                continue
            if not rec.get("success", True):
                errors += 1
                continue

            name = Path(str(rec.get("image_path") or "")).name
            targets = by_name.get(name)
            if not targets:
                unmatched += 1
                continue

            parsed = parse_output(rec.get("output"))
            update = to_manifest(parsed, model=model or rec.get("model"))
            for t in targets:
                t.update(update)
            matched += 1
            if parsed.get("category"):
                flagged += 1
                categories[parsed["category"]] = categories.get(parsed["category"], 0) + 1

    return {
        "stage_version": VISION_VERSION,
        "matched": matched,
        "unmatched_in_jsonl": unmatched,
        "warmup_skipped": warmups,
        "parse_or_call_errors": errors,
        "flagged": flagged,
        "by_category": categories,
        "filename_collisions": collisions,
        "note": ("Flags route to restricted_review through the standard "
                 "precedence rule. No image is discarded on a model's say-so."),
    }


def apply_flags(rows: list[dict]) -> int:
    """
    Route flagged images to a supervising archivist.

    Uses the same precedence rule as every other sensitivity signal rather than
    writing a decision directly, so a model flag cannot produce an outcome that
    the rules would not also produce.
    """
    from .schema import manifest as M
    n = 0
    for r in rows:
        if not r.get("s04_sensitivity_flags"):
            continue
        # A file that matched no rule arrives with s02_decision unset.
        # resolve_decision requires one of the four values and is right to —
        # but "no rule had an opinion" IS a decision in this vocabulary, and it
        # is spelled not_selected. Passing None instead crashed the run as soon
        # as enough images were described for the case to occur.
        before = r.get("s02_decision") or "not_selected"
        r["s02_decision"] = M.resolve_decision(before, r["s04_sensitivity_flags"])
        r["layer"] = M.compute_layer(r)
        if r["s02_decision"] != before:
            n += 1
    return n
