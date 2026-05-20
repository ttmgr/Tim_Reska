#!/usr/bin/env python3
"""Generate Medical Underwriting Study Guide as illustrated PDF.

Produces a ~25-page portrait A4 PDF with academic/scientific styling:
dense content, numbered figures with captions, numbered tables,
muted ColorBrewer palette, clean Helvetica typography.

Usage:
    python scripts/generate_study_guide.py
"""

from __future__ import annotations

import logging
import sys
from io import BytesIO
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from _academic_style import (  # noqa: E402
    AcademicPDF, chart_style, safe,
    M_BLUE, M_AMBER, M_GREEN, M_RED, M_DARK, M_GREY, M_LIGHT, M_PURPLE, M_TEAL,
    C_BODY, C_HEADING, C_CAPTION, C_FOOTNOTE, C_ACCENT, C_RULE,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

OUT = PROJECT_ROOT / "data" / "reports"
OUT.mkdir(parents=True, exist_ok=True)

# Aliases for backward compat within this file
_safe = safe
_chart_style = chart_style
StudyGuidePDF = lambda: AcademicPDF(  # noqa: E731
    header_left="Medical Underwriting Study Guide",
    header_right="MedRisk v2.0",
)


# ============================================================================
# Chart generators (academic style -- muted colours, no bold titles)
# ============================================================================

def chart_market_quality() -> BytesIO:
    _chart_style()
    markets = ["Germany (DE)", "France (FR)", "Spain (ES)", "International"]
    coding = [0.95, 0.90, 0.80, 0.60]
    labs = [0.92, 0.88, 0.75, 0.50]
    meds = [0.95, 0.88, 0.80, 0.60]

    x = np.arange(len(markets))
    width = 0.22
    fig, ax = plt.subplots(figsize=(6.5, 2.8))
    ax.bar(x - width, coding, width, label="Coding", color=M_BLUE, alpha=0.8)
    ax.bar(x, labs, width, label="Labs", color=M_AMBER, alpha=0.8)
    ax.bar(x + width, meds, width, label="Medications", color=M_GREEN, alpha=0.8)
    ax.set_ylabel("Completeness")
    ax.set_xticks(x)
    ax.set_xticklabels(markets, fontsize=7.5)
    ax.set_ylim(0, 1.08)
    ax.legend(fontsize=7, loc="lower left")
    ax.axhline(0.80, color=M_RED, linestyle=":", alpha=0.4, linewidth=0.8)
    for i in range(len(markets)):
        for j, vals in enumerate([coding, labs, meds]):
            offset = (j - 1) * width
            ax.text(i + offset, vals[i] + 0.015, f"{vals[i]:.0%}",
                    ha="center", fontsize=6, color=M_DARK)
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_lab_ranges() -> BytesIO:
    _chart_style()
    labs = [
        ("HbA1c (%)", 5.0, 8.0),
        ("eGFR (mL/min)", 90, 35),
        ("Systolic BP (mmHg)", 118, 150),
        ("NT-proBNP (pg/mL)", 60, 1500),
        ("Total Chol. (mg/dL)", 185, 260),
        ("LDL (mg/dL)", 100, 170),
    ]
    fig, axes = plt.subplots(len(labs), 1, figsize=(6.5, 4.5))
    for i, (name, normal, disease) in enumerate(labs):
        ax = axes[i]
        ax.barh(0.12, normal, 0.2, color=M_GREEN, alpha=0.7,
                label="Normal" if i == 0 else "")
        ax.barh(-0.12, disease, 0.2, color=M_RED, alpha=0.7,
                label="Disease" if i == 0 else "")
        ax.set_yticks([])
        ax.set_ylabel(name, fontsize=7, rotation=0, ha="right", labelpad=3)
        ax.tick_params(axis="x", labelsize=6.5)
        if i < len(labs) - 1:
            ax.set_xticklabels([])
        ax.spines["left"].set_visible(False)
    axes[0].legend(fontsize=7, loc="upper right", ncol=2)
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_charlson_weights() -> BytesIO:
    _chart_style()
    cats = ["MI", "CHF", "PVD", "CVD", "Dementia", "COPD", "Rheumatic",
            "Peptic ulcer", "Liver (mild)", "DM uncmpl.", "DM complic.",
            "Hemiplegia", "Renal", "Cancer", "Liver (severe)",
            "Metastatic", "AIDS/HIV"]
    weights = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 3, 6, 6]
    colors = [M_BLUE if w == 1 else M_AMBER if w == 2
              else M_RED if w == 3 else M_DARK for w in weights]
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    bars = ax.barh(range(len(cats)), weights, color=colors, alpha=0.75)
    ax.set_yticks(range(len(cats)))
    ax.set_yticklabels(cats, fontsize=7)
    ax.set_xlabel("Charlson weight")
    ax.invert_yaxis()
    for bar, w in zip(bars, weights):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                str(w), va="center", fontsize=6.5)
    patches = [mpatches.Patch(color=M_BLUE, label="Weight 1"),
               mpatches.Patch(color=M_AMBER, label="Weight 2"),
               mpatches.Patch(color=M_RED, label="Weight 3"),
               mpatches.Patch(color=M_DARK, label="Weight 6")]
    ax.legend(handles=patches, fontsize=6.5, loc="lower right")
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_age_multipliers() -> BytesIO:
    _chart_style()
    conds = ["HTN", "IHD", "MI", "HF", "DM", "CKD", "COPD", "Dementia", "Alzheimer"]
    young = [0.3, 0.1, 0.05, 0.05, 0.2, 0.1, 0.1, 0.01, 0.001]
    middle = [1.0, 1.0, 1.0, 0.8, 1.0, 0.8, 0.8, 0.1, 0.05]
    elderly = [1.8, 2.5, 2.5, 3.5, 1.5, 2.5, 2.0, 5.0, 8.0]
    data = np.array([young, middle, elderly])
    fig, ax = plt.subplots(figsize=(6.5, 2.5))
    im = ax.imshow(data, cmap="YlOrRd", aspect="auto", vmin=0, vmax=8)
    ax.set_xticks(range(len(conds)))
    ax.set_xticklabels(conds, fontsize=7, rotation=30, ha="right")
    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels(["Young (18-40)", "Middle (40-65)", "Elderly (65+)"], fontsize=7.5)
    for i in range(3):
        for j in range(len(conds)):
            v = data[i, j]
            c = "white" if v > 3 else "black"
            ax.text(j, i, f"{v:.1f}x" if v >= 0.1 else f"{v:.3f}x",
                    ha="center", va="center", fontsize=6, color=c)
    fig.colorbar(im, ax=ax, shrink=0.8, label="Multiplier")
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_comorbidity_cascade() -> BytesIO:
    _chart_style()
    fig, ax = plt.subplots(figsize=(6.5, 2.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3.5)
    ax.axis("off")
    boxes = [
        (0.3, 1.75, "Obesity\nbaseline", M_BLUE),
        (2.6, 2.8, "Diabetes\n(2.5x)", M_AMBER),
        (2.6, 0.7, "HTN\n(1.8x)", M_AMBER),
        (5.0, 2.8, "CKD\n(2.5x)", M_RED),
        (5.0, 0.7, "Stroke\n(2.0x)", M_RED),
        (7.5, 1.75, "Combined\n6.25x+", M_DARK),
    ]
    for x, y, label, color in boxes:
        r = mpatches.FancyBboxPatch((x, y - 0.4), 1.8, 0.8,
                                     boxstyle="round,pad=0.08",
                                     facecolor=color, alpha=0.75,
                                     edgecolor="none")
        ax.add_patch(r)
        ax.text(x + 0.9, y, label, ha="center", va="center",
                fontsize=6.5, color="white", fontweight="bold")
    arrows = [(2.1, 2.0, 0.3, 0.6), (2.1, 1.5, 0.3, -0.6),
              (4.4, 2.8, 0.4, 0.0), (4.4, 0.7, 0.4, 0.0),
              (6.8, 2.8, 0.5, -0.8), (6.8, 0.7, 0.5, 0.8)]
    for x, y, dx, dy in arrows:
        ax.annotate("", xy=(x + dx, y + dy), xytext=(x, y),
                    arrowprops=dict(arrowstyle="->", color=M_GREY, lw=1.2))
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_cv_progression() -> BytesIO:
    from medrisk.models.disease_configs import CARDIOVASCULAR_CONFIG, build_model
    _chart_style()
    model = build_model(CARDIOVASCULAR_CONFIG)
    times = np.linspace(0, 30, 200)
    probs = model.state_occupation_probabilities(0, times)
    fig, ax = plt.subplots(figsize=(6.5, 3))
    colors = [M_GREEN, M_BLUE, M_AMBER, M_RED, M_DARK]
    labels = [CARDIOVASCULAR_CONFIG.state_names[i] for i in range(5)]
    ax.stackplot(times, probs.T, labels=labels, colors=colors, alpha=0.65)
    ax.set_xlabel("Time (years)")
    ax.set_ylabel("Probability")
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 1)
    ax.legend(loc="center right", fontsize=6.5, framealpha=0.9)
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_alzheimer_progression() -> BytesIO:
    from medrisk.models.disease_configs import ALZHEIMER_CONFIG, build_model
    _chart_style()
    model = build_model(ALZHEIMER_CONFIG)
    times = np.linspace(0, 25, 200)
    probs = model.state_occupation_probabilities(0, times)
    fig, ax = plt.subplots(figsize=(6.5, 3))
    colors = [M_GREEN, "#B0C4DE", M_BLUE, M_AMBER, "#ED7D31", M_RED, M_DARK]
    labels = [ALZHEIMER_CONFIG.state_names[i] for i in range(7)]
    ax.stackplot(times, probs.T, labels=labels, colors=colors, alpha=0.65)
    ax.set_xlabel("Time (years)")
    ax.set_ylabel("Probability")
    ax.set_xlim(0, 25)
    ax.set_ylim(0, 1)
    ax.legend(loc="center right", fontsize=6, framealpha=0.9)
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_dqs_components() -> BytesIO:
    _chart_style()
    markets = ["DE", "FR", "ES", "INT"]
    comp = [0.38, 0.34, 0.30, 0.20]
    cons = [0.33, 0.30, 0.28, 0.18]
    rec = [0.20, 0.18, 0.14, 0.06]
    fig, ax = plt.subplots(figsize=(5.5, 2.8))
    x = np.arange(len(markets))
    w = 0.45
    ax.bar(x, comp, w, label="Completeness (0.40)", color=M_BLUE, alpha=0.75)
    ax.bar(x, cons, w, bottom=comp, label="Consistency (0.35)",
           color=M_GREEN, alpha=0.75)
    bots = [c + s for c, s in zip(comp, cons)]
    ax.bar(x, rec, w, bottom=bots, label="Recency (0.25)",
           color=M_AMBER, alpha=0.75)
    totals = [c + s + r for c, s, r in zip(comp, cons, rec)]
    for i, t in enumerate(totals):
        ax.text(i, t + 0.015, f"{t:.2f}", ha="center", fontsize=7.5)
    ax.axhline(0.80, color=M_GREEN, linestyle=":", alpha=0.5, linewidth=0.8)
    ax.axhline(0.60, color=M_RED, linestyle=":", alpha=0.5, linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(markets)
    ax.set_ylabel("DQS")
    ax.set_ylim(0, 1.02)
    ax.legend(fontsize=6.5, loc="upper right")
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_pbw_scatter() -> BytesIO:
    _chart_style()
    rng = np.random.default_rng(42)
    n = 100
    fig, ax = plt.subplots(figsize=(6.5, 3.5))
    for market, dqs_m, dqs_s, color, marker in [
        ("DE", 0.85, 0.08, M_BLUE, "o"),
        ("FR", 0.78, 0.10, M_GREEN, "s"),
        ("ES", 0.65, 0.12, M_AMBER, "^"),
        ("INT", 0.42, 0.15, M_RED, "D"),
    ]:
        dqs = np.clip(rng.normal(dqs_m, dqs_s, n), 0, 1)
        conf = np.clip(rng.beta(3, 2, n), 0.5, 1.0)
        ax.scatter(dqs, conf, c=color, marker=marker, s=15, alpha=0.45,
                   label=market, edgecolors="none")
    ax.axhspan(0.80, 1.01, xmin=0, xmax=0.60, alpha=0.08, color=M_RED)
    ax.axhline(0.80, color=M_RED, linestyle=":", alpha=0.35, linewidth=0.8)
    ax.axvline(0.60, color=M_RED, linestyle=":", alpha=0.35, linewidth=0.8)
    ax.text(0.05, 0.96, "PBW zone", fontsize=7.5, color=M_RED, style="italic")
    ax.set_xlabel("Data Quality Score (DQS)")
    ax.set_ylabel("Effective confidence")
    ax.set_xlim(0, 1.02)
    ax.set_ylim(0.45, 1.02)
    ax.legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_cost_decisions() -> BytesIO:
    _chart_style()
    pw = np.linspace(0, 1, 200)
    c_acc = pw * 5.0
    c_rej = (1 - pw) * 1.0
    c_rev = np.full_like(pw, 0.5)
    fig, ax = plt.subplots(figsize=(6.5, 3))
    ax.plot(pw, c_acc, color=M_RED, linewidth=1.5, label="E[cost | accept]")
    ax.plot(pw, c_rej, color=M_GREEN, linewidth=1.5, label="E[cost | reject]")
    ax.plot(pw, c_rev, color=M_BLUE, linewidth=1.5, linestyle="--",
            label="E[cost | review] = 0.5")
    ax.axvspan(0, 0.10, alpha=0.06, color=M_GREEN)
    ax.axvspan(0.10, 0.50, alpha=0.06, color=M_BLUE)
    ax.axvspan(0.50, 1.0, alpha=0.06, color=M_RED)
    ax.text(0.02, 4.5, "ACCEPT", fontsize=8, color=M_GREEN)
    ax.text(0.25, 4.5, "REVIEW", fontsize=8, color=M_BLUE)
    ax.text(0.70, 4.5, "REJECT", fontsize=8, color=M_RED)
    ax.set_xlabel("P(model is wrong)")
    ax.set_ylabel("Expected cost")
    ax.legend(fontsize=7, loc="center right")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 5.2)
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_ktg_pricing() -> BytesIO:
    _chart_style()
    stages = ["Healthy", "Risk\nFactors", "Chronic", "Compli-\ncation", "Major\nEvent"]
    p_au = [0.01, 0.03, 0.12, 0.35, 0.80]
    e_days = [7, 14, 28, 42, 120]
    costs = [p * d * 80 for p, d in zip(p_au, e_days)]
    colors = [M_GREEN, M_BLUE, M_AMBER, M_RED, M_DARK]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.5, 2.5))
    ax1.bar(range(5), [x * 100 for x in p_au], color=colors, alpha=0.75)
    ax1.set_xticks(range(5))
    ax1.set_xticklabels(stages, fontsize=6, rotation=0)
    ax1.set_ylabel("AU probability (%)")
    for i, v in enumerate(p_au):
        ax1.text(i, v * 100 + 1, f"{v:.0%}", ha="center", fontsize=6)
    ax2.bar(range(5), costs, color=colors, alpha=0.75)
    ax2.set_xticks(range(5))
    ax2.set_xticklabels(stages, fontsize=6, rotation=0)
    ax2.set_ylabel("Expected annual cost (EUR)")
    for i, v in enumerate(costs):
        ax2.text(i, v + 50, f"{v:,.0f}", ha="center", fontsize=6)
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_pipeline_flow() -> BytesIO:
    _chart_style()
    fig, ax = plt.subplots(figsize=(6.5, 1.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 2)
    ax.axis("off")
    steps = [
        (0.1, "Patient\nRecord", M_GREY),
        (1.5, "Feature\nMatrix", M_BLUE),
        (2.9, "Data\nProfile", M_BLUE),
        (4.3, "DQS v2", M_GREEN),
        (5.7, "Model\nRouter", M_AMBER),
        (7.1, "Reliability\nHead", M_RED),
        (8.5, "Decision\n+ Audit", M_DARK),
    ]
    for x, label, color in steps:
        r = mpatches.FancyBboxPatch((x, 0.5), 1.15, 0.9,
                                     boxstyle="round,pad=0.08",
                                     facecolor=color, alpha=0.8,
                                     edgecolor="none")
        ax.add_patch(r)
        ax.text(x + 0.575, 0.95, label, ha="center", va="center",
                fontsize=6.5, color="white", fontweight="bold")
    for i in range(len(steps) - 1):
        x_s = steps[i][0] + 1.15
        x_e = steps[i + 1][0]
        ax.annotate("", xy=(x_e, 0.95), xytext=(x_s, 0.95),
                    arrowprops=dict(arrowstyle="->", color=M_GREY, lw=1))
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_reserve_triangle() -> BytesIO:
    _chart_style()
    # Illustrative development triangle: CL vs BF for 5 accident years
    years = ["AY 2020", "AY 2021", "AY 2022", "AY 2023", "AY 2024"]
    cl_reserves = [105, 230, 380, 520, 850]
    bf_reserves = [108, 225, 360, 480, 620]
    x = np.arange(len(years))
    fig, ax = plt.subplots(figsize=(6.5, 2.8))
    w = 0.30
    ax.bar(x - w / 2, cl_reserves, w, label="Chain-Ladder", color=M_BLUE, alpha=0.8)
    ax.bar(x + w / 2, bf_reserves, w, label="Bornhuetter-Ferguson", color=M_AMBER, alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(years, fontsize=7.5)
    ax.set_ylabel("Reserve estimate (kEUR)")
    for i in range(len(years)):
        ax.text(i - w / 2, cl_reserves[i] + 15, f"{cl_reserves[i]}", ha="center", fontsize=6)
        ax.text(i + w / 2, bf_reserves[i] + 15, f"{bf_reserves[i]}", ha="center", fontsize=6)
    ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_sickness_absence() -> BytesIO:
    _chart_style()
    # AU frequency and duration by occupational risk class
    risk_classes = ["Class 1\n(Office)", "Class 2\n(Sales)", "Class 3\n(Manual)", "Class 4\n(Heavy)"]
    freq = [0.8, 1.0, 1.28, 1.68]
    dur = [14, 18, 25, 38]
    colors = [M_GREEN, M_BLUE, M_AMBER, M_RED]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.5, 2.5))
    ax1.bar(range(4), freq, color=colors, alpha=0.75)
    ax1.set_xticks(range(4))
    ax1.set_xticklabels(risk_classes, fontsize=6)
    ax1.set_ylabel("AU episodes / year")
    for i, v in enumerate(freq):
        ax1.text(i, v + 0.03, f"{v:.2f}", ha="center", fontsize=6)
    ax2.bar(range(4), dur, color=colors, alpha=0.75)
    ax2.set_xticks(range(4))
    ax2.set_xticklabels(risk_classes, fontsize=6)
    ax2.set_ylabel("Mean duration (days)")
    for i, v in enumerate(dur):
        ax2.text(i, v + 0.8, str(v), ha="center", fontsize=6)
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_full_pipeline() -> BytesIO:
    _chart_style()
    fig, ax = plt.subplots(figsize=(6.5, 2.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")
    steps = [
        (0.0, 2.5, "Cohort\nGeneration", M_GREY),
        (1.7, 2.5, "DataFrame\nConversion", M_GREY),
        (3.4, 2.5, "Feature\nMatrix", M_BLUE),
        (5.1, 2.5, "Data Profile\n+ DQS v2", M_GREEN),
        (6.8, 2.5, "Model\nRouter", M_AMBER),
        (8.5, 2.5, "Reliability\nHead", M_RED),
        # bottom row
        (3.4, 0.5, "Clinical\nChecks", M_PURPLE),
        (5.1, 0.5, "Underwriting\nEngine", M_DARK),
        (6.8, 0.5, "Human\nOverride", M_TEAL),
        (8.5, 0.5, "Audit\nLog", M_DARK),
    ]
    for x, y, label, color in steps:
        r = mpatches.FancyBboxPatch((x, y), 1.3, 0.85,
                                     boxstyle="round,pad=0.08",
                                     facecolor=color, alpha=0.8,
                                     edgecolor="none")
        ax.add_patch(r)
        ax.text(x + 0.65, y + 0.425, label, ha="center", va="center",
                fontsize=5.5, color="white", fontweight="bold")
    # top row arrows
    for i in range(5):
        x_s = steps[i][0] + 1.3
        x_e = steps[i + 1][0]
        ax.annotate("", xy=(x_e, 2.925), xytext=(x_s, 2.925),
                    arrowprops=dict(arrowstyle="->", color=M_GREY, lw=0.8))
    # bottom row arrows
    for i in range(6, 9):
        x_s = steps[i][0] + 1.3
        x_e = steps[i + 1][0]
        ax.annotate("", xy=(x_e, 0.925), xytext=(x_s, 0.925),
                    arrowprops=dict(arrowstyle="->", color=M_GREY, lw=0.8))
    # vertical arrows connecting rows
    ax.annotate("", xy=(5.75, 1.35), xytext=(5.75, 2.5),
                arrowprops=dict(arrowstyle="->", color=M_GREY, lw=0.8))
    ax.annotate("", xy=(9.15, 1.35), xytext=(9.15, 2.5),
                arrowprops=dict(arrowstyle="->", color=M_GREY, lw=0.8))
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


# ============================================================================
# Document builder
# ============================================================================

def build_study_guide():
    pdf = StudyGuidePDF()

    # ===== Title page =====
    pdf.add_page()
    pdf.ln(50)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(*C_FOOTNOTE)
    pdf.cell(0, 6, "MedRisk Study Guide", align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(*C_HEADING)
    pdf.multi_cell(0, 10, "Medical Underwriting\nFrom Data to Decision", align="C")
    pdf.ln(8)
    pdf.set_draw_color(*C_ACCENT)
    pdf.set_line_width(0.6)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*C_BODY)
    pdf.cell(0, 5, "the author", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*C_CAPTION)
    pdf.cell(0, 5, "Helmholtz Munich  |  March 2026", align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*C_FOOTNOTE)
    pdf.multi_cell(0, 4.5, _safe(
        "A practitioner's guide to AI-driven medical underwriting, grounded in "
        "the MedRisk codebase. Covers data sources, medical coding, "
        "comorbidity assessment, risk models, disease progression, data quality "
        "scoring, failure detection, insurance pricing, actuarial reserving, "
        "and the full validation pipeline.\n\n"
        "12 chapters  |  3 appendices  |  All data is synthetic"), align="C")

    # ===== Table of contents =====
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*C_HEADING)
    pdf.cell(0, 8, "Contents", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    toc = [
        (1, "Medical Underwriting"),
        (2, "Data Sources and Market Variation"),
        (3, "Medical Coding Systems"),
        (4, "Comorbidity Assessment"),
        (5, "Risk Classification Models"),
        (6, "Disease Progression Modeling"),
        (7, "Data Quality -- The DQS Framework"),
        (8, "Failure Detection and PBW"),
        (9, "Insurance Pricing -- KTG"),
        (10, "Pipeline and Validation"),
        (11, "Actuarial Reserving and Sickness Absence"),
        (12, "The Full Pipeline -- End to End"),
    ]
    for num, title in toc:
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(*C_BODY)
        pdf.cell(8, 5.5, str(num))
        pdf.cell(0, 5.5, _safe(title), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*C_CAPTION)
    pdf.cell(0, 5, "Appendix A: Reference Tables", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, "Appendix B: German-English Glossary", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, "Appendix C: Further Reading", new_x="LMARGIN", new_y="NEXT")

    # ================================================================
    # CHAPTER 1
    # ================================================================
    pdf.chapter_head(1, "Medical Underwriting")
    pdf.p("A medical underwriter receives an insurance application and estimates the "
          "expected cost of insuring that person. At a large European insurer processing "
          "100,000 policies per year, a 2% error rate in automated decisions produces "
          "2,000 mispriced policies annually -- each potentially costing tens of thousands "
          "in unexpected claims.")
    pdf.p("The underwriting workflow follows three steps: (1) receive application data -- "
          "demographics, diagnoses, lab results, medications; (2) assess risk -- map "
          "conditions to severity, evaluate comorbidities, check data completeness; "
          "(3) decide -- accept at standard terms, accept with premium loading, defer "
          "for more information, or decline.")

    pdf.key_concept("MedRisk maps this to three outcomes: accept (auto-process), "
                    "human_review (escalate), reject (decline). The Reliability Head "
                    "chooses the cost-optimal action per patient.")

    pdf.table_caption("Insurance products and their risk questions")
    pdf.table(
        ["Product", "German name", "Risk question", "MedRisk model"],
        [
            ["Life", "Lebensversicherung", "Mortality risk", "Cox PH"],
            ["Health", "Krankenversicherung", "Morbidity burden", "XGBoost"],
            ["Sickness benefit", "Krankentagegeld (KTG)", "Work incapacity", "CTMC"],
        ],
        [28, 38, 42, 40],
    )

    pdf.h2("Regulatory context")
    pdf.p("Three frameworks govern AI-driven underwriting in Europe: the EU AI Act "
          "(2024, enforcement 2026) classifies insurance AI as high-risk (Art. 6) and "
          "requires record-keeping (Art. 12) and human oversight (Art. 14); DSGVO/GDPR "
          "treats health data as special category (Art. 9) with rights to human review "
          "(Art. 22); and Solvency II mandates annual model validation and capital adequacy.")

    # ================================================================
    # CHAPTER 2
    # ================================================================
    pdf.chapter_head(2, "Data Sources and Market Variation")
    pdf.p("Underwriters work with claims databases, electronic health records (EHR), "
          "lab feeds, and self-reported questionnaires. The critical insight for German "
          "underwriting: GKV claims data (InGef, 8.8M patients) does not contain "
          "laboratory values. Only PKV data and CPRD (UK, 60M patients) have linked "
          "diagnoses, labs, and prescriptions.")

    logger.info("Generating charts...")
    pdf.figure(chart_market_quality(),
               "Data quality parameters across four European markets. Coding completeness "
               "ranges from 95% (Germany) to 60% (International). Source: MARKET_CONFIGS "
               "in src/medrisk/data/schemas.py.")

    pdf.table_caption("Market configuration parameters")
    pdf.table(
        ["Parameter", "DE", "ES", "FR", "INT"],
        [
            ["Coding completeness", "0.95", "0.80", "0.90", "0.60"],
            ["Lab completeness", "0.92", "0.75", "0.88", "0.50"],
            ["Lab noise (sigma)", "0.02", "0.05", "0.03", "0.10"],
            ["Diagnosis lag (days)", "14", "30", "60", "90"],
            ["Medication recording", "0.95", "0.80", "0.88", "0.60"],
        ],
        [40, 22, 22, 22, 22], num_cols=[1, 2, 3, 4],
    )

    pdf.p("A German record with 10 diagnoses likely represents 10 actual conditions. "
          "An International record with 10 diagnoses could represent approximately 17 "
          "actual conditions (40% missing). These differences directly impact confidence "
          "in risk scoring -- data from Germany warrants more trust than Spain or "
          "International markets.")

    # ================================================================
    # CHAPTER 3
    # ================================================================
    pdf.chapter_head(3, "Medical Coding Systems")
    pdf.p("Every diagnosis is an ICD-10 code, lab results use LOINC codes, and "
          "medications use ATC codes. MedRisk registers 56 curated ICD-10 codes "
          "(src/medrisk/data/icd10.py), 14 lab definitions with condition-specific "
          "distributions, and medication mappings for 10 conditions.")

    pdf.table_caption("Key ICD-10 codes for underwriting")
    pdf.table(
        ["Code", "Description", "Chapter", "Charlson wt."],
        [
            ["I10", "Essential hypertension", "IX (Circ.)", "--"],
            ["I21.0", "Acute STEMI, anterior wall", "IX (Circ.)", "1"],
            ["I50.0", "Congestive heart failure", "IX (Circ.)", "1"],
            ["E11.9", "T2D without complications", "IV (Metab.)", "1"],
            ["E11.21", "T2D with diabetic nephropathy", "IV (Metab.)", "2"],
            ["N18.4", "CKD stage 4", "XIV (Renal)", "2"],
            ["G30.1", "Alzheimer, late onset", "VI (Neuro.)", "1"],
        ],
        [20, 55, 30, 22], num_cols=[3],
    )

    pdf.p("The coding granularity matters enormously: E11.9 (diabetes without "
          "complications, Charlson weight 1) and E11.21 (diabetes with nephropathy, "
          "weight 2) differ by one decimal digit but double the comorbidity score. "
          "German underwriting uses ICD-10-GM which includes Alzheimer codes F00.0-F00.9 "
          "not present in the US ICD-10-CM.")

    pdf.figure(chart_lab_ranges(),
               "Normal vs. disease-state distributions for six key laboratory values. "
               "Green bars show healthy population means; red bars show disease-elevated "
               "means. Source: LAB_DEFINITIONS in src/medrisk/data/synthetic.py.")

    pdf.figure(chart_age_multipliers(),
               "Age-dependent prevalence multipliers relative to baseline. Alzheimer "
               "risk increases 8,000-fold from young (0.001x) to elderly (8.0x). "
               "Source: AGE_MULTIPLIERS in src/medrisk/data/synthetic.py.")

    # ================================================================
    # CHAPTER 4
    # ================================================================
    pdf.chapter_head(4, "Comorbidity Assessment")
    pdf.p("Comorbidity -- the co-occurrence of multiple conditions -- is multiplicative, "
          "not additive. A diabetic patient does not simply add CKD risk; diabetes "
          "increases CKD risk by 2.5x. The Charlson Comorbidity Index (Quan et al., "
          "2005) aggregates 17 disease categories into a single score with severity "
          "weights from 1 to 6.")

    pdf.figure(chart_comorbidity_cascade(),
               "Comorbidity cascade: obesity increases diabetes risk 2.5x, which "
               "increases CKD risk 2.5x -- yielding a combined 6.25x risk multiplier. "
               "Source: COMORBIDITY_LINKS in src/medrisk/data/synthetic.py.")

    pdf.figure(chart_charlson_weights(),
               "Charlson Comorbidity Index: 17 categories with severity weights. "
               "Three hierarchy rules apply: complicated diabetes (wt 2) supersedes "
               "uncomplicated (wt 1); severe liver (wt 3) supersedes mild (wt 1); "
               "metastatic cancer (wt 6) supersedes any malignancy (wt 2). "
               "Source: CHARLSON_CATEGORIES in src/medrisk/data/charlson.py.")

    pdf.h2("Worked example")
    pdf.p("Patient: 65-year-old male with I21.0 (MI, wt 1), E11.4 (T2D with neuro "
          "complications, wt 2), N18.4 (CKD stage 4, wt 2), J44.9 (COPD, wt 1). "
          "Charlson Index = 1 + 2 + 2 + 1 = 6. Note: hypertension (I10) has no "
          "Charlson category -- a patient with only HTN and dyslipidemia scores 0.")

    # ================================================================
    # CHAPTER 5
    # ================================================================
    pdf.chapter_head(5, "Risk Classification Models")
    pdf.p("The core underwriting model is an XGBoost gradient boosted classifier "
          "(200 trees, depth 6, learning rate 0.05) that predicts P(major adverse event) "
          "from approximately 40 features: 5 demographics, 17 Charlson indicators, "
          "10 lab values, and 8 medication flags. No imputation is performed -- missing "
          "features remain missing.")

    pdf.table_caption("Model Router: one model per data profile")
    pdf.table(
        ["Profile", "Features available", "Typical market"],
        [
            ["FULL", "All (demo + diag + labs + meds)", "Germany (DE)"],
            ["NO_LABS", "Demo + diagnoses + medications", "GKV claims"],
            ["NO_MEDS", "Demo + diagnoses + labs", "Research DBs"],
            ["MINIMAL", "Demo + diagnoses only", "International"],
            ["INSUFFICIENT", "Mandatory human review", "--"],
        ],
        [30, 70, 40],
    )

    pdf.key_concept("The Model Router trains separate XGBoost models per data profile. "
                    "A FULL model trained on German data would output high confidence "
                    "on sparse International data -- filling gaps with training priors, "
                    "not patient evidence. Profile-specific routing eliminates this.")

    pdf.table_caption("Model performance on synthetic cohort")
    pdf.table(
        ["Metric", "Value", "Interpretation"],
        [
            ["AUC-ROC", "0.71", "Better than random, realistic for broad risk scoring"],
            ["Brier score", "0.010", "Well-calibrated probabilities"],
            ["C-index (Cox)", "0.72", "Good survival model discrimination"],
        ],
        [30, 20, 95], num_cols=[1],
    )

    # ================================================================
    # CHAPTER 6
    # ================================================================
    pdf.chapter_head(6, "Disease Progression Modeling")
    pdf.p("An underwriter needs to know not just whether a patient will get sick, but "
          "when and how fast. MedRisk uses continuous-time Markov chains (CTMC) to "
          "model disease progression through discrete stages. The transition intensity "
          "matrix Q encodes rates between states; P(t) = expm(Qt) gives transition "
          "probabilities at time t.")

    pdf.figure(chart_cv_progression(),
               "Cardiovascular disease: 5-state CTMC starting from Healthy. State "
               "occupation probabilities over 30 years. Mean sojourn times: Healthy "
               "12.5y, Risk factors 16.7y, Chronic 25y. Source: CARDIOVASCULAR_CONFIG "
               "in src/medrisk/models/disease_configs.py.")

    pdf.table_caption("Cardiovascular CTMC transition intensities")
    pdf.table(
        ["Transition", "Intensity", "Mean sojourn (y)"],
        [
            ["Healthy -> Risk factors", "0.08", "12.5"],
            ["Risk factors -> Chronic", "0.06", "16.7"],
            ["Risk factors -> Healthy", "0.02", "(reverse)"],
            ["Chronic -> Complication", "0.04", "25.0"],
            ["Chronic -> Major event", "0.01", "(skip)"],
            ["Complication -> Major event", "0.03", "33.3"],
        ],
        [55, 30, 35], num_cols=[1, 2],
    )

    pdf.figure(chart_alzheimer_progression(),
               "Alzheimer's disease: 7-state CTMC starting from Normal Cognition. "
               "MCI-to-Mild AD conversion at 15%/year (Petersen et al., NEJM 2018). "
               "Severe AD: ~2-year mean survival (Brookmeyer et al.). Source: "
               "ALZHEIMER_CONFIG in src/medrisk/models/disease_configs.py.")

    pdf.table_caption("Alzheimer CTMC transition intensities")
    pdf.table(
        ["Transition", "Intensity", "Mean sojourn", "Source"],
        [
            ["NC -> SCD", "0.04", "25.0 y", "Subclinical phase"],
            ["SCD -> MCI", "0.08", "12.5 y", "Cognitive complaints"],
            ["MCI -> Mild AD", "0.15", "6.7 y", "Petersen 2018"],
            ["Mild -> Moderate AD", "0.25", "4.0 y", "Documented rate"],
            ["Moderate -> Severe AD", "0.33", "3.0 y", "Accelerated decline"],
            ["Severe AD -> Death", "0.50", "2.0 y", "Brookmeyer et al."],
        ],
        [40, 22, 25, 40], num_cols=[1, 2],
    )

    # ================================================================
    # CHAPTER 7
    # ================================================================
    pdf.chapter_head(7, "Data Quality -- The DQS Framework")
    pdf.p("The Data Quality Score is computed per patient before any model inference. "
          "It answers: how much should the downstream model trust its own input? "
          "DQS combines three components with fixed weights:")

    pdf.key_concept("DQS = 0.40 x completeness + 0.35 x consistency + 0.25 x recency. "
                    "Tiers: adequate (>= 0.80), caution (0.60-0.80), insufficient (< 0.60).")

    pdf.h3("Completeness (weight 0.40)")
    pdf.p("Fraction of 40 expected features observed: 5 demographics + 17 Charlson "
          "category indicators + 10 lab values + 8 medication flags.")

    pdf.h3("Consistency (weight 0.35)")
    pdf.table_caption("Domain consistency rules")
    pdf.table(
        ["Rule", "If condition", "Then check"],
        [
            ["diabetes_hba1c", "E11.x present", "HbA1c >= 5.7%"],
            ["ckd_egfr", "N18.4/5/6 present", "eGFR < 30"],
            ["hf_bnp", "I50.x present", "NT-proBNP > 125"],
            ["hypertension_bp", "I10.x present", "SBP > 120 or on meds"],
            ["no_diabetes_hba1c", "No E11.x", "HbA1c < 6.5%"],
        ],
        [38, 40, 50],
    )

    pdf.h3("Recency (weight 0.25)")
    pdf.p("Exponential decay with half-life 1.4 years: weight(age) = exp(-ln(2)/1.4 x "
          "age_years). A 1-year-old lab has weight 0.61; a 3-year-old lab, 0.23; "
          "a 5-year-old lab, 0.08. No labs at all yields recency = 0.")

    pdf.figure(chart_dqs_components(),
               "DQS component breakdown by market. Germany achieves DQS ~0.91 "
               "(adequate tier); International ~0.44 (insufficient -- mandatory "
               "human review). Dotted lines mark tier thresholds at 0.80 and 0.60. "
               "Source: compute_dqs_v2() in src/medrisk/validation/data_quality.py.")

    # ================================================================
    # CHAPTER 8
    # ================================================================
    pdf.chapter_head(8, "Failure Detection and PBW")
    pdf.p("The core contribution of MedRisk: detecting when a model produces a "
          "confident prediction on insufficient data. Three independent signals flag "
          "unreliable predictions.")

    pdf.table_caption("Three failure detection signals")
    pdf.table(
        ["Signal", "Formula", "Threshold", "Detects"],
        [
            ["CCM", "|raw - calibrated|", "> 0.20", "Calibration mismatch"],
            ["EPU", "max(decile) - min(decile)", "> 3", "Model disagreement"],
            ["PBW", "conf > 0.80 AND DQS < 0.60", "--", "Confident on bad data"],
        ],
        [18, 42, 22, 45],
    )

    pdf.key_concept("When PBW fires, the model cannot have enough information to "
                    "justify its confidence. The confidence comes from the training "
                    "distribution's prior, not the patient's data. This is the most "
                    "dangerous failure mode in automated underwriting.")

    pdf.figure(chart_pbw_scatter(),
               "Confidence vs. DQS for 400 synthetic patients across four markets. "
               "The PBW zone (upper left, shaded red) captures high-confidence "
               "predictions on low-quality data. International patients cluster in "
               "this zone. Source: detect_failure_modes() in "
               "src/medrisk/validation/failure_detection.py.", w=150)

    pdf.h2("Cost-optimal decisions")
    pdf.p("The v2 Reliability Head replaces fixed PBW thresholds with a learned model "
          "that estimates P(wrong | prediction, quality features) via logistic regression "
          "and makes cost-optimal decisions. Default cost parameters: cost_fn = 5.0 "
          "(accept a bad risk), cost_fp = 1.0 (reject a good applicant), "
          "cost_review = 0.5 (escalate to human).")

    pdf.figure(chart_cost_decisions(),
               "Expected cost curves for three actions as a function of P(wrong). "
               "Accept is optimal below P(wrong) = 0.10; review between 0.10-0.50; "
               "reject above 0.50. The 5:1 cost asymmetry reflects insurance reality: "
               "false negatives cost 5x more than false positives. Source: "
               "ReliabilityHead in src/medrisk/validation/reliability_head.py.", w=150)

    # ================================================================
    # CHAPTER 9
    # ================================================================
    pdf.chapter_head(9, "Insurance Pricing -- KTG")
    pdf.p("Krankentagegeld (KTG) pays a daily rate when the policyholder cannot work "
          "(Arbeitsunfaehigkeit, AU). Pricing depends on disease stage: each stage has "
          "a different AU probability and expected episode duration. The CTMC provides "
          "P(stage at time t), which feeds directly into premium calculation.")

    pdf.p("Pricing formula: Expected annual KTG cost = Sum over stages of "
          "P(state_i at t) x P(AU | state_i) x age_mult x E[days | state_i] x daily_rate. "
          "Monthly premium adds safety loading (15%) and admin surcharge (12%).")

    pdf.figure(chart_ktg_pricing(),
               "Hypertonie (I10): AU probability and expected annual KTG cost by "
               "disease stage. At stage 4 (Major Event), AU probability reaches 80% "
               "with 120-day episodes. Daily rate: EUR 80. Source: KTG disease "
               "configs in app/pages/5_KTG_Kalkulation.py.", w=150)

    pdf.table_caption("Three KTG disease examples")
    pdf.table(
        ["Disease", "ICD", "Prevalence", "Stages", "Max P(AU)", "Max days"],
        [
            ["Hypertonie", "I10", "30%", "5", "80%", "120"],
            ["Adipositas", "E66.0", "24%", "4", "25%", "45"],
            ["Rueckenschmerzen", "M54", "25%", "4", "75%", "90"],
        ],
        [33, 18, 22, 18, 18, 18], num_cols=[2, 3, 4, 5],
    )

    pdf.p("Data quality impact: the same ICD code (I10) produces up to 3x premium "
          "variance depending on data completeness. Complete data (DQS 0.85) allows "
          "precise staging and narrow premiums. Sparse data (DQS 0.40) leaves the "
          "stage indeterminate, forcing conservative assumptions.")

    # ================================================================
    # CHAPTER 10
    # ================================================================
    pdf.chapter_head(10, "Pipeline and Validation")

    pdf.figure(chart_pipeline_flow(),
               "MedRisk v2 pipeline: seven stages from patient record to audited "
               "decision. Each stage adds a quality gate. Source: MedRiskPipeline "
               "in src/medrisk/pipeline.py.", w=160)

    pdf.p("The pipeline executes 9 steps: (1) generate or accept cohort, (2) convert "
          "to DataFrame, (3) build feature matrix without imputation, (4) classify data "
          "profiles, (5) compute DQS v2 per patient, (6) train Model Router per profile, "
          "(7) generate predictions, (8) Reliability Head computes P(wrong) and "
          "cost-optimal decisions, (9) write audit log in JSON Lines format.")

    pdf.p("The audit log (src/medrisk/governance/audit_log.py) records every field "
          "needed for EU AI Act Art. 12 compliance: timestamp, patient_id, model_id, "
          "features used and missing, DQS components, predicted probability, P(wrong), "
          "decision, and human-readable explanation. Human overrides are tracked "
          "separately with reason codes.")

    pdf.table_caption("Validation roadmap")
    pdf.table(
        ["Phase", "Status", "Data", "Goal"],
        [
            ["Phase 1", "Complete", "Synthetic (4K patients)", "Demonstrate mechanism"],
            ["Phase 2", "Planned", "Real (CPRD, InGef, PKV)", "Validate thresholds"],
            ["Phase 3", "Vision", "Production (internal)", "Deploy with monitoring"],
        ],
        [25, 25, 45, 45],
    )

    pdf.p("Phase 1 limitations: performance metrics are synthetic-only; DQS thresholds "
          "(0.60/0.80) are heuristic; consistency rules are simplified. Phase 2 requires "
          "minimum 50,000 patients with 5+ years follow-up and linked outcomes. "
          "The bottleneck is data access and regulatory clearance, not engineering.")

    # ================================================================
    # CHAPTER 11
    # ================================================================
    pdf.chapter_head(11, "Actuarial Reserving and Sickness Absence")

    pdf.h2("Why reserves matter")
    pdf.p("An insurer collects premiums today to pay claims tomorrow. Reserves are "
          "the estimated future cost of claims already incurred but not yet fully "
          "reported (IBNR -- Incurred But Not Reported). Under-reserving creates "
          "solvency risk and regulatory intervention; over-reserving leads to capital "
          "inefficiency and competitive disadvantage.")

    pdf.h2("Chain-Ladder method")
    pdf.p("The Chain-Ladder method (src/medrisk/models/actuarial.py) estimates ultimate "
          "claims from a development triangle -- a matrix where rows are accident years "
          "and columns are development periods. Step 1: compute volume-weighted "
          "development factors f_k = Sum(C[i,k+1]) / Sum(C[i,k]). Step 2: project "
          "incomplete years by multiplying the latest observed value by remaining factors. "
          "Step 3: reserve = projected ultimate minus already paid.")

    pdf.key_concept("Chain-Ladder assumes past development patterns will repeat. It "
                    "performs poorly for recent accident years with little development "
                    "history. The Mack standard error quantifies this estimation "
                    "uncertainty without distributional assumptions.")

    pdf.h2("Bornhuetter-Ferguson method")
    pdf.p("BF addresses Chain-Ladder's instability by blending reported data with "
          "a prior estimate: BF_ultimate = reported + prior x (1 - 1/CDF), where "
          "prior is an external estimate (e.g. from pricing) and CDF is the cumulative "
          "development factor. BF is more stable for recent years because it does not "
          "rely solely on sparse reported data.")

    pdf.figure(chart_reserve_triangle(),
               "Chain-Ladder vs. Bornhuetter-Ferguson reserve estimates by accident "
               "year. BF produces more conservative, stable estimates for recent years "
               "(2023-2024) where development data is sparse. Source: "
               "src/medrisk/models/actuarial.py.", w=150)

    pdf.table_caption("Reserving method comparison")
    pdf.table(
        ["Method", "Strengths", "Weaknesses", "Best for"],
        [
            ["Chain-Ladder", "Simple, data-driven", "Unstable for recent years", "Mature accident years"],
            ["Bornhuetter-Ferguson", "Stable, uses prior info", "Depends on prior quality", "Recent accident years"],
            ["Mack std. error", "Distribution-free", "Wide intervals", "Uncertainty quantification"],
        ],
        [28, 35, 35, 35],
    )

    pdf.h2("Sickness absence models")
    pdf.p("The sickness_absence.py module models AU frequency and duration separately. "
          "Frequency uses Negative Binomial regression: log(mu) = b0 + b1*age + "
          "b2*male + b3*MRS + b4*log(occ_risk), where MRS is the MedRisk Score "
          "and occ_risk is the occupational risk class (1-4, with multipliers "
          "1.0, 1.25, 1.60, 2.10).")
    pdf.p("Duration uses a Weibull Accelerated Failure Time model: S(t) = exp(-(t/lambda)^k), "
          "with expected duration E[T] = lambda * Gamma(1 + 1/k). This models the "
          "probability of still being on sick leave at time t.")

    pdf.figure(chart_sickness_absence(),
               "AU frequency and mean duration by occupational risk class. Class 4 "
               "(heavy manual labor) shows 2.1x the frequency and 2.7x the duration "
               "of Class 1 (office work). Source: "
               "src/medrisk/models/sickness_absence.py.", w=150)

    pdf.h2("Aggregate claims distribution")
    pdf.p("For portfolio-level risk, Panjer recursion computes the compound distribution "
          "of total claims. Frequency follows a Negative Binomial (allowing overdispersion "
          "vs. Poisson), severity follows a Weibull (flexible shape for claim durations), "
          "and the aggregate is computed via recursive convolution using the (a,b,0) class. "
          "This feeds into Solvency II capital requirements and reinsurance pricing.")

    # ================================================================
    # CHAPTER 12
    # ================================================================
    pdf.chapter_head(12, "The Full Pipeline -- End to End")

    pdf.figure(chart_full_pipeline(),
               "MedRisk v2 complete pipeline: 11 stages from cohort generation "
               "to audited underwriting decision. The top row handles data processing "
               "and ML predictions; the bottom row adds clinical validation and "
               "governance. Source: src/medrisk/pipeline.py.", w=160)

    pdf.table_caption("Pipeline stages -- step by step")
    pdf.table(
        ["Step", "Component", "Source file"],
        [
            ["1", "Cohort generation", "data/synthetic.py"],
            ["2", "DataFrame conversion", "data/synthetic.py"],
            ["3", "Feature matrix (~40 features)", "features/engineering.py"],
            ["4", "Data profiling (FULL/NO_LABS/...)", "features/data_profile.py"],
            ["5", "DQS v2 per patient", "validation/data_quality.py"],
            ["6", "Model Router training", "models/model_router.py"],
            ["7", "Predictions per profile", "models/model_router.py"],
            ["8", "Reliability Head: P(wrong)", "validation/reliability_head.py"],
            ["9", "Clinical consistency checks", "underwriting/clinical_checks.py"],
            ["10", "Underwriting decision", "underwriting/decision_engine.py"],
            ["11", "Audit logging", "governance/audit_log.py"],
        ],
        [12, 50, 55], num_cols=[0],
    )

    pdf.h2("The audit trail")
    pdf.p("The AuditLogger (src/medrisk/governance/audit_log.py) writes one JSON "
          "object per patient per decision to an append-only JSON Lines file. Each "
          "entry contains: timestamp, run_id, patient_id, market, data_profile, "
          "model_id, features used/missing, DQS components, predicted probability, "
          "P(wrong), decision, and human-readable explanation. This directly supports "
          "EU AI Act Art. 12 (record-keeping).")

    pdf.h2("Human override")
    pdf.p("When a human underwriter disagrees with the model, the override is logged "
          "via src/medrisk/governance/human_override.py with the original decision, "
          "override decision, reason, and overrider ID. This supports EU AI Act "
          "Art. 14 (human oversight) and creates a feedback loop -- override patterns "
          "can identify systematic model failures.")

    pdf.h2("Distribution shift detection")
    pdf.p("Models degrade when the input population changes. "
          "src/medrisk/validation/shift_detection.py monitors this using PSI "
          "(Population Stability Index, threshold 0.20 for major shift) and "
          "Jensen-Shannon divergence (threshold 0.10). When shift is detected, "
          "the model should be recalibrated or retrained.")

    pdf.h2("Validation roadmap")
    pdf.table_caption("Validation phases and data requirements")
    pdf.table(
        ["Phase", "Status", "Data", "Goal"],
        [
            ["Phase 1", "Complete", "Synthetic (4K patients)", "Demonstrate mechanism"],
            ["Phase 2", "Planned", "Real (CPRD, InGef, PKV)", "Validate thresholds"],
            ["Phase 3", "Vision", "Production (a major European insurer)", "Deploy with monitoring"],
        ],
        [25, 25, 45, 45],
    )

    pdf.p("Phase 1 delivers a regulatory-ready skeleton: 442 tests, 4 European "
          "markets, 2 disease progression models, 5 notebooks, 7 Streamlit pages, "
          "8 external data adapters, automated underwriting with clinical consistency "
          "checks, Chain-Ladder/BF reserving, sickness absence models, SHAP "
          "explainability, and full audit trail. Phase 2 requires minimum 50,000 "
          "patients with 5+ years follow-up and linked outcomes.")

    pdf.key_concept("MedRisk answers the question: can we detect when an AI "
                    "underwriting model is confidently wrong? The answer is yes, on "
                    "synthetic data. Phase 2 answers: does this detection work on "
                    "real claims? The bottleneck is data access and regulatory "
                    "clearance, not engineering.")

    # ================================================================
    # APPENDIX A
    # ================================================================
    pdf.chapter_head(0, "Appendix A: Reference Tables")

    pdf.table_caption("Charlson Comorbidity Index (17 categories)")
    pdf.table(
        ["#", "Category", "Wt", "Key ICD-10 prefixes"],
        [
            ["1", "Myocardial infarction", "1", "I21, I22, I25.2"],
            ["2", "Congestive heart failure", "1", "I50, I42, I43"],
            ["3", "Peripheral vascular disease", "1", "I70, I71, I73"],
            ["4", "Cerebrovascular disease", "1", "I60-I68, G45, G46"],
            ["5", "Dementia", "1", "F00-F03, G30"],
            ["6", "Chronic pulmonary disease", "1", "J40-J47, J60-J67"],
            ["7", "Rheumatic disease", "1", "M05, M06, M32-M36"],
            ["8", "Peptic ulcer disease", "1", "K25-K28"],
            ["9", "Mild liver disease", "1", "B18, K70-K76"],
            ["10", "Diabetes, uncomplicated", "1", "E10-E14 (excl. .2-.7)"],
            ["11", "Diabetes, complicated", "2", "E10.2-E14.7"],
            ["12", "Hemiplegia/paraplegia", "2", "G81-G83"],
            ["13", "Renal disease", "2", "N18, N19, I12.0"],
            ["14", "Any malignancy", "2", "C00-C97 (excl. C77-C80)"],
            ["15", "Moderate/severe liver", "3", "I85, K70.4, K72"],
            ["16", "Metastatic solid tumor", "6", "C77-C80"],
            ["17", "AIDS/HIV", "6", "B20-B24"],
        ],
        [8, 45, 10, 55], num_cols=[0, 2],
    )

    pdf.table_caption("Laboratory reference ranges")
    pdf.table(
        ["Lab", "LOINC", "Unit", "Ref low", "Ref high"],
        [
            ["HbA1c", "4548-4", "%", "4.0", "5.6"],
            ["Creatinine", "2160-0", "mg/dL", "0.6", "1.2"],
            ["eGFR", "48642-3", "mL/min", "60", "120"],
            ["Total Chol.", "2093-3", "mg/dL", "125", "200"],
            ["HDL", "2085-9", "mg/dL", "40", "60"],
            ["LDL", "13457-7", "mg/dL", "0", "100"],
            ["Triglycerides", "2571-8", "mg/dL", "0", "150"],
            ["Systolic BP", "8480-6", "mmHg", "90", "120"],
            ["Diastolic BP", "8462-4", "mmHg", "60", "80"],
            ["NT-proBNP", "33762-6", "pg/mL", "0", "125"],
            ["MMSE", "72106-8", "score", "24", "30"],
            ["MoCA", "72172-0", "score", "26", "30"],
            ["CSF Ab42", "33203-1", "pg/mL", "600", "1500"],
            ["CSF p-tau181", "72260-3", "pg/mL", "0", "22"],
        ],
        [28, 22, 22, 22, 22], num_cols=[3, 4],
    )

    pdf.table_caption("Market configuration parameters")
    pdf.table(
        ["Parameter", "DE", "ES", "FR", "INT"],
        [
            ["Coding completeness", "0.95", "0.80", "0.90", "0.60"],
            ["Lab completeness", "0.92", "0.75", "0.88", "0.50"],
            ["Lab noise sigma", "0.02", "0.05", "0.03", "0.10"],
            ["Diagnosis lag (days)", "14+/-7", "30+/-20", "60+/-30", "90+/-60"],
            ["Medication recording", "0.95", "0.80", "0.88", "0.60"],
            ["Age (mean+/-std)", "52+/-14", "56+/-16", "54+/-15", "50+/-18"],
        ],
        [40, 22, 22, 22, 22], num_cols=[1, 2, 3, 4],
    )

    pdf.table_caption("Threshold and cost parameters")
    pdf.table(
        ["Parameter", "Value", "Source file"],
        [
            ["DQS: completeness weight", "0.40", "data_quality.py"],
            ["DQS: consistency weight", "0.35", "data_quality.py"],
            ["DQS: recency weight", "0.25", "data_quality.py"],
            ["Recency half-life", "1.4 years", "data_quality.py"],
            ["DQS adequate", ">= 0.80", "data_quality.py"],
            ["DQS caution", ">= 0.60", "data_quality.py"],
            ["CCM threshold", "0.20", "failure_detection.py"],
            ["EPU threshold", "3 deciles", "failure_detection.py"],
            ["PBW confidence", "> 0.80", "failure_detection.py"],
            ["PBW DQS", "< 0.60", "failure_detection.py"],
            ["Cost: false negative", "5.0", "reliability_head.py"],
            ["Cost: false positive", "1.0", "reliability_head.py"],
            ["Cost: human review", "0.5", "reliability_head.py"],
        ],
        [45, 25, 55],
    )

    # ================================================================
    # APPENDIX B
    # ================================================================
    pdf.chapter_head(0, "Appendix B: German-English Glossary")

    pdf.table_caption("German insurance and medical terminology")
    pdf.table(
        ["German", "English"],
        [
            ["Arbeitsunfaehigkeit (AU)", "Work incapacity"],
            ["Beitrag", "Premium"],
            ["Berufsunfaehigkeit (BU)", "Occupational disability"],
            ["Datenschutz-Grundverordnung (DSGVO)", "GDPR"],
            ["Deckungsrueckstellung", "Coverage reserve (life/health)"],
            ["Erkrankung", "Disease / condition"],
            ["Gesetzliche Krankenversicherung (GKV)", "Statutory health insurance"],
            ["Krankenkasse", "Health insurance fund"],
            ["Krankentagegeld (KTG)", "Daily sickness benefit"],
            ["Leistungsfall", "Benefit event / claim"],
            ["Nachversicherung", "Supplementary insurance"],
            ["Private Krankenversicherung (PKV)", "Private health insurance"],
            ["Risikopruefung", "Risk assessment / underwriting"],
            ["Risikoklasse", "Risk class / occupational risk category"],
            ["Rueckstellung", "Reserve (actuarial)"],
            ["Schadenreserve", "Claims reserve (P&C)"],
            ["Selbstbehalt", "Deductible"],
            ["Stadien", "Stages (disease severity)"],
            ["Tarifgestaltung", "Tariff design / pricing"],
            ["Uebergangsrate", "Transition rate"],
            ["Versicherungsnehmer", "Policyholder"],
            ["Versicherungsvertrag", "Insurance contract"],
            ["Vorerkrankung", "Pre-existing condition"],
            ["Wartezeit", "Waiting period"],
            ["Zuschlag", "Premium loading / surcharge"],
        ],
        [60, 60],
    )

    # ================================================================
    # APPENDIX C
    # ================================================================
    pdf.chapter_head(0, "Appendix C: Further Reading")

    refs = [
        ("Quan et al. (2005)", "Coding algorithms for defining comorbidities in "
         "ICD-9-CM and ICD-10 administrative data. Medical Care.",
         "Charlson Index ICD-10 adaptation"),
        ("Petersen et al. (2018)", "Practice guideline update: MCI. Neurology.",
         "MCI -> AD conversion rates"),
        ("Brookmeyer et al. (2007)", "Forecasting the global burden of Alzheimer's "
         "disease. Alzheimer's & Dementia.",
         "AD survival estimates"),
        ("Hernan & Robins (2020)", "Causal Inference: What If.",
         "Causal ML foundations (IPW)"),
        ("Vovk et al. (2005)", "Algorithmic Learning in a Random World.",
         "Conformal prediction theory"),
        ("Angelopoulos & Bates (2023)", "Conformal Prediction: A Gentle Introduction. "
         "Foundations and Trends in ML.",
         "Modern conformal methods"),
        ("EU AI Act (2024)", "Regulation (EU) 2024/1689.",
         "Regulatory framework for high-risk AI"),
        ("Guo et al. (2017)", "On Calibration of Modern Neural Networks. ICML.",
         "Calibration and confidence"),
        ("Platt (1999)", "Probabilistic Outputs for SVMs and Comparisons to "
         "Regularized Likelihood Methods.",
         "Platt calibration"),
        ("van Walraven et al. (2009)", "A modification of the Elixhauser comorbidity "
         "measures. Medical Care.",
         "Elixhauser scoring weights"),
        ("Mack (1993)", "Distribution-free Calculation of the Standard Error of "
         "Chain Ladder Reserve Estimates. ASTIN Bulletin.",
         "Chain-Ladder theory and Mack standard errors"),
        ("Bornhuetter & Ferguson (1972)", "The Actuary and IBNR. PCAS.",
         "BF reserve estimation method"),
        ("GBD 2019 Collaborators", "Diseases and Injuries. The Lancet.",
         "Global disease prevalence data"),
    ]
    pdf.table_caption("Key references")
    pdf.table(
        ["Citation", "Title / Journal", "Relevance"],
        [[a, b, c] for a, b, c in refs],
        [30, 55, 35],
    )

    # ===== Output =====
    output_path = OUT / "study_guide.pdf"
    pdf.output(str(output_path))
    logger.info("Study guide written to %s (%d pages, %d figures, %d tables)",
                output_path, pdf.page_no(), pdf._fig_n, pdf._tbl_n)
    return output_path


if __name__ == "__main__":
    build_study_guide()
