"""Deterministic synthetic Prairie Bee Survey data shared by every builder.

Built so the 'findings' told in emails and manuscripts are actually present:
richness saturates ~10 years after restoration; ground-nesting specialists keep
rising and the remnant (BRF) sits highest; B. affinis appears only at BRF 2019-22.
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from common import SITES, BEE_TAXA, SEED

YEARS = list(range(2016, 2023))
ROUNDS = [(5, 20), (6, 14), (7, 12), (8, 9)]   # month, day
COLORS = ["blue", "yellow", "white"]
STATIONS = [1, 2, 3]
SPECIALISTS = {"Andrena commoda", "Andrena carlini", "Calliopsis andreniformis",
               "Melissodes trinodis", "Svastra obliqua", "Nomada articulata",
               "Triepeolus lunatus"}
GROUND_NESTERS = SPECIALISTS | {"Agapostemon virescens", "Halictus ligatus",
                                "Lasioglossum pilosum", "Lasioglossum versatum",
                                "Augochlorella aurata", "Melissodes bimaculatus"}


def age(site, year):
    restored = site[3]
    return 100 if site[0] == "BRF" else max(0, year - restored)


@lru_cache(maxsize=1)
def specimens():
    """List of specimen-level tuples."""
    r = np.random.default_rng(SEED)
    rows = []
    sid = 0
    for site in SITES:
        code = site[0]
        for year in YEARS:
            a = age(site, year)
            general_level = 1 - math.exp(-a / 4.0)          # saturates ~10 y
            special_level = min(1.0, a / 40.0) if code != "BRF" else 1.0
            for rnd, (mo, dy) in enumerate(ROUNDS):
                for st in STATIONS:
                    for col in COLORS:
                        tipped = r.random() < 0.06
                        if tipped:
                            continue
                        col_mult = {"blue": 1.25, "yellow": 1.0, "white": 0.7}[col]
                        for ti, taxon in enumerate(BEE_TAXA):
                            w = math.exp(-ti / 7.0)              # rarity: later taxa rarer
                            if taxon == "Bombus affinis":
                                lam = 0.12 if (code == "BRF" and year >= 2019 and mo in (6, 7)) else 0
                            elif taxon in SPECIALISTS:
                                lam = 0.07 * special_level ** 1.5
                            elif taxon == "Apis mellifera":
                                lam = 0.9
                            else:
                                lam = (0.03 + 1.6 * w) * general_level
                            lam *= col_mult * (1.2 if mo in (6, 7) else 0.8)
                            n = r.poisson(lam) if lam > 0 else 0
                            for _ in range(n):
                                sid += 1
                                sex = "F" if r.random() < 0.78 else "M"
                                barcode = (r.random() < 0.15)
                                rows.append((f"PBS-{year}-{sid:06d}", code, year,
                                             f"{year}-{mo:02d}-{dy:02d}", rnd + 1, st, col,
                                             taxon, sex, "Y" if barcode else "N",
                                             "PN" if year >= 2018 and r.random() < .6 else "MA"))
    return rows


SPEC_HEADER = ["specimen_id", "site", "year", "date", "round", "station", "trap_color",
               "taxon", "sex", "barcoded", "determiner"]


@lru_cache(maxsize=1)
def richness_table():
    """(site, year, age, richness, specialist_richness, abundance)"""
    from collections import defaultdict
    taxa = defaultdict(set)
    ab = defaultdict(int)
    for s in specimens():
        taxa[(s[1], s[2])].add(s[7])
        ab[(s[1], s[2])] += 1
    out = []
    for site in SITES:
        for y in YEARS:
            k = (site[0], y)
            out.append((site[0], y, age(site, y), len(taxa[k]),
                        len(taxa[k] & SPECIALISTS), ab[k]))
    return out
