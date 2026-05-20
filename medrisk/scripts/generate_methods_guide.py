#!/usr/bin/env python3
"""Methods Guide: DQS fuer Nicht-Mathematiker.

Erzeugt eine ~10-seitige PDF, die den Data Quality Score (DQS) und die
PBW-Erkennung verstaendlich erklaert -- mit Alltagsanalogien, konkreten
Beispielen und Visualisierungen.

Usage:
    python scripts/generate_methods_guide.py
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

from scripts._academic_style import (
    AcademicPDF, chart_style, safe,
    C_ACCENT, C_BODY, C_BOX_BG, C_CAPTION, C_FOOTNOTE, C_HEADING,
    C_RULE, C_TABLE_HDR, C_WHITE, C_GREEN_BG, C_RED_BG,
    M_BLUE, M_AMBER, M_GREEN, M_RED, M_DARK, M_GREY,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

OUT = PROJECT_ROOT / "data" / "reports"
OUT.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Charts
# ============================================================================

def chart_dqs_components() -> BytesIO:
    """Stacked bar showing DQS component weights."""
    chart_style()
    fig, ax = plt.subplots(figsize=(5.5, 2.5))
    components = ["Vollstaendigkeit\n(C)", "Konsistenz\n(S)", "Aktualitaet\n(R)"]
    weights = [0.40, 0.35, 0.25]
    colors = [M_BLUE, M_AMBER, M_GREEN]
    bars = ax.barh(components, weights, color=colors, alpha=0.8, height=0.6)
    for bar, w in zip(bars, weights):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{w:.0%}", va="center", fontsize=9, fontweight="bold")
    ax.set_xlim(0, 0.55)
    ax.set_xlabel("Gewicht im DQS", fontsize=9)
    ax.set_title("Die drei Saeulen des Data Quality Score", fontsize=10, fontweight="bold")
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_traffic_light() -> BytesIO:
    """Traffic light visualization for DQS tiers."""
    chart_style()
    fig, ax = plt.subplots(figsize=(6, 2.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Three zones
    zones = [
        (0.0, 0.60, "#E15759", "Rot: < 0.60\nSTOPP", "white"),
        (0.60, 0.80, "#ED7D31", "Gelb: 0.60-0.80\nManuell pruefen", "white"),
        (0.80, 1.00, "#70AD47", "Gruen: >= 0.80\nAutomatisch", "white"),
    ]
    for x0, x1, color, label, tc in zones:
        width = x1 - x0
        rect = mpatches.FancyBboxPatch((x0 + 0.005, 0.15), width - 0.01, 0.7,
                                        boxstyle="round,pad=0.02",
                                        facecolor=color, alpha=0.85, edgecolor="none")
        ax.add_patch(rect)
        ax.text((x0 + x1) / 2, 0.5, label, ha="center", va="center",
                fontsize=9, color=tc, fontweight="bold")

    # Scale markers
    for v in [0.0, 0.20, 0.40, 0.60, 0.80, 1.0]:
        ax.text(v, 0.02, f"{v:.1f}", ha="center", fontsize=7, color="#666")

    ax.set_title("DQS-Ampelsystem", fontsize=10, fontweight="bold", pad=10)
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_recency_decay() -> BytesIO:
    """Exponential decay curve for lab recency."""
    chart_style()
    fig, ax = plt.subplots(figsize=(5.5, 3))
    half_life = 1.4
    decay_rate = np.log(2) / half_life
    years = np.linspace(0, 6, 200)
    weight = np.exp(-decay_rate * years)

    ax.fill_between(years, weight, alpha=0.15, color=M_BLUE)
    ax.plot(years, weight, color=M_BLUE, linewidth=2)

    # Annotate key points
    for y_val, label in [(1.4, "50%"), (2.8, "25%"), (4.2, "12.5%")]:
        w = np.exp(-decay_rate * y_val)
        ax.plot(y_val, w, "o", color=M_RED, markersize=6, zorder=5)
        ax.annotate(f"{y_val:.1f} J -> {w:.0%}", xy=(y_val, w),
                    xytext=(y_val + 0.3, w + 0.08),
                    fontsize=8, color=M_RED,
                    arrowprops=dict(arrowstyle="->", color=M_RED, lw=0.8))

    ax.axhline(0.5, color=M_GREY, linestyle=":", alpha=0.5)
    ax.set_xlabel("Alter des Laborwerts (Jahre)", fontsize=9)
    ax.set_ylabel("Gewicht im DQS", fontsize=9)
    ax.set_title("Aktualitaet: Exponentieller Zerfall (Halbwertszeit = 1.4 Jahre)", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 6)
    ax.set_ylim(0, 1.05)
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_pbw_scatter() -> BytesIO:
    """PBW detection scatter: Confidence vs DQS."""
    chart_style()
    rng = np.random.default_rng(42)
    n = 80
    fig, ax = plt.subplots(figsize=(5.5, 3.8))

    for market, dqs_m, dqs_s, col, mk, label in [
        ("DE", 0.85, 0.08, M_BLUE, "o", "Deutschland"),
        ("FR", 0.78, 0.10, M_GREEN, "s", "Frankreich"),
        ("ES", 0.65, 0.12, M_AMBER, "^", "Spanien"),
        ("INT", 0.42, 0.15, M_RED, "D", "International"),
    ]:
        dqs = np.clip(rng.normal(dqs_m, dqs_s, n), 0, 1)
        conf = np.clip(rng.beta(3, 2, n), 0.5, 1.0)
        ax.scatter(dqs, conf, c=col, marker=mk, s=18, alpha=0.5,
                   label=label, edgecolors="none")

    # PBW zone
    ax.axhspan(0.80, 1.01, xmin=0, xmax=0.60, alpha=0.10, color=M_RED)
    ax.axhline(0.80, color=M_RED, linestyle=":", alpha=0.4)
    ax.axvline(0.60, color=M_RED, linestyle=":", alpha=0.4)
    ax.text(0.05, 0.96, "PBW-Zone\n(Plausible-but-Wrong)", fontsize=8,
            color=M_RED, style="italic", fontweight="bold")

    ax.set_xlabel("Data Quality Score (DQS)", fontsize=9)
    ax.set_ylabel("Modellkonfidenz", fontsize=9)
    ax.set_xlim(0, 1.02)
    ax.set_ylim(0.45, 1.02)
    ax.legend(fontsize=7, loc="lower right")
    ax.set_title("PBW-Erkennung: Hohe Konfidenz bei schlechter Datenqualitaet", fontsize=10, fontweight="bold")
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_market_comparison() -> BytesIO:
    """Bar chart comparing DQS across markets."""
    chart_style()
    fig, ax = plt.subplots(figsize=(5.5, 2.8))
    markets = ["Deutschland\n(DE)", "Frankreich\n(FR)", "Spanien\n(ES)", "International\n(INT)"]
    dqs_means = [0.85, 0.78, 0.65, 0.42]
    colors = [M_GREEN, M_BLUE, M_AMBER, M_RED]
    bars = ax.bar(markets, dqs_means, color=colors, alpha=0.8, width=0.6)

    for bar, val in zip(bars, dqs_means):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                f"{val:.2f}", ha="center", fontsize=9, fontweight="bold")

    # Tier lines
    ax.axhline(0.80, color=M_GREEN, linestyle="--", alpha=0.5, label="Adequate (0.80)")
    ax.axhline(0.60, color=M_RED, linestyle="--", alpha=0.5, label="Insufficient (0.60)")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Durchschnittlicher DQS", fontsize=9)
    ax.set_title("DQS-Marktvergleich: Warum der Markt entscheidet", fontsize=10, fontweight="bold")
    ax.legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_two_patients() -> BytesIO:
    """Side-by-side comparison of two hypertension patients."""
    chart_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6, 3))

    # Patient A: complete file
    cats_a = ["Diagnosen", "Labore", "Medikamente", "Blutdruck", "Anamnese"]
    vals_a = [1.0, 0.9, 1.0, 1.0, 0.8]
    ax1.barh(cats_a, vals_a, color=M_GREEN, alpha=0.8, height=0.5)
    ax1.set_xlim(0, 1.15)
    ax1.set_title("Patient A: DQS = 0.85", fontsize=9, fontweight="bold", color=M_GREEN)
    for i, v in enumerate(vals_a):
        ax1.text(v + 0.02, i, f"{v:.0%}", va="center", fontsize=8)

    # Patient B: sparse file
    vals_b = [0.6, 0.1, 0.0, 0.0, 0.3]
    ax2.barh(cats_a, vals_b, color=M_RED, alpha=0.8, height=0.5)
    ax2.set_xlim(0, 1.15)
    ax2.set_title("Patient B: DQS = 0.40", fontsize=9, fontweight="bold", color=M_RED)
    for i, v in enumerate(vals_b):
        ax2.text(v + 0.02, i, f"{v:.0%}", va="center", fontsize=8)

    fig.suptitle("Gleicher ICD-Code (I10 Hypertonie), unterschiedliche Datenqualitaet",
                 fontsize=9, fontweight="bold")
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    return buf


# ============================================================================
# PDF Generation
# ============================================================================

def build_methods_guide():
    logger.info("Generiere Methods Guide...")
    pdf = AcademicPDF(
        header_left="MedRisk v2.0",
        header_right="Methods Guide: DQS",
        footer_left="the author | Helmholtz Munich | April 2026",
    )

    # ── Cover ──
    pdf.cover(
        title="Data Quality Score (DQS)",
        subtitle="Eine verstaendliche Einfuehrung in die Datenqualitaetsbewertung\n"
                 "fuer medizinisches Underwriting",
        byline="the author",
        extra="Dieses Dokument erklaert den DQS-Ansatz ohne tiefe mathematische "
              "Vorkenntnisse.\nAlle Formeln werden Schritt fuer Schritt mit "
              "konkreten Beispielen erlaeutert.",
    )

    # ── Table of Contents ──
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*C_HEADING)
    pdf.cell(0, 8, "Inhalt", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    toc = [
        ("1", "Was ist der DQS?"),
        ("2", "Die drei Saeulen des DQS"),
        ("3", "Die Formel -- Schritt fuer Schritt"),
        ("4", "Das Ampelsystem"),
        ("5", "PBW-Erkennung: Wenn das Modell sich irrt"),
        ("6", "Konkretes Beispiel: Zwei Hypertonie-Patienten"),
        ("7", "Marktvergleich: Warum der Standort zaehlt"),
        ("8", "EU AI Act: Was das fuer DQS bedeutet"),
        ("9", "Variablenverzeichnis"),
    ]
    for num, title in toc:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*C_BODY)
        pdf.cell(8, 5.5, num)
        pdf.cell(0, 5.5, safe(title), new_x="LMARGIN", new_y="NEXT")

    # ── Chapter 1: Was ist der DQS? ──
    pdf.chapter_head(1, "Was ist der DQS?")

    pdf.key_concept(
        "Der DQS ist eine Bonitaetsauskunft fuer Patientendaten. "
        "Bevor wir das Risiko eines Patienten bewerten, pruefen wir "
        "die Qualitaet seiner Akte."
    )

    pdf.p(
        "In der Finanzwelt prueft man vor einer Kreditvergabe die Bonitaet "
        "des Antragstellers. Im medizinischen Underwriting tun wir etwas "
        "Aehnliches -- aber nicht fuer den Patienten, sondern fuer seine Daten."
    )
    pdf.p(
        "Die zentrale Frage lautet: Sind die vorliegenden Daten gut genug, "
        "um eine zuverlaessige Risikoeinschaetzung zu treffen? Wenn nicht, "
        "sollte das Modell keine Entscheidung treffen -- egal wie 'sicher' "
        "es sich fuehlt."
    )
    pdf.p(
        "Der Data Quality Score (DQS) ist eine einzelne Zahl zwischen 0 und 1, "
        "die genau das misst. Ein DQS von 0.90 bedeutet: Die Akte ist fast "
        "vollstaendig, konsistent und aktuell. Ein DQS von 0.30 bedeutet: "
        "Es fehlen wesentliche Informationen."
    )

    pdf.h2("Warum brauchen wir das?")
    pdf.p(
        "Klassische ML-Modelle geben eine Konfidenz aus -- z.B. '92% Wahrschein-"
        "lichkeit fuer niedriges Risiko'. Aber diese Konfidenz sagt nichts darueber "
        "aus, ob die Eingabedaten ueberhaupt aussagekraeftig waren. Ein Modell, "
        "das nur den ICD-Code I10 (Hypertonie) sieht, aber keine Labore, keine "
        "Medikamente und keinen Blutdruck hat, kann trotzdem 92% ausgeben -- weil "
        "es aus dem Trainingsdatensatz gelernt hat, dass Hypertonie-Patienten "
        "im Schnitt ein bestimmtes Risikoprofil haben."
    )
    pdf.p(
        "Das Problem: Der Durchschnitt ist kein Individuum. Stadium I (kontrolliert) "
        "und Stadium IV (Herzinfarkt + Dialyse) haben denselben ICD-Code, aber "
        "voellig unterschiedliche Kosten."
    )

    # ── Chapter 2: Die drei Saeulen ──
    pdf.chapter_head(2, "Die drei Saeulen des DQS")

    pdf.figure(chart_dqs_components(),
               "Die drei Komponenten des DQS und ihre Gewichtung.")

    pdf.h2("Vollstaendigkeit (C) -- Wie viele Seiten fehlen im Buch?")
    pdf.p(
        "Wir erwarten 40 Informationen pro Patient: 5 demographische Merkmale "
        "(Alter, Geschlecht, BMI, Rauchstatus, Markt), 17 Diagnose-Kategorien "
        "(nach Charlson), 10 Laborwerte und 8 Medikamenten-Gruppen."
    )
    pdf.p(
        "Vollstaendigkeit = (vorhandene Informationen) / 40. Wenn ein Patient "
        "5 Demographics + 3 Diagnosen + 2 Labore + 1 Medikament = 11 Features "
        "hat, ist C = 11/40 = 0.275."
    )
    pdf.li("Analogie: Stellen Sie sich eine Krankenakte als Buch mit 40 Seiten "
           "vor. Wenn 30 Seiten vorhanden sind, ist die Akte zu 75% vollstaendig.")

    pdf.h2("Konsistenz (S) -- Passt die Geschichte zusammen?")
    pdf.p(
        "Selbst wenn Daten vorhanden sind, koennen sie widerspruechlich sein. "
        "Fuenf klinische Regeln pruefen die interne Plausibilitaet:"
    )
    pdf.li("Diabetes + HbA1c: Wenn Diabetes (E11) codiert ist, muss HbA1c >= 5.7% sein.")
    pdf.li("CKD + eGFR: Bei schwerer CKD (N18.4-6) muss eGFR < 30 sein.")
    pdf.li("Herzinsuffizienz + NT-proBNP: Bei HF (I50) muss NT-proBNP > 125 sein.")
    pdf.li("Hypertonie + Blutdruck: Bei I10 muss SBP > 120 oder Antihypertensiva vorhanden sein.")
    pdf.li("Kein Diabetes + HbA1c: Ohne E11-Code sollte HbA1c < 6.5% sein.")
    pdf.p(
        "Konsistenz = (bestandene Regeln) / (anwendbare Regeln). Wenn 3 von "
        "4 anwendbaren Regeln bestanden werden, ist S = 0.75. Wenn keine Regel "
        "anwendbar ist (z.B. keine Labore vorhanden), ist S = 1.0 per Default."
    )
    pdf.li("Analogie: Ein Detektiv prueft, ob die Zeugenaussagen zusammenpassen. "
           "Wenn jemand sagt 'Ich bin Diabetiker' aber der Blutzucker normal ist, "
           "stimmt etwas nicht.")

    pdf.h2("Aktualitaet (R) -- Wie alt sind die Laborwerte?")
    pdf.p(
        "Laborwerte verlieren mit der Zeit an Aussagekraft. Ein HbA1c von vor "
        "6 Monaten ist aussagekraeftiger als einer von vor 5 Jahren. Wir "
        "modellieren das mit exponentiellem Zerfall:"
    )

    pdf.figure(chart_recency_decay(),
               "Exponentieller Zerfall der Laborwert-Relevanz. "
               "Nach 1.4 Jahren ist die Aussagekraft halbiert.")

    pdf.p(
        "Die Halbwertszeit betraegt 1.4 Jahre. Das bedeutet:"
    )
    pdf.li("Heute: 100% Gewicht")
    pdf.li("Nach 1.4 Jahren: 50% Gewicht")
    pdf.li("Nach 2.8 Jahren: 25% Gewicht")
    pdf.li("Nach 5 Jahren: nur noch ~5% Gewicht")
    pdf.p(
        "Aktualitaet = Durchschnitt aller Laborwert-Gewichte. Wenn alle "
        "Labore von gestern sind, ist R nahe 1.0. Wenn alle 5 Jahre alt sind, "
        "ist R nahe 0.05."
    )

    # ── Chapter 3: Die Formel ──
    pdf.chapter_head(3, "Die Formel -- Schritt fuer Schritt")

    pdf.key_concept(
        "DQS = 0.40 x C + 0.35 x S + 0.25 x R"
    )

    pdf.h2("Variablen erklaert")
    pdf.table(
        headers=["Symbol", "Name", "Beschreibung", "Wertebereich"],
        rows=[
            ["DQS", "Data Quality Score", "Gesamtbewertung der Datenqualitaet", "0 bis 1"],
            ["C", "Completeness", "Anteil vorhandener Features (von 40 erwartet)", "0 bis 1"],
            ["S", "Consistency", "Anteil bestandener Plausibilitaetsregeln", "0 bis 1"],
            ["R", "Recency", "Durchschnittliche Aktualitaet der Laborwerte", "0 bis 1"],
            ["0.40", "alpha", "Gewicht fuer Vollstaendigkeit", "fest"],
            ["0.35", "beta", "Gewicht fuer Konsistenz", "fest"],
            ["0.25", "gamma", "Gewicht fuer Aktualitaet", "fest"],
        ],
        col_widths=[18, 32, 80, 28],
    )

    pdf.h2("Warum diese Gewichte?")
    pdf.li("Vollstaendigkeit (40%): Der wichtigste Faktor. Fehlende Daten sind "
           "schlimmer als alte Daten -- weil alte Daten wenigstens einen Hinweis "
           "geben, fehlende Daten aber gar keine Information liefern.")
    pdf.li("Konsistenz (35%): Widersprueche deuten auf Codier- oder Eingabefehler "
           "hin. Ein widerspruchsfreier Datensatz ist vertrauenswuerdiger.")
    pdf.li("Aktualitaet (25%): Alte Laborwerte sind weniger aussagekraeftig, "
           "aber immer noch besser als gar keine.")

    pdf.h2("Beispielrechnung")
    pdf.p("Patient: 55 Jahre, maennlich, Hypertonie (I10), Diabetes (E11)")
    pdf.li("Vorhandene Features: 5 Demo + 2 Diagnosen + 4 Labore + 2 Meds = 13")
    pdf.li("C = 13/40 = 0.325")
    pdf.li("Anwendbare Regeln: 3 (Diabetes-HbA1c, Hypertonie-BP, kein-Diabetes). "
           "Bestanden: 2. S = 2/3 = 0.667")
    pdf.li("Labore: 2 von heute (Gewicht 1.0), 2 von vor 2 Jahren (Gewicht 0.37). "
           "R = (1.0 + 1.0 + 0.37 + 0.37) / 4 = 0.685")
    pdf.li("DQS = 0.40 x 0.325 + 0.35 x 0.667 + 0.25 x 0.685")
    pdf.li("DQS = 0.130 + 0.233 + 0.171 = 0.534")
    pdf.p(
        "Ergebnis: DQS = 0.534. Das liegt unter 0.60 -- die Akte ist "
        "unzureichend fuer eine automatisierte Entscheidung. Empfehlung: "
        "Mehr Daten anfordern oder manuell pruefen."
    )

    # ── Chapter 4: Ampelsystem ──
    pdf.chapter_head(4, "Das Ampelsystem")

    pdf.figure(chart_traffic_light(),
               "DQS-Ampelsystem: Gruen (automatisch), Gelb (pruefen), Rot (stopp).")

    pdf.table(
        headers=["Stufe", "DQS-Bereich", "Aktion", "Typischer Markt"],
        rows=[
            ["Gruen (Adequate)", ">= 0.80", "Automatische Verarbeitung", "Deutschland"],
            ["Gelb (Caution)", "0.60 - 0.80", "Manuelle Pruefung empfohlen", "Spanien"],
            ["Rot (Insufficient)", "< 0.60", "STOPP -- Vorhersage ablehnen", "International"],
        ],
        col_widths=[38, 28, 52, 38],
    )

    pdf.p(
        "Das Ampelsystem stellt sicher, dass Entscheidungen nur dann "
        "automatisiert werden, wenn die Datenlage es rechtfertigt. Bei "
        "gelber oder roter Ampel wird ein menschlicher Underwriter einbezogen."
    )

    # ── Chapter 5: PBW-Erkennung ──
    pdf.chapter_head(5, "PBW-Erkennung: Wenn das Modell sich irrt")

    pdf.key_concept(
        "PBW = Plausible-but-Wrong. Das Modell gibt eine hohe Konfidenz aus, "
        "aber die Datenlage rechtfertigt das nicht. Es klingt plausibel -- "
        "ist aber falsch."
    )

    pdf.p(
        "Das Konzept stammt aus the authors Forschung zur LLM-Evaluation "
        "(ISME Communications, 2024). Bei der Evaluation von 22 KI-Modellen "
        "wurde ein wiederkehrendes Muster entdeckt: Die Modelle erzeugten "
        "Ergebnisse, die auf den ersten Blick korrekt aussahen, aber bei "
        "Expertenpruefung scheiterten."
    )

    pdf.h2("Erkennung")
    pdf.p("Ein Fall wird als PBW markiert, wenn zwei Bedingungen gleichzeitig erfuellt sind:")
    pdf.li("Modellkonfidenz > 80% (das Modell ist sich 'sicher')")
    pdf.li("DQS < 60% (die Datenlage ist unzureichend)")

    pdf.h2("Die PBW-Formel")
    pdf.table(
        headers=["Symbol", "Name", "Beschreibung", "Schwellenwert"],
        rows=[
            ["PBW", "Plausible-but-Wrong", "Fehlerkennungs-Flag (ja/nein)", "ja wenn beide Bed. erfuellt"],
            ["conf", "Konfidenz", "Modell-Sicherheit fuer die Vorhersage", "> 0.80"],
            ["DQS", "Data Quality Score", "Datenqualitaet (siehe oben)", "< 0.60"],
            ["theta_c", "Konfidenzschwelle", "Ab wann gilt 'hohe Konfidenz'", "0.80"],
            ["theta_d", "DQS-Schwelle", "Ab wann gilt 'schlechte Daten'", "0.60"],
        ],
        col_widths=[22, 36, 66, 38],
    )

    pdf.figure(chart_pbw_scatter(),
               "PBW-Zone (rot schattiert): Hohe Konfidenz + niedrige Datenqualitaet. "
               "Internationale Patienten landen haeufiger in dieser Zone.")

    pdf.h2("Weitere Warnsignale")
    pdf.p("Neben PBW gibt es zwei zusaetzliche Indikatoren:")

    pdf.li("CCM (Calibration-Confidence Mismatch): Die Differenz zwischen "
           "roher und kalibrierter Vorhersage. Wenn |P_raw - P_calibrated| > 0.20, "
           "befindet sich der Patient in einem unsicheren Bereich des Feature-Raums.")
    pdf.li("EPU (Epistemic Prediction Uncertainty): Unterschied zwischen den "
           "Vorhersagen verschiedener Modelle (XGBoost, Cox PH, CTMC). Wenn die "
           "Modelle sich um mehr als 3 Dezile unterscheiden, ist die Unsicherheit hoch.")

    # ── Chapter 6: Beispiel ──
    pdf.chapter_head(6, "Konkretes Beispiel: Zwei Hypertonie-Patienten")

    pdf.figure(chart_two_patients(),
               "Vergleich zweier Patienten mit ICD-10 I10 (Hypertonie). "
               "Gleicher Code, voellig unterschiedliche Datenqualitaet.")

    pdf.h2("Patient A: Vollstaendige Akte (DQS 0.85)")
    pdf.li("Diagnosen: I10 (Hypertonie), E78 (Dyslipidaemie), E11 (Diabetes)")
    pdf.li("Labore: HbA1c 7.2%, Kreatinin 0.9, eGFR 85, Cholesterin 245")
    pdf.li("Medikamente: 3 Antihypertensiva (Ramipril, Amlodipin, HCT)")
    pdf.li("Blutdruck: 135/85 mmHg (vor 2 Monaten gemessen)")
    pdf.li("-> Stadium II gesichert, Praemie berechenbar: ca. EUR 90/Monat")

    pdf.h2("Patient B: Lueckenhafte Akte (DQS 0.40)")
    pdf.li("Diagnosen: I10 (Hypertonie) -- sonst nichts codiert")
    pdf.li("Labore: keine vorhanden")
    pdf.li("Medikamente: keine Dokumentation")
    pdf.li("Blutdruck: unbekannt")
    pdf.li("-> Stadium unklar. Ist es Stadium I (3% AU-Risiko) oder Stadium III "
           "(35% AU-Risiko)? Ohne weitere Daten unmoeglich zu sagen.")

    pdf.p(
        "Ergebnis: Obwohl beide Patienten denselben ICD-Code haben, ist nur "
        "bei Patient A eine zuverlaessige Risikoeinschaetzung moeglich. Bei "
        "Patient B wuerde ein Modell trotzdem eine Vorhersage machen -- "
        "aber DQS sagt: STOPP."
    )

    # ── Chapter 7: Marktvergleich ──
    pdf.chapter_head(7, "Marktvergleich: Warum der Standort zaehlt")

    pdf.figure(chart_market_comparison(),
               "Durchschnittlicher DQS nach Markt. Deutschland hat die beste "
               "Datenqualitaet, internationale Maerkte die schlechteste.")

    pdf.p(
        "Die Datenqualitaet haengt stark vom Gesundheitssystem ab. Deutschland "
        "hat ein gut strukturiertes Codierungssystem mit hoher Vollstaendigkeit "
        "(ICD-10-GM, EBM, ATC). Internationale Maerkte haben oft lueckenhafte "
        "Akten mit laengeren Verzoegerungen zwischen Diagnose und Dokumentation."
    )

    pdf.table(
        headers=["Parameter", "DE", "FR", "ES", "INT"],
        rows=[
            ["Codierungsvollstaendigkeit", "95%", "90%", "80%", "60%"],
            ["Labordaten vorhanden", "92%", "88%", "75%", "50%"],
            ["Diagnoseverzoegerung", "14 Tage", "60 Tage", "30 Tage", "90 Tage"],
            ["Medikamentendoku.", "95%", "88%", "80%", "60%"],
            ["Erwarteter DQS", "0.85", "0.80", "0.70", "0.45"],
        ],
        col_widths=[55, 22, 22, 22, 22],
    )

    pdf.p(
        "Konsequenz: Ein Modell, das auf deutschen Daten trainiert wurde, "
        "funktioniert nicht automatisch in internationalen Maerkten. Der DQS "
        "erkennt diesen Unterschied und passt die Entscheidungslogik an."
    )

    # ── Chapter 8: EU AI Act ──
    pdf.chapter_head(8, "EU AI Act: Was das fuer DQS bedeutet")

    pdf.key_concept(
        "Der EU AI Act (Verordnung 2024/1689) klassifiziert KI-Systeme fuer "
        "Krankenversicherungs-Underwriting als Hochrisiko (Annex III, 5(a)). "
        "Ab August 2026 muessen alle solchen Systeme volle Compliance nachweisen."
    )

    pdf.h2("Nicht Datenlokalisierung -- Systemdesign")
    pdf.p(
        "Ein haeufiges Missverstaendnis: Der AI Act hat NICHTS mit Daten-"
        "lokalisierung zu tun. Er regelt nicht, wo Daten gespeichert werden "
        "(das ist DSGVO). Er regelt, wie das KI-System selbst gebaut, "
        "getestet und ueberwacht wird."
    )
    pdf.p(
        "Das bedeutet: Auch ein lokal gehostetes, auf anonymisierten Daten "
        "fine-getunetes Open-Source-Modell (Llama, GBERT) ist ein Hochrisiko-"
        "System, wenn es individuelle Risikobewertungen erstellt. "
        "Anonymisierung loest ca. 10% des Compliance-Problems."
    )

    pdf.h2("Zwei-Schichten-Architektur")
    pdf.p(
        "Art. 6(3) definiert Ausnahmen fuer 'enge prozedurale Aufgaben'. "
        "Daraus ergibt sich eine strategische Zweiteilung:"
    )

    pdf.table_caption("Schicht 1 -- Sofort automatisierbar (kein High-Risk)")
    pdf.table(
        headers=["Automatisierung", "Begruendung", "Beispiel"],
        rows=[
            ["OCR/NER aus Arztbriefen", "Prozedurale Aufgabe", "Datenextraktion"],
            ["Dokumenten-Routing", "Prozedurale Aufgabe", "Akte -> Underwriter"],
            ["Workflow-Orchestrierung", "Keine KI-Risikobewertung", "Pipelines aktivieren"],
            ["Portfolio-Analytik", "Kein Personenbezug", "Markt-Dashboards"],
            ["Wissensmanagement", "Vorbereitend", "Richtliniensuche"],
            ["Datenvalidierung (DQS)", "Prozedurale Aufgabe", "Vollstaendigkeitspruefung"],
        ],
        col_widths=[50, 45, 45],
    )

    pdf.table_caption("Schicht 2 -- High-Risk (ab Aug 2026)")
    pdf.table(
        headers=["Automatisierung", "Warum High-Risk", "Anforderung"],
        rows=[
            ["Individuelle Risikobewertung", "Annex III 5(a)", "Art. 9-15 vollstaendig"],
            ["Individuelle Preisgestaltung", "Annex III 5(a)", "Art. 9-15 vollstaendig"],
            ["Profiling mit Gesundheitsdaten", "Profiling-Sperre", "Art. 9-15 + Art. 27"],
        ],
        col_widths=[50, 45, 45],
    )

    pdf.h2("Wo DQS reinpasst")
    pdf.p(
        "Der DQS als reine technische Vollstaendigkeitspruefung ('Sind 40 "
        "Features vorhanden? Sind Labore aktuell?') kann als Art. 6(3)(a) "
        "'enge prozedurale Aufgabe' argumentiert werden -- Schicht 1."
    )
    pdf.p(
        "Sobald der DQS-Output aber die Underwriting-Entscheidung materiell "
        "beeinflusst (z.B. DQS < 0.60 -> automatische Ablehnung), wird er "
        "Teil des Hochrisiko-Systems -- Schicht 2."
    )
    pdf.p(
        "Empfehlung: Architektonische Trennung. DQS als unabhaengige "
        "Datenqualitaetsschicht, die Informationen LIEFERT aber keine "
        "Entscheidungen TRIFFT. Die Entscheidungslogik sitzt in der "
        "Decision Engine (Schicht 2), die voll compliant sein muss."
    )

    pdf.h2("Compliance-Status MedRisk")
    pdf.table(
        headers=["Anforderung", "Artikel", "Status"],
        rows=[
            ["Risikomanagementsystem", "Art. 9", "PBW, DQS-Tiers, Failure Modes"],
            ["Data Governance", "Art. 10", "DQS v2 prueft C, S, R"],
            ["Technische Dokumentation", "Art. 11", "Architektur dokumentiert"],
            ["Automatische Protokollierung", "Art. 12", "Audit-Trail (JSON Lines)"],
            ["Transparenz", "Art. 13", "SHAP, DQS-Ampel, Logs"],
            ["Menschliche Aufsicht", "Art. 14", "Human Override implementiert"],
            ["Genauigkeit + Robustheit", "Art. 15", "442 Tests, Metriken"],
            ["Grundrechte-Folgenabschaetzung", "Art. 27", "Offen (vor Produktion)"],
        ],
        col_widths=[50, 25, 65],
    )

    pdf.source_line(
        "Quellen: EU AI Act (VO 2024/1689), Annex III 5(a), Art. 6(2)-(3), "
        "Art. 9-15. Milliman (2024), Harvard Data Science Review (2025)."
    )

    # ── Chapter 9: Variablenverzeichnis ──
    pdf.chapter_head(9, "Variablenverzeichnis")

    pdf.p("Alle Variablen und Formelzeichen in MedRisk auf einen Blick:")

    pdf.h2("DQS-Framework")
    pdf.table(
        headers=["Symbol", "Name", "Formel/Wert", "Einheit"],
        rows=[
            ["DQS", "Data Quality Score", "alpha*C + beta*S + gamma*R", "[0, 1]"],
            ["C", "Completeness", "n_observed / n_expected", "[0, 1]"],
            ["S", "Consistency", "n_passed / n_applicable", "[0, 1]"],
            ["R", "Recency", "(1/|L|) Sum exp(-lambda * age(l))", "[0, 1]"],
            ["alpha", "Gewicht Vollstaendigkeit", "0.40", "dimensionslos"],
            ["beta", "Gewicht Konsistenz", "0.35", "dimensionslos"],
            ["gamma", "Gewicht Aktualitaet", "0.25", "dimensionslos"],
            ["lambda", "Zerfallsrate", "ln(2)/1.4 = 0.495", "1/Jahr"],
            ["t_1/2", "Halbwertszeit", "1.4", "Jahre"],
            ["n_expected", "Erwartete Features", "40", "Stueck"],
            ["|L|", "Anzahl Laborwerte", "variabel", "Stueck"],
            ["age(l)", "Alter eines Laborwerts", "heute - Messdatum", "Jahre"],
        ],
        col_widths=[22, 42, 60, 30],
    )

    pdf.h2("PBW-Erkennung")
    pdf.table(
        headers=["Symbol", "Name", "Formel/Wert", "Einheit"],
        rows=[
            ["PBW", "Plausible-but-Wrong Flag", "(conf > theta_c) AND (DQS < theta_d)", "bool"],
            ["conf", "Modellkonfidenz", "max(p, 1-p)", "[0.5, 1]"],
            ["theta_c", "Konfidenzschwelle", "0.80", "dimensionslos"],
            ["theta_d", "DQS-Schwelle", "0.60", "dimensionslos"],
            ["CCM", "Calibration-Confidence Mismatch", "|P_raw - P_calibrated|", "[0, 1]"],
            ["EPU", "Epistemic Prediction Uncertainty", "max(deciles) - min(deciles)", "[0, 9]"],
        ],
        col_widths=[22, 50, 55, 28],
    )

    pdf.h2("KTG-Kalkulation")
    pdf.table(
        headers=["Symbol", "Name", "Formel/Wert", "Einheit"],
        rows=[
            ["KTG", "Krankentagegeld-Praemie", "P(AU) x E[Dauer] x Tagessatz", "EUR/Jahr"],
            ["P(AU)", "AU-Wahrscheinlichkeit", "stadienabhaengig (3%-80%)", "[0, 1]"],
            ["E[Dauer]", "Erwartete AU-Dauer", "stadienabhaengig (14-120 Tage)", "Tage"],
            ["Tagessatz", "Netto-Tagessatz", "70-90% des Brutto", "EUR/Tag"],
        ],
        col_widths=[28, 42, 52, 28],
    )

    pdf.h2("CTMC (Continuous-Time Markov Chain)")
    pdf.table(
        headers=["Symbol", "Name", "Formel/Wert", "Einheit"],
        rows=[
            ["Q", "Uebergangsmatrix", "5x5 Matrix der Raten", "1/Jahr"],
            ["P(t)", "Zustandsverteilung", "P(0) x exp(Q*t)", "Wahrscheinlichkeit"],
            ["q_ij", "Uebergangsrate i->j", "siehe Konfiguration", "1/Jahr"],
            ["exp(Qt)", "Matrix-Exponential", "numerisch berechnet", "dimensionslos"],
        ],
        col_widths=[22, 42, 60, 30],
    )

    pdf.source_line(
        "MedRisk v2.0 | Methods Guide | the author | Helmholtz Munich | April 2026"
    )

    # ── Save ──
    output_path = OUT / "methods_guide.pdf"
    pdf.output(str(output_path))
    logger.info("Methods Guide geschrieben: %s (%d Seiten)",
                output_path, pdf.pages_count)
    return output_path


if __name__ == "__main__":
    build_methods_guide()
