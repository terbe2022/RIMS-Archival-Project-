"""
stage02a.py — free exclusions and the appraisal rules. No GPU, no model.

Issue #15 defines the scope: exact duplicates by hash, NSRL known files,
zero-byte, `~$` lock files, `.DS_Store`, `Thumbs.db`, caches, `node_modules`,
`.git` internals. Nothing is deleted. Every exclusion is written to the
manifest as a Layer 0 decision, which a person can inspect and reverse.

Perceptual near-duplicates use a 256-bit dhash at a threshold of 18 bits. An
8x8 average hash calls every landscape a copy of every other landscape and must
not be used here; the measured separation on this corpus is 17 bits for a
next-exposure pair against 79 for different subjects, which only survives at
256 bits.

The rules come from schema.rules and are applied through resolve_decision(),
so sensitivity beats discard by precedence rather than by weight. A file that
matches nothing becomes `not_selected` — "no rule had an opinion" — and never
`discard_candidate`.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from .schema import manifest as M
from .schema.rules import POLICY_VERSION, evaluate, ruleset_for

STAGE_VERSION = "s02a-0.1.0"
DHASH_BITS = 256
DHASH_THRESHOLD = 18

# --------------------------------------------------------- structural junk --
_JUNK_NAMES = {
    ".ds_store": "macos_finder_metadata",
    "thumbs.db": "windows_thumbnail_cache",
    "desktop.ini": "windows_folder_config",
    "ehthumbs.db": "windows_thumbnail_cache",
    ".localized": "macos_marker",
    "icon\r": "macos_custom_icon",
}
_JUNK_DIR_PARTS = {
    "node_modules": "dependency_tree",
    ".git": "vcs_internals",
    ".svn": "vcs_internals",
    "__pycache__": "bytecode_cache",
    ".cache": "cache_directory",
    "$recycle.bin": "recycle_bin",
    ".trashes": "trash",
    "system volume information": "filesystem_metadata",
}
_LOCK_RE = re.compile(r"^~\$")
_APPLEDOUBLE_RE = re.compile(r"^\._")


def structural_exclusion(row: dict) -> str | None:
    """
    Return an exclusion reason, or None. Named reasons, not a boolean, so the
    reduction figure can be broken down by cause when someone asks what the
    percentage is actually made of.
    """
    name = (row.get("filename") or "")
    low = name.lower()
    if low in _JUNK_NAMES:
        return _JUNK_NAMES[low]
    if _LOCK_RE.match(name):
        return "office_lock_file"
    if _APPLEDOUBLE_RE.match(name):
        return "appledouble_resource_fork"
    parts = [p.lower() for p in Path(row.get("path_norm") or "").parts[:-1]]
    for part in parts:
        if part in _JUNK_DIR_PARTS:
            return _JUNK_DIR_PARTS[part]
    if row.get("size_bytes") == 0:
        return "zero_byte"
    return None


# ---------------------------------------------------------------- NSRL ----
class NSRL:
    """
    National Software Reference Library known-file lookup.

    Issue #15 lists this as a free exclusion. It is not wired up: the RDS set
    is a multi-gigabyte download and huggingface.co and api.box.com are blocked
    from urbadvanalytics1, so where it comes from is an open question.

    Absent, this reports `available=False` and every row gets s02_nsrl_hit=None
    rather than False. None means "not checked"; False would claim we looked.
    The distinction matters because NSRL is plausibly a large share of the
    reduction percentage on a tree like Hanratty's, and a run that silently
    skipped it would understate the number without saying so.
    """

    def __init__(self, sha1_set: set[str] | None = None):
        self.sha1_set = sha1_set
        self.available = sha1_set is not None

    def hit(self, sha1: str | None) -> bool | None:
        if not self.available:
            return None
        return sha1 is not None and sha1.lower() in self.sha1_set


# ----------------------------------------------------------- exact dupes --
# Names that mark a file as a derived copy rather than the original. The
# Hanratty tree carries Dropbox conflict markers from 2011 and `.doc 1` /
# `.pdf 1` mangled extensions from the same event. Sorting those purely
# alphabetically makes " 1" sort ahead of the clean name, which would elect the
# damaged copy as canonical and point the intact file at it as a duplicate.
_CONFLICT_RE = re.compile(
    r"(conflicted copy|\(\d+\)|\bcopy\b|\.\w{2,4} \d+$|~\d+$)", re.IGNORECASE)


def _canonical_rank(row: dict) -> tuple:
    """
    Order candidates for "which of these identical files is the original".
    Clean names first, then shallowest, then alphabetical for determinism.
    """
    name = row.get("filename") or ""
    return (
        1 if _CONFLICT_RE.search(name) else 0,
        1 if row.get("s01_ext_mismatch") else 0,
        row.get("depth", 0),
        row.get("path_norm") or "",
    )


def collapse_exact(rows: list[dict]) -> int:
    """
    Group by sha256, keep the shallowest-then-alphabetical path as the original,
    point the rest at it. Nothing is removed from the manifest.
    """
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        h = r.get("content_sha256")
        if h and r.get("size_bytes"):
            groups[h].append(r)

    n = 0
    for h, members in groups.items():
        if len(members) < 2:
            for m in members:
                m["duplicate_count"] = 1
            continue
        members.sort(key=_canonical_rank)
        keeper = members[0]
        keeper["duplicate_count"] = len(members)
        for dup in members[1:]:
            dup["duplicate_of"] = keeper["file_uid"]
            dup["duplicate_count"] = len(members)
            n += 1
    return n


# ------------------------------------------------------------- near dupes --
def dhash256(path: str | Path) -> int | None:
    """
    256-bit difference hash: 17x16 grayscale, compare horizontally adjacent
    pixels. Returns an int, or None if the image cannot be read.
    """
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(path) as im:
            im = im.convert("L").resize((17, 16), Image.LANCZOS)
            px = list(im.getdata())
    except Exception:
        return None
    bits = 0
    for y in range(16):
        base = y * 17
        for x in range(16):
            bits = (bits << 1) | int(px[base + x] > px[base + x + 1])
    return bits


def near_duplicates(rows: list[dict], threshold: int = DHASH_THRESHOLD) -> int:
    """
    Flag perceptual near-duplicates among rows that already have a dhash.

    Pairwise within an accession. At sample scale that is fine; at 12,000
    images it wants BK-tree bucketing, which is a change of data structure and
    not of threshold.
    """
    imgs = [r for r in rows if r.get("_dhash") is not None and not r.get("duplicate_of")]
    imgs.sort(key=lambda r: r.get("path_norm") or "")
    n = 0
    for i, a in enumerate(imgs):
        if a.get("duplicate_of"):
            continue
        for b in imgs[i + 1:]:
            if b.get("duplicate_of"):
                continue
            if bin(a["_dhash"] ^ b["_dhash"]).count("1") <= threshold:
                b["duplicate_of"] = a["file_uid"]
                b["s02_structural_exclusion"] = "near_duplicate_image"
                n += 1
    return n


# ---------------------------------------------------------------- rules ----
def apply_rules(rows: list[dict], accession: dict) -> dict:
    """
    Apply the appraisal ruleset. Returns a small report.

    If accession_type is absent the rules are SKIPPED, not defaulted. Every row
    gets s02_status='skipped' and a stated reason. This is the 020 case: the
    intake form is draft, nobody has said what the images are, and scoring them
    against a generic appraisal would produce confident rankings that mean
    nothing.
    """
    acc_type = accession.get("accession_type")
    if acc_type not in M.ACCESSION_TYPES:
        reason = (f"accession_type is {acc_type!r}; appraisal not attempted. "
                  f"Stage 01 characterisation is still valid.")
        for r in rows:
            r["s02_status"] = "skipped"
            r["s02_error"] = reason
            r["s02_version"] = STAGE_VERSION
        return {"applied": False, "reason": reason, "matched": {}}

    rs = ruleset_for(acc_type)
    matched: dict[str, int] = defaultdict(int)
    for r in rows:
        result = evaluate(r, rs)
        r.update(result)
        # Sensitivity beats discard. Precedence, not weight.
        r["s02_decision"] = M.resolve_decision(
            r.get("s02_decision"), r.get("s04_sensitivity_flags"))
        r["s02_policy_version"] = POLICY_VERSION
        r["s02_version"] = STAGE_VERSION
        r["s02_status"] = "ok"
        matched[r.get("s02_rule_matched") or "(no rule had an opinion)"] += 1
    return {"applied": True, "ruleset": rs.name, "matched": dict(matched)}


# ------------------------------------------------------------ the number ---
def reduction_report(rows: list[dict], nsrl: NSRL) -> dict:
    """
    Issue #15's number, with its own caveats attached rather than reported bare.
    """
    total = len(rows)
    causes: dict[str, int] = defaultdict(int)
    layer0 = 0
    for r in rows:
        layer = M.compute_layer(r)
        r["layer"] = layer
        if layer != 0:
            continue
        layer0 += 1
        if r.get("duplicate_of"):
            causes[r.get("s02_structural_exclusion") or "exact_duplicate"] += 1
        elif r.get("s02_nsrl_hit"):
            causes["nsrl_known_file"] += 1
        elif r.get("s02_structural_exclusion"):
            causes[r["s02_structural_exclusion"]] += 1
        elif r.get("s02_decision") == "discard_candidate":
            causes["rule:" + (r.get("s02_rule_matched") or "unnamed")] += 1

    pct = (layer0 / total * 100) if total else 0.0
    caveats = [
        "Both corpora are pre-filtered. Box extracts contain no OS files, and "
        "the network-share material has already been through preservation "
        "processing. A low number here is evidence about the corpus, not about "
        "the architecture.",
        "This sample is not the backlog. It is 2,375 files drawn deliberately "
        "to carry known edge cases, and the email portion is over-weighted to "
        "50% correspondence against a true 22.6%.",
    ]
    if not nsrl.available:
        caveats.append(
            "NSRL was NOT checked — no known-file set is installed. Issue #15 "
            "lists it as a free exclusion, so this percentage is a floor and "
            "the gap is unmeasured, not zero.")
    return {
        "total_files": total,
        "layer_0": layer0,
        "reduction_pct": round(pct, 2),
        "by_cause": dict(sorted(causes.items(), key=lambda kv: -kv[1])),
        "nsrl_checked": nsrl.available,
        "caveats": caveats,
    }


def run(rows: list[dict], accession: dict, nsrl: NSRL | None = None,
        do_images: bool = True) -> dict:
    """Structural, then dupes, then rules, then the number."""
    nsrl = nsrl or NSRL()
    for r in rows:
        r["s02_structural_exclusion"] = structural_exclusion(r)
        r["s02_nsrl_hit"] = nsrl.hit(r.get("content_sha1"))

    exact = collapse_exact(rows)

    near = 0
    if do_images:
        for r in rows:
            if r.get("s01_puid") in {"fmt/43", "fmt/11", "fmt/353", "fmt/3", "fmt/4"} \
                    and not r.get("duplicate_of"):
                r["_dhash"] = dhash256(r["path_raw"])
        near = near_duplicates(rows)

    rules = apply_rules(rows, accession)
    report = reduction_report(rows, nsrl)
    report["exact_duplicates"] = exact
    report["near_duplicates"] = near
    report["rules"] = rules
    for r in rows:
        r.pop("_dhash", None)
    return report
