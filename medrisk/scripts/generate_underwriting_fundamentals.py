#!/usr/bin/env python3
"""Generate Medical Underwriting Fundamentals PDF for a major European insurer.

Produces a ~35-page portrait A4 PDF covering the essential knowledge
a medical underwriter needs: disease profiles, AU statistics, comorbidity
assessment, temporal risk framework, case studies, KTG pricing, and
regulatory context.

Usage:
    python scripts/generate_underwriting_fundamentals.py
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
    M_BLUE, M_AMBER, M_GREEN, M_RED, M_DARK, M_GREY, M_PURPLE, M_LIGHT,
    C_BODY, C_HEADING, C_CAPTION, C_ACCENT, C_RULE, C_BOX_BG,
    C_TABLE_HDR, C_TABLE_ALT, C_WHITE, C_GREEN_BG, C_RED_BG,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

OUT = PROJECT_ROOT / "data" / "reports"
OUT.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Chart generators
# ============================================================================

def chart_ktg_coverage_chain() -> BytesIO:
    """Timeline showing employer -> GKV -> KTG coverage chain."""
    chart_style()
    fig, ax = plt.subplots(figsize=(6.5, 1.8))

    bars = [
        (0, 42, M_DARK, "Employer 100%\n(Lohnfortzahlung)"),
        (42, 504, M_BLUE, "GKV Krankengeld\n(70% gross / 90% net)"),
        (3, 543, M_AMBER, "KTG private gap\n(after Karenzzeit)"),
    ]
    for start, dur, color, label in bars:
        y = 0 if label.startswith("KTG") else 0.6
        h = 0.35
        ax.barh(y, dur, left=start, height=h, color=color, alpha=0.85)
        ax.text(start + dur / 2, y, label, ha="center", va="center",
                fontsize=7, color="white" if y == 0.6 else "black", fontweight="bold")

    ax.set_xlim(-5, 560)
    ax.set_ylim(-0.3, 1.2)
    ax.set_xlabel("Days since incapacity", fontsize=8)
    ax.set_yticks([])
    ax.axvline(42, color=M_GREY, ls="--", lw=0.5, alpha=0.5)
    ax.axvline(546, color=M_GREY, ls="--", lw=0.5, alpha=0.5)
    ax.text(42, 1.05, "Day 43", ha="center", fontsize=6.5, color=M_GREY)
    ax.text(546, 1.05, "Day 546", ha="center", fontsize=6.5, color=M_GREY)
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_dqs_components() -> BytesIO:
    """Bar chart showing DQS component weights."""
    chart_style()
    fig, ax = plt.subplots(figsize=(4.5, 2.2))
    components = ["Completeness", "Consistency", "Recency"]
    weights = [0.40, 0.35, 0.25]
    colors = [M_BLUE, M_GREEN, M_AMBER]
    ax.barh(components, weights, color=colors, height=0.5)
    for i, v in enumerate(weights):
        ax.text(v + 0.01, i, f"{v:.0%}", va="center", fontsize=8)
    ax.set_xlim(0, 0.55)
    ax.set_xlabel("Weight in DQS composite", fontsize=8)
    ax.invert_yaxis()
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_sick_days_by_chapter() -> BytesIO:
    """Horizontal bar chart of sick-day share by ICD chapter."""
    chart_style()
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    chapters = ["M - Musculoskeletal", "F - Mental/Behavioural",
                "S/T - Injuries", "J - Respiratory", "I - Circulatory",
                "C/D - Neoplasms", "A/B - Infectious", "E - Metabolic",
                "G - Nervous", "K - Digestive", "Z - Health factors"]
    pcts = [25, 18, 12, 11, 8, 6, 5, 4, 4, 4, 3]
    colors_list = [M_AMBER, M_PURPLE, M_GREY, M_LIGHT, M_RED,
                   M_DARK, M_GREEN, M_BLUE, "#0d7377", M_GREY, M_LIGHT]
    ax.barh(chapters, pcts, color=colors_list, height=0.6)
    for i, v in enumerate(pcts):
        ax.text(v + 0.3, i, f"{v}%", va="center", fontsize=7)
    ax.set_xlim(0, 30)
    ax.set_xlabel("Share of total sick days (%)", fontsize=8)
    ax.invert_yaxis()
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_cv_ctmc() -> BytesIO:
    """Cardiovascular 5-state CTMC occupation probabilities."""
    chart_style()
    Q = np.array([
        [-0.08, 0.08, 0, 0, 0],
        [0.02, -0.08, 0.06, 0, 0],
        [0, 0, -0.05, 0.04, 0.01],
        [0, 0, 0, -0.03, 0.03],
        [0, 0, 0, 0, 0],
    ])
    dt = 0.01
    steps = int(30 / dt)
    p = np.array([1.0, 0, 0, 0, 0])
    times, probs = [], []
    for i in range(steps + 1):
        t = i * dt
        if abs(t - round(t)) < dt / 2:
            times.append(t)
            probs.append(p.copy())
        dp = p @ Q
        p = np.maximum(p + dt * dp, 0)
        p /= p.sum()
    probs = np.array(probs)
    fig, ax = plt.subplots(figsize=(5.5, 3))
    names = ["Healthy", "Risk Factors", "Chronic Condition", "Complication", "Major Event"]
    colors_cv = ["#48bb78", "#4299e1", "#ed8936", "#e53e3e", "#1a202c"]
    ax.stackplot(times, probs.T, labels=names, colors=colors_cv, alpha=0.8)
    ax.set_xlabel("Years")
    ax.set_ylabel("Probability")
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 1)
    ax.legend(fontsize=6.5, loc="center right")
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_alz_ctmc() -> BytesIO:
    """Alzheimer 7-state CTMC occupation probabilities."""
    chart_style()
    Q = np.array([
        [-0.04, 0.04, 0, 0, 0, 0, 0],
        [0, -0.08, 0.08, 0, 0, 0, 0],
        [0, 0, -0.15, 0.15, 0, 0, 0],
        [0, 0, 0, -0.27, 0.25, 0, 0.02],
        [0, 0, 0, 0, -0.38, 0.33, 0.05],
        [0, 0, 0, 0, 0, -0.50, 0.50],
        [0, 0, 0, 0, 0, 0, 0],
    ])
    dt = 0.01
    steps = int(35 / dt)
    p = np.array([1.0, 0, 0, 0, 0, 0, 0])
    times, probs = [], []
    for i in range(steps + 1):
        t = i * dt
        if abs(t - round(t)) < dt / 2:
            times.append(t)
            probs.append(p.copy())
        dp = p @ Q
        p = np.maximum(p + dt * dp, 0)
        p /= p.sum()
    probs = np.array(probs)
    fig, ax = plt.subplots(figsize=(5.5, 3))
    names = ["Normal", "SCD", "MCI", "Mild AD", "Moderate AD", "Severe AD", "Death"]
    colors_alz = ["#48bb78", "#90cdf4", "#4299e1", "#edbb36", "#ed8936", "#e53e3e", "#1a202c"]
    ax.stackplot(times, probs.T, labels=names, colors=colors_alz, alpha=0.8)
    ax.set_xlabel("Years")
    ax.set_ylabel("Probability")
    ax.set_xlim(0, 35)
    ax.set_ylim(0, 1)
    ax.legend(fontsize=6, loc="center right")
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


def chart_occ_classes() -> BytesIO:
    """Bar chart of occupational risk factors."""
    chart_style()
    fig, ax = plt.subplots(figsize=(4, 2))
    classes = ["Class 1\nSedentary", "Class 2\nLight manual", "Class 3\nSkilled trades", "Class 4\nHeavy manual"]
    factors = [1.00, 1.25, 1.60, 2.10]
    colors_occ = [M_GREEN, M_BLUE, M_AMBER, M_RED]
    ax.bar(classes, factors, color=colors_occ, width=0.6)
    for i, v in enumerate(factors):
        ax.text(i, v + 0.03, f"{v:.2f}x", ha="center", fontsize=7.5, fontweight="bold")
    ax.set_ylabel("Risk factor", fontsize=8)
    ax.set_ylim(0, 2.5)
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf


# ============================================================================
# PDF builder
# ============================================================================

def build_pdf() -> Path:
    """Build the Medical Underwriting Fundamentals PDF."""

    pdf = AcademicPDF(
        header_left="Medical Underwriting Fundamentals",
        header_right="a major European insurer",
        footer_left="the author | Helmholtz Munich | April 2026",
    )

    # ── Cover ──
    pdf.cover(
        title="Medical Underwriting Fundamentals",
        subtitle="Essential knowledge for AI-augmented risk assessment at a major European insurer",
        byline="the author",
        extra="Based on MedRisk v2.0 -- AI-driven medical underwriting with confidence-calibrated failure mode detection",
    )

    # ── Table of Contents ──
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*C_HEADING)
    pdf.cell(0, 8, "Contents", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    toc = [
        ("1", "What Is Medical Underwriting?"),
        ("2", "Medical Coding Systems: ICD-10, LOINC, ATC"),
        ("3", "Krankentagegeld (KTG) -- Product & Pricing"),
        ("4", "Disease Profiles: Psychiatric Conditions"),
        ("5", "Disease Profiles: Musculoskeletal Conditions"),
        ("6", "Disease Profiles: Cardiovascular Conditions"),
        ("7", "Disease Profiles: Metabolic & Renal Conditions"),
        ("8", "Disease Profiles: Neurological Conditions"),
        ("9", "Comorbidity Assessment & Interactions"),
        ("10", "Temporal Risk Framework"),
        ("11", "Data Quality & Failure Mode Detection"),
        ("12", "Decision Framework & Case Studies"),
    ]
    for num, title in toc:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*C_BODY)
        pdf.cell(8, 6, safe(num))
        pdf.cell(0, 6, safe(title), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*C_CAPTION)
    pdf.multi_cell(pdf._cw, 4, safe(
        "This document contains synthetic data and clinical parameters "
        "from the MedRisk proof-of-concept. Evidence tiers: "
        "[T1] = guideline-level, [T2] = observational, [T3] = expert judgment."
    ))

    # ================================================================
    # CHAPTER 1: What Is Medical Underwriting?
    # ================================================================
    pdf.chapter_head(1, "What Is Medical Underwriting?")

    pdf.p(
        "Medical underwriting is the process of evaluating the health risk "
        "of an insurance applicant to determine whether to accept, modify, "
        "or decline coverage. In disability and sickness-benefit insurance "
        "(Krankentagegeld), the primary question is: how many weeks of "
        "Arbeitsunfaehigkeit (AU -- work incapacity) should we expect from "
        "this applicant per year?"
    )

    pdf.h2("The Five Underwriting Decisions")
    pdf.table(
        headers=["Decision", "Meaning", "When Applied"],
        rows=[
            ["Accept", "Standard terms", "No material health findings, or findings within normal risk tolerance"],
            ["Accept + Loading", "+25% to +300% premium surcharge", "Elevated risk from specific conditions; quantifiable with data"],
            ["Accept + Exclusion", "Condition-specific AU excluded", "Identifiable risk that can be isolated (e.g., MSK exclusion)"],
            ["Postpone", "Defer 6-24 months", "Insufficient data or recent event; reassess after stabilisation"],
            ["Decline", "No coverage offered", "Risk exceeds insurable threshold or unquantifiable"],
        ],
        col_widths=[28, 42, 104],
    )

    pdf.h2("Products at a major European insurer")
    pdf.p(
        "The primary product is Krankentagegeld (KTG) -- private daily "
        "sickness benefit insurance covering the income gap between GKV "
        "Krankengeld and the insured's actual earnings. Secondary products "
        "include Berufsunfaehigkeitsversicherung (BU -- disability insurance) "
        "and private health insurance (PKV Vollversicherung). Each product "
        "has different risk horizons: KTG is short-tail (weeks to months), "
        "BU is long-tail (years to decades)."
    )

    pdf.key_concept(
        "At portfolio scale (100,000 decisions/year), a 2% error rate "
        "produces 2,000 mispriced policies annually -- invisible in standard "
        "accuracy metrics, material in claims experience."
    )

    # ================================================================
    # CHAPTER 2: Medical Coding Systems
    # ================================================================
    pdf.chapter_head(2, "Medical Coding Systems")

    pdf.h2("ICD-10: International Classification of Diseases")
    pdf.p(
        "ICD-10 codes are the primary language of diagnosis in underwriting. "
        "Germany uses ICD-10-GM (German Modification), which differs from "
        "ICD-10-CM (US Clinical Modification) in several codes. The MedRisk "
        "system maintains 73 curated codes across cardiovascular, metabolic, "
        "renal, respiratory, psychiatric, musculoskeletal, and neurological categories."
    )
    pdf.p(
        "Code specificity matters enormously. For example: I48.0 (paroxysmal AF) "
        "carries a fundamentally different risk than I48.1 (persistent AF). "
        "M51 (disc degeneration) is categorically different from M51.1 "
        "(radiculopathy). E11.9 (T2D without complications) is a different "
        "underwriting case than E11.2 (T2D with kidney complications). "
        "Algorithms that treat all codes within a block identically will "
        "systematically misprice."
    )

    pdf.h2("LOINC: Laboratory Observation Codes")
    pdf.p(
        "LOINC codes standardise laboratory results. The system tracks "
        "14 biomarkers across metabolic, renal, cardiovascular, and "
        "cognitive domains. Key examples:"
    )
    pdf.table(
        headers=["LOINC", "Name", "Unit", "Normal", "Disease State"],
        rows=[
            ["4548-4", "HbA1c", "%", "5.0 +/- 0.3", "Diabetes: 8.0 +/- 1.5"],
            ["48642-3", "eGFR", "mL/min", "90 +/- 15", "CKD: 35 +/- 15"],
            ["33762-6", "NT-proBNP", "pg/mL", "60 +/- 30", "HF: 1500 +/- 800"],
            ["8480-6", "Systolic BP", "mmHg", "118 +/- 10", "HTN: 150 +/- 15"],
            ["72106-8", "MMSE", "score", "28 +/- 1.5", "Early AD: 22 +/- 3"],
        ],
        col_widths=[20, 22, 18, 28, 38],
    )
    pdf.source_line("Source: synthetic.py LAB_DEFINITIONS")

    pdf.h2("ATC: Anatomical Therapeutic Chemical Classification")
    pdf.p(
        "Medication prescriptions are powerful severity markers. ATC codes "
        "reveal what a patient is being treated for, even when ICD coding "
        "is incomplete. Key examples: Metformin (A10BA02) signals diabetes, "
        "Donepezil (N06DA02) signals confirmed dementia, Rivaroxaban "
        "(B01AF01) signals AF on anticoagulation, Sertraline signals "
        "depression/anxiety treatment."
    )

    # ================================================================
    # CHAPTER 3: KTG Product & Pricing
    # ================================================================
    pdf.chapter_head(3, "Krankentagegeld (KTG)")

    pdf.h2("Statutory Coverage Chain")
    pdf.p(
        "Understanding KTG requires understanding the German social "
        "insurance cascade. When an employee becomes incapacitated:"
    )
    pdf.figure(chart_ktg_coverage_chain(),
               "GKV coverage chain: employer (6 weeks) -> GKV Krankengeld -> KTG gap coverage",
               w=150)

    pdf.p(
        "KTG covers the income gap between GKV Krankengeld and actual "
        "earnings. The daily Krankengeld is: min(gross x 0.70 / 30, "
        "net x 0.90 / 30, BBG_daily x 0.70). With BBG = 4,987.50 EUR/month "
        "(2024), the maximum daily Krankengeld is approximately 116 EUR. "
        "For high earners, the gap can be substantial."
    )

    pdf.h2("Pricing Formula")
    pdf.p(
        "The KTG net premium follows the equivalence principle: "
        "E[annual KTG] = frequency x SUM(weight_ch x ktg_rr_ch x "
        "E[benefit_days_ch]) x daily_benefit. "
        "Frequency is modelled as NegBin(mu, alpha=0.45). Duration per "
        "ICD chapter follows a Weibull AFT distribution."
    )

    pdf.h2("Occupational Risk Classes")
    pdf.figure(chart_occ_classes(),
               "Occupational risk factors range from 1.0x (sedentary) to 2.1x (heavy manual)",
               w=100)

    pdf.h2("Sick-Day Distribution by ICD Chapter")
    pdf.figure(chart_sick_days_by_chapter(),
               "Musculoskeletal (25%) and psychiatric (18%) conditions dominate sick days in Germany",
               w=130)

    pdf.key_concept(
        "The two highest-impact chapters for KTG are musculoskeletal (M) "
        "with 25% of all sick days and psychiatric (F) with 18%. However, "
        "psychiatric conditions have the highest KTG relative risk (4.2x) "
        "because their episodes are much longer (mean 42.5 days vs 19.5 "
        "for MSK). Understanding this distinction is critical for pricing."
    )

    # ================================================================
    # CHAPTER 4: Psychiatric Conditions
    # ================================================================
    pdf.chapter_head(4, "Psychiatric Conditions")

    pdf.p(
        "Chapter F conditions account for 18% of sick days and carry "
        "the highest KTG relative risk (4.2x). Three clusters require "
        "separate assessment: mood disorders, anxiety/stress, and "
        "personality disorders."
    )

    pdf.h2("Mood Disorders (F31-F34)")
    pdf.p(
        "Depression and bipolar disorder are the highest-impact psychiatric "
        "conditions. The single most important prognostic factor is episode "
        "count: a single mild episode in full remission is near-standard "
        "risk; recurrent depression (>=3 episodes) is often a decline."
    )
    pdf.table(
        headers=["Scenario", "Median AU", "5yr Recurrence", "Evidence"],
        rows=[
            ["Single mild (F32.0), remission >2yr", "6-12 weeks", "~30%", "[T2]"],
            ["Single moderate (F32.1), remission >1yr", "8-16 weeks", "~40%", "[T2]"],
            ["Recurrent (F33), 3+ episodes", "12-24 weeks", "~70%", "[T1]"],
            ["Severe with psychotic features (F32.3)", "16-30 weeks", "~80%", "[T2]"],
            ["Bipolar (F31), without optimal medication", "8-20 wk/yr", "Near-certain", "[T1]"],
        ],
        col_widths=[52, 24, 24, 14],
    )
    pdf.table_caption("AU duration and recurrence by depression severity")

    pdf.h3("Underwriting Responses")
    pdf.table(
        headers=["Scenario", "Decision", "Loading/Exclusion"],
        rows=[
            ["Single mild F32, remission >3yr, no meds", "Accept", "Standard"],
            ["Single moderate, remission 1-3yr", "Loading", "+25-50%"],
            ["Recurrent F33, stable on SSRI", "Loading", "+50-100% + psych excl."],
            ["F33 with hospitalisation history", "Decline", "--"],
            ["Bipolar F31 (most cases)", "Decline", "--"],
        ],
        col_widths=[55, 18, 40],
    )

    pdf.h3("Key Prognostic Factors")
    pdf.li("Remission status: full vs partial vs active episode")
    pdf.li("Episode count: >=3 = chronic pattern, no time decay [T1]")
    pdf.li("Time since last episode: risk decays but not to baseline for F33")
    pdf.li("Medication status: maintenance SSRI = ongoing vulnerability")
    pdf.li("Comorbid anxiety (F41.1): increases AU duration by ~30% [T2]")
    pdf.li("Substance use: active F10.2 is a major negative modifier")
    pdf.ln(2)

    pdf.h2("Anxiety & Stress-Related (F40-F43)")
    pdf.p(
        "Key distinction: adjustment disorder (F43) is time-limited by "
        "ICD definition (onset within 1 month, resolution within 6 months) "
        "and carries a much better prognosis than GAD (F41.1). Z73 (burnout) "
        "is NOT a psychiatric diagnosis -- it is a Z-code and should be "
        "underwritten near-standard unless accompanied by an F-code."
    )
    pdf.table(
        headers=["Condition", "Median AU", "Decision Guidance"],
        rows=[
            ["F43 adjustment, resolved >1yr", "2-4 weeks", "Accept standard"],
            ["GAD (F41.1), controlled on SSRI", "4-6 wk/yr", "Loading +25-50%"],
            ["Panic disorder (F41.0), untreated", "3-8 wk/yr", "Loading +50% or postpone"],
            ["PTSD (F43.1), chronic", "Variable", "Often decline; severity-dependent"],
            ["Z73 burnout, no F-code", "1-3 weeks", "Accept near-standard"],
        ],
        col_widths=[52, 22, 50],
    )

    pdf.h2("Personality Disorders (F60-F61)")
    pdf.p(
        "Personality disorders are chronic by definition -- remission is not "
        "applicable. Borderline PD (F60.3) carries the highest KTG risk. "
        "Important: anankastic PD (F60.5) may have zero or negative AU "
        "impact in structured occupations. DBT completion for borderline "
        "is a significantly positive prognostic marker [T1]."
    )

    # ================================================================
    # CHAPTER 5: Musculoskeletal Conditions
    # ================================================================
    pdf.chapter_head(5, "Musculoskeletal Conditions")

    pdf.p(
        "Chapter M accounts for 25% of all sick days -- the largest single "
        "chapter. Non-specific back pain (M54) is the highest-volume "
        "AU diagnosis in Germany. The critical underwriting question is "
        "always: acute vs chronic."
    )

    pdf.h2("Non-Specific Back Pain (M54)")
    pdf.table(
        headers=["Stage", "AU Profile", "Decision", "Evidence"],
        rows=[
            ["Acute (<12 wk), single episode >1yr ago", "1-4 weeks, >90% resolve", "Accept standard", "[T1]"],
            ["Recurrent, 2-3 episodes in 3yr", "6-12 wk/yr", "Loading +25-50%", "[T2]"],
            ["Chronic (>12 wk), on opioids", "8-14 wk/yr", "Loading + MSK excl.", "[T1]"],
            ["Chronic + opioid dependence + failed rehab", "Permanent risk", "Decline", "[T1]"],
        ],
        col_widths=[46, 32, 30, 14],
    )

    pdf.h3("Red Flags for Back Pain")
    pdf.li("Opioid prescription -- signals failed conservative management")
    pdf.li("Occupational class 3-4 (physical labour) -- multiplicative risk")
    pdf.li("Comorbid depression -- central sensitisation pathway")
    pdf.li("Chronification >12 weeks -- dramatically different prognosis")
    pdf.ln(2)

    pdf.h2("Disc Disease (M50/M51)")
    pdf.p(
        "Distinguish: M51 (degeneration) vs M51.1 (radiculopathy with "
        "nerve root involvement). Post-discectomy status requires surgical "
        "outcome assessment. Failed back surgery syndrome (persistent M54.5 "
        "post-surgery) is typically a decline."
    )

    pdf.h2("Fibromyalgia (M79.7)")
    pdf.p(
        "Central sensitisation condition with strong psychiatric comorbidity "
        "(depression in ~50%). Must be separated from generic M79 myalgia. "
        "Expected AU: 6-12 weeks/year. FMS + depression = Interaction Case A "
        "(synergistic amplification, 1.75x AU multiplier). Medication markers: "
        "duloxetine, pregabalin, amitriptyline indicate confirmed FMS."
    )

    pdf.h2("Rheumatoid Arthritis (M05/M06)")
    pdf.p(
        "Key distinction: seropositive RA (M05) is more erosive than "
        "seronegative (M06). DAS28 <2.6 = remission marker. Medication "
        "escalation (mono csDMARD -> combination -> biologics/JAK) indicates "
        "disease severity. RA elevates CV risk by ~50% [T1]. Accept loading "
        "20-40% if remission >12mo, DAS28 <2.6, stable DMARD, no erosions."
    )

    # ================================================================
    # CHAPTER 6: Cardiovascular Conditions
    # ================================================================
    pdf.chapter_head(6, "Cardiovascular Conditions")

    pdf.p(
        "Cardiovascular disease is modelled as a 5-state continuous-time "
        "Markov chain: Healthy -> Risk Factors -> Chronic Condition -> "
        "Complication -> Major Event (absorbing). The model captures "
        "the progressive, irreversible nature of CV disease."
    )
    pdf.figure(chart_cv_ctmc(),
               "Cardiovascular 5-state CTMC: state occupation probabilities starting from Healthy",
               w=130)

    pdf.h2("Hypertension (I10-I13)")
    pdf.table(
        headers=["Scenario", "Decision", "Loading"],
        rows=[
            ["Stage 1, monotherapy, no organ damage", "Accept", "Standard"],
            ["Stage 2, 2+ agents, no organ damage", "Loading", "+25-50%"],
            ["Resistant (3+ agents) or organ damage (LVH, CKD)", "Loading", "+75-150%"],
            ["Malignant HTN or hypertensive emergency", "Decline", "--"],
        ],
        col_widths=[60, 18, 28],
    )

    pdf.h2("IHD & Acute MI (I20-I25)")
    pdf.p(
        "LVEF is the single most important prognostic parameter for "
        "ischaemic heart disease. LVEF >=50% (preserved) vs 30-49% "
        "(reduced) vs <30% (severely reduced) determines the entire "
        "underwriting trajectory. Time since last event is the second "
        "key factor: risk decays exponentially over the first 2 years."
    )

    pdf.h2("Heart Failure (I50)")
    pdf.p(
        "NYHA class and LVEF drive the rating. NYHA I with LVEF >=45% "
        "on guideline therapy: loading +100-200%. NYHA III-IV or LVEF "
        "<35%: decline. Consistency rule: if I50 diagnosed, NT-proBNP "
        "should be >125 pg/mL."
    )

    pdf.h2("Atrial Fibrillation (I48)")
    pdf.p(
        "CHA2DS2-VASc score determines stroke risk loading. Paroxysmal "
        "AF (I48.0) on DOAC: loading +25-50%. Permanent AF with "
        "structural heart disease: loading +100-200%. Key algorithmic "
        "failure: I48.91 (unspecified) should be resolved to subtype "
        "before loading."
    )

    # ================================================================
    # CHAPTER 7: Metabolic & Renal
    # ================================================================
    pdf.chapter_head(7, "Metabolic & Renal Conditions")

    pdf.h2("Type 2 Diabetes (E11)")
    pdf.p(
        "HbA1c is the primary control metric. E11.9 (uncomplicated) on "
        "metformin with HbA1c <7.0%: loading +25-50%. Organ damage "
        "(E11.2 renal, E11.3 ophthalmic): loading +100-200%. "
        "Insulin-dependent with HbA1c >10%: decline. "
        "Diabetes has the most extensive downstream comorbidity multipliers: "
        "IHD 2.0x, CKD 2.5x, PVD 1.8x, stroke 1.5x, HF 1.5x, Alzheimer 1.5x."
    )

    pdf.h2("CKD Staging (N18)")
    pdf.table(
        headers=["Stage", "eGFR", "Decision", "Loading"],
        rows=[
            ["Stage 1 (N18.1)", ">=90", "Accept", "Investigate cause"],
            ["Stage 2 (N18.2)", "60-89", "Loading", "+25-50%"],
            ["Stage 3 (N18.3)", "30-59", "Loading", "+75-150%"],
            ["Stage 4 (N18.4)", "15-29", "Decline", "--"],
            ["Stage 5/ESRD (N18.5/6)", "<15", "Decline", "--"],
        ],
        col_widths=[30, 18, 18, 28],
    )

    pdf.h2("Obesity (E66)")
    pdf.p(
        "Key as a comorbidity amplifier: obesity -> diabetes 2.5x, "
        "-> hypertension 1.8x, -> dyslipidemia 2.0x, -> MSK 1.5x. "
        "Post-bariatric surgery: assess on current metabolic parameters, "
        "not historical code (Interaction Case H -- risk reversal)."
    )

    # ================================================================
    # CHAPTER 8: Neurological Conditions
    # ================================================================
    pdf.chapter_head(8, "Neurological Conditions")

    pdf.h2("Alzheimer's Disease (G30, F00)")
    pdf.p(
        "Alzheimer's disease follows a 7-state CTMC trajectory. Any "
        "confirmed diagnosis is typically a decline for life and disability "
        "products. MCI is a postpone pending longitudinal assessment. "
        "Prescription of cholinesterase inhibitors (Donepezil, Rivastigmine, "
        "Galantamine) or Memantine signals confirmed dementia."
    )
    pdf.figure(chart_alz_ctmc(),
               "Alzheimer 7-state CTMC: progression from Normal Cognition through Death",
               w=130)

    pdf.h2("Multiple Sclerosis (G35)")
    pdf.p(
        "EDSS (0-10) is the most important functional marker. RRMS on "
        "high-efficacy DMT with EDSS 0-1.5 and 0 relapses in 2 years: "
        "possible acceptance with neuro exclusion. EDSS >=3.0 or SPMS/PPMS: "
        "decline. Newly diagnosed: postpone 3-5 years."
    )

    # ================================================================
    # CHAPTER 9: Comorbidity Assessment
    # ================================================================
    pdf.chapter_head(9, "Comorbidity Assessment & Interactions")

    pdf.p(
        "Comorbidity is multiplicative, not additive. The Charlson "
        "Comorbidity Index (Quan-adapted) assigns weights to 17 categories. "
        "10-year survival: S(10) = 0.983^exp(CCI x 0.9). Higher-severity "
        "categories supersede lower (complicated diabetes weight=2 supersedes "
        "uncomplicated weight=1)."
    )

    pdf.h2("Key Comorbidity Interactions")
    pdf.p(
        "Eight documented cases demonstrate why naive additive loading "
        "is clinically incorrect. Algorithms that sum separate condition "
        "loadings will systematically misprice these combinations."
    )
    pdf.table(
        headers=["Case", "Conditions", "Interaction", "AU Impact", "Recommendation"],
        rows=[
            ["A", "Depression + FMS", "Synergistic", "12-20 wk/yr", "Decline or dual exclusion"],
            ["B", "T2DM + HTN + Obesity", "Multiplicative CV", "4-8 wk/yr", "40-60% integrated loading"],
            ["C", "RRMS + Depression", "Neurobiological", "16-24 wk/yr", "Decline standard KTG"],
            ["D", "Paroxysmal AF + HTN", "Over-penalised", "2-4 wk/yr", "25-30% single loading"],
            ["E", "Borderline + Substance", "Synergistic psych", "8-24 wk/yr", "Decline"],
            ["F", "Post-disc surgery + LBP", "Recovery-dependent", "2-12 wk/yr", "Physician report req."],
            ["G", "Migraine + GAD", "Bidirectional", "4-8 wk/yr", "20-30% loading"],
            ["H", "Obesity post-bariatric", "Risk reversal", "Near-normal", "Assess current labs"],
        ],
        col_widths=[10, 30, 24, 20, 42],
    )
    pdf.table_caption("Comorbidity interaction matrix (8 documented cases)")

    pdf.key_concept(
        "Case D (AF + controlled HTN) and Case H (post-bariatric) are "
        "cases where algorithms OVER-penalise. Recognising when an "
        "algorithm is too harsh is as important as catching underestimation."
    )

    # ================================================================
    # CHAPTER 10: Temporal Risk Framework
    # ================================================================
    pdf.chapter_head(10, "Temporal Risk Framework")

    pdf.p(
        "A diagnosis coded 5 years ago does not carry the same risk as "
        "one coded 6 months ago. The temporal framework defines look-back "
        "windows, remission criteria, and red flags per condition."
    )

    pdf.table(
        headers=["Condition", "Standard", "Extended", "Remission Definition"],
        rows=[
            ["Mood (F32-F34)", "3yr", "5yr", "No MH codes + no psych meds 24mo"],
            ["Bipolar (F31)", "10yr", "Lifetime", "Stable lithium >5yr, no hospital"],
            ["Anxiety (F40-F41)", "2yr", "3yr", "No AU >12mo, <=1 medication"],
            ["Adjustment (F43)", "1yr", "2yr", "Resolved by definition (<6mo)"],
            ["Acute LBP (M54)", "1yr", "3yr recurrent", "No AU >6 months"],
            ["Post-MI (I21)", "2yr", "5yr", "LVEF >=50%, no recurrence"],
            ["CV chronic (I10-I50)", "Ongoing", "Ongoing", "Chronic, does not remit"],
            ["Cancer (C00-C97)", "5yr", "10yr", "Complete remission, no treatment"],
            ["T2 Diabetes (E11)", "Ongoing", "Ongoing", "Chronic (bariatric exception)"],
            ["MS (G35)", "Lifetime", "Lifetime", "Chronic progressive, no decay"],
        ],
        col_widths=[32, 16, 18, 60],
    )
    pdf.table_caption("Look-back windows and remission definitions by condition")

    pdf.h2("Red Flags That Override Time Decay")
    pdf.li(">=3 psychiatric episodes regardless of timing")
    pdf.li("Inpatient hospitalisation for any psychiatric condition")
    pdf.li("Opioid prescription for any MSK condition")
    pdf.li("Failed rehabilitation or Wiedereingliederung")
    pdf.li("Escalation from monotherapy to polytherapy")
    pdf.li("Disability pension application (Erwerbsminderungsrente)")
    pdf.li("Active substance dependence (F10-F19 within 2 years)")
    pdf.li("LVEF <40% at any time")
    pdf.li("CKD progression (>=1 stage decline in 12 months)")
    pdf.ln(2)

    pdf.key_concept(
        "Absence of evidence is not evidence of absence. No GP visits "
        "and no diagnosis codes may mean untreated, not remitted. "
        "Self-employed applicants often have no AU history because they "
        "work through illness -- this reflects payment structure, not health."
    )

    # ================================================================
    # CHAPTER 11: Data Quality & Failure Detection
    # ================================================================
    pdf.chapter_head(11, "Data Quality & Failure Mode Detection")

    pdf.p(
        "MedRisk computes a Data Quality Score (DQS) for each patient "
        "before any model makes a prediction. The DQS determines how much "
        "a downstream model should trust its own input."
    )
    pdf.figure(chart_dqs_components(),
               "DQS component weights: Completeness (40%), Consistency (35%), Recency (25%)",
               w=100)

    pdf.h2("DQS Components")
    pdf.table(
        headers=["Component", "Weight", "Definition"],
        rows=[
            ["Completeness", "0.40", "Fraction of 40 expected features observed"],
            ["Consistency", "0.35", "Fraction of 5 clinical rules that pass"],
            ["Recency", "0.25", "Exponential decay on lab ages (t1/2 = 1.4yr)"],
        ],
        col_widths=[28, 14, 84],
    )

    pdf.h3("Consistency Rules")
    pdf.li("Diabetes (E11) diagnosed -> HbA1c >= 5.7%")
    pdf.li("CKD stage 4-5 (N18.4/5/6) -> eGFR < 30")
    pdf.li("Heart failure (I50) -> NT-proBNP > 125 pg/mL")
    pdf.li("Hypertension (I10) -> SBP > 120 OR on antihypertensive")
    pdf.li("No diabetes code -> HbA1c < 6.5%")
    pdf.ln(2)

    pdf.h2("Plausible-But-Wrong (PBW) Detection")
    pdf.p(
        "The core intellectual contribution of MedRisk. PBW detects "
        "when a model produces a confident prediction on insufficient "
        "data -- the most dangerous failure mode in automated underwriting. "
        "Three signals:"
    )
    pdf.table(
        headers=["Signal", "Threshold", "Meaning"],
        rows=[
            ["CCM (Calibration-Confidence Mismatch)", "|raw - calibrated| > 0.20", "Model confidence diverges from Platt-scaled estimate"],
            ["EPU (Epistemic Prediction Uncertainty)", "Decile spread > 3", "XGBoost, Cox, CTMC disagree on risk"],
            ["PBW (Plausible-But-Wrong)", "Conf > 80% AND DQS < 0.60", "High confidence on low-quality data"],
        ],
        col_widths=[48, 38, 50],
    )

    pdf.p(
        "Decision logic: No flags -> ACCEPT. CCM or EPU only -> REVIEW. "
        "PBW -> REJECT PREDICTION and escalate to human underwriter."
    )

    # ================================================================
    # CHAPTER 12: Decision Framework & Case Studies
    # ================================================================
    pdf.chapter_head(12, "Decision Framework & Case Studies")

    pdf.p(
        "Each case study presents an algorithm's output alongside the "
        "clinically correct decision, demonstrating common failure modes."
    )

    pdf.h2("Case 1: Single Mild Depression -- Algorithm Overreaction")
    pdf.p(
        "34F, admin worker, class 1. F32.0 (mild depression) 4 years "
        "ago. No current medication. No AU in 3 years. Algorithm: "
        "Loading +50% with psychiatric exclusion. Correct: Accept "
        "standard terms. The F32 code is outside the 3-year standard "
        "look-back window. Time-decay rules are essential."
    )

    pdf.h2("Case 2: Recurrent Depression -- Algorithm Underestimation")
    pdf.p(
        "42M, teacher, class 2. F33 with 3 episodes in 5 years "
        "(escalating AU: 5, 9, 11 weeks). Currently on sertraline. "
        "Algorithm: Loading +50%. Correct: Decline. Three episodes = "
        "chronic pattern. 5-year recurrence ~70%. Episode count >=3 "
        "is a red flag overriding time decay."
    )

    pdf.h2("Case 3: Metabolic Triad -- Naive Linear Stacking")
    pdf.p(
        "55M, office worker. E11.9 (T2D, HbA1c 7.2%), I10 (HTN), "
        "E66.0 (obesity, BMI 34). Algorithm: +175% (T2D +50%, HTN "
        "+50%, Obesity +75% summed). Correct: +40-60% integrated "
        "metabolic loading. This is Interaction Case B -- the "
        "metabolic triad requires a single integrated cardiovascular "
        "risk assessment, not naive addition."
    )

    pdf.h2("Case 4: Post-Bariatric -- Code Anchoring")
    pdf.p(
        "45F, marketing. Historical E66.0 (BMI 44). Post-bariatric "
        "sleeve 3 years ago. Current: BMI 27, HbA1c 5.3%, BP 120/78, "
        "lipids normal. Algorithm: Decline (based on historical code). "
        "Correct: Loading +15-25%. Current metabolic parameters are "
        "near-normal. This is Case H -- code-driven algorithms produce "
        "the wrong answer for risk reversal."
    )

    pdf.h2("Case 5: Algorithm Was Correct")
    pdf.p(
        "50M, construction supervisor. F33.2 (3 episodes, 10-14 weeks "
        "each), M51.1 + microdiscectomy, M54.5 recurrence (worsening), "
        "E11.9 (HbA1c 8.2%). Algorithm: Decline. Correct: Decline "
        "confirmed. Three independent high-risk conditions with no "
        "favourable markers. Validation is as important as override."
    )

    pdf.key_concept(
        "Five override categories: (1) Factual error -- wrong ICD "
        "interpretation. (2) Missing clinical context -- occupation, "
        "medication, functional status. (3) Interaction failure -- "
        "naive risk addition for synergistic conditions. (4) Threshold "
        "judgment -- boundary case, human discretion. (5) Algorithm "
        "validated -- human confirms output correct."
    )

    # ── Final note ──
    pdf.ln(6)
    pdf.set_draw_color(*C_ACCENT)
    pdf.set_line_width(0.6)
    pdf.line(18, pdf.get_y(), pdf._pw - 18, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*C_CAPTION)
    pdf.multi_cell(pdf._cw, 4, safe(
        "Medical Underwriting Fundamentals -- a major European insurer. "
        "All clinical data is synthetic (MedRisk v2.0). "
        "Evidence tiers: [T1] guideline-level, [T2] observational, "
        "[T3] expert judgment. Not medical advice; for risk assessment only. "
        "the author, Helmholtz Munich, April 2026."
    ))

    # ── Output ──
    out_path = OUT / "underwriting_fundamentals.pdf"
    pdf.output(str(out_path))
    n_pages = pdf.page_no()
    size_kb = out_path.stat().st_size / 1024
    logger.info("Generated %s: %d pages, %.0f KB", out_path.name, n_pages, size_kb)
    return out_path


if __name__ == "__main__":
    build_pdf()
