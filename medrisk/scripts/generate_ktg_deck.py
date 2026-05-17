#!/usr/bin/env python3
"""Generate Krankentagegeld-Kalkulation deck (Hypertonie-Beispiel).

Produces a 7-slide landscape PDF with academic/scientific styling,
including a CTMC state-occupation chart from the existing cardiovascular
disease model.

Usage:
    python scripts/generate_ktg_deck.py
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

# Ensure project root is on path
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
    C_TABLE_ALT,
    C_TABLE_HDR,
    C_WHITE,
    M_BLUE,
    M_GREEN,
    M_AMBER,
    M_RED,
    M_DARK,
)
from medrisk.models.disease_configs import CARDIOVASCULAR_CONFIG
from medrisk.models.multistate import MultistateModel

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

OUT = PROJECT_ROOT / "data" / "reports"
OUT.mkdir(parents=True, exist_ok=True)

# Layout constants
PAGE_W = 297
PAGE_H = 210
MARGIN = 15
CONTENT_W = PAGE_W - 2 * MARGIN
N_SLIDES = 7


# ============================================================================
# Chart: CV state-occupation probabilities (30 years)
# ============================================================================

def chart_cv_progression() -> BytesIO:
    """Generate stacked area chart of CV CTMC state probabilities."""
    chart_style()

    cfg = CARDIOVASCULAR_CONFIG
    Q = np.zeros((cfg.n_states, cfg.n_states))
    for (i, j), rate in cfg.default_intensities.items():
        Q[i, j] = rate
    for i in range(cfg.n_states):
        Q[i, i] = -sum(Q[i, j] for j in range(cfg.n_states) if j != i)

    model = MultistateModel(n_states=cfg.n_states, absorbing_states=cfg.absorbing_states)
    model.Q = Q

    times = np.linspace(0, 30, 300)
    probs = model.state_occupation_probabilities(1, times)  # start in state 1 (risk factors)

    de_labels = [
        "Gesund", "Risikofaktoren", "Chronisch",
        "Komplikation", "Schweres Ereignis",
    ]
    colors = [M_GREEN, M_BLUE, M_AMBER, M_RED, M_DARK]

    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.stackplot(times, probs.T, labels=de_labels, colors=colors, alpha=0.75)
    ax.set_xlabel("Jahre nach Erstdiagnose", fontsize=9)
    ax.set_ylabel("Aufenthaltswahrscheinlichkeit", fontsize=9)
    ax.set_title("Krankheitsverlauf Hypertonie -- CTMC 5 Stadien",
                 fontweight="bold", fontsize=10)
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 1)
    ax.legend(loc="upper right", fontsize=7)
    fig.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    return buf


# ============================================================================
# Slides
# ============================================================================

def slide_01_title(pdf: SlidePDF) -> None:
    """Title slide."""
    pdf.add_page()

    # Clean academic cover -- white background, centred text
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*C_FOOTNOTE)
    pdf.set_xy(MARGIN, 45)
    pdf.cell(CONTENT_W, 5, safe("MedRisk-ADH v2.0"), align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*C_HEADING)
    pdf.set_x(MARGIN)
    pdf.cell(CONTENT_W, 14, safe("Krankentagegeld-Kalkulation"), align="C",
             new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(*C_BODY)
    pdf.set_x(MARGIN)
    pdf.cell(CONTENT_W, 10, safe("am Beispiel Hypertonie"), align="C",
             new_x="LMARGIN", new_y="NEXT")

    # Accent divider
    pdf.ln(4)
    y = pdf.get_y()
    pdf.set_draw_color(*C_ACCENT)
    pdf.set_line_width(0.6)
    pdf.line(PAGE_W / 2 - 35, y, PAGE_W / 2 + 35, y)
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*C_BODY)
    pdf.set_x(MARGIN)
    pdf.cell(CONTENT_W, 6, safe("the author  |  Helmholtz Munich"), align="C",
             new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*C_CAPTION)
    pdf.set_x(MARGIN)
    pdf.cell(CONTENT_W, 6,
             safe("Proof of Concept  |  Synthetische Daten  |  Maerz 2026"),
             align="C")


def slide_02_ktg_basics(pdf: SlidePDF) -> None:
    """Was ist Krankentagegeld?"""
    pdf.add_page()
    pdf.slide_title(
        "KTG zahlt ab dem 43. Tag der Arbeitsunfaehigkeit -- "
        "die Kalkulation erfordert individuelle Risikoschaetzung",
    )

    pdf.body_text(
        "Krankentagegeld (KTG) ueberbrueckt den Einkommensverlust bei laengerer "
        "Arbeitsunfaehigkeit. Die Praemienkalkulation haengt von drei Groessen ab: "
        "der Wahrscheinlichkeit einer AU, der erwarteten Dauer und dem vereinbarten "
        "Tagessatz."
    )

    # KPI boxes
    y_kpi = pdf.get_y() + 4
    pdf.key_metric("Karenzzeit", "42 d", MARGIN, y_kpi, w=80)
    pdf.key_metric("Max. Leistungsdauer", "78 Wo", MARGIN + 90, y_kpi, w=80)
    pdf.key_metric("Netto-Tagessatz", "70-90%", MARGIN + 180, y_kpi, w=80)

    # Formula
    pdf.set_xy(MARGIN, y_kpi + 30)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*C_ACCENT)
    pdf.cell(CONTENT_W, 10,
             safe("KTG-Praemie  ~  P(AU)  x  E[Dauer_AU]  x  Tagessatz"),
             align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(MARGIN, pdf.get_y() + 2)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*C_CAPTION)
    pdf.cell(CONTENT_W, 5,
             safe("P(AU) = Wahrscheinlichkeit der Arbeitsunfaehigkeit  |  "
                  "E[Dauer] = erwartete AU-Dauer in Tagen"),
             align="C")
    pdf.set_text_color(*C_BODY)

    pdf.source_line("Quelle: SGB V Sec.44, VVG Sec.192, PKV-Verband Musterbedingungen")

    # Bottom insight line
    _insight_line(pdf,
                  "Individuelle Risikomerkmale bestimmen alle drei Kalkulationsgroessen")


def slide_03_why_hypertonie(pdf: SlidePDF) -> None:
    """Warum Hypertonie?"""
    pdf.add_page()
    pdf.slide_title(
        "Hypertonie betrifft 30% der Erwachsenen -- "
        "das AU-Risiko variiert 8-fach je nach Stadium",
    )

    pdf.bullet(
        "Praevalenz: 30% Praevalenz in DE (RKI DEGS1 2012) -- "
        "haeufigste chronische Erkrankung in der KTG-Kalkulation",
    )
    pdf.bullet(
        "AU-Relevanz: ICD-10 I10 (Essentielle Hypertonie) ist eine der "
        "haeufigsten Einzeldiagnosen bei AU-Bescheinigungen",
    )
    pdf.bullet(
        "Progression: Kontrolliert (Stadium I) -> Unkontrolliert (II) -> "
        "Organschaeden (III) -> Kardiovaskulaeres Ereignis (IV)",
    )
    pdf.bullet(
        "Varianz: Das AU-Risiko steigt von ~3% (Stadium I) auf ~80% "
        "(Stadium IV) -- pauschale Tarife ignorieren diese Varianz",
    )

    # Comparison boxes
    y_box = pdf.get_y() + 6
    _comparison_box(
        pdf, MARGIN, y_box, 125, 35,
        C_GREEN_BG, C_ACCENT,
        "Kontrollierte Hypertonie (Stadium I)",
        "3 Antihypertensiva, RR 135/85 mmHg\n"
        "AU-Risiko: ~3%/Jahr, E[Dauer]: 14 Tage\n"
        "KTG-Risiko: niedrig",
    )
    _comparison_box(
        pdf, MARGIN + 140, y_box, 125, 35,
        C_RED_BG, (200, 80, 80),
        "Unkontrollierte Hypertonie (Stadium III)",
        "Keine Medikation, RR 175/110 mmHg\n"
        "AU-Risiko: ~35%/Jahr, E[Dauer]: 42 Tage\n"
        "KTG-Risiko: hoch",
    )

    pdf.source_line("Quelle: RKI DEGS1 2012, GBD 2019, BfArM AU-Statistik 2023")
    _insight_line(pdf,
                  "Gleiche Diagnose, gleicher ICD-Code -- aber 8-fach unterschiedliches KTG-Risiko")


def slide_04_ctmc(pdf: SlidePDF, chart_buf: BytesIO) -> None:
    """CTMC-Modell fuer Krankheitsverlauf."""
    pdf.add_page()
    pdf.slide_title(
        "Ein 5-Stadien-Markov-Modell berechnet stadienspezifische "
        "AU-Wahrscheinlichkeiten ueber 30 Jahre",
    )

    # Chart on the right
    chart_buf.seek(0)
    pdf.image(chart_buf, x=MARGIN + 130, w=130)

    # Table on the left
    pdf.set_xy(MARGIN, 42)
    pdf._tbl_n += 1
    pdf.set_font("Helvetica", "BI", 8)
    pdf.set_text_color(*C_CAPTION)
    pdf.cell(125, 5,
             safe(f"Table {pdf._tbl_n}. AU-Risiko nach Krankheitsstadium"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*C_BODY)
    pdf.ln(1)

    # Table header
    col_w = [55, 30, 30]
    headers = ["Stadium", "P(AU/Jahr)", "E[Dauer]"]
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(*C_TABLE_HDR)
    pdf.set_text_color(*C_HEADING)
    pdf.set_draw_color(*C_RULE)
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 6, safe(h), border="TB", fill=True,
                 align="C" if i > 0 else "L")
    pdf.ln()

    # Table rows
    rows = [
        ("Risikofaktoren (I)", "3%", "14 Tage"),
        ("Chronisch (II)", "12%", "28 Tage"),
        ("Komplikation (III)", "35%", "42 Tage"),
        ("Schweres Ereignis (IV)", "80%", "120 Tage"),
    ]

    pdf.set_font("Helvetica", "", 8)
    for ri, (stadium, p_au, dauer) in enumerate(rows):
        pdf.set_x(MARGIN)
        if ri % 2 == 0:
            pdf.set_fill_color(*C_TABLE_ALT)
        else:
            pdf.set_fill_color(*C_WHITE)
        pdf.set_text_color(*C_BODY)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(col_w[0], 5.5, safe(stadium), border="B", fill=True, align="L")
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(col_w[1], 5.5, safe(p_au), border="B", fill=True, align="C")
        pdf.cell(col_w[2], 5.5, safe(dauer), border="B", fill=True, align="C")
        pdf.ln()

    pdf.set_text_color(*C_BODY)

    # Note below table
    pdf.set_xy(MARGIN, pdf.get_y() + 4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*C_CAPTION)
    pdf.multi_cell(125, 4.5,
                   safe("CTMC = Continuous-Time Markov Chain. "
                        "Uebergangsraten aus Framingham Heart Study "
                        "und SCORE2-Risikotabellen."))
    pdf.set_text_color(*C_BODY)

    pdf.source_line("Quelle: MedRisk-ADH CTMC, Framingham Heart Study, SCORE2 (ESC 2021)")
    _insight_line(pdf,
                  "Jedes Stadium hat eigene AU-Wahrscheinlichkeit und erwartete Dauer")


def slide_05_beispiel(pdf: SlidePDF) -> None:
    """Beispielrechnung: konkreter Patient."""
    pdf.add_page()
    pdf.slide_title(
        "Fuer einen 50-jaehrigen Hypertoniker im Stadium II "
        "ergibt sich ein jaehrliches KTG-Risiko von ~EUR840",
    )

    # Patient profile
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*C_HEADING)
    pdf.cell(CONTENT_W, 6, safe("Patientenprofil"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(*C_BODY)
    pdf.cell(CONTENT_W, 6,
             safe("50 Jahre, maennlich, BMI 28, Hypertonie Stadium II (chronisch), "
                  "3 Medikamente, Tagessatz EUR80"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Calculation table
    col_w = [55, 40, 30, 30, 30, 42]
    headers = ["Stadium", "P(in 5 Jahren)", "P(AU)", "E[Dauer]",
               "EUR/Tag", "Erwartete Kosten"]

    pdf._tbl_n += 1
    pdf.set_font("Helvetica", "BI", 8)
    pdf.set_text_color(*C_CAPTION)
    pdf.cell(sum(col_w), 5,
             safe(f"Table {pdf._tbl_n}. KTG-Kalkulation nach Stadien"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*C_BODY)
    pdf.ln(1)

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(*C_TABLE_HDR)
    pdf.set_text_color(*C_HEADING)
    pdf.set_draw_color(*C_RULE)
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 6, safe(h), border="TB", fill=True,
                 align="C" if i > 0 else "L")
    pdf.ln()

    rows = [
        ("Risikofaktoren (I)", "10%", "3%", "14 d", "EUR80", "EUR3"),
        ("Chronisch (II)", "60%", "12%", "28 d", "EUR80", "EUR161"),
        ("Komplikation (III)", "25%", "35%", "42 d", "EUR80", "EUR294"),
        ("Schweres Ereignis (IV)", "5%", "80%", "120 d", "EUR80", "EUR384"),
    ]

    pdf.set_font("Helvetica", "", 8)
    for ri, row in enumerate(rows):
        pdf.set_x(MARGIN)
        if ri % 2 == 0:
            pdf.set_fill_color(*C_TABLE_ALT)
        else:
            pdf.set_fill_color(*C_WHITE)
        pdf.set_text_color(*C_BODY)
        for i, val in enumerate(row):
            if i == 0:
                pdf.set_font("Helvetica", "B", 8)
            else:
                pdf.set_font("Helvetica", "", 8)
            pdf.cell(col_w[i], 5.5, safe(val), border="B", fill=True,
                     align="C" if i > 0 else "L")
        pdf.ln()

    # Total row
    pdf.set_x(MARGIN)
    pdf.set_fill_color(*C_ACCENT)
    pdf.set_text_color(*C_WHITE)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(col_w[0], 6, safe("Gesamt (gewichtet)"), border="TB", fill=True,
             align="L")
    for i in range(1, 5):
        pdf.cell(col_w[i], 6, "", border="TB", fill=True, align="C")
    pdf.cell(col_w[5], 6, safe("EUR839/Jahr"), border="TB", fill=True, align="C")
    pdf.ln()
    pdf.set_text_color(*C_BODY)

    # Premium calculation
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*C_ACCENT)
    pdf.cell(CONTENT_W, 8,
             safe("KTG-Monatspraemie (inkl. Sicherheits- und Kostenzuschlaege): "
                  "~EUR95-110 / Monat"),
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*C_BODY)

    pdf.ln(2)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*C_CAPTION)
    pdf.cell(CONTENT_W, 5,
             safe("Berechnung: EUR839 x 1.15 (Sicherheitszuschlag) x 1.12 "
                  "(Verwaltung/Provision) / 12 Monate ~ EUR105/Monat"),
             align="C")
    pdf.set_text_color(*C_BODY)

    pdf.source_line("Quelle: MedRisk-ADH Modellrechnung, synthetische Daten, "
                    "DAV-Sterbetafel 2004 T")
    _insight_line(pdf,
                  "Stadienspezifische Kalkulation statt Pauschaltarif -- "
                  "jeder Patient erhaelt eine risikoadaequate Praemie")


def slide_06_dqs(pdf: SlidePDF) -> None:
    """Datenqualitaet bestimmt die Preissicherheit."""
    pdf.add_page()
    pdf.slide_title(
        "Ohne DQS-Pruefung werden kontrollierte und unkontrollierte "
        "Hypertoniker gleich kalkuliert",
    )

    pdf.body_text(
        "Die Stadienzuordnung haengt von der Datenlage ab. Ohne Medikamenten- "
        "und Labordaten kann nicht zwischen kontrollierter und unkontrollierter "
        "Hypertonie unterschieden werden."
    )

    y_box = pdf.get_y() + 2

    # Left column: complete data
    _list_box(
        pdf, MARGIN, y_box, 125, 58,
        C_GREEN_BG, C_ACCENT,
        "Vollstaendige Akte (DQS 0.85)",
        [
            "3 Antihypertensiva dokumentiert",
            "RR 135/85 mmHg (letzte 6 Monate)",
            "HbA1c, Lipidprofil vorhanden",
            "Stadium II gesichert",
            "KTG-Praemie: EUR105/Monat",
        ],
        marker="+",
    )

    # Right column: sparse data
    _list_box(
        pdf, MARGIN + 140, y_box, 125, 58,
        C_RED_BG, (200, 80, 80),
        "Lueckenhafte Akte (DQS 0.40)",
        [
            "Keine Medikamentendaten",
            "Kein Blutdruck dokumentiert",
            "Nur 1 Diagnose: I10",
            "Stadium unklar (I? II? III?)",
            "KTG-Praemie: ???",
        ],
        marker="-",
    )

    # Insight below boxes
    pdf.set_xy(MARGIN, y_box + 64)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*C_ACCENT)
    pdf.cell(CONTENT_W, 6,
             safe("Ergebnis: 3x Risikovarianz bei identischem ICD-Code -- "
                  "DQS erkennt dies vor der Kalkulation"),
             align="C")
    pdf.set_text_color(*C_BODY)

    pdf.source_line("Quelle: MedRisk-ADH DQS v2, synthetische Patientendaten")
    _insight_line(pdf,
                  "Datenqualitaet ist kein Metadaten-Problem -- "
                  "sie bestimmt direkt die Praemienhoehe")


def slide_07_summary(pdf: SlidePDF) -> None:
    """Zusammenfassung & Naechste Schritte."""
    pdf.add_page()
    pdf.slide_title(
        "Stadienspezifische KTG-Kalkulation mit DQS senkt "
        "Fehlkalkulation um geschaetzt 15-25%",
    )

    # KPI boxes
    y_kpi = 40
    pdf.key_metric("Praevalenz DE", "30%", MARGIN, y_kpi, w=80)
    pdf.key_metric("AU-Varianz", "8x", MARGIN + 90, y_kpi, w=80)
    pdf.key_metric("Weniger Fehlkalk.", "15-25%", MARGIN + 180, y_kpi, w=80)

    # Next steps
    pdf.set_xy(MARGIN, y_kpi + 30)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*C_HEADING)
    pdf.cell(CONTENT_W, 7, safe("Naechste Schritte"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    pdf.bullet(
        "Validierung: Retrospektive Validierung mit echten KTG-Schadensdaten "
        "(InGef, GePaRD oder PKV-Verband)",
    )
    pdf.bullet(
        "Kalibrierung: Kalibrierung der AU-Wahrscheinlichkeiten gegen reale "
        "AU-Bescheinigungen und Leistungsfaelle",
    )
    pdf.bullet(
        "Skalierung: Erweiterung auf weitere Indikationen: Diabetes (E11), "
        "Ruecken (M54), Depression (F32)",
    )
    pdf.bullet(
        "Integration: Integration in bestehende Tarifkalkulation als "
        "zusaetzlicher Risikoparameter",
    )

    # Contact bar -- subtle box at bottom
    pdf.set_xy(MARGIN, PAGE_H - 32)
    pdf.set_fill_color(*C_BOX_BG)
    pdf.rect(MARGIN, PAGE_H - 32, CONTENT_W, 10, "F")
    pdf.set_fill_color(*C_ACCENT)
    pdf.rect(MARGIN, PAGE_H - 32, 2, 10, "F")
    pdf.set_xy(MARGIN + 6, PAGE_H - 31)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*C_ACCENT)
    pdf.cell(CONTENT_W - 10, 8,
             safe("Tim Reska  |  timreska@gmail.com"),
             align="L")
    pdf.set_text_color(*C_BODY)

    pdf.source_line("Proof of Concept | Synthetische Daten | Maerz 2026")


# ============================================================================
# Helpers
# ============================================================================

def _insight_line(pdf: SlidePDF, text: str) -> None:
    """Render a subtle insight line near the bottom of a slide."""
    y = PAGE_H - 20
    pdf.set_draw_color(*C_ACCENT)
    pdf.set_line_width(0.4)
    pdf.line(MARGIN, y, MARGIN + 50, y)
    pdf.set_draw_color(*C_RULE)
    pdf.set_line_width(0.2)
    pdf.line(MARGIN + 50, y, PAGE_W - MARGIN, y)
    pdf.set_xy(MARGIN, y + 1)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(*C_ACCENT)
    pdf.cell(CONTENT_W, 4, safe(text), align="C")
    pdf.set_text_color(*C_BODY)


def _comparison_box(pdf: SlidePDF, x: float, y: float, w: float, h: float,
                    bg_color: tuple, accent_color: tuple,
                    title: str, body: str) -> None:
    """Draw a comparison box with accent bar, title and body text."""
    pdf.set_fill_color(*bg_color)
    pdf.rect(x, y, w, h, "F")
    pdf.set_fill_color(*accent_color)
    pdf.rect(x, y, 2, h, "F")

    pdf.set_xy(x + 6, y + 2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*accent_color)
    pdf.cell(w - 10, 6, safe(title), new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(x + 6, y + 10)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*C_BODY)
    pdf.multi_cell(w - 10, 5, safe(body))


def _list_box(pdf: SlidePDF, x: float, y: float, w: float, h: float,
              bg_color: tuple, accent_color: tuple,
              title: str, items: list[str], marker: str = "-") -> None:
    """Draw a box with title and bulleted list items."""
    pdf.set_fill_color(*bg_color)
    pdf.rect(x, y, w, h, "F")
    pdf.set_fill_color(*accent_color)
    pdf.rect(x, y, 2, h, "F")

    pdf.set_xy(x + 6, y + 2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*accent_color)
    pdf.cell(w - 10, 6, safe(title), new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(x + 6, y + 11)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*C_BODY)
    for item in items:
        pdf.set_x(x + 8)
        pdf.cell(4, 5.5, marker)
        pdf.cell(w - 16, 5.5, safe(f"  {item}"), new_x="LMARGIN", new_y="NEXT")


# ============================================================================
# Main
# ============================================================================

def main() -> None:
    logger.info("Generating KTG Hypertonie deck...")

    # Generate chart
    chart_buf = chart_cv_progression()

    # Build deck
    pdf = SlidePDF(n_slides=N_SLIDES, header_right="MedRisk-ADH v2.0")
    slide_01_title(pdf)
    slide_02_ktg_basics(pdf)
    slide_03_why_hypertonie(pdf)
    slide_04_ctmc(pdf, chart_buf)
    slide_05_beispiel(pdf)
    slide_06_dqs(pdf)
    slide_07_summary(pdf)

    path = OUT / "ktg_hypertonie_deck.pdf"
    pdf.output(str(path))
    logger.info("Written %s (%.1f KB, %d pages)", path, path.stat().st_size / 1024, pdf.pages_count)


if __name__ == "__main__":
    main()
