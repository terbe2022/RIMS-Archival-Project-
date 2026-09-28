"""
relevance.py — turn an intake form into a ranking, with the reason attached.

The form is the contract between the archivist and the models. `valuable` and
`exclude` are prose an archivist wrote about *this* collection, and the point of
this module is that a file's rank must be traceable to a specific clause of it.
"ranked high, score 0.82" is not usable by an archivist. "ranked high because it
matches 'referee reports and the correspondence that accompanies them'" is,
because it can be disagreed with — and changing the form and re-running is the
intended way to correct a bad result.

So the unit of scoring is the CLAUSE, not the form. Each sentence in `valuable`
and `exclude` becomes a criterion carrying its own text, and the winning
criterion's text goes into the rationale verbatim.

Three properties this must not lose:

1. **Scoring never discards.** Rules decide disposition; scores decide order.
   A low score means "look at this last", never "throw this away". Only
   schema.rules writes s02_decision.

2. **Retention by association is visibly different.** All three forms carry the
   instruction in the same words: mark files kept because of their neighbours
   so a reviewer can tell them from files we actually understand. That is a
   separate flag and a separate rationale, not a discounted score.

3. **The method is recorded.** Embeddings when available, lexical overlap when
   not. A lexical run is a weaker run and must not be mistaken for a strong one,
   so s02_rationale names which was used.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

SCORER_VERSION = "relevance-0.1.0"

_MATCH_CAP = 6      # distinctive terms above which a match is already convincing
BAND_HIGH = 0.55
BAND_MID = 0.30

_STOP = set("""a an the and or but if then than that this these those of in on at to for from by
with without into over under is are was were be been being it its as such not no nor any all
some each which who whom whose what when where why how there here we our us they them their
should would could may might must can will shall do does did done have has had having more most
other others same own very just also about against between during before after above below only
own too s t don now""".split())


def _clauses(text: str | None) -> list[str]:
    """
    Split form prose into criteria. Sentences, then long sentences on semicolons
    and ' and ' at clause length, because archivists write long compound
    sentences and a whole paragraph as one criterion loses the attribution.
    """
    if not text:
        return []
    out: list[str] = []
    for sent in re.split(r"(?<=[.!?])\s+", str(text).strip()):
        sent = sent.strip()
        if len(sent) < 12:
            continue
        if len(sent) > 220:
            parts = re.split(r";\s+|,\s+(?=and\s+)", sent)
        else:
            parts = [sent]
        out.extend(p.strip(" .;,") for p in parts if len(p.strip()) >= 12)
    return out


def _tokens(text: str | None) -> set[str]:
    if not text:
        return set()
    words = re.findall(r"[a-z][a-z0-9_\-]{2,}", str(text).lower())
    return {w for w in words if w not in _STOP}


@dataclass
class Criterion:
    text: str
    polarity: str          # retain | exclude | sensitive
    source_field: str      # which form field it came from
    tokens: set[str] = field(default_factory=set)
    vector: object = None


@dataclass
class Profile:
    """Everything from one intake form that bears on ranking."""
    accession: str
    criteria: list[Criterion]
    context_tokens: set[str]      # research, role, scope — topical anchor
    method: str = "lexical"

    def context_overlap(self, tokens: set[str]) -> float:
        if not self.context_tokens or not tokens:
            return 0.0
        return len(self.context_tokens & tokens) / math.sqrt(len(self.context_tokens))


def build_profile(form: dict) -> Profile:
    """
    Read one ACC-*.json into scoring criteria.

    `valuable` and `exclude` give retain and exclude criteria. `access` gives
    sensitivity criteria, which are scored but never used to lower a rank —
    they raise it, because sensitive material needs a person sooner, not later.
    `research`, `role` and `scope` become the topical anchor: what this
    collection is *about*, used to tell a file that belongs here from one that
    merely mentions something.
    """
    criteria: list[Criterion] = []
    for fieldname, polarity in (("valuable", "retain"),
                                ("exclude", "exclude"),
                                ("access", "sensitive")):
        for c in _clauses(form.get(fieldname)):
            criteria.append(Criterion(text=c, polarity=polarity,
                                      source_field=fieldname, tokens=_tokens(c)))

    context = set()
    for fieldname in ("research", "role", "scope"):
        context |= _tokens(form.get(fieldname))

    return Profile(accession=form.get("accession", "?"),
                   criteria=criteria, context_tokens=context)


def attach_embeddings(profile: Profile, model_name: str = "all-MiniLM-L6-v2") -> Profile:
    """
    Optional. CPU-only sentence embeddings, no GPU needed.

    Left as a separate call so a run without sentence-transformers installed
    still produces a ranking and says plainly that it was lexical. Note POC 2
    defect 3: MiniLM truncates at 256 tokens silently. Criteria are single
    sentences so that is safe here, but file text must be pre-truncated by
    sentence selection before it reaches this, exactly as POC 2 did.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return profile
    model = SentenceTransformer(model_name)
    vecs = model.encode([c.text for c in profile.criteria], normalize_embeddings=True)
    for c, v in zip(profile.criteria, vecs):
        c.vector = v
    profile.method = f"embedding:{model_name}"
    profile._model = model                     # noqa: SLF001 — used by score_row
    return profile


def _evidence_split(row: dict) -> tuple[str, str]:
    """
    Separate what we know from the file's LOCATION from what we know from its
    CONTENT. A match on location alone is proximity evidence: the file is kept
    because of where it sits, not because we understand it. That is a different
    archival claim and the forms ask for it to be visible.
    """
    location = " ".join(str(b) for b in (
        row.get("path_norm"), row.get("parent_folder"), row.get("sample_reason")) if b)
    content = " ".join(str(b) for b in (
        row.get("filename"), row.get("s01_format_name"), row.get("s03_text_sample"),
        row.get("s04_summary"), row.get("s04_description"),
        " ".join(row.get("s02_keywords") or [])) if b)
    return location, content


def _file_context(row: dict) -> str:
    """
    Everything we know about a file in words. Deliberately includes the path:
    in a working research computer the folder a file sits in carries the
    creator's own judgement about what it relates to, which is often the only
    description that exists.
    """
    loc, con = _evidence_split(row)
    return f"{loc} {con}".strip()


def score_row(row: dict, profile: Profile) -> dict:
    """
    Score one file against one form. Returns stage 02 scoring columns.

    Never writes s02_decision. Disposition belongs to the rules.
    """
    ctx = _file_context(row)
    tokens = _tokens(ctx)

    best = {"retain": (0.0, None), "exclude": (0.0, None), "sensitive": (0.0, None)}

    model = getattr(profile, "_model", None)
    if model is not None and profile.criteria:
        vec = model.encode([ctx], normalize_embeddings=True)[0]
        for c in profile.criteria:
            sim = float(vec @ c.vector)
            if sim > best[c.polarity][0]:
                best[c.polarity] = (sim, c)
    else:
        for c in profile.criteria:
            if not c.tokens:
                continue
            # How many distinctive terms from this criterion appear, counted
            # up to a cap. Bounded [0,1].
            #
            # Two earlier attempts were both wrong in instructive ways.
            # Cosine divides by the FILE's token count, so a document with
            # real extracted text scored lower than a bare path — inverting
            # the point of extraction. Dividing by the CRITERION's length
            # instead biases toward short criteria: "Out of office and
            # auto-reply messages" is four words and trivially matched in
            # full, while a forty-word retention clause can never be. Since
            # exclusion clauses are almost always the short ones, every file
            # scored zero.
            #
            # A cap removes the length bias in both directions. Matching six
            # distinctive terms is strong evidence whether the clause was
            # eight words or eighty.
            overlap = min(len(c.tokens & tokens), _MATCH_CAP) / _MATCH_CAP
            if overlap > best[c.polarity][0]:
                best[c.polarity] = (overlap, c)

    retain_s, retain_c = best["retain"]
    exclude_s, exclude_c = best["exclude"]
    sens_s, sens_c = best["sensitive"]

    proximity = False
    topical = profile.context_overlap(tokens)
    # Exclude pulls the score down but cannot zero it, because the form's
    # exclude clauses are appraisal guidance and not a disposal instruction.
    score = min(1.0, max(0.0, retain_s + 0.25 * topical - 0.5 * exclude_s))
    if sens_s > BAND_MID:
        score = max(score, sens_s)      # sensitive material surfaces sooner

    band = "high" if score >= BAND_HIGH else "mid" if score >= BAND_MID else "low"
    # If the form excludes this more strongly than it retains it, the band
    # must not say "mid" while the rationale says "matches the exclusion
    # criterion". A reviewer reading those two together would rightly
    # distrust both.
    if exclude_s > retain_s and sens_s <= BAND_MID:
        band = "low"

    if retain_c and retain_s >= max(exclude_s, BAND_MID * 0.6):
        # Did this match on the file itself, or only on where it sits?
        loc, con = _evidence_split(row)
        content_tokens = _tokens(con)
        by_content = bool(retain_c.tokens & content_tokens)
        if not by_content:
            proximity = True
            why = (f"retained by association — nothing about the file itself "
                   f"matched. Its location matches the form's criterion: "
                   f"\"{retain_c.text}\". A reviewer should be able to see the "
                   f"difference between this and a file we understand.")
        else:
            why = f"matches the form's retention criterion: \"{retain_c.text}\""
    elif exclude_c and exclude_s > retain_s:
        why = f"matches the form's exclusion criterion: \"{exclude_c.text}\""
    else:
        why = "no criterion in the form matched; ranked on topical fit alone"
    if sens_c and sens_s > BAND_MID:
        why += f" — and the access instruction: \"{sens_c.text}\""

    return {
        "s02_file_score": round(score, 4),
        "s02_score": round(score, 4),
        "s02_band": band,
        "s02_rationale": f"[{profile.method}] {why}",
        "retained_by_association": proximity or None,
        "_topical": round(topical, 4),
        "_retain_sim": round(retain_s, 4),
        "_exclude_sim": round(exclude_s, 4),
    }


def score_folders(rows: list[dict], threshold: float = BAND_HIGH) -> int:
    """
    Folder-level score, and the association flag.

    A folder substantially made of material worth keeping carries its
    unidentified neighbours. All three forms ask for this in the same words,
    and ask that the reason be visibly different from ordinary retention — so
    it is a distinct rationale, not a bumped score.

    Returns the number of files retained by association.
    """
    from collections import defaultdict
    by_folder: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_folder[str(r.get("parent_folder") or "")].append(r)

    n = 0
    for folder, members in by_folder.items():
        scores = [m.get("s02_file_score") or 0.0 for m in members]
        if not scores:
            continue
        folder_score = sum(sorted(scores, reverse=True)[:max(1, len(scores) // 3)]) / \
            max(1, len(sorted(scores, reverse=True)[:max(1, len(scores) // 3)]))
        strong = sum(1 for s in scores if s >= threshold)
        for m in members:
            m["s02_folder_score"] = round(folder_score, 4)
        if folder_score < threshold or strong < 2:
            continue
        for m in members:
            if (m.get("s02_file_score") or 0.0) >= BAND_MID:
                continue
            if m.get("duplicate_of") or m.get("s02_structural_exclusion"):
                continue
            m["s02_band"] = "mid"
            m["retained_by_association"] = True
            m["s02_rationale"] = (
                f"retained by association — not understood on its own merits, "
                f"kept because {strong} files in \"{folder}\" match the form's "
                f"retention criteria. A reviewer should be able to see the "
                f"difference between this and a file we understand."
            )
            n += 1
    return n


def run(rows: list[dict], form: dict, use_embeddings: bool = True) -> dict:
    """Score an accession's files against its own intake form."""
    profile = build_profile(form)
    if use_embeddings:
        profile = attach_embeddings(profile)
    if not profile.criteria:
        for r in rows:
            r["s02_rationale"] = ("intake form carries no retention or exclusion "
                                  "criteria; no ranking attempted")
        return {"scored": 0, "method": "none",
                "reason": "form has no valuable/exclude prose to score against"}

    for r in rows:
        r.update(score_row(r, profile))
    associated = score_folders(rows)

    bands: dict[str, int] = {}
    for r in rows:
        bands[r.get("s02_band") or "?"] = bands.get(r.get("s02_band") or "?", 0) + 1
    for r in rows:
        for k in ("_topical", "_retain_sim", "_exclude_sim"):
            r.pop(k, None)

    return {
        "scored": len(rows),
        "method": profile.method,
        "scorer_version": SCORER_VERSION,
        "criteria_count": len(profile.criteria),
        "criteria_by_field": {
            f: sum(1 for c in profile.criteria if c.source_field == f)
            for f in ("valuable", "exclude", "access")},
        "bands": bands,
        "retained_by_association": associated,
    }
