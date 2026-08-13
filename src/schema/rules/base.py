"""
rules/base.py — the rule engine.

A rule is a named, ordered predicate that produces a disposition and a reason.
Rules are data, not code branches, so that:

  - `s02_rule_matched` can name exactly which one fired
  - the whole ruleset can be printed in plain language and sent to an archivist
    for confirmation, which is the point of this exercise
  - changing appraisal policy means editing a list, not editing logic

Two rulesets exist because the Archives has two kinds of material with
genuinely different rules — see rules/personal_papers.py and
rules/administrative.py, and manifest.ACCESSION_TYPES.

RULE ORDER MATTERS. Rules are evaluated in order and the first match wins,
except that sensitivity is applied afterwards and overrides everything —
see `evaluate()` and manifest.resolve_decision().

POLICY_VERSION is written to every row as `s02_policy_version`. Bump it on any
change to a rule, so decisions made under an old policy stay identifiable.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Iterable

POLICY_VERSION = "0.1-draft"   # not confirmed by the Archives yet

# --------------------------------------------------------------- primitives --
# Matchers take the manifest row (a dict) and return True/False. Kept tiny and
# composable so a rule reads close to the sentence an archivist would say.


def ext(*extensions: str) -> Callable[[dict], bool]:
    """File extension is one of these. Lowercase, no dot."""
    wanted = {e.lower().lstrip(".") for e in extensions}
    return lambda r: (r.get("extension") or "").lower() in wanted


def path_contains(*fragments: str) -> Callable[[dict], bool]:
    """Any fragment appears anywhere in the normalised path, case-insensitively."""
    frags = [f.lower() for f in fragments]
    return lambda r: any(f in (r.get("path_norm_ci") or "") for f in frags)


def folder_named(*names: str) -> Callable[[dict], bool]:
    """A path segment matches one of these exactly. Narrower than path_contains."""
    wanted = {n.lower() for n in names}
    return lambda r: bool(wanted & set((r.get("path_norm_ci") or "").split("/")))


def filename_matches(pattern: str) -> Callable[[dict], bool]:
    rx = re.compile(pattern, re.I)
    return lambda r: bool(rx.search(r.get("filename") or ""))


def text_mentions(*terms: str) -> Callable[[dict], bool]:
    """
    Terms appear in the peek text or the extracted sample. Word-boundary matched,
    so 'grant' does not fire on 'granted' — appraisal terms are specific enough
    that loose matching produces noise.
    """
    rx = re.compile(r"\b(" + "|".join(re.escape(t) for t in terms) + r")\b", re.I)

    def _m(r: dict) -> bool:
        for k in ("s02_peek_text", "s03_text_sample", "s04_summary"):
            v = r.get(k)
            if isinstance(v, str) and rx.search(v):
                return True
        return False
    return _m


def keyword_in(*terms: str) -> Callable[[dict], bool]:
    wanted = {t.lower() for t in terms}
    return lambda r: bool(wanted & {k.lower() for k in (r.get("s02_keywords") or [])})


def any_of(*matchers: Callable[[dict], bool]) -> Callable[[dict], bool]:
    return lambda r: any(m(r) for m in matchers)


def all_of(*matchers: Callable[[dict], bool]) -> Callable[[dict], bool]:
    return lambda r: all(m(r) for m in matchers)


def not_(m: Callable[[dict], bool]) -> Callable[[dict], bool]:
    return lambda r: not m(r)


def profile_field_in(*fields: str) -> Callable[[dict], bool]:
    """
    Discipline gate. Answer 3.2: drafts of published work are valuable for
    humanities scholars and routine for others. This is the matcher that makes
    the accession profile a rule selector rather than model context.
    """
    wanted = {f.lower() for f in fields}
    return lambda r: (r.get("profile_field") or "").lower() in wanted


# --------------------------------------------------------------------- rule --
@dataclass(frozen=True)
class Rule:
    name: str                       # written to s02_rule_matched
    disposition: str                # selected | not_selected | discard_candidate | restricted_review
    match: Callable[[dict], bool]
    because: str                    # human-readable, written to s02_rationale
    source: str = ""                # which answer this came from
    confidence: str = "firm"        # firm | tentative — tentative rules get sampled harder
    notes: str = ""                 # anything an archivist should push back on

    def applies(self, row: dict) -> bool:
        try:
            return self.match(row)
        except Exception:
            # A broken matcher must never take down a crawl. It fails closed:
            # the rule simply does not fire, and the file falls through to the
            # default, which is human review rather than disposal.
            return False


@dataclass
class Ruleset:
    name: str                       # matches manifest.ACCESSION_TYPES
    description: str
    retain: list[Rule] = field(default_factory=list)
    discard: list[Rule] = field(default_factory=list)
    sensitive: list[Rule] = field(default_factory=list)

    def all_rules(self) -> Iterable[Rule]:
        return [*self.sensitive, *self.retain, *self.discard]


# ----------------------------------------------------------------- evaluate --
def evaluate(row: dict, ruleset: Ruleset) -> dict:
    """
    Apply a ruleset to one row. Returns the columns Stage 02 should write.

    Order is deliberate and is the whole safety property:

      1. Sensitivity rules first. If any fires, the answer is restricted_review
         and nothing else gets to change it.
      2. Retain rules. First match wins.
      3. Discard rules. First match wins.
      4. Nothing matched -> not_selected, which means "no rule had an opinion",
         NOT "discard". It sits in layer 1 and a person can still look at it.

    Answer 3.3 lists HR material as both routinely disposable and sensitive.
    Step 1 running before step 3 is what stops the system binning a personnel
    file nobody has read.
    """
    for rule in ruleset.sensitive:
        if rule.applies(row):
            return _result(rule, ruleset, sensitive=True)

    for rule in ruleset.retain:
        if rule.applies(row):
            return _result(rule, ruleset)

    for rule in ruleset.discard:
        if rule.applies(row):
            return _result(rule, ruleset)

    return {
        "s02_decision": "not_selected",
        "s02_rule_matched": None,
        "s02_ruleset": ruleset.name,
        "s02_rationale": "No rule matched. Not a decision to discard — this file "
                         "simply did not meet a retain rule and is available for review.",
        "s02_policy_version": POLICY_VERSION,
    }


def _result(rule: Rule, ruleset: Ruleset, sensitive: bool = False) -> dict:
    return {
        "s02_decision": "restricted_review" if sensitive else rule.disposition,
        "s02_rule_matched": rule.name,
        "s02_ruleset": ruleset.name,
        "s02_rationale": rule.because,
        "s02_policy_version": POLICY_VERSION,
    }


# --------------------------------------------------------------- selection --
def ruleset_for(accession_type: str) -> Ruleset:
    """Pick the ruleset. Unknown type is an error, not a silent default."""
    from . import personal_papers, administrative
    table = {
        "personal_papers": personal_papers.RULESET,
        "administrative": administrative.RULESET,
    }
    if accession_type not in table:
        raise ValueError(
            f"unknown accession_type {accession_type!r}. Expected one of "
            f"{sorted(table)}. Triage must not guess — an accession with no type "
            f"set should be flagged for a person."
        )
    return table[accession_type]


# ------------------------------------------------------------- explanation --
def to_markdown(ruleset: Ruleset) -> str:
    """
    Print a ruleset as plain language, for sending to an archivist.

    This is the deliverable that matters. The rules are our reading of what the
    Archives told us, and they should be able to correct it without reading
    Python.
    """
    out = [f"# {ruleset.name}", "", ruleset.description, "",
           f"Policy version `{POLICY_VERSION}` — **draft, not yet confirmed**.", ""]

    for label, rules, blurb in (
        ("Always flagged for a supervising archivist", ruleset.sensitive,
         "These are never discarded automatically, whatever else matches them."),
        ("Kept", ruleset.retain,
         "Matched in this order; the first match wins."),
        ("Set aside", ruleset.discard,
         "Proposed for disposal, subject to sampling and the retention clock. "
         "Never applied to anything above."),
    ):
        if not rules:
            continue
        out += [f"## {label}", "", blurb, ""]
        for r in rules:
            flag = "" if r.confidence == "firm" else "  *(tentative — please check)*"
            out += [f"**{r.name}**{flag}", "", f"{r.because}", ""]
            if r.source:
                out += [f"*Source: {r.source}*", ""]
            if r.notes:
                out += [f"> {r.notes}", ""]

    out += ["## Anything else", "",
            "A file matching no rule is **not** discarded. It is marked "
            "`not_selected`, which means no rule had an opinion about it, and it "
            "stays available for review.", ""]
    return "\n".join(out)
