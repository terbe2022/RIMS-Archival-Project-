"""Figures generated from the synthetic survey, reused across PDFs, slides and figure files."""
from __future__ import annotations

import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from survey import richness_table, specimens, YEARS
from common import SITES

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})


def _save(fig, fmt="png", dpi=150):
    b = io.BytesIO()
    fig.savefig(b, format=fmt, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return b.getvalue()


def richness_vs_age(fmt="png", specialists=False, drop_brf=False, dpi=150, title=None):
    rt = [r for r in richness_table() if not (drop_brf and r[0] == "BRF")]
    x = np.array([min(r[2], 40) for r in rt])
    y = np.array([r[4] if specialists else r[3] for r in rt])
    fig, ax = plt.subplots(figsize=(5, 3.4))
    for code in {r[0] for r in rt}:
        pts = [(min(r[2], 40), r[4] if specialists else r[3]) for r in rt if r[0] == code]
        ax.scatter(*zip(*pts), s=14, label=code, alpha=.8,
                   marker="*" if code == "BRF" else "o")
    order = np.argsort(x)
    k = 9
    smooth = np.convolve(y[order], np.ones(k) / k, mode="valid")
    ax.plot(x[order][k // 2: -(k // 2)], smooth, color="k", lw=2)
    ax.set_xlabel("Years since restoration (remnant plotted at 40)")
    ax.set_ylabel("Specialist species" if specialists else "Species richness")
    ax.set_title(title or ("Ground-nesting specialists" if specialists else "Total bee richness"))
    ax.legend(fontsize=6, ncol=2, frameon=False)
    return _save(fig, fmt, dpi)


def abundance_by_color(fmt="png", dpi=150):
    from collections import Counter
    c = Counter((s[2], s[6]) for s in specimens())
    fig, ax = plt.subplots(figsize=(5, 3))
    for col, mc in [("blue", "#3060c0"), ("yellow", "#d8b020"), ("white", "#999999")]:
        ax.plot(YEARS, [c[(y, col)] for y in YEARS], marker="o", color=mc, label=col)
    ax.set_ylabel("Specimens"); ax.set_title("Pan-trap captures by bowl colour")
    ax.legend(frameon=False)
    return _save(fig, fmt, dpi)


def taxa_bar(fmt="png", dpi=150, top=15):
    from collections import Counter
    c = Counter(s[7] for s in specimens()).most_common(top)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.barh([t for t, _ in c][::-1], [n for _, n in c][::-1], color="#7a9a3a")
    ax.set_xlabel("Specimens 2016-2022"); ax.set_title("Most abundant taxa")
    for lbl in ax.get_yticklabels():
        lbl.set_style("italic")
    return _save(fig, fmt, dpi)


def site_map(fmt="png", dpi=150, exact_brf=True):
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    for code, name, county, yr, lat, lon, own in SITES:
        if code == "BRF" and not exact_brf:
            continue
        ax.scatter(lon, lat, s=40, c="#b03a2e" if own == "private" else "#2e6eb0")
        ax.annotate(code, (lon, lat), xytext=(4, 4), textcoords="offset points", fontsize=8)
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    ax.set_title("Prairie Bee Survey sites" + ("" if exact_brf else " (BRF withheld)"))
    ax.grid(alpha=.3)
    return _save(fig, fmt, dpi)


def budget_pie(fmt="png", dpi=150):
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie([212, 96, 61, 38, 27], labels=["Personnel", "Fringe", "Travel/field", "Barcoding", "Supplies"],
           autopct="%1.0f%%", colors=["#4a7", "#8c6", "#dc8", "#c96", "#999"])
    ax.set_title("Budget, $K (Years 1-4)")
    return _save(fig, fmt, dpi)


def unrelated_chart(fmt="png", dpi=120):
    """Household budget chart (personal, irrelevant)."""
    fig, ax = plt.subplots(figsize=(4.5, 3))
    ax.bar(["Mortgage", "Groceries", "Utilities", "Car", "Kids", "Savings"],
           [1650, 820, 310, 440, 600, 900], color="#c77")
    ax.set_title("Monthly household budget 2021")
    return _save(fig, fmt, dpi)
