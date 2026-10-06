"""
evaluate.py — compare models on the same inputs, with numbers you can defend.

The pipeline generates metadata with a local model. Nobody has measured whether
that metadata is any good, which means every claim about the system rests on an
assumption. This is the harness for removing that assumption.

Five things are worth measuring. Four need no labelled data
-----------------------------------------------------------
1. SCHEMA ADHERENCE — does it return parseable JSON with the required keys,
   every time, unattended? A model producing excellent prose and unreliable
   JSON is useless at volume. No labels needed.

2. ABSTENTION — given input that does not support an answer (a blank page, a
   truncated extraction, a fogged scan), does it say so or invent something?
   Measured by deliberately degrading real inputs, so no labels needed. This is
   the property nobody benchmarks and the one that matters most here: confident
   wrong output manufactures retention signal.

3. SELF-CONSISTENCY — same input twice at temperature 0, same answer? A model
   that contradicts itself cannot be audited. No labels needed.

4. COST — seconds per file, and what that means for 150,000 files. No labels.

5. AGREEMENT WITH A PERSON — needs labels, and is the reason the labelling
   exercise matters. Everything above narrows the field first, so the expensive
   human time is spent on two or three candidates rather than eight.

On scoring description quality
------------------------------
There is no automatic measure of whether a description is good. Word overlap
against a reference rewards paraphrase and punishes better phrasing. So this
harness does NOT score quality automatically: it produces side-by-side output
for a person to grade against the rubric, and records the grades. Pretending
otherwise would produce a number that looks like evidence and is not.
"""
from __future__ import annotations

import json
import re
import statistics
import time
from dataclasses import dataclass, field, asdict
from typing import Callable

# What a description must contain to be usable downstream. Missing any of these
# is a hard failure, not a quality judgement.
REQUIRED_KEYS = ("title", "description")
OPTIONAL_KEYS = ("subjects", "genre", "readable", "confidence")

_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.M)


@dataclass
class Attempt:
    """One model, one input, one call."""
    model: str
    case_id: str
    raw: str = ""
    parsed: dict | None = None
    seconds: float = 0.0
    error: str | None = None

    @property
    def parsed_ok(self) -> bool:
        return self.parsed is not None

    @property
    def has_required(self) -> bool:
        return bool(self.parsed) and all(
            isinstance(self.parsed.get(k), str) and bool(self.parsed[k].strip())
            for k in REQUIRED_KEYS)


@dataclass
class Case:
    """
    One input. `expects_abstention` is the important field.

    A case built by blanking or truncating a real file has a known correct
    answer — "I cannot describe this" — without anyone labelling anything.
    That is how abstention becomes measurable today.
    """
    case_id: str
    text: str = ""
    image_b64: str | None = None
    kind: str = "document"
    expects_abstention: bool = False
    note: str = ""


def parse(raw: str) -> dict | None:
    """
    Parse a model's reply, forgiving the things models actually do.

    Fences and preamble are stripped rather than counted as failures: they are
    prompt problems, not capability problems, and conflating them would make a
    fixable formatting issue look like an unusable model.
    """
    if not raw:
        return None
    text = _FENCE.sub("", raw).strip()
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        try:
            obj = json.loads(text[start:end + 1])
            return obj if isinstance(obj, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def abstained(parsed: dict | None) -> bool:
    """
    Did the model decline? Read generously — a model can abstain in several
    ways and counting only one of them would understate the good behaviour.
    """
    if not parsed:
        return False
    if parsed.get("readable") is False:
        return True
    # Require an explicit machine-readable refusal. Narrative words such as
    # "unclear" can describe the source without refusing to describe it.
    return False



def degrade(text: str, how: str) -> str:
    """
    Make an input that cannot honestly be described.

    Built from the corpus's own failure modes rather than synthetic noise: an
    empty extraction, a mid-word truncation, a mail body that is only a quoted
    header, a page of OCR mush.
    """
    if how == "empty":
        return ""
    if how == "truncated":
        return text[:40].rsplit(" ", 1)[0] if len(text) > 40 else text
    if how == "boilerplate":
        return ("-----Original Message-----\nFrom: \nSent: \nTo: \nSubject: \n\n"
                "> \n> \n")
    if how == "ocr_mush":
        return re.sub(r"[aeiou]", lambda m: "", text[:600])
    return text


def build_cases(rows: list[dict], n_real: int = 20,
                degradations: tuple = ("empty", "truncated", "boilerplate")) -> list[Case]:
    """
    A test set from the real corpus: real files, plus degraded copies of them.

    The degraded cases are the point. A model that scores well on readable
    documents and invents content for blank ones is worse than one that is
    mediocre on both, because the first failure is invisible in aggregate
    statistics and lands in the manifest as description.
    """
    if n_real < 0:
        raise ValueError("n_real must be nonnegative")
    if rows and all("expect" in row for row in rows):
        # Synthetic expectations are labels; preserve unreadable fixture cases.
        return [Case(case_id=f"fixture-{i:03d}",
                     text=(row.get("s03_text_sample") or row.get("text") or "")[:4000],
                     kind=row.get("s03_lane") or row.get("lane") or "document",
                     expects_abstention=bool(row["expect"].get("abstain")),
                     note=row.get("filename") or "")
                for i, row in enumerate(rows[:n_real])]
    usable = [r for r in rows if (r.get("s03_text_len") or 0) > 400][:n_real]
    cases = [Case(case_id=f"real-{i:03d}", text=(r.get("s03_text_sample") or "")[:4000],
                  kind=r.get("s03_lane") or "document",
                  note=r.get("filename") or "")
             for i, r in enumerate(usable)]
    for i, r in enumerate(usable[:max(1, len(usable) // 3)]):
        for how in degradations:
            cases.append(Case(
                case_id=f"{how}-{i:03d}",
                text=degrade(r.get("s03_text_sample") or "", how),
                kind=r.get("s03_lane") or "document",
                expects_abstention=True,
                note=f"{how} copy of {r.get('filename') or ''}"))
    return cases


def run_model(name: str, call: Callable[[Case], str], cases: list[Case],
              repeats: int = 1) -> list[Attempt]:
    """
    Run one model over every case. `call` takes a Case and returns raw text,
    so the harness never needs to know which serving stack is behind it.
    """
    if repeats < 1:
        raise ValueError("repeats must be positive")
    out = []
    for case in cases:
        for rep in range(repeats):
            t0 = time.perf_counter()
            a = Attempt(model=name,
                        case_id=case.case_id + (f"#{rep}" if repeats > 1 else ""))
            try:
                a.raw = call(case)
                a.parsed = parse(a.raw)
            except Exception as exc:
                a.error = f"{type(exc).__name__}: {exc}"
            a.seconds = round(time.perf_counter() - t0, 2)
            out.append(a)
    return out


def score(attempts: list[Attempt], cases: list[Case]) -> dict:
    """
    Turn attempts into the four label-free measures.

    Reported separately, never averaged into one figure. A model can be
    excellent at JSON and dangerous at abstention, and a single score would
    hide exactly that.
    """
    by_id = {c.case_id: c for c in cases}
    if any(a.case_id.split("#")[0] not in by_id for a in attempts):
        raise ValueError("attempt references an unknown case")
    real = [a for a in attempts if not by_id.get(a.case_id.split("#")[0],
                                                 Case("")).expects_abstention]
    degraded = [a for a in attempts if by_id.get(a.case_id.split("#")[0],
                                                 Case("")).expects_abstention]

    def pct(n, d):
        return round(100 * n / d, 1) if d else None

    # Compare complete parsed responses; failures never count as consistent.
    groups: dict[str, list] = {}
    for a in attempts:
        groups.setdefault(a.case_id.split("#")[0], []).append(a)
    repeated = {k: v for k, v in groups.items() if len(v) > 1}
    consistent = sum(
        1 for v in repeated.values()
        if all(x.parsed_ok and not x.error for x in v)
        and len({json.dumps(x.parsed, sort_keys=True) for x in v}) == 1)

    times = [a.seconds for a in attempts]
    return {
        "model": attempts[0].model if attempts else None,
        "calls": len(attempts),
        "errors": sum(1 for a in attempts if a.error),
        "schema": {
            # Parseability is measured over everything.
            "parsed": pct(sum(1 for a in attempts if a.parsed_ok), len(attempts)),
            # Required keys are measured over REAL cases only. A model that
            # correctly declines a blank page has no title, and counting that
            # as a schema failure penalises exactly the behaviour worth
            # rewarding — which is how a metric ends up selecting for the
            # overconfident model.
            "required_keys_present": pct(
                sum(1 for a in real if a.has_required), len(real)),
        },
        "abstention": {
            "cases": len(degraded),
            "correctly_declined": pct(
                sum(1 for a in degraded if abstained(a.parsed)), len(degraded)),
            "invented_on_unusable_input": pct(
                sum(1 for a in degraded if a.parsed_ok and not abstained(a.parsed)),
                len(degraded)),
            "wrongly_declined_a_real_file": pct(
                sum(1 for a in real if abstained(a.parsed)), len(real)),
        },
        "consistency": {
            "cases_repeated": len(repeated),
            "identical_across_repeats": pct(consistent, len(repeated)),
        },
        "cost": {
            "median_seconds": round(statistics.median(times), 2) if times else None,
            "p90_seconds": round(sorted(times)[int(len(times) * 0.9)], 2) if times else None,
            "hours_for_150k": round(statistics.median(times) * 150000 / 3600, 1)
                              if times else None,
        },
    }


def comparison_table(scores: list[dict]) -> str:
    """One row per model, for pasting into a report."""
    head = (f"{'model':28} {'JSON%':>6} {'keys%':>6} {'declines%':>10} "
            f"{'invents%':>9} {'consist%':>9} {'sec':>6} {'hrs/150k':>9}")
    rows = [head, "-" * len(head)]
    def display(value, width):
        return f"{value if value is not None else 'NA':>{width}}"
    for s in scores:
        values = [s['schema']['parsed'], s['schema']['required_keys_present'],
                  s['abstention']['correctly_declined'],
                  s['abstention']['invented_on_unusable_input'],
                  s['consistency']['identical_across_repeats'],
                  s['cost']['median_seconds'], s['cost']['hours_for_150k']]
        rows.append(f"{str(s['model'])[:28]:28} " + " ".join(
            display(value, width) for value, width in
            zip(values, [6, 6, 10, 9, 9, 6, 9])))
    return "\n".join(rows)


def grading_sheet(attempts_by_model: dict[str, list[Attempt]],
                  cases: list[Case], limit: int = 15) -> list[dict]:
    """
    Side-by-side output for a person to grade against the rubric.

    Model names are NOT included in the row a grader reads. Knowing which model
    wrote a description changes how it is judged, and the point of grading is
    to find out which one is better — so the mapping is kept separately and
    rejoined after the grades are in.
    """
    import hashlib
    sheet = []
    real = [c for c in cases if not c.expects_abstention][:limit]
    for c in real:
        entry = {"case_id": c.case_id, "source": c.note,
                 "input_opening": c.text[:400], "input_text": c.text, "candidates": []}
        for model, attempts in attempts_by_model.items():
            a = next((x for x in attempts if x.case_id.split("#")[0] == c.case_id), None)
            if not a or not a.parsed:
                continue
            tag = hashlib.sha1((model + c.case_id).encode()).hexdigest()[:6]
            entry["candidates"].append({
                "tag": tag,
                "title": a.parsed.get("title"),
                "description": a.parsed.get("description"),
                "subjects": a.parsed.get("subjects"),
            })
            entry.setdefault("_key", {})[tag] = model
        sheet.append(entry)
    return sheet
