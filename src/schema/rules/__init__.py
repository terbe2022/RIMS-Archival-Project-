"""
Appraisal rulesets, drafted from the University Archives' answers of 12 Aug 2026.

Two rulesets because the Archives has two kinds of material with genuinely
different rules — see manifest.ACCESSION_TYPES.

    from schema.rules import evaluate, ruleset_for, to_markdown

    rs = ruleset_for(row["accession_type"])
    row.update(evaluate(row, rs))

Nothing here is confirmed. `to_markdown()` prints a ruleset in plain language
for sending to an archivist, which is the point of the exercise.
"""
from .base import (Rule, Ruleset, evaluate, ruleset_for, to_markdown,
                   POLICY_VERSION)
from . import personal_papers, administrative

__all__ = ["Rule", "Ruleset", "evaluate", "ruleset_for", "to_markdown",
           "POLICY_VERSION", "personal_papers", "administrative"]
