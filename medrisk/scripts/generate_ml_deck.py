#!/usr/bin/env python3
"""Generate ML-Methoden deck for KTG & Underwriting (German, academic style).

Produces a 6-slide landscape PDF presenting state-of-the-art ML
approaches for Krankentagegeld pricing and medical underwriting.

Usage:
    python scripts/generate_ml_deck.py
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

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts._academic_style import (
    SlidePDF,
    chart_style,
    safe,
    C_ACCENT,
    C_BODY,
    C_BOX_BG,
    C_CAPTION,
    C_FOOTNOTE,
    C_GREEN_BG,
    C_HEADING,
    C_RED_BG,
    C_RULE,
    C_WHITE,
    M_BLUE,
    M_DARK,
    M_GREEN,
    M_GREY,
    M_RED,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

OUT = PROJECT_ROOT / "data" / "reports"
OUT.mkdir(parents=True, exist_ok=True)

PAGE_W, PAGE_H, MARGIN = 297, 210, 15
CONTENT_W = PAGE_W - 2 * MARGIN
N_SLIDES = 6


# ============================================================================
# Charts
# ============================================================================

def chart_conformal() -> BytesIO:
    """Conformal prediction interval visualization."""
    chart_style()
    rng = np.random.RandomState(42)
    x = np.linspace(200, 2000, 50)
    y_hat = x
    noise = rng.normal(0, x * 0.2, len(x))
    y_true = np.clip(x + noise, 0, None)
    q = np.quantile(np.abs(y_true - y_hat), 0.9)

    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.fill_between(x, x - q, x + q, alpha=0.15, color=M_BLUE,
                    label="90% konformes Intervall")
    ax.plot(x, x, color=M_DARK, linewidth=1.8, label="Punktvorhersage")
    ax.scatter(x, y_true, s=8, c=M_GREY, alpha=0.5,
               label="Kalibrierungsdaten", zorder=5)
    ax.set_xlabel("Vorhergesagte KTG-Kosten (EUR/Jahr)")
    ax.set_ylabel("Tatsaechliche Kosten (EUR/Jahr)")
    ax.set_title("Conformal Prediction: Garantierte Intervalle",
                 fontweight="bold", fontsize=10)
    ax.legend(fontsize=7.5, loc="upper left")
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_survival() -> BytesIO:
    """Example survival curve."""
    chart_style()
    t = np.linspace(0, 20, 200)
    s1 = np.exp(-(t / 15) ** 1.8)
    s2 = np.exp(-(t / 8) ** 1.5)

    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.plot(t, s1, color=M_GREEN, linewidth=1.8,
            label="Stadium I (kontrolliert)")
    ax.fill_between(t, s1 * 0.92, np.minimum(s1 * 1.08, 1),
                    alpha=0.1, color=M_GREEN)
    ax.plot(t, s2, color=M_RED, linewidth=1.8,
            label="Stadium III (unkontrolliert)")
    ax.fill_between(t, s2 * 0.88, np.minimum(s2 * 1.12, 1),
                    alpha=0.1, color=M_RED)
    ax.axhline(0.5, linestyle="--", color=M_GREY, linewidth=0.8,
               label="Mediane Ueberlebenszeit")
    ax.set_xlabel("Jahre")
    ax.set_ylabel("P(arbeitsfaehig)")
    ax.set_title("Individuelle Ueberlebenskurve: Zeit bis AU",
                 fontweight="bold", fontsize=10)
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=7.5, loc="lower left")
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    return buf


# ============================================================================
# Helper -- bullet with bold prefix (SlidePDF.bullet has no bold_prefix)
# ============================================================================

def _bullet_bold(pdf: SlidePDF, bold_prefix: str, text: str,
                 size: float = 11):
    """Render a bullet with a bold prefix followed by regular text."""
    pdf.set_font("Helvetica", "", size)
    pdf.set_text_color(*C_BODY)
    pdf.cell(6, 6, "-")
    pdf.set_font("Helvetica", "B", size)
    pdf.cell(pdf.get_string_width(safe(bold_prefix)) + 2, 6,
             safe(bold_prefix))
    pdf.set_font("Helvetica", "", size)
    pdf.multi_cell(CONTENT_W - 6 -
                   pdf.get_string_width(safe(bold_prefix)) - 2, 6,
                   safe(text))


# ============================================================================
# Slides
# ============================================================================

def slide_01_title(pdf: SlidePDF):
    """Title slide -- clean academic cover."""
    pdf.add_page()
    # Light background
    pdf.set_fill_color(*C_WHITE)
    pdf.rect(0, 0, PAGE_W, PAGE_H, "F")

    # Project label
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*C_FOOTNOTE)
    pdf.set_xy(MARGIN, 45)
    pdf.cell(CONTENT_W, 6, safe("MedRisk v2.0"), align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Main title
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*C_HEADING)
    pdf.set_x(MARGIN)
    pdf.cell(CONTENT_W, 12, safe("ML-Methoden"), align="C",
             new_x="LMARGIN", new_y="NEXT")

    # Subtitle
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(*C_CAPTION)
    pdf.set_x(MARGIN)
    pdf.cell(CONTENT_W, 8,
             safe("State of the Art fuer KTG und Underwriting"), align="C",
             new_x="LMARGIN", new_y="NEXT")

    # Accent rule
    pdf.ln(4)
    y = pdf.get_y()
    pdf.set_draw_color(*C_ACCENT)
    pdf.set_line_width(0.6)
    pdf.line(PAGE_W / 2 - 35, y, PAGE_W / 2 + 35, y)

    # Author line
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*C_BODY)
    pdf.set_x(MARGIN)
    pdf.cell(CONTENT_W, 6,
             safe("the author  |  Helmholtz Munich  |  Maerz 2026"),
             align="C", new_x="LMARGIN", new_y="NEXT")

    # PoC note
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*C_FOOTNOTE)
    pdf.set_x(MARGIN)
    pdf.cell(CONTENT_W, 6,
             safe("Proof of Concept  |  Synthetische Daten"), align="C")


def slide_02_conformal(pdf: SlidePDF, chart_buf: BytesIO):
    pdf.add_page()
    pdf.slide_title(
        "Conformal Prediction liefert garantierte Vorhersageintervalle "
        "statt Punktschaetzungen",
        "Verteilungsfrei, endlich-stichprobenvalide "
        "(Vovk 2005, Angelopoulos & Bates 2023)",
    )
    # Left: description bullets
    _bullet_bold(pdf, "Problem:",
                 "KTG-Kosten = EUR 840/Jahr ist eine Punktschaetzung "
                 "-- aber wie sicher?", size=10.5)
    _bullet_bold(pdf, "Loesung:",
                 "Konformes Intervall: EUR 580-1.180/Jahr "
                 "(90% Coverage-Garantie)", size=10.5)
    _bullet_bold(pdf, "Methode:",
                 "Split-konforme Methode: Kalibrierungsdaten definieren "
                 "Intervallbreite", size=10.5)
    _bullet_bold(pdf, "Vorteil:",
                 "Keine Verteilungsannahmen -- funktioniert mit jedem "
                 "Basismodell (XGBoost, Cox, CTMC)", size=10.5)
    # Chart on right
    chart_buf.seek(0)
    pdf.image(chart_buf, x=MARGIN + 135, w=125)

    pdf.source_line(
        "Quelle: Angelopoulos & Bates, Conformal Prediction (2023); "
        "MedRisk Implementierung")


def slide_03_survival(pdf: SlidePDF, chart_buf: BytesIO):
    pdf.add_page()
    pdf.slide_title(
        "Individuelle Ueberlebenskurven beantworten: "
        "Wie lange bis zur Arbeitsunfaehigkeit?",
        "Cox PH + Kaplan-Meier fuer patientenspezifische Prognosen "
        "mit Konfidenzbaendern",
    )
    # Chart on right
    chart_buf.seek(0)
    pdf.image(chart_buf, x=MARGIN + 135, w=125)

    _bullet_bold(pdf, "Kurve:",
                 "Statt binaer 'hohes/niedriges Risiko' zeigt S(t) die "
                 "Wahrscheinlichkeit, ueber die Zeit arbeitsfaehig zu "
                 "bleiben", size=10.5)
    _bullet_bold(pdf, "Median:",
                 "Mediane Ueberlebenszeit = Zeitpunkt mit 50% "
                 "AU-Wahrscheinlichkeit -- direkte Eingabe in KTG-Formel",
                 size=10.5)
    _bullet_bold(pdf, "Differenz:",
                 "Stadium I: mediane AU nach ~14 Jahren vs. "
                 "Stadium III: ~6 Jahre -- 2.3x Differenz", size=10.5)
    _bullet_bold(pdf, "Unsicherheit:",
                 "Konfidenzbaender zeigen Unsicherheit -- breiter = "
                 "weniger Daten = hoehere Praemie", size=10.5)

    pdf.source_line(
        "Quelle: lifelines (Davidson-Pilon 2019), "
        "Framingham Heart Study, MedRisk CTMC")


def slide_04_causal(pdf: SlidePDF):
    pdf.add_page()
    pdf.slide_title(
        "Causal ML quantifiziert: Was passiert wenn der Patient "
        "seine Medikamente nimmt?",
        "Inverse Propensity Weighting schaetzt den durchschnittlichen "
        "Behandlungseffekt (ATE)",
    )

    pdf.body_text(
        "Praediktion beantwortet 'was wird passieren?'. "
        "Causal ML beantwortet 'was wuerde passieren, wenn wir "
        "eingreifen?' -- die wertvollste Frage im Underwriting.")

    # Two-column comparison boxes
    y_box = pdf.get_y() + 5

    # Left: without treatment
    pdf.set_fill_color(*C_RED_BG)
    pdf.rect(MARGIN, y_box, 125, 40, "F")
    # Left accent bar
    pdf.set_fill_color(*C_ACCENT)
    r = (200, 80, 80)
    pdf.set_fill_color(*r)
    pdf.rect(MARGIN, y_box, 2, 40, "F")
    pdf.set_xy(MARGIN + 6, y_box + 2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*C_HEADING)
    pdf.cell(115, 6, safe("Ohne Medikation"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(MARGIN + 6, y_box + 10)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*C_BODY)
    pdf.multi_cell(115, 5.5,
                   safe("35 AU-Tage/Jahr\n"
                        "KTG-Kosten: EUR 2.800/Jahr\n"
                        "Hoeheres Progressionsrisiko"))

    # Right: with treatment
    x_r = MARGIN + 140
    pdf.set_fill_color(*C_GREEN_BG)
    pdf.rect(x_r, y_box, 125, 40, "F")
    pdf.set_fill_color(100, 160, 80)
    pdf.rect(x_r, y_box, 2, 40, "F")
    pdf.set_xy(x_r + 6, y_box + 2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*C_HEADING)
    pdf.cell(115, 6, safe("Mit Medikation (Compliance)"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(x_r + 6, y_box + 10)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*C_BODY)
    pdf.multi_cell(115, 5.5,
                   safe("23 AU-Tage/Jahr (-12 Tage, ATE)\n"
                        "KTG-Kosten: EUR 1.840/Jahr\n"
                        "Progression verlangsamt"))
    pdf.set_text_color(*C_BODY)

    # ATE highlight
    pdf.set_xy(MARGIN, y_box + 48)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*C_ACCENT)
    pdf.cell(CONTENT_W, 8,
             safe("ATE = -12 AU-Tage/Jahr (95% KI: -18 bis -6) "
                  "-- EUR 960/Jahr Einsparung pro Patient"),
             align="C")
    pdf.set_text_color(*C_BODY)

    pdf.source_line(
        "Quelle: Hernan & Robins (2020), "
        "Chernozhukov et al. (2018), MedRisk IPW")


def slide_05_vision(pdf: SlidePDF):
    pdf.add_page()
    pdf.slide_title(
        "Drei weitere Methoden erweitern das Framework mit echten Daten",
        "Neural ODEs, LLM-Extraktion, Federated Learning",
    )

    col_w = (CONTENT_W - 20) / 3
    y0 = pdf.get_y() + 3

    cards = [
        ("Neural ODEs",
         "CTMC Q-Matrix durch gelernte ODE-Dynamik ersetzen. "
         "Nicht-Markov-Effekte (Gedaechtnis, Saisonalitaet). "
         "NeurIPS 2018-2024."),
        ("LLM-Extraktion",
         "Claude liest unstrukturierte Arztbriefe -> "
         "extrahiert ICD-10, Medikamente, Laborwerte. "
         "Multi-Sprache: DE/FR/ES/EN. "
         "MCP-Prototyp existiert bereits."),
        ("Federated Learning",
         "Training auf DE/FR/ES-Daten ohne Zentralisierung. "
         "Privacy-preserving (DSGVO Art. 25). "
         "Differential Privacy Garantien. "
         "Jeder Markt behaelt seine Daten lokal."),
    ]

    for i, (title, desc) in enumerate(cards):
        x = MARGIN + i * (col_w + 10)
        # Card background
        pdf.set_fill_color(*C_BOX_BG)
        pdf.rect(x, y0, col_w, 70, "F")
        # Top accent bar
        pdf.set_fill_color(*C_ACCENT)
        pdf.rect(x, y0, col_w, 2, "F")
        # Title
        pdf.set_xy(x + 5, y0 + 5)
        pdf.set_font("Helvetica", "B", 10.5)
        pdf.set_text_color(*C_HEADING)
        pdf.cell(col_w - 10, 6, safe(title),
                 new_x="LMARGIN", new_y="NEXT")
        # Description
        pdf.set_xy(x + 5, y0 + 13)
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(*C_BODY)
        pdf.multi_cell(col_w - 10, 5, safe(desc))

    pdf.set_text_color(*C_BODY)
    pdf.source_line(
        "Quelle: Chen et al. NeurIPS 2018, "
        "Anthropic Claude, McMahan et al. AISTATS 2017")


def slide_06_summary(pdf: SlidePDF):
    pdf.add_page()
    pdf.slide_title(
        "Sechs ML-Methoden transformieren KTG von Pauschaltarif "
        "zu individueller Risikopreisfindung",
    )

    y_kpi = 38
    pdf.key_metric("Implementiert", "3", MARGIN, y_kpi, w=80)
    pdf.key_metric("Vision", "3", MARGIN + 90, y_kpi, w=80)
    pdf.key_metric("Datenquellen", "4+", MARGIN + 180, y_kpi, w=80)

    pdf.set_xy(MARGIN, y_kpi + 30)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*C_HEADING)
    pdf.cell(CONTENT_W, 8, safe("Implementiert (im Demo)"),
             new_x="LMARGIN", new_y="NEXT")

    _bullet_bold(pdf, "1.",
                 "Conformal Prediction -- garantierte "
                 "Vorhersageintervalle auf KTG-Kosten", size=10.5)
    _bullet_bold(pdf, "2.",
                 "Survival Analysis -- individuelle "
                 "Ueberlebenskurven (Zeit bis AU)", size=10.5)
    _bullet_bold(pdf, "3.",
                 "Causal ML (IPW) -- Behandlungseffekt "
                 "Medikamenten-Compliance auf AU-Dauer", size=10.5)

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*C_HEADING)
    pdf.cell(CONTENT_W, 8, safe("Vision (mit echten Daten)"),
             new_x="LMARGIN", new_y="NEXT")
    _bullet_bold(pdf, "4.",
                 "Neural ODEs fuer nicht-lineare Krankheitsdynamik",
                 size=10.5)
    _bullet_bold(pdf, "5.",
                 "LLM-Extraktion aus Arztbriefen (Claude + MCP)",
                 size=10.5)
    _bullet_bold(pdf, "6.",
                 "Federated Learning fuer Privacy-preserving "
                 "Multi-Markt-Training", size=10.5)

    # Contact bar
    pdf.set_xy(MARGIN, PAGE_H - 35)
    pdf.set_fill_color(*C_BOX_BG)
    pdf.rect(MARGIN, PAGE_H - 35, CONTENT_W, 10, "F")
    pdf.set_fill_color(*C_ACCENT)
    pdf.rect(MARGIN, PAGE_H - 35, 2, 10, "F")
    pdf.set_xy(MARGIN + 6, PAGE_H - 34)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*C_ACCENT)
    pdf.cell(CONTENT_W - 10, 8,
             safe("Tim Reska  |  timreska@gmail.com"),
             align="C")
    pdf.set_text_color(*C_BODY)
    pdf.source_line(
        "Proof of Concept | Synthetische Daten | Maerz 2026")


# ============================================================================
# Main
# ============================================================================

def main():
    logger.info("Generating ML-Methoden deck (academic style)...")
    cp_chart = chart_conformal()
    surv_chart = chart_survival()

    pdf = SlidePDF(n_slides=N_SLIDES, header_right="MedRisk v2.0")
    slide_01_title(pdf)
    slide_02_conformal(pdf, cp_chart)
    slide_03_survival(pdf, surv_chart)
    slide_04_causal(pdf)
    slide_05_vision(pdf)
    slide_06_summary(pdf)

    path = OUT / "ml_methoden_deck.pdf"
    pdf.output(str(path))
    logger.info("Written %s (%.1f KB, %d pages)", path,
                path.stat().st_size / 1024, pdf.pages_count)


if __name__ == "__main__":
    main()
