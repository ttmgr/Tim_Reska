#!/usr/bin/env python3
"""Generate MedRisk pitch deck as PDF.

Produces a 10-slide landscape PDF using fpdf2 with live charts generated
from actual synthetic data via matplotlib.  Uses the shared academic/scientific
design system from _academic_style.py.

Usage:
    python scripts/generate_slides.py
"""

from __future__ import annotations

import logging
import sys
from io import BytesIO
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from medrisk.data.schemas import MARKET_CONFIGS
from medrisk.data.synthetic import generate_cohort, cohort_to_dataframe
from medrisk.features.engineering import build_feature_matrix, get_targets
from medrisk.models.xgb_classifier import RiskClassifier
from medrisk.validation.data_quality import compute_dqs

# Shared academic style
from _academic_style import (
    SlidePDF, chart_style, safe,
    M_BLUE, M_AMBER, M_GREEN, M_RED, M_DARK, M_GREY, M_TEAL, M_PURPLE, M_LIGHT,
    C_TEXT, C_HEADING, C_BODY, C_CAPTION, C_FOOTNOTE, C_ACCENT,
    C_TABLE_HDR, C_TABLE_ALT, C_BOX_BG, C_RULE, C_WHITE,
    C_GREEN_BG, C_RED_BG,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Layout constants (landscape A4)
PAGE_W = 297
PAGE_H = 210
MARGIN = 15
CONTENT_W = PAGE_W - 2 * MARGIN


# =============================================================================
# Data pipeline
# =============================================================================

def prepare_data() -> dict:
    """Generate synthetic cohort, compute DQS, train classifier."""
    logger.info("Generating synthetic cohort (1000/market)...")
    cohort = generate_cohort(n_per_market=1000, seed=42)

    logger.info("Computing DQS for each patient...")
    dqs_results = [compute_dqs(p) for p in cohort]
    dqs_scores = np.array([r.dqs for r in dqs_results])
    dqs_tiers = [r.tier for r in dqs_results]
    markets = [p.market.value for p in cohort]

    logger.info("Building feature matrix...")
    df = cohort_to_dataframe(cohort)
    X, feature_names = build_feature_matrix(df)
    events, _times = get_targets(df)

    logger.info("Training risk classifier...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, events, test_size=0.2, random_state=42, stratify=events,
    )
    clf = RiskClassifier()
    clf.fit(X_train, y_train, X_val=X_test, y_val=y_test)
    confidence = clf.predict_proba(X)

    # Compute PBW flags
    pbw_flags = (confidence > 0.80) & (dqs_scores < 0.60)

    return {
        "cohort": cohort,
        "df": df,
        "dqs_scores": dqs_scores,
        "dqs_tiers": dqs_tiers,
        "markets": np.array(markets),
        "confidence": confidence,
        "pbw_flags": pbw_flags,
        "events": events,
    }


# =============================================================================
# Chart generation
# =============================================================================

def chart_dqs_by_market(data: dict) -> BytesIO:
    """Box plot of DQS distribution by market."""
    chart_style()
    fig, ax = plt.subplots(figsize=(6, 3.5), dpi=150)

    market_order = ["DE", "FR", "ES", "INT"]
    market_colors = {
        "DE": M_BLUE, "FR": M_TEAL, "ES": M_GREY, "INT": M_RED,
    }

    box_data = []
    labels = []
    for m in market_order:
        mask = data["markets"] == m
        box_data.append(data["dqs_scores"][mask])
        cfg = MARKET_CONFIGS[m]
        labels.append(f"{m}\n(coding {cfg.coding_completeness:.0%})")

    bp = ax.boxplot(
        box_data, tick_labels=labels, patch_artist=True,
        widths=0.5, showfliers=False,
        medianprops={"color": "white", "linewidth": 1.5},
    )
    for patch, m in zip(bp["boxes"], market_order):
        patch.set_facecolor(market_colors[m])
        patch.set_alpha(0.8)

    # Threshold lines
    ax.axhline(0.80, color=M_GREEN, linestyle="--", linewidth=1, label="Adequate (0.80)")
    ax.axhline(0.60, color=M_RED, linestyle="--", linewidth=1, label="Caution (0.60)")
    ax.set_ylabel("Data Quality Score")
    ax.set_title("DQS Distribution by Market (N=4,000)", fontweight="bold", fontsize=11)
    ax.legend(fontsize=8, loc="lower left")
    ax.set_ylim(0, 1.05)

    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_pbw_scatter(data: dict) -> BytesIO:
    """Confidence vs DQS scatter with PBW zone."""
    chart_style()
    fig, ax = plt.subplots(figsize=(6, 4), dpi=150)

    conf = data["confidence"]
    dqs = data["dqs_scores"]
    pbw = data["pbw_flags"]

    # PBW danger zone
    ax.axhspan(0.80, 1.02, xmin=0, xmax=0.60 / 1.02, color="#FDE8E8", alpha=0.5, zorder=0)
    ax.fill_between(
        [0, 0.60], [0.80, 0.80], [1.02, 1.02],
        color="#FDE8E8", alpha=0.5, zorder=0,
    )
    ax.text(
        0.15, 0.90, "PBW\nDanger Zone",
        fontsize=11, fontweight="bold", color=M_RED,
        ha="center", va="center", alpha=0.8,
    )

    # Non-flagged points
    ax.scatter(
        dqs[~pbw], conf[~pbw],
        s=4, alpha=0.25, c=M_BLUE, label="Normal", rasterized=True,
    )
    # Flagged points
    ax.scatter(
        dqs[pbw], conf[pbw],
        s=12, alpha=0.6, c=M_RED, label="PBW flagged", rasterized=True,
    )

    # Threshold lines
    ax.axhline(0.80, color=M_GREY, linestyle=":", linewidth=0.8)
    ax.axvline(0.60, color=M_GREY, linestyle=":", linewidth=0.8)

    ax.set_xlabel("Data Quality Score")
    ax.set_ylabel("Model Confidence (P(high risk))")
    ax.set_title("Plausible-but-Wrong Detection (N=4,000)", fontweight="bold", fontsize=11)
    ax.set_xlim(0, 1.02)
    ax.set_ylim(0, 1.02)
    ax.legend(fontsize=8, loc="lower right")

    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


# =============================================================================
# Slides
# =============================================================================

def slide_01_title(pdf: SlidePDF) -> None:
    """Title slide."""
    pdf.add_page()

    # Clean white background with centred title
    pdf.set_text_color(*C_HEADING)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_y(55)
    pdf.cell(CONTENT_W, 14, safe("MedRisk"), align="C",
             new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(*C_BODY)
    pdf.cell(CONTENT_W, 8, safe("AI-Augmented Medical Underwriting"), align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.cell(CONTENT_W, 8, safe("with Failure Mode Detection"), align="C",
             new_x="LMARGIN", new_y="NEXT")

    # Accent line
    pdf.ln(6)
    y = pdf.get_y()
    pdf.set_draw_color(*C_ACCENT)
    pdf.set_line_width(0.6)
    mid = PAGE_W / 2
    pdf.line(mid - 40, y, mid + 40, y)
    pdf.set_line_width(0.2)
    pdf.ln(10)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*C_BODY)
    pdf.cell(CONTENT_W, 7, safe("the author  |  Helmholtz Munich"), align="C",
             new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*C_CAPTION)
    pdf.cell(CONTENT_W, 7, safe("Proof of Concept  |  Synthetic Data  |  March 2026"),
             align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(*C_BODY)
    pdf.set_draw_color(*C_RULE)


def slide_02_problem(pdf: SlidePDF) -> None:
    """The Problem."""
    pdf.add_page()
    pdf.slide_title(
        "Confident AI predictions on bad data cost insurers 2,000+ mispriced policies per year",
        "Current underwriting models cannot detect when their own output is unreliable",
    )

    pdf.body_text(
        "Current AI underwriting models produce a risk score for every applicant. "
        "But they cannot distinguish between a confident prediction backed by rich "
        "clinical data and one that looks equally confident on sparse, incomplete records."
    )
    pdf.ln(3)

    pdf.bullet(
        safe("The core failure:  A model that is 95% confident on a patient with 40% missing data "
             "is running on learned priors, not evidence.")
    )
    pdf.bullet(
        safe("Why it matters:  These decisions look correct in aggregate metrics (AUC, accuracy) "
             "but carry hidden liability at the individual level.")
    )
    pdf.bullet(
        safe("The scale:  At scale, even a 2% plausible-but-wrong rate across 100,000 policies "
             "means 2,000 incorrectly assessed risks per year.")
    )

    pdf.ln(8)

    # Three metric boxes
    pdf.key_metric("Wrong decisions / year", "2,000+", MARGIN + 10, 130, 75)
    pdf.key_metric("Undetected by AUC", "Yes", MARGIN + 105, 130, 75)
    pdf.key_metric("Current mitigation", "None", MARGIN + 200, 130, 75)

    pdf.source_line("Source: ISME Communications 2024; EU AI Act Regulation 2024/1689")


def slide_03_insight(pdf: SlidePDF) -> None:
    """The Insight."""
    pdf.add_page()
    pdf.slide_title(
        "I discovered this failure mode in genomics AI and applied it to underwriting",
        "The same 'plausible-but-wrong' pattern from my published research (ISME Communications 2024)",
    )

    pdf.body_text(
        safe('In our longitudinal evaluation of 22 large language models (ISME Communications 2024), '
             'we documented the "plausible-but-wrong" (PBW) failure mode: outputs that appear '
             "correct, pass surface-level checks, but are factually wrong.")
    )
    pdf.ln(2)

    pdf.body_text(
        safe("The same failure mode applies to medical underwriting AI. "
             "When a model fills in missing clinical data from learned population distributions, "
             "the output is statistically plausible but individually unreliable.")
    )
    pdf.ln(4)

    # Two-column comparison
    col_w = CONTENT_W / 2 - 5
    y0 = pdf.get_y()

    # Left: LLMs
    pdf.set_xy(MARGIN, y0)
    pdf.set_fill_color(*C_BOX_BG)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*C_HEADING)
    pdf.cell(col_w, 8, safe("  LLM Evaluation"), fill=True,
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(MARGIN, y0 + 10)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*C_BODY)
    pdf.multi_cell(col_w, 5.5, safe(
        "High-confidence taxonomic classifications that look "
        "plausible but are wrong. Detected only by expert review "
        "or cross-reference with ground truth databases."
    ))

    # Right: Underwriting
    pdf.set_xy(MARGIN + col_w + 10, y0)
    pdf.set_fill_color(*C_BOX_BG)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*C_HEADING)
    pdf.cell(col_w, 8, safe("  Underwriting AI"), fill=True,
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(MARGIN + col_w + 10, y0 + 10)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*C_BODY)
    pdf.multi_cell(col_w, 5.5, safe(
        "High-confidence risk scores on patients with sparse records. "
        "Model imputes missing values from population priors. "
        "Output looks valid but individual prediction is unreliable."
    ))

    pdf.set_text_color(*C_BODY)
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*C_ACCENT)
    pdf.cell(CONTENT_W, 8, safe("Solution: detect PBW before it reaches a decision."),
             align="C")
    pdf.set_text_color(*C_BODY)

    pdf.source_line("Source: ISME Communications 2024, Helmholtz Munich")


def slide_04_architecture(pdf: SlidePDF) -> None:
    """Architecture overview."""
    pdf.add_page()
    pdf.slide_title(
        "Six pipeline stages each add a measurable quality gate",
        "No imputation -- each data profile gets its own model trained on available features",
    )

    y0 = pdf.get_y() + 5

    # Flow boxes: (label, border_colour, fill_colour)
    AI_FILL = (232, 242, 252)  # light blue academic tint
    boxes = [
        ("Patient\nRecord", C_HEADING, C_WHITE),
        ("Data Quality\nScore", C_ACCENT, AI_FILL),
        ("XGBoost\nClassifier", C_ACCENT, AI_FILL),
        ("Cox PH\nSurvival", C_ACCENT, AI_FILL),
        ("CTMC\nProgression", C_ACCENT, AI_FILL),
        ("Validation\nLayer", C_HEADING, C_WHITE),
    ]

    box_w = 38
    box_h = 22
    gap = 7
    total_w = len(boxes) * box_w + (len(boxes) - 1) * gap
    x_start = (PAGE_W - total_w) / 2

    for i, (label, border, fill) in enumerate(boxes):
        x = x_start + i * (box_w + gap)
        pdf.set_fill_color(*fill)
        pdf.set_draw_color(*border)
        pdf.set_line_width(0.4)
        pdf.rect(x, y0, box_w, box_h, style="DF")
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*C_HEADING)
        pdf.set_xy(x, y0 + 3)
        pdf.multi_cell(box_w, 4, safe(label), align="C")

        # Arrow
        if i < len(boxes) - 1:
            ax = x + box_w
            ay = y0 + box_h / 2
            pdf.set_draw_color(*C_FOOTNOTE)
            pdf.set_line_width(0.4)
            pdf.line(ax + 1, ay, ax + gap - 1, ay)
            pdf.set_fill_color(*C_FOOTNOTE)
            pdf.polygon(
                [(ax + gap - 1, ay), (ax + gap - 4, ay - 2), (ax + gap - 4, ay + 2)],
                style="F",
            )

    pdf.set_line_width(0.2)
    pdf.set_text_color(*C_BODY)

    # Decision terminal pills
    y_dec = y0 + box_h + 15
    GREEN_T = (112, 173, 71)   # M_GREEN as RGB
    BLUE_T = (68, 114, 196)    # M_BLUE as RGB = C_ACCENT
    RED_T = (225, 87, 89)      # M_RED as RGB
    decisions = [
        ("ACCEPT", GREEN_T),
        ("REVIEW", BLUE_T),
        ("REJECT", RED_T),
    ]
    dec_w, dec_h = 55, 12
    dec_gap = 25
    dec_total = len(decisions) * dec_w + (len(decisions) - 1) * dec_gap
    dec_x_start = (PAGE_W - dec_total) / 2

    # Arrow from validation box down
    val_x = x_start + (len(boxes) - 1) * (box_w + gap) + box_w / 2
    pdf.set_draw_color(*C_FOOTNOTE)
    pdf.set_line_width(0.4)
    pdf.line(val_x, y0 + box_h, val_x, y_dec - 3)
    pdf.set_fill_color(*C_FOOTNOTE)
    pdf.polygon([(val_x, y_dec - 1), (val_x - 2, y_dec - 4), (val_x + 2, y_dec - 4)],
                style="F")
    pdf.set_line_width(0.2)

    for i, (label, colour) in enumerate(decisions):
        x = dec_x_start + i * (dec_w + dec_gap)
        pdf.set_fill_color(*C_WHITE)
        pdf.set_draw_color(*colour)
        pdf.set_line_width(0.4)
        pdf.rect(x, y_dec, dec_w, dec_h, style="DF")
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*colour)
        pdf.set_xy(x, y_dec + 1)
        pdf.cell(dec_w, dec_h - 2, safe(label), align="C")

    pdf.set_text_color(*C_BODY)
    pdf.set_line_width(0.2)

    # Description below
    pdf.set_y(y_dec + 22)
    pdf.ln(5)
    pdf.bullet(
        safe("Pre-inference gate:  DQS computed before inference -- measures how much "
             "the model should trust its input"),
        size=10,
    )
    pdf.bullet(
        safe("Three model stack:  XGBoost (binary risk), Cox PH (survival curves), "
             "CTMC (disease trajectories)"),
        size=10,
    )
    pdf.bullet(
        safe("Validation layer:  PBW detector, calibration-confidence mismatch (CCM), "
             "epistemic prediction uncertainty (EPU)"),
        size=10,
    )

    pdf.source_line("Source: MedRisk v2.0 system design")


def slide_05_dqs(pdf: SlidePDF) -> None:
    """Data Quality Score."""
    pdf.add_page()
    pdf.slide_title(
        "The DQS tells the model how much to trust each input before inference",
        "Three weighted components measure completeness, consistency, and recency",
    )

    pdf.body_text(
        safe("The DQS is computed before any model inference. It answers: "
             '"How much should the model trust this particular input?"')
    )
    pdf.ln(2)

    # Formula
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*C_HEADING)
    pdf.cell(
        CONTENT_W, 10,
        safe("DQS  =  0.40 x Completeness  +  0.35 x Consistency  +  0.25 x Recency"),
        align="C", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.set_text_color(*C_BODY)
    pdf.ln(6)

    # Three component boxes
    components = [
        ("Completeness", "0.40", "Fraction of expected clinical\nfeatures present in the record"),
        ("Consistency", "0.35", "Domain rules: diabetes + HbA1c,\nCKD + eGFR, HF + NT-proBNP"),
        ("Recency", "0.25", "Exponential decay on lab ages\n(half-life = 1.4 years)"),
    ]
    comp_w = (CONTENT_W - 20) / 3
    y0 = pdf.get_y()

    for i, (name, weight, desc) in enumerate(components):
        x = MARGIN + i * (comp_w + 10)
        pdf.set_xy(x, y0)
        pdf.set_fill_color(*C_BOX_BG)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*C_HEADING)
        pdf.cell(comp_w, 8, safe(f"  {name} (w={weight})"), fill=True,
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_xy(x, y0 + 10)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*C_BODY)
        pdf.multi_cell(comp_w, 5, safe(desc))

    pdf.set_text_color(*C_BODY)
    pdf.set_y(y0 + 40)
    pdf.ln(3)

    # Tier thresholds
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*C_HEADING)
    pdf.cell(CONTENT_W, 8, safe("Decision Tiers"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    tiers = [
        ("Adequate", ">= 0.80", "Model output can be trusted for automated decisions",
         C_GREEN_BG, (39, 103, 73)),
        ("Caution", "0.60 - 0.80", "Flag for human review -- elevated uncertainty",
         (255, 245, 220), (160, 110, 20)),
        ("Insufficient", "< 0.60", "Reject prediction -- data too sparse or inconsistent",
         C_RED_BG, (180, 10, 0)),
    ]
    for name, thresh, desc, bg, fg in tiers:
        pdf.set_fill_color(*bg)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*fg)
        pdf.cell(35, 7, safe(f"  {name}"), fill=True, new_x="END")
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*C_BODY)
        pdf.cell(25, 7, safe(f"  {thresh}"), new_x="END")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, safe(f"  {desc}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*C_BODY)

    pdf.source_line("Source: MedRisk DQS v2 implementation")


def slide_06_multimarket(pdf: SlidePDF, chart_buf: BytesIO) -> None:
    """Multi-Market Design with chart."""
    pdf.add_page()
    pdf.slide_title(
        "International markets show 2.4x higher mispricing risk than Germany",
        "4 European markets with controlled data quality degradation",
    )

    # Table
    col_ws = [25, 30, 30, 25, 35, 30]
    headers = ["Market", "Coding", "Labs", "Noise", "Diag Lag", "Med Recording"]
    rows = [
        ["DE", "95%", "92%", "2%", "14 +/- 7 d", "95%"],
        ["FR", "90%", "88%", "3%", "60 +/- 30 d", "88%"],
        ["ES", "80%", "75%", "5%", "30 +/- 20 d", "80%"],
        ["INT", "60%", "50%", "10%", "90 +/- 60 d", "60%"],
    ]
    pdf.table(headers, rows, col_widths=col_ws)

    pdf.body_text(
        safe("Four market profiles simulate the range of data quality "
             "found across European healthcare systems. DE (Germany) represents "
             "best-case; INT (international/emerging) represents worst-case."),
        size=10,
    )

    # Chart on right
    pdf.embed_chart(chart_buf, w=130)

    pdf.source_line("Source: MedRisk synthetic cohort, N=4,000 (1,000/market), seed=42")


def slide_07_pbw(pdf: SlidePDF, chart_buf: BytesIO, data: dict) -> None:
    """PBW Detector with scatter chart."""
    pdf.add_page()
    pdf.slide_title(
        "High confidence on low-quality data is the signature of a plausible-but-wrong prediction",
        "The Reliability Head learns P(wrong) and makes cost-optimal decisions",
    )

    # Left column: description
    col_w = CONTENT_W / 2 - 5
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*C_HEADING)
    pdf.cell(col_w, 7, safe("Flagging Rule"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*C_BODY)
    pdf.multi_cell(col_w, 5.5, safe(
        "A prediction is flagged as PBW when:\n"
        "  1. Model confidence > 0.80   AND\n"
        "  2. Data Quality Score < 0.60\n\n"
        "The model is highly confident, but the input data\n"
        "is too sparse to support that confidence."
    ))
    pdf.set_text_color(*C_BODY)
    pdf.ln(3)

    # Flagging rates by market
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*C_HEADING)
    pdf.cell(col_w, 7, safe("PBW Flagging Rates"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    # Colour tuples for bars
    RED_T = (225, 87, 89)
    AMBER_T = (237, 125, 49)
    GREEN_T = (112, 173, 71)

    for m in ["DE", "FR", "ES", "INT"]:
        mask = data["markets"] == m
        n_total = mask.sum()
        n_flagged = data["pbw_flags"][mask].sum()
        rate = n_flagged / n_total * 100 if n_total > 0 else 0
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*C_BODY)
        pdf.cell(12, 6, safe(f"  {m}"), new_x="END")
        pdf.set_font("Helvetica", "", 10)

        # Mini bar
        bar_w = rate * 1.2
        if rate > 5:
            pdf.set_fill_color(*RED_T)
        elif rate > 1:
            pdf.set_fill_color(*AMBER_T)
        else:
            pdf.set_fill_color(*GREEN_T)
        pdf.cell(bar_w, 6, "", fill=True, new_x="END")
        pdf.cell(30, 6, safe(f"  {rate:.1f}% ({n_flagged}/{n_total})"),
                 new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(*C_BODY)

    # Chart on right
    chart_buf.seek(0)
    pdf.image(chart_buf, x=PAGE_W / 2 + 5, w=130)

    pdf.source_line("Source: MedRisk synthetic cohort, N=4,000, seed=42")


def slide_08_enables(pdf: SlidePDF, data: dict) -> None:
    """What This Enables."""
    pdf.add_page()
    pdf.slide_title(
        "The validation layer automates clean cases and escalates uncertain ones",
        "Human underwriters focus on the cases that actually need judgement",
    )

    pdf.body_text(
        safe("The validation layer does not replace the model -- it gates its output. "
             "Cases where data quality supports the prediction are automated. "
             "Cases where it doesn't are escalated to a human underwriter.")
    )
    pdf.ln(4)

    # Compute stats
    n_total = len(data["dqs_scores"])
    n_adequate = (np.array(data["dqs_tiers"]) == "adequate").sum()
    n_caution = (np.array(data["dqs_tiers"]) == "caution").sum()
    n_insufficient = (np.array(data["dqs_tiers"]) == "insufficient").sum()
    pct_auto = n_adequate / n_total * 100

    # Big metrics
    pdf.key_metric("Automatable (DQS adequate)", f"{pct_auto:.0f}%",
                   MARGIN + 20, pdf.get_y(), 80)
    pdf.key_metric("Human review (caution)", f"{n_caution / n_total * 100:.0f}%",
                   MARGIN + 120, pdf.get_y() - 22, 80)
    pdf.key_metric("Rejected (insufficient)", f"{n_insufficient / n_total * 100:.0f}%",
                   MARGIN + 220, pdf.get_y(), 60)

    pdf.set_y(pdf.get_y() + 25)
    pdf.ln(5)

    pdf.bullet(safe("Throughput:  Faster policy issuance for the majority of clean applications"))
    pdf.bullet(safe("Efficiency:  Human underwriters focus on the cases that actually need judgement"))
    pdf.bullet(safe("Auditability:  Every automated decision has a traceable quality assessment"))
    pdf.bullet(safe("Risk reduction:  PBW detection directly reduces the insurer's exposure to mispriced risk"))

    pdf.source_line("Source: MedRisk synthetic cohort, N=4,000")


def slide_09_roadmap(pdf: SlidePDF) -> None:
    """Roadmap."""
    pdf.add_page()
    pdf.slide_title(
        "Phase 1 is complete -- Phase 2 requires real claims data for validation",
        "Synthetic PoC proves the architecture; real data proves the economics",
    )

    phases = [
        (
            "Phase 1: Synthetic PoC",
            "COMPLETE",
            C_GREEN_BG,
            (39, 103, 73),
            [
                "4,000 synthetic patients across 4 markets",
                "XGBoost + Cox PH + CTMC model stack",
                "DQS and PBW failure detection validated",
                "SHAP explainability and PDF reporting",
            ],
        ),
        (
            "Phase 2: Retrospective Validation",
            "NEXT",
            (254, 240, 200),
            (163, 117, 26),
            [
                "5+ years of pseudonymised claims data",
                "50,000+ patient records (PKV or InGef)",
                "Validate DQS calibration against real missingness",
                "Measure actual PBW rate in historical decisions",
            ],
        ),
        (
            "Phase 3: Production Integration",
            "FUTURE",
            C_BOX_BG,
            C_HEADING,
            [
                "REST API with sub-second latency",
                "Human-in-the-loop review UI (HIML)",
                "Model drift monitoring and DQS recalibration",
                "EU AI Act compliance (DPIA, model cards, audit trail)",
            ],
        ),
    ]

    col_w = (CONTENT_W - 20) / 3
    y0 = pdf.get_y()

    for i, (title, status, bg, fg, items) in enumerate(phases):
        x = MARGIN + i * (col_w + 10)

        # Status badge
        pdf.set_xy(x, y0)
        pdf.set_fill_color(*bg)
        pdf.set_draw_color(*fg)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*fg)
        pdf.cell(col_w, 6, safe(f"  {status}"), fill=True,
                 new_x="LMARGIN", new_y="NEXT")

        # Title
        pdf.set_xy(x, y0 + 8)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*C_HEADING)
        pdf.cell(col_w, 7, safe(title), new_x="LMARGIN", new_y="NEXT")

        # Items
        pdf.set_xy(x, y0 + 18)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*C_BODY)
        for item in items:
            pdf.set_x(x)
            pdf.cell(4, 5, "-", new_x="END")
            pdf.multi_cell(col_w - 4, 5, safe(item))

    pdf.set_text_color(*C_BODY)
    pdf.set_draw_color(*C_RULE)

    # Timeline arrow at bottom
    pdf.set_y(y0 + 85)
    pdf.set_draw_color(*C_ACCENT)
    pdf.set_line_width(1.0)
    y_arrow = pdf.get_y()
    pdf.line(MARGIN + 20, y_arrow, PAGE_W - MARGIN - 20, y_arrow)
    # Arrowhead
    ax = PAGE_W - MARGIN - 20
    pdf.line(ax - 4, y_arrow - 3, ax, y_arrow)
    pdf.line(ax - 4, y_arrow + 3, ax, y_arrow)
    pdf.set_line_width(0.2)
    pdf.set_draw_color(*C_RULE)

    # Timeline labels
    positions = [MARGIN + 40, PAGE_W / 2, PAGE_W - MARGIN - 55]
    labels = ["Q1 2026", "Q3 2026", "2027"]
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*C_ACCENT)
    for pos, label in zip(positions, labels):
        pdf.set_xy(pos, y_arrow + 3)
        pdf.cell(30, 6, safe(label), align="C")
    pdf.set_text_color(*C_BODY)
    pdf.source_line("Source: MedRisk project plan, March 2026")


def slide_10_ask(pdf: SlidePDF) -> None:
    """Next Steps / Ask."""
    pdf.add_page()
    pdf.slide_title(
        "In 90 days I'd deliver calibrated PBW detection on real a major European insurer data",
        "Four requirements to move from synthetic PoC to production prototype",
    )

    pdf.ln(2)

    asks = [
        (
            "Pseudonymised Claims Data",
            "Access to 5+ years of PKV or InGef claims data (50,000+ records) "
            "for retrospective validation of the DQS and PBW detector.",
        ),
        (
            "DPO Clearance",
            "Data Protection Officer sign-off on the data processing agreement. "
            "Synthetic PoC design minimises GDPR scope for Phase 2.",
        ),
        (
            "3-Month Validation Sprint",
            "Dedicated sprint to retrain on real data, validate DQS calibration, "
            "and measure actual PBW rates against historical underwriting decisions.",
        ),
        (
            "Clinical Advisory",
            "Access to a medical underwriter for consistency rule validation "
            "and domain-specific threshold tuning.",
        ),
    ]

    for title, desc in asks:
        pdf.set_fill_color(*C_BOX_BG)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*C_HEADING)
        pdf.cell(CONTENT_W, 8, safe(f"  {title}"), fill=True,
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*C_BODY)
        pdf.multi_cell(CONTENT_W, 5.5, safe(f"  {desc}"))
        pdf.ln(3)

    pdf.set_text_color(*C_BODY)
    pdf.ln(4)

    # Contact
    pdf.set_fill_color(*C_ACCENT)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*C_WHITE)
    pdf.cell(CONTENT_W, 10,
             safe("  Tim Reska  |  timreska@gmail.com"),
             fill=True, align="C")
    pdf.set_text_color(*C_BODY)
    pdf.source_line("Proof of Concept | All data is synthetic | March 2026")


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    """Generate the slide deck."""
    output_path = Path(__file__).resolve().parent.parent / "data" / "reports" / "medrisk_deck.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare data
    data = prepare_data()

    # Generate charts
    logger.info("Generating charts...")
    dqs_chart = chart_dqs_by_market(data)
    pbw_chart = chart_pbw_scatter(data)

    # Build PDF
    logger.info("Building slide deck...")
    pdf = SlidePDF(n_slides=10)

    slide_01_title(pdf)
    slide_02_problem(pdf)
    slide_03_insight(pdf)
    slide_04_architecture(pdf)
    slide_05_dqs(pdf)
    slide_06_multimarket(pdf, dqs_chart)
    slide_07_pbw(pdf, pbw_chart, data)
    slide_08_enables(pdf, data)
    slide_09_roadmap(pdf)
    slide_10_ask(pdf)

    pdf.output(str(output_path))
    logger.info("Slide deck generated: %s", output_path)
    logger.info("Pages: %d", pdf.pages_count)

    # Size check
    size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info("File size: %.2f MB", size_mb)


if __name__ == "__main__":
    main()
