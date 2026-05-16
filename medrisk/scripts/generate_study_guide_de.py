#!/usr/bin/env python3
"""Deutscher KTG-Hypertonie Study Guide — PDF mit reportlab + LaTeX-Formeln.

Erzeugt einen ~20-25-seitigen Study Guide (Portrait A4) mit Fokus auf
Krankentagegeld-Kalkulation am Beispiel Hypertonie (I10).

Reportlab + DejaVu Sans TTF für volle Unicode-Unterstützung (Umlaute).
Formeln via matplotlib → PNG.  Nature-style Formatierung.

Usage:
    python scripts/generate_study_guide_de.py
"""

from __future__ import annotations

import logging
import os
import sys
from io import BytesIO
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm, cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, NextPageTemplate, PageBreak, PageTemplate,
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

OUT = PROJECT_ROOT / "data" / "reports"
OUT.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Fonts — DejaVu Sans from matplotlib's bundled TTF
# ============================================================================

_MPL_FONTS = os.path.join(os.path.dirname(matplotlib.__file__),
                          "mpl-data", "fonts", "ttf")

pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(_MPL_FONTS, "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", os.path.join(_MPL_FONTS, "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Oblique", os.path.join(_MPL_FONTS, "DejaVuSans-Oblique.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-BoldOblique", os.path.join(_MPL_FONTS, "DejaVuSans-BoldOblique.ttf")))
pdfmetrics.registerFontFamily(
    "DejaVu", normal="DejaVu", bold="DejaVu-Bold",
    italic="DejaVu-Oblique", boldItalic="DejaVu-BoldOblique",
)

# ============================================================================
# Color palette (matching _academic_style.py)
# ============================================================================

C_HEADING = colors.HexColor("#1A1A1A")
C_BODY = colors.HexColor("#333333")
C_CAPTION = colors.HexColor("#555555")
C_FOOTNOTE = colors.HexColor("#888888")
C_ACCENT = colors.HexColor("#4472C4")
C_ACCENT2 = colors.HexColor("#107ACA")
C_TABLE_HDR = colors.HexColor("#E8E8E8")
C_TABLE_ALT = colors.HexColor("#FAFAFA")
C_BOX_BG = colors.HexColor("#F5F5F5")
C_RULE = colors.HexColor("#C8C8C8")
C_GREEN = colors.HexColor("#70AD47")
C_RED = colors.HexColor("#E15759")
C_WHITE = colors.white

# Matplotlib colors
M_BLUE, M_AMBER, M_GREEN, M_RED = "#4472C4", "#ED7D31", "#70AD47", "#E15759"
M_DARK, M_GREY, M_PURPLE = "#333333", "#888888", "#9467BD"

# ============================================================================
# Paragraph styles
# ============================================================================

def _build_styles() -> dict[str, ParagraphStyle]:
    """Build Nature-style paragraph styles."""
    return {
        "title": ParagraphStyle(
            "title", fontName="DejaVu-Bold", fontSize=22, leading=26,
            textColor=C_HEADING, alignment=TA_CENTER, spaceAfter=6,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontName="DejaVu", fontSize=12, leading=16,
            textColor=C_BODY, alignment=TA_CENTER, spaceAfter=4,
        ),
        "author": ParagraphStyle(
            "author", fontName="DejaVu", fontSize=10, leading=14,
            textColor=C_BODY, alignment=TA_CENTER, spaceAfter=2,
        ),
        "meta": ParagraphStyle(
            "meta", fontName="DejaVu-Oblique", fontSize=9, leading=12,
            textColor=C_FOOTNOTE, alignment=TA_CENTER, spaceAfter=4,
        ),
        "chapter": ParagraphStyle(
            "chapter", fontName="DejaVu-Bold", fontSize=15, leading=19,
            textColor=C_HEADING, spaceBefore=24, spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2", fontName="DejaVu-Bold", fontSize=11, leading=14,
            textColor=C_HEADING, spaceBefore=12, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body", fontName="DejaVu", fontSize=9.5, leading=14,
            textColor=C_BODY, alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "bullet", fontName="DejaVu", fontSize=9.5, leading=13,
            textColor=C_BODY, leftIndent=12, bulletIndent=0,
            spaceBefore=1, spaceAfter=1,
        ),
        "key_concept": ParagraphStyle(
            "key_concept", fontName="DejaVu-Bold", fontSize=9, leading=13,
            textColor=C_ACCENT, spaceBefore=0, spaceAfter=0,
        ),
        "key_concept_body": ParagraphStyle(
            "key_concept_body", fontName="DejaVu", fontSize=9, leading=13,
            textColor=C_BODY, spaceBefore=2, spaceAfter=0,
        ),
        "caption": ParagraphStyle(
            "caption", fontName="DejaVu-Oblique", fontSize=8, leading=11,
            textColor=C_CAPTION, alignment=TA_LEFT, spaceBefore=2,
            spaceAfter=8,
        ),
        "code_ref": ParagraphStyle(
            "code_ref", fontName="DejaVu-Oblique", fontSize=7, leading=10,
            textColor=C_FOOTNOTE, spaceAfter=4,
        ),
        "where": ParagraphStyle(
            "where", fontName="DejaVu-Oblique", fontSize=8.5, leading=12,
            textColor=C_CAPTION, leftIndent=8, spaceAfter=6,
        ),
        "toc_entry": ParagraphStyle(
            "toc_entry", fontName="DejaVu", fontSize=10, leading=16,
            textColor=C_BODY, leftIndent=12,
        ),
        "toc_appendix": ParagraphStyle(
            "toc_appendix", fontName="DejaVu-Oblique", fontSize=9.5, leading=15,
            textColor=C_CAPTION, leftIndent=12,
        ),
        "eq_label": ParagraphStyle(
            "eq_label", fontName="DejaVu", fontSize=9, leading=12,
            textColor=C_FOOTNOTE, alignment=TA_RIGHT,
        ),
    }


# ============================================================================
# Page templates with header/footer
# ============================================================================

PAGE_W, PAGE_H = A4  # 595.27, 841.89 points
MARGIN = 18 * mm

_fig_n = 0
_tbl_n = 0


def _header_footer(canvas, doc):
    """Draw header line and footer on content pages."""
    canvas.saveState()
    if doc.page > 2:
        # Header
        canvas.setStrokeColor(C_RULE)
        canvas.setLineWidth(0.3)
        canvas.line(MARGIN, PAGE_H - 14 * mm, PAGE_W - MARGIN, PAGE_H - 14 * mm)
        canvas.setFont("DejaVu", 7)
        canvas.setFillColor(C_FOOTNOTE)
        canvas.drawString(MARGIN, PAGE_H - 12.5 * mm,
                          "KTG-Kalkulation: Hypertonie")
        canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 12.5 * mm,
                               "MedRisk-ADH v2.0")
    # Footer
    canvas.setStrokeColor(C_RULE)
    canvas.setLineWidth(0.3)
    canvas.line(MARGIN, 10 * mm, PAGE_W - MARGIN, 10 * mm)
    canvas.setFont("DejaVu", 7)
    canvas.setFillColor(C_FOOTNOTE)
    canvas.drawString(MARGIN, 6.5 * mm, "the author | Helmholtz Munich | April 2026")
    canvas.drawRightString(PAGE_W - MARGIN, 6.5 * mm, str(doc.page))
    canvas.restoreState()


# ============================================================================
# Helper builders
# ============================================================================

def _chart_style():
    plt.rcParams.update({
        "font.family": "sans-serif", "font.size": 8.5,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.6, "axes.grid": True, "grid.alpha": 0.15,
        "grid.linewidth": 0.4, "figure.facecolor": "white", "figure.dpi": 200,
    })


def latex_to_image(latex: str, fontsize: int = 14, dpi: int = 300) -> BytesIO:
    """Render LaTeX via matplotlib mathtext → PNG buffer."""
    fig, ax = plt.subplots(figsize=(0.01, 0.01))
    ax.axis("off")
    text = ax.text(0, 0, f"${latex}$", fontsize=fontsize, color="#2D3436",
                   ha="left", va="bottom", transform=ax.transAxes)
    fig.canvas.draw()
    bbox = text.get_window_extent(renderer=fig.canvas.get_renderer())
    bi = bbox.transformed(fig.dpi_scale_trans.inverted())
    fig.set_size_inches(bi.width + 0.1, bi.height + 0.1)
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                pad_inches=0.05, transparent=True)
    plt.close(fig)
    buf.seek(0)
    return buf


def make_equation(latex: str, label: str | None = None,
                  where: str | None = None, styles: dict = None) -> list:
    """Build flowables for a styled equation block."""
    buf = latex_to_image(latex, fontsize=13)
    from PIL import Image as PILImage
    img = PILImage.open(buf)
    img_w_pt = img.width / (300 / 72)
    img_h_pt = img.height / (300 / 72)
    buf.seek(0)

    content_w = PAGE_W - 2 * MARGIN
    # Equation image (centred in a table with background)
    eq_img = Image(buf, width=min(img_w_pt, content_w - 40),
                   height=img_h_pt)

    if label:
        label_para = Paragraph(label, styles["eq_label"])
        eq_table = Table(
            [[eq_img, label_para]],
            colWidths=[content_w - 40, 35],
        )
    else:
        eq_table = Table([[eq_img]], colWidths=[content_w - 5])

    eq_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_BOX_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (0, 0), 12),
        ("RIGHTPADDING", (-1, -1), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        # Left accent bar via line
        ("LINEBEFOREPURE", (0, 0), (0, -1), 2, C_ACCENT),
    ]))

    result = [Spacer(1, 4), eq_table]
    if where:
        result.append(Paragraph(f"wobei {where}", styles["where"]))
    else:
        result.append(Spacer(1, 4))
    return result


def make_key_concept(text: str, styles: dict) -> list:
    """Build a key-concept box as a table with accent bar."""
    content_w = PAGE_W - 2 * MARGIN
    label = Paragraph("KERNAUSSAGE", styles["key_concept"])
    body = Paragraph(text, styles["key_concept_body"])
    t = Table([[label], [body]], colWidths=[content_w - 10])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_BOX_BG),
        ("LINEBEFOREPURE", (0, 0), (0, -1), 2, C_ACCENT),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (0, 0), 6),
        ("BOTTOMPADDING", (-1, -1), (-1, -1), 6),
    ]))
    return [Spacer(1, 4), t, Spacer(1, 6)]


def make_table(headers: list[str], rows: list[list[str]],
               col_widths: list[float] | None = None,
               caption: str | None = None,
               styles: dict = None) -> list:
    """Build a styled table with optional caption."""
    global _tbl_n
    content_w = PAGE_W - 2 * MARGIN
    if col_widths is None:
        w = content_w / len(headers)
        col_widths = [w] * len(headers)
    else:
        total = sum(col_widths)
        col_widths = [c / total * content_w for c in col_widths]

    data = [headers] + rows
    t = Table(data, colWidths=col_widths, repeatRows=1)

    style_cmds = [
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), C_TABLE_HDR),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_HEADING),
        ("FONTNAME", (0, 0), (-1, 0), "DejaVu-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 7.5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
        ("TOPPADDING", (0, 0), (-1, 0), 4),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, C_ACCENT),
        # Body
        ("FONTNAME", (0, 1), (-1, -1), "DejaVu"),
        ("FONTSIZE", (0, 1), (-1, -1), 7.5),
        ("TEXTCOLOR", (0, 1), (-1, -1), C_BODY),
        ("TOPPADDING", (0, 1), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, C_RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    # Alternating row colors
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), C_TABLE_ALT))

    t.setStyle(TableStyle(style_cmds))

    result = []
    if caption:
        _tbl_n += 1
        result.append(Paragraph(f"<b>Tabelle {_tbl_n}.</b> {caption}",
                                styles["caption"]))
    result.append(t)
    result.append(Spacer(1, 6))
    return result


def make_figure(chart_func, caption: str, styles: dict,
                width: float = 145 * mm) -> list:
    """Embed a chart with numbered caption."""
    global _fig_n
    _fig_n += 1
    buf = chart_func()
    buf.seek(0)
    img = Image(buf, width=width, height=width * 0.45)
    img.hAlign = "CENTER"
    cap = Paragraph(f"<b>Abbildung {_fig_n}.</b> {caption}", styles["caption"])
    return [Spacer(1, 4), img, cap, Spacer(1, 4)]


# ============================================================================
# Charts (same logic as before, cleaner)
# ============================================================================

def chart_coverage_timeline() -> BytesIO:
    _chart_style()
    fig, ax = plt.subplots(figsize=(6.5, 1.6))
    ax.set_xlim(0, 560); ax.set_ylim(0, 2); ax.axis("off")
    for x0, w, label, col in [
        (0, 42, "Lohnfortzahlung\n100 % (6 Wo.)", M_GREEN),
        (44, 502, "GKV-Krankengeld: 70 % brutto / 90 % netto (78 Wo.)", M_BLUE),
    ]:
        r = mpatches.FancyBboxPatch((x0, 0.7), w, 0.8, boxstyle="round,pad=0.02",
                                     facecolor=col, alpha=0.8, edgecolor="none")
        ax.add_patch(r)
        ax.text(x0 + w / 2, 1.1, label, ha="center", va="center",
                fontsize=6.5, color="white", fontweight="bold")
    ax.annotate("KTG schließt\ndie Lücke", xy=(295, 0.55), fontsize=7,
                ha="center", va="top", color=M_RED, fontweight="bold")
    for d, lbl in [(0, "Tag 1"), (42, "Tag 43"), (546, "Tag 546")]:
        ax.axvline(d, color=M_GREY, linewidth=0.5, alpha=0.5, ymin=0.3, ymax=0.9)
        ax.text(d, 0.3, lbl, ha="center", fontsize=6, color=M_GREY)
    fig.tight_layout()
    buf = BytesIO(); fig.savefig(buf, format="png", bbox_inches="tight"); plt.close(fig)
    return buf


def chart_au_by_stadium() -> BytesIO:
    _chart_style()
    stadien = ["Risiko-\nfaktoren", "Chronisch", "Kompli-\nkation", "Schweres\nEreignis"]
    p_au = [0.03, 0.12, 0.35, 0.80]
    e_days = [14, 28, 42, 120]
    cols = [M_BLUE, M_AMBER, M_RED, M_DARK]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.5, 2.5))
    a1.bar(range(4), [x * 100 for x in p_au], color=cols, alpha=0.75)
    a1.set_xticks(range(4)); a1.set_xticklabels(stadien, fontsize=6)
    a1.set_ylabel("AU-Wahrscheinlichkeit (%)")
    for i, v in enumerate(p_au):
        a1.text(i, v * 100 + 1.5, f"{v:.0%}", ha="center", fontsize=6.5)
    a2.bar(range(4), e_days, color=cols, alpha=0.75)
    a2.set_xticks(range(4)); a2.set_xticklabels(stadien, fontsize=6)
    a2.set_ylabel("Erwartete AU-Dauer (Tage)")
    for i, v in enumerate(e_days):
        a2.text(i, v + 2, str(v), ha="center", fontsize=6.5)
    fig.tight_layout()
    buf = BytesIO(); fig.savefig(buf, format="png", bbox_inches="tight"); plt.close(fig)
    return buf


def chart_q_matrix() -> BytesIO:
    _chart_style()
    Q = np.array([[-0.08, 0.08, 0, 0, 0], [0.02, -0.08, 0.06, 0, 0],
                  [0, 0, -0.05, 0.04, 0.01], [0, 0, 0, -0.03, 0.03],
                  [0, 0, 0, 0, 0]])
    labels = ["Gesund", "Risiko", "Chron.", "Kompl.", "Schw.Er."]
    fig, ax = plt.subplots(figsize=(4.5, 3.2))
    im = ax.imshow(Q, cmap="RdBu_r", vmin=-0.10, vmax=0.10, aspect="equal")
    ax.set_xticks(range(5)); ax.set_xticklabels(labels, fontsize=7, rotation=30, ha="right")
    ax.set_yticks(range(5)); ax.set_yticklabels(labels, fontsize=7)
    ax.set_xlabel("Nach (j)", fontsize=8); ax.set_ylabel("Von (i)", fontsize=8)
    for i in range(5):
        for j in range(5):
            v = Q[i, j]
            txt = "0" if v == 0 else f"{v:+.2f}"
            c = "#999" if v == 0 else ("white" if abs(v) > 0.04 else "black")
            ax.text(j, i, txt, ha="center", va="center", fontsize=8,
                    fontweight="bold" if v != 0 else "normal", color=c)
    ax.set_title("Q = Intensitätsmatrix (Raten pro Jahr)", fontsize=9, fontweight="bold")
    fig.colorbar(im, ax=ax, shrink=0.7, label="Rate (1/Jahr)")
    fig.tight_layout()
    buf = BytesIO(); fig.savefig(buf, format="png", bbox_inches="tight"); plt.close(fig)
    return buf


def chart_ctmc_progression() -> BytesIO:
    _chart_style()
    from scipy.linalg import expm
    Q = np.zeros((5, 5))
    for (i, j), r in {(0,1):0.08,(1,2):0.06,(1,0):0.02,(2,3):0.04,(3,4):0.03,(2,4):0.01}.items():
        Q[i, j] = r
    for i in range(5):
        Q[i, i] = -sum(Q[i, j] for j in range(5) if j != i)
    times = np.linspace(0, 30, 300)
    p0 = np.array([0, 1, 0, 0, 0])
    probs = np.array([p0 @ expm(Q * t) for t in times])
    labels = ["Gesund", "Risikofaktoren", "Chronisch", "Komplikation", "Schweres Ereignis"]
    cols = [M_GREEN, M_BLUE, M_AMBER, M_RED, M_DARK]
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    ax.stackplot(times, probs.T, labels=labels, colors=cols, alpha=0.75)
    ax.set_xlabel("Jahre nach Erstdiagnose", fontsize=9)
    ax.set_ylabel("Aufenthaltswahrscheinlichkeit", fontsize=9)
    ax.set_xlim(0, 30); ax.set_ylim(0, 1)
    ax.legend(loc="upper right", fontsize=6.5)
    fig.tight_layout()
    buf = BytesIO(); fig.savefig(buf, format="png", bbox_inches="tight"); plt.close(fig)
    return buf


def chart_au_by_beruf() -> BytesIO:
    _chart_style()
    kl = ["Klasse 1\n(Büro)", "Klasse 2\n(Vertrieb)", "Klasse 3\n(Handwerk)", "Klasse 4\n(Schwer)"]
    freq, dur = [0.80, 1.00, 1.28, 1.68], [14, 18, 25, 38]
    cols = [M_GREEN, M_BLUE, M_AMBER, M_RED]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.5, 2.5))
    a1.bar(range(4), freq, color=cols, alpha=0.75)
    a1.set_xticks(range(4)); a1.set_xticklabels(kl, fontsize=6)
    a1.set_ylabel("AU-Episoden / Jahr")
    for i, v in enumerate(freq):
        a1.text(i, v + 0.03, f"{v:.2f}", ha="center", fontsize=6.5)
    a2.bar(range(4), dur, color=cols, alpha=0.75)
    a2.set_xticks(range(4)); a2.set_xticklabels(kl, fontsize=6)
    a2.set_ylabel("Mittlere Dauer (Tage)")
    for i, v in enumerate(dur):
        a2.text(i, v + 0.8, str(v), ha="center", fontsize=6.5)
    fig.tight_layout()
    buf = BytesIO(); fig.savefig(buf, format="png", bbox_inches="tight"); plt.close(fig)
    return buf


def chart_pbw_scatter() -> BytesIO:
    _chart_style()
    rng = np.random.default_rng(42)
    n = 100
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    for market, dqs_m, dqs_s, col, mk in [
        ("DE", 0.85, 0.08, M_BLUE, "o"), ("FR", 0.78, 0.10, M_GREEN, "s"),
        ("ES", 0.65, 0.12, M_AMBER, "^"), ("INT", 0.42, 0.15, M_RED, "D"),
    ]:
        dqs = np.clip(rng.normal(dqs_m, dqs_s, n), 0, 1)
        conf = np.clip(rng.beta(3, 2, n), 0.5, 1.0)
        ax.scatter(dqs, conf, c=col, marker=mk, s=15, alpha=0.45,
                   label=market, edgecolors="none")
    ax.axhspan(0.80, 1.01, xmin=0, xmax=0.60, alpha=0.08, color=M_RED)
    ax.axhline(0.80, color=M_RED, linestyle=":", alpha=0.35, linewidth=0.8)
    ax.axvline(0.60, color=M_RED, linestyle=":", alpha=0.35, linewidth=0.8)
    ax.text(0.05, 0.96, "PBW-Zone", fontsize=7.5, color=M_RED, style="italic")
    ax.set_xlabel("Data Quality Score (DQS)"); ax.set_ylabel("Modellkonfidenz")
    ax.set_xlim(0, 1.02); ax.set_ylim(0.45, 1.02)
    ax.legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    buf = BytesIO(); fig.savefig(buf, format="png", bbox_inches="tight"); plt.close(fig)
    return buf


# ============================================================================
# Document builder
# ============================================================================

def build_study_guide_de():
    global _fig_n, _tbl_n
    _fig_n = 0
    _tbl_n = 0

    logger.info("Generiere Charts und Formeln...")
    S = _build_styles()
    output_path = str(OUT / "study_guide_de.pdf")

    doc = BaseDocTemplate(
        output_path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=18 * mm, bottomMargin=16 * mm,
        title="KTG-Kalkulation am Beispiel Hypertonie",
        author="the author",
    )

    content_frame = Frame(
        MARGIN, 16 * mm,
        PAGE_W - 2 * MARGIN, PAGE_H - 34 * mm,
        id="content",
    )
    doc.addPageTemplates([
        PageTemplate(id="content", frames=[content_frame],
                     onPage=_header_footer),
    ])

    story = []
    cw = PAGE_W - 2 * MARGIN

    # ===== TITELSEITE =====
    story.append(Spacer(1, 80))
    story.append(Paragraph("MedRisk-ADH v2.0", S["meta"]))
    story.append(Spacer(1, 16))
    story.append(Paragraph("KTG-Kalkulation", S["title"]))
    story.append(Paragraph("am Beispiel Hypertonie", S["subtitle"]))
    story.append(Spacer(1, 16))

    # Accent line via small colored table
    line_t = Table([[""]], colWidths=[80], rowHeights=[2])
    line_t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), C_ACCENT)]))
    line_t.hAlign = "CENTER"
    story.append(line_t)
    story.append(Spacer(1, 16))

    story.append(Paragraph("the author", S["author"]))
    story.append(Paragraph("Helmholtz Munich  |  April 2026", S["meta"]))
    story.append(Spacer(1, 40))
    story.append(Paragraph(
        "Krankentagegeld-Kalkulation mit individuellem Risikoprofil.<br/>"
        "CTMC-Krankheitsverlauf, NegBin-Frequenz, Weibull-Dauer,<br/>"
        "Äquivalenzprinzip und Datenqualitätsbewertung.<br/><br/>"
        "7 Kapitel  |  2 Anhänge  |  Alle Daten synthetisch",
        S["meta"]))

    # ===== INHALTSVERZEICHNIS =====
    story.append(PageBreak())
    story.append(Paragraph("Inhalt", S["chapter"]))
    story.append(Spacer(1, 8))
    for num, title in [
        (1, "Was ist Krankentagegeld?"),
        (2, "Warum Hypertonie?"),
        (3, "Krankheitsverlauf: Das CTMC-Modell"),
        (4, "AU-Frequenz und -Dauer"),
        (5, "KTG-Prämienberechnung"),
        (6, "Datenqualität bestimmt die Prämie"),
        (7, "Was ich gebaut habe"),
    ]:
        story.append(Paragraph(f"<b>{num}</b>&nbsp;&nbsp;&nbsp;{title}", S["toc_entry"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Anhang A: Formelsammlung", S["toc_appendix"]))
    story.append(Paragraph("Anhang B: Glossar Deutsch–Englisch", S["toc_appendix"]))

    # ================================================================
    # KAPITEL 1: Was ist Krankentagegeld?
    # ================================================================
    story.append(PageBreak())
    story.append(Paragraph("1 &nbsp; Was ist Krankentagegeld?", S["chapter"]))

    story.append(Paragraph(
        "Krankentagegeld (KTG) ist eine private Zusatzversicherung, die den "
        "Einkommensverlust bei längerer Arbeitsunfähigkeit (AU) überbrückt. "
        "Die gesetzliche Absicherung läuft in drei Stufen:", S["body"]))

    story += make_figure(chart_coverage_timeline,
        "Leistungskette bei Arbeitsunfähigkeit. Tag 1–42: Arbeitgeber zahlt "
        "100 % (Lohnfortzahlung, §3 EFZG). Tag 43–546: GKV zahlt Krankengeld "
        "(§44 SGB V). KTG deckt die Lücke zwischen Krankengeld und "
        "tatsächlichem Einkommen.", S, width=155 * mm)

    story.append(Paragraph("GKV-Krankengeld (§44 SGB V)", S["h2"]))
    story.append(Paragraph(
        "Das gesetzliche Krankengeld berechnet sich als Minimum aus drei Grenzen:",
        S["body"]))

    story += make_equation(
        r"\text{KG}_{\text{tgl}} = \min\left("
        r"\frac{0{,}70 \cdot G}{30},\;"
        r"\frac{0{,}90 \cdot N}{30},\;"
        r"0{,}70 \cdot \frac{\text{BBG}}{30}\right)",
        label="(1)",
        where="G = Bruttomonatsgehalt, N = Nettomonatsgehalt, "
              "BBG = Beitragsbemessungsgrenze (5.175 EUR/Monat, 2024)",
        styles=S)

    story.append(Paragraph("KTG-Leistung", S["h2"]))
    story.append(Paragraph(
        "Die private KTG-Versicherung zahlt die Differenz zwischen dem "
        "vereinbarten Tagessatz und dem GKV-Krankengeld:", S["body"]))

    story += make_equation(
        r"\text{KTG}_{\text{tgl}} = \max("
        r"\text{Tagessatz}_{\text{versichert}} - \text{KG}_{\text{tgl}},\; 0)",
        label="(2)",
        where="Tagessatz = vertraglich vereinbarter KTG-Tagessatz (z. B. 80 EUR/Tag)",
        styles=S)
    story.append(Paragraph(
        "Code: src/medrisk/models/krankentagegeld.py — "
        "krankengeld_daily(), ktg_benefit_above_krankengeld()", S["code_ref"]))

    story.append(Paragraph("Wichtige Parameter", S["h2"]))
    story += make_table(
        ["Parameter", "Wert", "Rechtsgrundlage"],
        [
            ["Lohnfortzahlung", "6 Wochen (42 Tage), 100 %", "§3 EFZG"],
            ["Krankengeld", "Max. 78 Wochen, 70 % brutto", "§44 SGB V"],
            ["BBG (monatlich, 2024)", "5.175 EUR", "SGB IV"],
            ["KTG-Karenzzeit", "Typisch 3 Tage", "Vertrag"],
            ["Max. Leistungsdauer KTG", "78 Wochen", "§192 VVG"],
        ],
        col_widths=[40, 42, 40],
        caption="KTG-Leistungsparameter", styles=S)

    # ================================================================
    # KAPITEL 2: Warum Hypertonie?
    # ================================================================
    story.append(PageBreak())
    story.append(Paragraph("2 &nbsp; Warum Hypertonie?", S["chapter"]))

    story.append(Paragraph(
        "Hypertonie (ICD-10: I10) ist mit 30 % Prävalenz (RKI DEGS1 2012) "
        "die häufigste chronische Erkrankung in Deutschland und eine der "
        "wichtigsten Einzeldiagnosen bei AU-Bescheinigungen. "
        "Sie eignet sich ideal als Proof of Concept:", S["body"]))

    for bullet in [
        "Die Progression ist klar in Stadien abbildbar",
        "Das AU-Risiko variiert 8-fach — gleicher ICD-Code, völlig unterschiedliche Kosten",
        "Pauschaltarife ignorieren diese Varianz",
    ]:
        story.append(Paragraph(f"• {bullet}", S["bullet"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("5-Stadien-Modell", S["h2"]))
    story += make_table(
        ["Stadium", "Beschreibung", "P(AU/Jahr)", "E[Dauer]", "Beispiel"],
        [
            ["0 – Gesund", "Keine Hypertonie", "1 %", "7 d", "Normaler Blutdruck"],
            ["I – Risikofaktoren", "Erhöhter RR", "3 %", "14 d", "RR 145/95, 1 Medikament"],
            ["II – Chronisch", "Dauermedikation", "12 %", "28 d", "RR 155/100, 3 Medikamente"],
            ["III – Komplikation", "Organschäden", "35 %", "42 d", "LVH, CKD Stad. 3"],
            ["IV – Schweres Ereignis", "MI, Schlaganfall", "80 %", "120 d", "Akutes Koronarereignis"],
        ],
        col_widths=[25, 28, 15, 12, 35],
        caption="Hypertonie-Stadien mit AU-Parametern", styles=S)

    story += make_figure(chart_au_by_stadium,
        "AU-Wahrscheinlichkeit und erwartete Dauer nach Hypertonie-Stadium. "
        "Das Risiko steigt von 3 % (Stadium I) auf 80 % (Stadium IV). "
        "Ein Pauschaltarif mittelt über diese Stadien und kalkuliert beide Enden falsch.", S)

    story += make_key_concept(
        "Gleiche Diagnose (I10), gleicher ICD-Code — aber das "
        "KTG-Risiko variiert um den Faktor 8. Stadienspezifische "
        "Kalkulation ist der Schlüssel zu risikoadäquaten Prämien.", S)

    # ================================================================
    # KAPITEL 3: Das CTMC-Modell
    # ================================================================
    story.append(PageBreak())
    story.append(Paragraph("3 &nbsp; Krankheitsverlauf: Das CTMC-Modell", S["chapter"]))

    story.append(Paragraph(
        "Ein Continuous-Time Markov Chain (CTMC) Modell beschreibt den "
        "Krankheitsverlauf als stochastischen Prozess mit 5 Zuständen. "
        "Die Übergangsraten zwischen den Zuständen bestimmen, wie schnell "
        "ein Patient von einem Stadium zum nächsten fortschreitet.", S["body"]))

    story.append(Paragraph("Intensitätsmatrix Q", S["h2"]))

    story += make_figure(chart_q_matrix,
        "Intensitätsmatrix Q für das 5-Stadien-Hypertonie-CTMC. "
        "Nebendiagonale: Übergangsraten (pro Jahr). Diagonale: "
        "negative Zeilensumme. Zustand 4 ist absorbierend.", S, width=110 * mm)

    story += make_equation(
        r"q_{ii} = -\sum_{j \neq i} q_{ij} \quad,\quad q_{ij} \geq 0",
        label="(3)",
        where="q_ij = Übergangsrate von Zustand i nach j (pro Jahr), "
              "q_ii = negative Zeilensumme (Verweilrate). "
              "Zustand 4 ist absorbierend (Zeile = 0).",
        styles=S)

    story.append(Paragraph("Übergangswahrscheinlichkeiten", S["h2"]))
    story += make_equation(
        r"\mathbf{P}(t) = e^{\mathbf{Q} \cdot t}"
        r"\qquad\text{und}\qquad"
        r"\pi(t) = \pi(0) \cdot \mathbf{P}(t)",
        label="(4)",
        where="P(t) = Übergangsmatrix für Zeitraum t, "
              "π(0) = Anfangsverteilung, "
              "π(t) = Aufenthaltswahrscheinlichkeiten zum Zeitpunkt t",
        styles=S)
    story.append(Paragraph(
        "Code: src/medrisk/models/multistate.py — "
        "MultistateModel.transition_probability(), state_occupation_probabilities()",
        S["code_ref"]))

    story += make_table(
        ["Von", "Nach", "Rate (1/Jahr)", "Interpretation"],
        [
            ["Gesund", "Risikofaktoren", "0,08", "8 % Neuerkrankung pro Jahr"],
            ["Risikofaktoren", "Gesund", "0,02", "2 % Rückbildung"],
            ["Risikofaktoren", "Chronisch", "0,06", "6 % Progression trotz Therapie"],
            ["Chronisch", "Komplikation", "0,04", "4 % Organschäden pro Jahr"],
            ["Chronisch", "Schweres Ereignis", "0,01", "1 % direkt zum Ereignis"],
            ["Komplikation", "Schweres Ereignis", "0,03", "3 % MI/Schlaganfall pro Jahr"],
        ],
        col_widths=[28, 32, 20, 50],
        caption="Übergangsraten für Hypertonie (pro Jahr)", styles=S)

    story += make_figure(chart_ctmc_progression,
        "CTMC-Aufenthaltswahrscheinlichkeiten über 30 Jahre, Start in "
        "Stadium I (Risikofaktoren). Nach 15 Jahren befinden sich ca. 35 % im "
        "chronischen Stadium, ca. 15 % haben eine Komplikation. "
        "Quelle: Framingham Heart Study, SCORE2 (ESC 2021).", S)

    # ================================================================
    # KAPITEL 4: AU-Frequenz und -Dauer
    # ================================================================
    story.append(PageBreak())
    story.append(Paragraph("4 &nbsp; AU-Frequenz und -Dauer", S["chapter"]))

    story.append(Paragraph(
        "Die KTG-Kalkulation braucht zwei Größen: wie oft tritt eine AU auf "
        "(Frequenz) und wie lange dauert sie (Dauer). Beide werden getrennt "
        "modelliert.", S["body"]))

    story.append(Paragraph("Frequenzmodell: Negative Binomialverteilung", S["h2"]))
    story += make_equation(
        r"Y \sim \text{NegBin}(\mu, \alpha)"
        r"\qquad\text{mit}\qquad"
        r"\log(\mu) = \beta_0 + \beta_1 \cdot \text{Alter}"
        r" + \beta_2 \cdot \mathbb{1}_{\text{M}}"
        r" + \beta_3 \cdot \text{MRS}"
        r" + \beta_4 \cdot \log(\text{BK})",
        label="(5)",
        where="μ = erwartete AU-Episoden/Jahr, α = 0,5 (Überdispersion), "
              "MRS = MedRisk-Score (0–1), BK = Berufsklassen-Faktor (1,0–2,1)",
        styles=S)

    story += make_table(
        ["Koeffizient", "Wert", "Interpretation"],
        [
            ["β₀ (Intercept)", "0,30", "Baseline log-Frequenz"],
            ["β₁ (Alter)", "−0,004", "Pro Lebensjahr −0,4 % (ältere: seltener, aber länger AU)"],
            ["β₂ (Mann)", "−0,08", "Männer ca. 8 % seltener AU als Frauen"],
            ["β₃ (MRS)", "0,12", "+13 % AU-Frequenz pro Einheit MRS"],
            ["β₄ (log BK)", "0,18", "+20 % pro Berufsklasse (Klasse 4 vs. 1: 2,1×)"],
        ],
        col_widths=[22, 12, 85],
        caption="Regressionskoeffizienten (GKV-Referenztabelle kalibriert)", styles=S)
    story.append(Paragraph(
        "Code: src/medrisk/models/sickness_absence.py — NegBinomFrequencyModel",
        S["code_ref"]))

    story.append(Paragraph("Dauermodell: Weibull AFT", S["h2"]))
    story += make_equation(
        r"S(t) = \exp\left(-\left(\frac{t}{\lambda}\right)^k\right)"
        r"\qquad\text{mit}\qquad"
        r"\mathbb{E}[T] = \lambda \cdot \Gamma\left(1 + \frac{1}{k}\right)",
        label="(6)",
        where="S(t) = Überlebenswahrscheinlichkeit (P(AU-Dauer > t)), "
              "λ = Skalenparameter, k = Formparameter, "
              "Γ = Gammafunktion. Parameter sind ICD-Kapitel-spezifisch.",
        styles=S)

    story += make_equation(
        r"h(t) = \frac{k}{\lambda} \cdot "
        r"\left(\frac{t}{\lambda}\right)^{k-1}",
        label="(7)",
        where="h(t) = Hazardfunktion (momentane Rate der Genesung zum Zeitpunkt t)",
        styles=S)
    story.append(Paragraph(
        "Code: src/medrisk/models/sickness_absence.py — WeibullDurationModel",
        S["code_ref"]))

    story += make_figure(chart_au_by_beruf,
        "AU-Frequenz und mittlere Dauer nach Berufsklasse. Schwere körperliche "
        "Arbeit (Klasse 4) führt zu 2,1× häufigeren und 2,7× längeren "
        "AU-Episoden als Büroarbeit (Klasse 1). "
        "Quelle: BAuA Fehlzeiten 2022, TK Gesundheitsreport 2023.", S)

    # ================================================================
    # KAPITEL 5: KTG-Prämienberechnung
    # ================================================================
    story.append(PageBreak())
    story.append(Paragraph("5 &nbsp; KTG-Prämienberechnung", S["chapter"]))

    story.append(Paragraph("Erwarteter Jahresschaden", S["h2"]))
    story += make_equation(
        r"\mathbb{E}[\text{KTG}_{\text{Jahr}}] = f \cdot "
        r"\sum_{\text{ch}} w_{\text{ch}} \cdot "
        r"\mathbb{E}[\max(T_{\text{ch}} - d, \; 0)] "
        r"\cdot \text{KTG}_{\text{tgl}}",
        label="(8)",
        where="f = AU-Frequenz (Episoden/Jahr), w_ch = ICD-Kapitel-Gewicht, "
              "T_ch = AU-Dauer für Kapitel ch, d = Karenzzeit (Tage), "
              "KTG_tgl = tägliche KTG-Leistung (Formel 2)",
        styles=S)

    story.append(Paragraph("Excess-Dauer über Karenzzeit", S["h2"]))
    story += make_equation(
        r"\mathbb{E}[\max(T - d, 0)] = "
        r"\int_d^{\infty} S(t)\, dt = "
        r"\int_d^{\infty} \exp\left(-\left(\frac{t}{\lambda}\right)^k\right) dt",
        label="(9)",
        where="d = Karenzzeit (typisch 3 Tage), S(t) = Weibull-Überlebensfunktion",
        styles=S)
    story.append(Paragraph(
        "Code: src/medrisk/models/krankentagegeld.py — expected_annual_claim()",
        S["code_ref"]))

    story.append(Paragraph("Äquivalenzprinzip: Nettoprämie", S["h2"]))
    story.append(Paragraph(
        "Die jährliche Nettoprämie wird über das versicherungsmathematische "
        "Äquivalenzprinzip bestimmt: der Barwert aller zukünftigen Prämien "
        "muss dem Barwert aller zukünftigen erwarteten Leistungen entsprechen:",
        S["body"]))
    story += make_equation(
        r"P_{\text{netto}} \cdot \ddot{a}_x = "
        r"\sum_{t=0}^{T-1} v^t \cdot {}_t p_x \cdot "
        r"\mathbb{E}[\text{Schaden}(x+t)]",
        label="(10)",
        where="ä_x = Barwertfaktor (Rentenbarwert), v = 1/(1+i) (Diskontfaktor, "
              "i = Rechnungszins), ₜpₓ = Überlebenswahrscheinlichkeit von "
              "Alter x bis x+t (DAV-Sterbetafel)",
        styles=S)

    story.append(Paragraph("Bruttoprämie", S["h2"]))
    story += make_equation(
        r"P_{\text{brutto}} = \frac{P_{\text{netto}}}"
        r"{1 - \varepsilon - \gamma}",
        label="(11)",
        where="ε = Kostenzuschlag (20 %), γ = Gewinnzuschlag (5 %)",
        styles=S)
    story.append(Paragraph(
        "Code: src/medrisk/models/krankentagegeld.py — "
        "level_premium(), gross_premium()", S["code_ref"]))

    story.append(Paragraph("Durchgerechnetes Beispiel", S["h2"]))
    story.append(Paragraph(
        "50 Jahre, männlich, BMI 28, Hypertonie Stadium II (chronisch), "
        "3 Antihypertensiva, Tagessatz 80 EUR, Bruttoeinkommen 5.000 EUR/Monat.",
        S["body"]))

    story += make_table(
        ["Stadium", "P(in 5 J)", "P(AU)", "E[Dauer]", "EUR/Tag", "E[Kosten]"],
        [
            ["I – Risikofaktoren", "10 %", "3 %", "14 d", "80", "3 EUR"],
            ["II – Chronisch", "60 %", "12 %", "28 d", "80", "161 EUR"],
            ["III – Komplikation", "25 %", "35 %", "42 d", "80", "294 EUR"],
            ["IV – Schweres Ereignis", "5 %", "80 %", "120 d", "80", "384 EUR"],
        ],
        col_widths=[30, 16, 14, 14, 14, 20],
        caption="Stadiengewichtete KTG-Kalkulation", styles=S)

    story += make_key_concept(
        "Erwarteter Jahresschaden: ca. 839 EUR. "
        "Mit Sicherheitszuschlag (15 %) und Verwaltung (12 %): "
        "839 × 1,15 × 1,12 / 12 Monate ≈ 90 EUR/Monat Bruttoprämie.", S)

    # ================================================================
    # KAPITEL 6: Datenqualität
    # ================================================================
    story.append(PageBreak())
    story.append(Paragraph("6 &nbsp; Datenqualität bestimmt die Prämie", S["chapter"]))

    story.append(Paragraph(
        "Die Stadienzuordnung hängt vollständig von der Datenlage ab. "
        "Ohne Medikamenten- und Labordaten kann nicht zwischen kontrollierter "
        "und unkontrollierter Hypertonie unterschieden werden. Der Data Quality "
        "Score (DQS) quantifiziert diese Unsicherheit:", S["body"]))

    story += make_equation(
        r"\text{DQS} = 0{,}40 \cdot C + 0{,}35 \cdot S + 0{,}25 \cdot R",
        label="(12)",
        where="C = Vollständigkeit (Anteil vorhandener Felder), "
              "S = Konsistenz (1 − Widersprüche/Prüfungen), "
              "R = Aktualität (exponentieller Zerfall, Halbwertszeit 1,4 Jahre)",
        styles=S)
    story.append(Paragraph(
        "Code: src/medrisk/validation/data_quality.py — compute_dqs()",
        S["code_ref"]))

    story.append(Paragraph("Auswirkung auf die Prämie", S["h2"]))
    story += make_table(
        ["", "Vollständige Akte (DQS 0,85)", "Lückenhafte Akte (DQS 0,40)"],
        [
            ["Medikamente", "3 Antihypertensiva dokumentiert", "Keine Daten"],
            ["Blutdruck", "RR 135/85 mmHg (6 Monate)", "Kein Wert"],
            ["Labor", "HbA1c, Lipidprofil vorhanden", "Keine Labore"],
            ["Stadium", "II (Chronisch) gesichert", "Unklar (I? II? III?)"],
            ["KTG-Prämie", "ca. 90 EUR/Monat", "???"],
        ],
        col_widths=[20, 50, 50],
        caption="Gleicher ICD-Code (I10) — unterschiedliche Datenlage", styles=S)

    story.append(Paragraph("PBW-Erkennung", S["h2"]))
    story.append(Paragraph(
        "Ein plausible-but-wrong (PBW) Fehler liegt vor, wenn das Modell "
        "eine hohe Konfidenz ausgibt, obwohl die Datenlage schlecht ist:",
        S["body"]))

    story += make_equation(
        r"\text{PBW-Flag} \Leftrightarrow "
        r"\text{Konfidenz} > 0{,}80 \;\wedge\; \text{DQS} < 0{,}60",
        label="(13)", styles=S)

    story += make_figure(chart_pbw_scatter,
        "Konfidenz vs. DQS für 400 synthetische Patienten aus 4 Märkten. "
        "Die PBW-Zone (oben links, rot) zeigt hohe Konfidenz bei niedriger "
        "Datenqualität — hier muss an einen menschlichen "
        "Underwriter eskaliert werden.", S)

    # ================================================================
    # KAPITEL 7: Was ich gebaut habe
    # ================================================================
    story.append(PageBreak())
    story.append(Paragraph("7 &nbsp; Was ich gebaut habe", S["chapter"]))

    story.append(Paragraph(
        "MedRisk-ADH ist ein Proof of Concept für KI-gestütztes medizinisches "
        "Underwriting mit Fehlererkennung. Es demonstriert die gesamte Pipeline "
        "von Patientendaten bis zur auditierten Entscheidung.", S["body"]))

    story += make_table(
        ["Komponente", "Details"],
        [
            ["Tests", "442 Pytest-Tests, alle bestanden"],
            ["Märkte", "4 (DE, FR, ES, INT) mit realistischer Datenqualitätsvarianz"],
            ["Modelle", "XGBoost, Cox PH, CTMC, NegBin, Weibull, Chain-Ladder, BF"],
            ["Streamlit-App", "7 Seiten (Assessment, PBW, Portfolio, Alzheimer, KTG, Simulator, Flashcards)"],
            ["Datenadapter", "8 externe Quellen (NHANES, CDC PLACES, Zenodo, UK Biobank, …)"],
            ["Underwriting", "Automatisierte Entscheidung mit klinischen Konsistenzprüfungen"],
            ["Erklärbarkeit", "SHAP für jede Vorhersage"],
            ["Governance", "Audit-Trail (JSON Lines) + Human Override (EU AI Act Art. 12/14)"],
        ],
        col_widths=[25, 95],
        caption="MedRisk-ADH v2.0 — Komponenten", styles=S)

    story.append(Paragraph("Hypertonie als Demonstrator", S["h2"]))
    story.append(Paragraph(
        "Für Hypertonie (I10) zeigt das Tool den kompletten Weg: "
        "ICD-10-Code → 5-Stadien-CTMC → stadienspezifische AU-Parameter → "
        "individuelle KTG-Prämie → Datenqualitätsprüfung → "
        "Entscheidung (accept/review/reject) → Audit-Log.", S["body"]))

    story.append(Paragraph("Was Phase 2 braucht", S["h2"]))
    story += make_table(
        ["Phase", "Status", "Daten", "Ziel"],
        [
            ["Phase 1", "Fertig", "Synthetisch (4.000 Patienten)", "Mechanismus demonstrieren"],
            ["Phase 2", "Geplant", "Real (InGef, CPRD, PKV-Verband)", "Schwellenwerte validieren"],
            ["Phase 3", "Vision", "Produktion (intern)", "Deployment mit Monitoring"],
        ],
        col_widths=[18, 18, 42, 42],
        caption="Validierungsfahrplan", styles=S)

    story.append(Paragraph(
        "Phase 2 erfordert mindestens 50.000 Patienten mit 5+ Jahren "
        "Follow-up und verknüpften Leistungsdaten. Rechtsgrundlage: "
        "DSGVO Art. 89 (Forschungsausnahme) + institutionelles Ethikvotum. "
        "Der Engpass ist nicht die Technik — sondern der Datenzugang.",
        S["body"]))

    story += make_key_concept(
        "MedRisk-ADH beantwortet die Frage: Kann man erkennen, "
        "wenn ein KI-Underwriting-Modell sicher falsch liegt? "
        "Die Antwort ist ja, auf synthetischen Daten. "
        "Phase 2 beantwortet: Funktioniert das auf echten Schäden?", S)

    # ================================================================
    # ANHANG A: Formelsammlung
    # ================================================================
    story.append(PageBreak())
    story.append(Paragraph("Anhang A: Formelsammlung", S["chapter"]))

    formulas = [
        ("(1)", "GKV-Krankengeld",
         r"\text{KG}_{\text{tgl}} = \min\left("
         r"\frac{0{,}70 \cdot G}{30}, \frac{0{,}90 \cdot N}{30},"
         r" 0{,}70 \cdot \frac{\text{BBG}}{30}\right)"),
        ("(2)", "KTG-Leistung",
         r"\text{KTG}_{\text{tgl}} = \max("
         r"\text{Tagessatz} - \text{KG}_{\text{tgl}}, 0)"),
        ("(3)", "CTMC",
         r"q_{ii} = -\sum_{j \neq i} q_{ij},\; q_{ij} \geq 0"),
        ("(4)", "Übergangswahrscheinlichkeit",
         r"\mathbf{P}(t) = e^{\mathbf{Q} \cdot t}"),
        ("(5)", "AU-Frequenz",
         r"\log(\mu) = \beta_0 + \beta_1 \cdot \text{Alter}"
         r" + \beta_2 \cdot \mathbb{1}_M + \beta_3 \cdot \text{MRS}"
         r" + \beta_4 \cdot \log(\text{BK})"),
        ("(6)", "AU-Dauer",
         r"S(t) = \exp\left(-\left(\frac{t}{\lambda}\right)^k\right),"
         r"\; \mathbb{E}[T] = \lambda \cdot \Gamma(1 + 1/k)"),
        ("(7)", "Hazardfunktion",
         r"h(t) = \frac{k}{\lambda}\left(\frac{t}{\lambda}\right)^{k-1}"),
        ("(8)", "Erwarteter Jahresschaden",
         r"\mathbb{E}[\text{KTG}] = f \cdot \sum_{\text{ch}} w_{\text{ch}}"
         r"\cdot \mathbb{E}[\max(T_{\text{ch}} - d, 0)] \cdot \text{KTG}_{\text{tgl}}"),
        ("(9)", "Excess-Dauer",
         r"\mathbb{E}[\max(T-d,0)] = \int_d^\infty S(t)\,dt"),
        ("(10)", "Äquivalenzprinzip",
         r"P \cdot \ddot{a}_x = \sum_t v^t \cdot {}_tp_x"
         r"\cdot \mathbb{E}[\text{Schaden}(x+t)]"),
        ("(11)", "Bruttoprämie",
         r"P_{\text{brutto}} = P_{\text{netto}} / (1 - \varepsilon - \gamma)"),
        ("(12)", "Data Quality Score",
         r"\text{DQS} = 0{,}40 \cdot C + 0{,}35 \cdot S + 0{,}25 \cdot R"),
        ("(13)", "PBW-Flag",
         r"\text{PBW} \Leftrightarrow \text{Konfidenz} > 0{,}80"
         r"\;\wedge\; \text{DQS} < 0{,}60"),
    ]

    # Build formula reference as a proper table
    formula_rows = []
    for num, name, latex in formulas:
        buf = latex_to_image(latex, fontsize=10, dpi=300)
        from PIL import Image as PILImage
        img = PILImage.open(buf)
        img_w_pt = img.width / (300 / 72)
        img_h_pt = img.height / (300 / 72)
        buf.seek(0)
        formula_rows.append([
            num, name,
            Image(buf, width=min(img_w_pt, 260), height=img_h_pt),
        ])

    ft = Table(
        [["Nr.", "Name", "Formel"]] + formula_rows,
        colWidths=[25, 80, PAGE_W - 2 * MARGIN - 110],
        repeatRows=1,
    )
    ft.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "DejaVu-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 7.5),
        ("FONTNAME", (0, 1), (1, -1), "DejaVu"),
        ("FONTSIZE", (0, 1), (1, -1), 7.5),
        ("TEXTCOLOR", (0, 0), (-1, -1), C_BODY),
        ("TEXTCOLOR", (0, 1), (0, -1), C_ACCENT),
        ("BACKGROUND", (0, 0), (-1, 0), C_TABLE_HDR),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, C_ACCENT),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, C_RULE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
    ]))
    story.append(ft)

    # ================================================================
    # ANHANG B: Glossar
    # ================================================================
    story.append(PageBreak())
    story.append(Paragraph("Anhang B: Glossar Deutsch–Englisch", S["chapter"]))

    story += make_table(
        ["Deutsch", "Englisch"],
        [
            ["Arbeitsunfähigkeit (AU)", "Work incapacity"],
            ["Beitrag", "Premium"],
            ["Beitragsbemessungsgrenze (BBG)", "Contribution assessment ceiling"],
            ["Berufsklasse (BK)", "Occupational risk class"],
            ["Berufsunfähigkeit (BU)", "Occupational disability"],
            ["Entgeltfortzahlung", "Continued pay (employer, 6 weeks)"],
            ["Karenzzeit", "Waiting period (before KTG pays)"],
            ["Krankengeld", "Statutory sickness benefit (GKV)"],
            ["Krankentagegeld (KTG)", "Daily sickness benefit (private)"],
            ["Leistungsfall", "Benefit event / claim"],
            ["Lohnfortzahlung", "Continued pay (= Entgeltfortzahlung)"],
            ["Nettoprämie", "Net premium (actuarial fair value)"],
            ["Private Krankenversicherung (PKV)", "Private health insurance"],
            ["Risikoprüfung", "Risk assessment / underwriting"],
            ["Risikoklasse", "Risk class"],
            ["Rückstellung", "Reserve (actuarial)"],
            ["Sicherheitszuschlag", "Safety loading"],
            ["Tarifgestaltung", "Tariff design / pricing"],
            ["Übergangsrate", "Transition rate (CTMC)"],
            ["Versicherungsnehmer", "Policyholder"],
            ["Vorerkrankung", "Pre-existing condition"],
            ["Zuschlag", "Premium loading / surcharge"],
        ],
        col_widths=[55, 55],
        caption="Fachbegriffe", styles=S)

    # ===== BUILD =====
    doc.build(story)
    n_pages = doc.page
    logger.info("Study Guide (DE) geschrieben: %s (%d Seiten, %d Abbildungen, %d Tabellen)",
                output_path, n_pages, _fig_n, _tbl_n)
    return Path(output_path)


if __name__ == "__main__":
    build_study_guide_de()
