#!/usr/bin/env python3
"""Generate MedRisk-ADH pitch deck as PDF.

Produces a 10-slide landscape PDF using fpdf2 with live charts generated
from actual synthetic data via matplotlib.

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
from fpdf import FPDF
from sklearn.model_selection import train_test_split

from medrisk.data.schemas import MARKET_CONFIGS
from medrisk.data.synthetic import generate_cohort, cohort_to_dataframe
from medrisk.features.engineering import build_feature_matrix, get_targets
from medrisk.models.xgb_classifier import RiskClassifier
from medrisk.validation.data_quality import compute_dqs

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# --- Layout constants ---
PAGE_W = 297  # landscape A4 width mm
PAGE_H = 210  # landscape A4 height mm
MARGIN = 15
CONTENT_W = PAGE_W - 2 * MARGIN

# --- Colour palette ---
DARK_BLUE = (26, 54, 93)       # #1a365d
ACCENT_BLUE = (43, 108, 176)   # #2b6cb0
LIGHT_BLUE = (235, 242, 250)   # #ebf2fa
PBW_RED = (252, 129, 129)      # #fc8181
PBW_RED_LIGHT = (254, 215, 215)  # #fed7d7
GREEN = (104, 211, 145)        # #68d391
GREEN_LIGHT = (198, 246, 213)  # #c6f6d5
GREY_TEXT = (60, 60, 60)
WHITE = (255, 255, 255)
BLACK = (30, 30, 30)


class SlideDeck(FPDF):
    """Landscape A4 slide deck."""

    def __init__(self) -> None:
        super().__init__(orientation="L", unit="mm", format="A4")
        self.set_auto_page_break(auto=False)
        self.set_margins(MARGIN, MARGIN, MARGIN)

    def header(self) -> None:
        """Thin top bar with project name."""
        if self.page_no() == 1:
            return  # title slide has its own layout
        self.set_fill_color(*DARK_BLUE)
        self.rect(0, 0, PAGE_W, 8, "F")
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*WHITE)
        self.set_xy(MARGIN, 1)
        self.cell(0, 6, "MedRisk-ADH", new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*BLACK)
        self.ln(4)

    def footer(self) -> None:
        """Page number in bottom-right."""
        self.set_y(-10)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(140, 140, 140)
        self.cell(0, 5, f"{self.page_no()} / 10", align="R")
        self.set_text_color(*BLACK)

    # --- Reusable slide elements ---

    def slide_title(self, title: str, subtitle: str = "") -> None:
        """Slide heading block."""
        self.set_font("Helvetica", "B", 24)
        self.set_text_color(*DARK_BLUE)
        self.cell(CONTENT_W, 14, title, new_x="LMARGIN", new_y="NEXT")
        if subtitle:
            self.set_font("Helvetica", "", 12)
            self.set_text_color(*ACCENT_BLUE)
            self.cell(CONTENT_W, 8, subtitle, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*BLACK)
        self.ln(3)
        # accent line
        self.set_draw_color(*ACCENT_BLUE)
        self.set_line_width(0.6)
        y = self.get_y()
        self.line(MARGIN, y, MARGIN + 60, y)
        self.set_line_width(0.2)
        self.set_draw_color(0, 0, 0)
        self.ln(5)

    def body_text(self, text: str, size: int = 11) -> None:
        """Body paragraph."""
        self.set_font("Helvetica", "", size)
        self.set_text_color(*GREY_TEXT)
        self.multi_cell(CONTENT_W, 6, text)
        self.set_text_color(*BLACK)
        self.ln(2)

    def bullet(self, text: str, size: int = 11, bold_prefix: str = "") -> None:
        """Single bullet point."""
        x0 = self.get_x()
        self.set_font("Helvetica", "", size)
        self.set_text_color(*GREY_TEXT)
        self.cell(6, 6, "-", new_x="END")
        if bold_prefix:
            self.set_font("Helvetica", "B", size)
            self.cell(0, 6, bold_prefix + " ", new_x="END")
            self.set_font("Helvetica", "", size)
        self.multi_cell(CONTENT_W - 6 - (self.get_x() - x0 - 6), 6, text)
        self.set_text_color(*BLACK)

    def key_metric(self, label: str, value: str, x: float, y: float, w: float = 60) -> None:
        """Centred metric box."""
        self.set_xy(x, y)
        self.set_fill_color(*LIGHT_BLUE)
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(*DARK_BLUE)
        self.cell(w, 14, value, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_xy(x, y + 14)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*ACCENT_BLUE)
        self.cell(w, 6, label, align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*BLACK)

    def embed_chart(self, buf: BytesIO, x: float | None = None, w: float = 130) -> None:
        """Embed a matplotlib chart from a BytesIO buffer."""
        buf.seek(0)
        if x is not None:
            self.image(buf, x=x, w=w)
        else:
            self.image(buf, w=w)


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

def _chart_style() -> None:
    """Apply clean chart style."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "figure.facecolor": "white",
    })


def chart_dqs_by_market(data: dict) -> BytesIO:
    """Box plot of DQS distribution by market."""
    _chart_style()
    fig, ax = plt.subplots(figsize=(6, 3.5), dpi=150)

    market_order = ["DE", "FR", "ES", "INT"]
    market_colors = {
        "DE": "#2b6cb0", "FR": "#4299e1", "ES": "#ed8936", "INT": "#e53e3e",
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
    ax.axhline(0.80, color="#38a169", linestyle="--", linewidth=1, label="Adequate (0.80)")
    ax.axhline(0.60, color="#dd6b20", linestyle="--", linewidth=1, label="Caution (0.60)")
    ax.set_ylabel("Data Quality Score")
    ax.set_title("DQS Distribution by Market", fontweight="bold", fontsize=12)
    ax.legend(fontsize=8, loc="lower left")
    ax.set_ylim(0, 1.05)

    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_pbw_scatter(data: dict) -> BytesIO:
    """Confidence vs DQS scatter with PBW zone."""
    _chart_style()
    fig, ax = plt.subplots(figsize=(6, 4), dpi=150)

    conf = data["confidence"]
    dqs = data["dqs_scores"]
    pbw = data["pbw_flags"]

    # PBW danger zone
    ax.axhspan(0.80, 1.02, xmin=0, xmax=0.60 / 1.02, color="#fed7d7", alpha=0.5, zorder=0)
    ax.fill_between(
        [0, 0.60], [0.80, 0.80], [1.02, 1.02],
        color="#fed7d7", alpha=0.5, zorder=0,
    )
    ax.text(
        0.15, 0.90, "PBW\nDanger Zone",
        fontsize=11, fontweight="bold", color="#c53030",
        ha="center", va="center", alpha=0.8,
    )

    # Non-flagged points
    ax.scatter(
        dqs[~pbw], conf[~pbw],
        s=4, alpha=0.25, c="#2b6cb0", label="Normal", rasterized=True,
    )
    # Flagged points
    ax.scatter(
        dqs[pbw], conf[pbw],
        s=12, alpha=0.6, c="#e53e3e", label="PBW flagged", rasterized=True,
    )

    # Threshold lines
    ax.axhline(0.80, color="#718096", linestyle=":", linewidth=0.8)
    ax.axvline(0.60, color="#718096", linestyle=":", linewidth=0.8)

    ax.set_xlabel("Data Quality Score")
    ax.set_ylabel("Model Confidence (P(high risk))")
    ax.set_title("Plausible-but-Wrong Detection", fontweight="bold", fontsize=12)
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

def slide_01_title(pdf: SlideDeck) -> None:
    """Title slide."""
    pdf.add_page()
    # Full dark blue background band
    pdf.set_fill_color(*DARK_BLUE)
    pdf.rect(0, 0, PAGE_W, PAGE_H, "F")

    # White text centred
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_y(55)
    pdf.cell(CONTENT_W, 18, "MedRisk-ADH", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(180, 210, 245)
    pdf.cell(CONTENT_W, 10, "AI-Augmented Medical Underwriting", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(CONTENT_W, 10, "with Failure Mode Detection", align="C", new_x="LMARGIN", new_y="NEXT")

    # Accent line
    pdf.ln(6)
    y = pdf.get_y()
    pdf.set_draw_color(*ACCENT_BLUE)
    pdf.set_line_width(1.0)
    mid = PAGE_W / 2
    pdf.line(mid - 40, y, mid + 40, y)
    pdf.set_line_width(0.2)
    pdf.ln(10)

    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(*WHITE)
    pdf.cell(CONTENT_W, 8, "Tim Reska  |  Helmholtz Munich", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(160, 190, 230)
    pdf.cell(CONTENT_W, 8, "Proof of Concept  |  Synthetic Data  |  March 2026", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(*BLACK)
    pdf.set_draw_color(0, 0, 0)


def slide_02_problem(pdf: SlideDeck) -> None:
    """The Problem."""
    pdf.add_page()
    pdf.slide_title("The Problem", "Confident-but-wrong decisions at scale")

    pdf.body_text(
        "Current AI underwriting models produce a risk score for every applicant. "
        "But they cannot distinguish between a confident prediction backed by rich "
        "clinical data and one that looks equally confident on sparse, incomplete records."
    )
    pdf.ln(3)

    pdf.bullet(
        "A model that is 95% confident on a patient with 40% missing data "
        "is running on learned priors, not evidence.",
        bold_prefix="The core failure:",
    )
    pdf.bullet(
        "These decisions look correct in aggregate metrics (AUC, accuracy) "
        "but carry hidden liability at the individual level.",
        bold_prefix="Why it matters:",
    )
    pdf.bullet(
        "At scale, even a 2% plausible-but-wrong rate across 100,000 policies "
        "means 2,000 incorrectly assessed risks per year.",
        bold_prefix="The scale:",
    )

    pdf.ln(8)

    # Three metric boxes
    pdf.key_metric("Wrong decisions / year", "2,000+", MARGIN + 10, 130, 75)
    pdf.key_metric("Undetected by AUC", "Yes", MARGIN + 105, 130, 75)
    pdf.key_metric("Current mitigation", "None", MARGIN + 200, 130, 75)


def slide_03_insight(pdf: SlideDeck) -> None:
    """The Insight."""
    pdf.add_page()
    pdf.slide_title("The Insight", "A failure mode we have seen before")

    pdf.body_text(
        'In our longitudinal evaluation of 22 large language models (ISME Communications 2024), '
        'we documented the "plausible-but-wrong" (PBW) failure mode: outputs that appear '
        "correct, pass surface-level checks, but are factually wrong."
    )
    pdf.ln(2)

    pdf.body_text(
        "The same failure mode applies to medical underwriting AI. "
        "When a model fills in missing clinical data from learned population distributions, "
        "the output is statistically plausible but individually unreliable."
    )
    pdf.ln(4)

    # Two-column comparison
    col_w = CONTENT_W / 2 - 5
    y0 = pdf.get_y()

    # Left: LLMs
    pdf.set_xy(MARGIN, y0)
    pdf.set_fill_color(*LIGHT_BLUE)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(col_w, 8, "  LLM Evaluation", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(MARGIN, y0 + 10)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GREY_TEXT)
    pdf.multi_cell(col_w, 5.5, (
        "High-confidence taxonomic classifications that look "
        "plausible but are wrong. Detected only by expert review "
        "or cross-reference with ground truth databases."
    ))

    # Right: Underwriting
    pdf.set_xy(MARGIN + col_w + 10, y0)
    pdf.set_fill_color(*LIGHT_BLUE)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(col_w, 8, "  Underwriting AI", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(MARGIN + col_w + 10, y0 + 10)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GREY_TEXT)
    pdf.multi_cell(col_w, 5.5, (
        "High-confidence risk scores on patients with sparse records. "
        "Model imputes missing values from population priors. "
        "Output looks valid but individual prediction is unreliable."
    ))

    pdf.set_text_color(*BLACK)
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*ACCENT_BLUE)
    pdf.cell(CONTENT_W, 8, "Solution: detect PBW before it reaches a decision.", align="C")
    pdf.set_text_color(*BLACK)


def slide_04_architecture(pdf: SlideDeck) -> None:
    """Architecture overview."""
    pdf.add_page()
    pdf.slide_title("Architecture", "End-to-end pipeline with validation gate")

    y0 = pdf.get_y() + 5

    # Flow boxes
    boxes = [
        ("Patient\nRecord", LIGHT_BLUE, DARK_BLUE),
        ("Data Quality\nScore (DQS)", (198, 246, 213), (39, 103, 73)),
        ("XGBoost\nRisk Classifier", LIGHT_BLUE, DARK_BLUE),
        ("Cox PH\nSurvival", LIGHT_BLUE, DARK_BLUE),
        ("CTMC\nProgression", LIGHT_BLUE, DARK_BLUE),
        ("Validation\nLayer", (254, 215, 215), (155, 44, 44)),
    ]

    box_w = 38
    box_h = 22
    gap = 7
    total_w = len(boxes) * box_w + (len(boxes) - 1) * gap
    x_start = (PAGE_W - total_w) / 2

    for i, (label, bg, fg) in enumerate(boxes):
        x = x_start + i * (box_w + gap)
        pdf.set_fill_color(*bg)
        pdf.set_draw_color(*fg)
        pdf.rect(x, y0, box_w, box_h, "DF")
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*fg)
        pdf.set_xy(x, y0 + 3)
        pdf.multi_cell(box_w, 4, label, align="C")

        # Arrow
        if i < len(boxes) - 1:
            ax = x + box_w
            ay = y0 + box_h / 2
            pdf.set_draw_color(*ACCENT_BLUE)
            pdf.set_line_width(0.5)
            pdf.line(ax + 1, ay, ax + gap - 1, ay)
            # Arrowhead
            pdf.line(ax + gap - 3, ay - 2, ax + gap - 1, ay)
            pdf.line(ax + gap - 3, ay + 2, ax + gap - 1, ay)

    pdf.set_line_width(0.2)
    pdf.set_draw_color(0, 0, 0)
    pdf.set_text_color(*BLACK)

    # Decision outputs
    y_dec = y0 + box_h + 15
    decisions = [
        ("ACCEPT", (39, 103, 73), GREEN_LIGHT),
        ("REVIEW", (163, 117, 26), (254, 240, 200)),
        ("REJECT", (155, 44, 44), (254, 215, 215)),
    ]
    dec_w = 55
    dec_gap = 25
    dec_total = len(decisions) * dec_w + (len(decisions) - 1) * dec_gap
    dec_x_start = (PAGE_W - dec_total) / 2

    # Arrow from validation box down
    val_x = x_start + (len(boxes) - 1) * (box_w + gap) + box_w / 2
    pdf.set_draw_color(*ACCENT_BLUE)
    pdf.set_line_width(0.5)
    pdf.line(val_x, y0 + box_h, val_x, y_dec - 3)
    pdf.set_line_width(0.2)

    for i, (label, fg, bg) in enumerate(decisions):
        x = dec_x_start + i * (dec_w + dec_gap)
        pdf.set_fill_color(*bg)
        pdf.set_draw_color(*fg)
        pdf.rect(x, y_dec, dec_w, 12, "DF")
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*fg)
        pdf.set_xy(x, y_dec + 2)
        pdf.cell(dec_w, 8, label, align="C")

    pdf.set_text_color(*BLACK)
    pdf.set_draw_color(0, 0, 0)

    # Description below
    pdf.set_y(y_dec + 22)
    pdf.ln(5)
    pdf.bullet(
        "DQS computed before inference -- measures how much the model should trust its input",
        size=10, bold_prefix="Pre-inference gate:",
    )
    pdf.bullet(
        "XGBoost (binary risk), Cox PH (survival curves), CTMC (disease trajectories)",
        size=10, bold_prefix="Three model stack:",
    )
    pdf.bullet(
        "PBW detector, calibration-confidence mismatch (CCM), epistemic prediction uncertainty (EPU)",
        size=10, bold_prefix="Validation layer:",
    )


def slide_05_dqs(pdf: SlideDeck) -> None:
    """Data Quality Score."""
    pdf.add_page()
    pdf.slide_title("Data Quality Score", "Per-patient input quality assessment")

    pdf.body_text(
        "The DQS is computed before any model inference. It answers: "
        '"How much should the model trust this particular input?"'
    )
    pdf.ln(2)

    # Formula
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(
        CONTENT_W, 10,
        "DQS  =  0.40 x Completeness  +  0.35 x Consistency  +  0.25 x Recency",
        align="C", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.set_text_color(*BLACK)
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
        pdf.set_fill_color(*LIGHT_BLUE)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*DARK_BLUE)
        pdf.cell(comp_w, 8, f"  {name} (w={weight})", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_xy(x, y0 + 10)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*GREY_TEXT)
        pdf.multi_cell(comp_w, 5, desc)

    pdf.set_text_color(*BLACK)
    pdf.set_y(y0 + 40)
    pdf.ln(3)

    # Tier thresholds
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(CONTENT_W, 8, "Decision Tiers", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    tiers = [
        ("Adequate", ">= 0.80", "Model output can be trusted for automated decisions", GREEN_LIGHT, (39, 103, 73)),
        ("Caution", "0.60 - 0.80", "Flag for human review -- elevated uncertainty", (254, 240, 200), (163, 117, 26)),
        ("Insufficient", "< 0.60", "Reject prediction -- data too sparse or inconsistent", (254, 215, 215), (155, 44, 44)),
    ]
    for name, thresh, desc, bg, fg in tiers:
        pdf.set_fill_color(*bg)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*fg)
        pdf.cell(35, 7, f"  {name}", fill=True, new_x="END")
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*GREY_TEXT)
        pdf.cell(25, 7, f"  {thresh}", new_x="END")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, f"  {desc}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*BLACK)


def slide_06_multimarket(pdf: SlideDeck, chart_buf: BytesIO) -> None:
    """Multi-Market Design with chart."""
    pdf.add_page()
    pdf.slide_title("Multi-Market Design", "Controlled data quality variance across healthcare systems")

    # Table
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(*DARK_BLUE)
    pdf.set_text_color(*WHITE)
    col_ws = [25, 30, 30, 25, 35, 30]
    headers = ["Market", "Coding", "Labs", "Noise", "Diag Lag", "Med Recording"]
    for w, h in zip(col_ws, headers):
        pdf.cell(w, 7, f"  {h}", fill=True, new_x="END")
    pdf.ln()

    rows = [
        ("DE", "95%", "92%", "2%", "14 +/- 7 d", "95%"),
        ("FR", "90%", "88%", "3%", "60 +/- 30 d", "88%"),
        ("ES", "80%", "75%", "5%", "30 +/- 20 d", "80%"),
        ("INT", "60%", "50%", "10%", "90 +/- 60 d", "60%"),
    ]
    pdf.set_text_color(*BLACK)
    for i, row in enumerate(rows):
        bg = LIGHT_BLUE if i % 2 == 0 else WHITE
        pdf.set_fill_color(*bg)
        pdf.set_font("Helvetica", "B" if row[0] in ("DE", "INT") else "", 9)
        for w, val in zip(col_ws, row):
            pdf.cell(w, 6, f"  {val}", fill=True, new_x="END")
        pdf.ln()

    pdf.ln(4)
    pdf.body_text(
        "Four market profiles simulate the range of data quality "
        "found across European healthcare systems. DE (Germany) represents "
        "best-case; INT (international/emerging) represents worst-case.",
        size=10,
    )

    # Chart on right
    pdf.embed_chart(chart_buf, x=PAGE_W / 2 + 5, w=130)


def slide_07_pbw(pdf: SlideDeck, chart_buf: BytesIO, data: dict) -> None:
    """PBW Detector with scatter chart."""
    pdf.add_page()
    pdf.slide_title("The PBW Detector", "Catching plausible-but-wrong predictions")

    # Left column: description
    col_w = CONTENT_W / 2 - 5
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(col_w, 7, "Flagging Rule", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GREY_TEXT)
    pdf.multi_cell(col_w, 5.5, (
        "A prediction is flagged as PBW when:\n"
        "  1. Model confidence > 0.80   AND\n"
        "  2. Data Quality Score < 0.60\n\n"
        "The model is highly confident, but the input data\n"
        "is too sparse to support that confidence."
    ))
    pdf.set_text_color(*BLACK)
    pdf.ln(3)

    # Flagging rates by market
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(col_w, 7, "PBW Flagging Rates", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    for m in ["DE", "FR", "ES", "INT"]:
        mask = data["markets"] == m
        n_total = mask.sum()
        n_flagged = data["pbw_flags"][mask].sum()
        rate = n_flagged / n_total * 100 if n_total > 0 else 0
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*GREY_TEXT)
        pdf.cell(12, 6, f"  {m}", new_x="END")
        pdf.set_font("Helvetica", "", 10)

        # Mini bar
        bar_w = rate * 1.2
        if rate > 5:
            pdf.set_fill_color(*PBW_RED)
        elif rate > 1:
            pdf.set_fill_color(237, 137, 54)  # orange
        else:
            pdf.set_fill_color(*GREEN)
        pdf.cell(bar_w, 6, "", fill=True, new_x="END")
        pdf.cell(30, 6, f"  {rate:.1f}% ({n_flagged}/{n_total})", new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(*BLACK)

    # Chart on right
    pdf.embed_chart(chart_buf, x=PAGE_W / 2 + 5, w=130)


def slide_08_enables(pdf: SlideDeck, data: dict) -> None:
    """What This Enables."""
    pdf.add_page()
    pdf.slide_title("What This Enables", "Automated underwriting with a safety net")

    pdf.body_text(
        "The validation layer does not replace the model -- it gates its output. "
        "Cases where data quality supports the prediction are automated. "
        "Cases where it doesn't are escalated to a human underwriter."
    )
    pdf.ln(4)

    # Compute stats
    n_total = len(data["dqs_scores"])
    n_adequate = (np.array(data["dqs_tiers"]) == "adequate").sum()
    n_caution = (np.array(data["dqs_tiers"]) == "caution").sum()
    n_insufficient = (np.array(data["dqs_tiers"]) == "insufficient").sum()
    pct_auto = n_adequate / n_total * 100

    # Big metric
    pdf.key_metric("Automatable (DQS adequate)", f"{pct_auto:.0f}%", MARGIN + 20, pdf.get_y(), 80)
    pdf.key_metric("Human review (caution)", f"{n_caution / n_total * 100:.0f}%", MARGIN + 120, pdf.get_y() - 20, 80)
    pdf.key_metric("Rejected (insufficient)", f"{n_insufficient / n_total * 100:.0f}%", MARGIN + 220, pdf.get_y() - 20, 60)

    pdf.set_y(pdf.get_y() + 25)
    pdf.ln(5)

    pdf.bullet(
        "Faster policy issuance for the majority of clean applications",
        bold_prefix="Throughput:",
    )
    pdf.bullet(
        "Human underwriters focus on the cases that actually need judgement",
        bold_prefix="Efficiency:",
    )
    pdf.bullet(
        "Every automated decision has a traceable quality assessment",
        bold_prefix="Auditability:",
    )
    pdf.bullet(
        "PBW detection directly reduces the insurer's exposure to mispriced risk",
        bold_prefix="Risk reduction:",
    )


def slide_09_roadmap(pdf: SlideDeck) -> None:
    """Roadmap."""
    pdf.add_page()
    pdf.slide_title("Roadmap", "From proof of concept to production")

    phases = [
        (
            "Phase 1: Synthetic PoC",
            "COMPLETE",
            GREEN_LIGHT,
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
            LIGHT_BLUE,
            DARK_BLUE,
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
        pdf.cell(col_w, 6, f"  {status}", fill=True, new_x="LMARGIN", new_y="NEXT")

        # Title
        pdf.set_xy(x, y0 + 8)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*DARK_BLUE)
        pdf.cell(col_w, 7, title, new_x="LMARGIN", new_y="NEXT")

        # Items
        pdf.set_xy(x, y0 + 18)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*GREY_TEXT)
        for item in items:
            pdf.set_x(x)
            pdf.cell(4, 5, "-", new_x="END")
            pdf.multi_cell(col_w - 4, 5, item)

    pdf.set_text_color(*BLACK)
    pdf.set_draw_color(0, 0, 0)

    # Timeline arrow at bottom
    pdf.set_y(y0 + 85)
    pdf.set_draw_color(*ACCENT_BLUE)
    pdf.set_line_width(1.0)
    y_arrow = pdf.get_y()
    pdf.line(MARGIN + 20, y_arrow, PAGE_W - MARGIN - 20, y_arrow)
    # Arrowhead
    ax = PAGE_W - MARGIN - 20
    pdf.line(ax - 4, y_arrow - 3, ax, y_arrow)
    pdf.line(ax - 4, y_arrow + 3, ax, y_arrow)
    pdf.set_line_width(0.2)
    pdf.set_draw_color(0, 0, 0)

    # Timeline labels
    positions = [MARGIN + 40, PAGE_W / 2, PAGE_W - MARGIN - 55]
    labels = ["Q1 2026", "Q3 2026", "2027"]
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*ACCENT_BLUE)
    for pos, label in zip(positions, labels):
        pdf.set_xy(pos, y_arrow + 3)
        pdf.cell(30, 6, label, align="C")
    pdf.set_text_color(*BLACK)


def slide_10_ask(pdf: SlideDeck) -> None:
    """Next Steps / Ask."""
    pdf.add_page()
    pdf.slide_title("Next Steps", "What we need to move to Phase 2")

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
        pdf.set_fill_color(*LIGHT_BLUE)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*DARK_BLUE)
        pdf.cell(CONTENT_W, 8, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*GREY_TEXT)
        pdf.multi_cell(CONTENT_W, 5.5, f"  {desc}")
        pdf.ln(3)

    pdf.set_text_color(*BLACK)
    pdf.ln(4)

    # Contact
    pdf.set_fill_color(*DARK_BLUE)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*WHITE)
    pdf.cell(CONTENT_W, 10, "  Tim Reska  |  Helmholtz Munich  |  tim.reska@helmholtz-munich.de", fill=True, align="C")
    pdf.set_text_color(*BLACK)


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    """Generate the slide deck."""
    output_path = Path(__file__).resolve().parent.parent / "data" / "reports" / "medrisk_adh_deck.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare data
    data = prepare_data()

    # Generate charts
    logger.info("Generating charts...")
    dqs_chart = chart_dqs_by_market(data)
    pbw_chart = chart_pbw_scatter(data)

    # Build PDF
    logger.info("Building slide deck...")
    pdf = SlideDeck()

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
