"""MedRisk-ADH -- KTG Domain Reference Flashcards.

Quick-reference flashcard page for a major European insurer domain referencearation.
Covers clinical thresholds, ICD-10 codes, failure modes, comorbidity interactions,
and regulatory/process knowledge.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
_APP_DIR = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

import streamlit as st

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="KTG Flashcards — Domain Reference",
    page_icon="🗂",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Page styling (Doctolib Oxygen — same as page 5)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .block-container { max-width: 1100px; }
    .stApp, .main, [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
    }
    .section-label {
        color: #1a365d; font-size: 0.72rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 1.5px;
        margin-bottom: 0.8rem; padding-bottom: 0.4rem;
        border-bottom: 2px solid #2b6cb0; display: inline-block;
    }
    .page-subtitle {
        color: #2d3748; font-size: 0.95rem; margin-top: -0.5rem; margin-bottom: 1.2rem;
    }
    h1, h2, h3, h4 { color: #1a365d !important; }
    p, li { color: #2d3748 !important; }
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div,
    [data-testid="stSidebar"] > div > div {
        background-color: #f7fafc !important;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: #1a365d !important; }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span { color: #2d3748 !important; }
    .icd-badge {
        display: inline-block; background: #edf2f7; color: #2b6cb0;
        padding: 3px 10px; border-radius: 8px; font-weight: 700;
        font-size: 0.8rem; letter-spacing: 0.5px; margin-left: 8px;
    }
    .dqs-box {
        border-radius: 8px; padding: 18px; margin-bottom: 8px;
    }
    .dqs-good { background: #f0fff4; border: 1px solid #c6f6d5; }
    .dqs-bad  { background: #fff5f5; border: 1px solid #fed7d7; }
    /* Flashcard-specific */
    .fc-question {
        background: #ebf4ff;
        border-left: 4px solid #2b6cb0;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 4px;
        font-size: 0.97rem;
        color: #1a365d !important;
        font-weight: 600;
    }
    .fc-answer {
        background: #f0fff4;
        border-left: 4px solid #38a169;
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 0.93rem;
        color: #22543d !important;
        margin-bottom: 4px;
    }
    .fc-answer-warn {
        background: #fffaf0;
        border-left: 4px solid #d69e2e;
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 0.93rem;
        color: #744210 !important;
        margin-bottom: 4px;
    }
    .fc-answer-danger {
        background: #fff5f5;
        border-left: 4px solid #c53030;
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 0.93rem;
        color: #742a2a !important;
        margin-bottom: 4px;
    }
    .score-badge {
        background: #2b6cb0; color: #ffffff;
        border-radius: 12px; padding: 6px 16px;
        font-size: 1.05rem; font-weight: 700;
        display: inline-block; margin-bottom: 8px;
    }
    .category-pill {
        display: inline-block; background: #bee3f8; color: #2b6cb0;
        padding: 2px 8px; border-radius: 10px;
        font-size: 0.72rem; font-weight: 700;
        margin-right: 4px; letter-spacing: 0.3px;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
if "fc_revealed" not in st.session_state:
    st.session_state.fc_revealed: dict[str, bool] = {}
if "fc_correct" not in st.session_state:
    st.session_state.fc_correct: set[str] = set()
if "fc_total_seen" not in st.session_state:
    st.session_state.fc_total_seen: set[str] = set()


def _card_key(tab: str, idx: int) -> str:
    return f"{tab}_{idx}"


def _reveal(key: str) -> None:
    st.session_state.fc_revealed[key] = True
    st.session_state.fc_total_seen.add(key)


def _mark_correct(key: str) -> None:
    st.session_state.fc_correct.add(key)


def _reset_all() -> None:
    st.session_state.fc_revealed = {}
    st.session_state.fc_correct = set()
    st.session_state.fc_total_seen = set()


# ---------------------------------------------------------------------------
# Flashcard data
# ---------------------------------------------------------------------------

# Answer style: "good" (green), "warn" (yellow), "danger" (red)
# "danger" used for ABLEHNUNG / synergistic worst-case combos
# "warn" used for failure modes and cautionary notes
# Default: "good" (standard factual answers)

CARDS_KLINISCH: list[dict] = [
    {
        "q": "HbA1c-Schwelle fuer gut kontrollierte T2DM?",
        "a": "<7.0%  [Tier 1 — ADA/EASD Konsensus]",
        "style": "good",
    },
    {
        "q": "Anfallsfreie Dauer fuer Epilepsie-Annahme mit Zuschlag?",
        "a": ">=24 Monate auf stabiler Monotherapie  [Tier 1]",
        "style": "good",
    },
    {
        "q": "Rezidivrisiko nach 3 depressiven Episoden?",
        "a": ">90% Lebenszeitrezidiv  [Tier 1 — DGPPN S3-Leitlinie]",
        "style": "warn",
    },
    {
        "q": "Medianer AU bei einzelner schwerer Depression (F32.2)?",
        "a": "3-6 Monate; ~50% Rezidiv innerhalb 2 Jahre  [Tier 2]",
        "style": "warn",
    },
    {
        "q": "EDSS-Schwelle fuer MS-Ablehnung im KTG?",
        "a": "EDSS >= 3.0 — bedeutsame funktionelle Einschraenkung  [Tier 1]",
        "style": "danger",
    },
    {
        "q": "Migraene-Frequenz fuer Standardannahme (ggf. mit Zuschlag)?",
        "a": "<=4 Tage/Monat, gutes Triptanansprechen  [Tier 2]",
        "style": "good",
    },
    {
        "q": "Blutdruckmedikamente als Schweregrad-Proxy (I10)?",
        "a": "1 Mittel = mild; 2-3 = moderat; >=4 = resistent / hohes Risiko  [Tier 2]",
        "style": "warn",
    },
    {
        "q": "Karenzzeit bei privatem KTG?",
        "a": "42 Tage (6 Wochen Lohnfortzahlung nach §3 EFZG) — erst danach greift privates KTG",
        "style": "good",
    },
    {
        "q": "Maximale GKV-Krankengeld-Dauer pro Erkrankung?",
        "a": "78 Wochen total: 6 Wochen Lohnfortzahlung + 72 Wochen GKV-Krankengeld",
        "style": "good",
    },
    {
        "q": "DQS-Schwelle fuer PBW-Flag (Plausible-but-Wrong)?",
        "a": "DQS < 0.60 bei Modellkonfidenz > 0.80 — Widerspruch triggert Review",
        "style": "warn",
    },
    {
        "q": "Charlson-Score ab dem KTG-Ablehnung wahrscheinlich?",
        "a": "CCI >= 5 — signifikant erhoehte Mortalitaet und AU-Wahrscheinlichkeit",
        "style": "danger",
    },
    {
        "q": "RA-Remissionskriterium (DAS28)?",
        "a": "DAS28 < 2.6 fuer >=6 Monate  [Tier 1 — ACR/EULAR 2010]",
        "style": "good",
    },
    {
        "q": "Schwelle chronischer Kreuzschmerz (M54.5)?",
        "a": ">12 Wochen Beschwerdedauer — Risiko zentraler Sensibilisierung  [Tier 1 — NVL]",
        "style": "warn",
    },
    {
        "q": "Fibromyalgie (M79.7): typische jaehrliche AU-Last?",
        "a": "6-10 Wochen/Jahr; 10-20% dauerhaft krankgeschrieben  [Tier 2]",
        "style": "warn",
    },
]

CARDS_ICD: list[dict] = [
    {
        "q": "F33.1 — Welche KTG-Risikokategorie und Begruendung?",
        "a": (
            "Rezidivierende depressive Stoerung, mittelgradig — HOHES KTG-Risiko.\n\n"
            "Lebenszeitrezidiv >90% nach 3 Episoden. Median-AU 3-6 Monate je Schub."
        ),
        "style": "danger",
    },
    {
        "q": "M51 vs M51.1 — klinischer Unterschied im Underwriting?",
        "a": (
            "M51 = Bandscheibendegeneration (moderat, mechanisch).\n\n"
            "M51.1 = Lumbale Radikulopathie (signifikant hoeher: Operationsrisiko, laengere AU). "
            "Kategorisch verschieden — nicht interchangeable!"
        ),
        "style": "warn",
    },
    {
        "q": "I48.0 vs I48.2 — Prognose-Unterschied?",
        "a": (
            "I48.0 = paroxysmales Vorhofflimmern (intermittierend, Kardioversion moeglich, besser).\n\n"
            "I48.2 = permanentes Vorhofflimmern (chronisch, weniger kardiale Reserve). "
            "I48.2 traegt hoehere Schlaganfall- und HI-Last."
        ),
        "style": "warn",
    },
    {
        "q": "E11.9 vs E11.7 — warum nicht addierbar?",
        "a": (
            "E11.9 = T2DM ohne Komplikationen (kontrollierbar, gutartig).\n\n"
            "E11.7 = T2DM mit multiplen Komplikationen (Nephropathie + Retinopathie + Neuropathie). "
            "Nicht vergleichbar — E11.7 erfordert eigene Kalkulation!"
        ),
        "style": "danger",
    },
    {
        "q": "Z73 — Ist das eine psychiatrische Diagnose?",
        "a": (
            "NEIN. Z73 (Ausgebranntsein / Burnout) ist ein ICD-10 Kontaktanlasscode (Z-Kapitel).\n\n"
            "Keine F-Diagnose. Immer nach zugrundeliegendem F-Code suchen (F32, F41, F48). "
            "Alleiniger Z73 hat deutlich geringeres Risiko."
        ),
        "style": "warn",
    },
    {
        "q": "M79.1 vs M79.7 — Schweregrad und AU-Muster?",
        "a": (
            "M79.1 = Myalgie (selbstlimitierend, Tage bis Wochen).\n\n"
            "M79.7 = Fibromyalgie (chronisch, 6-10 Wochen AU/Jahr, zentrales Schmerzsyndrom). "
            "Gleicher Code-Block, voellig unterschiedliches Risikoprofil."
        ),
        "style": "warn",
    },
    {
        "q": "F60.3 vs F60.5 — AU-Risiko im Vergleich?",
        "a": (
            "F60.3 = Emotional instabile Persoenlichkeitsstoerung / Borderline: HOECHSTES AU-Risiko. "
            "Krisenhafte Dekompensation, Impulsivitaet, haeufige Kurzerkrankungen.\n\n"
            "F60.5 = Anankastische PS: kann AU sogar reduzieren (hohe Pflichterfullung). "
            "Gegensaetzliche Risikorichtungen!"
        ),
        "style": "danger",
    },
    {
        "q": "M05 vs M06 — serologische RA und Prognose?",
        "a": (
            "M05 = Seropositiv RA (RF+/CCP+): erosiver Verlauf, raschere Gelenkdestruktion, "
            "schlechtere langfristige Prognose  [Tier 1 — ACR/EULAR].\n\n"
            "M06 = Seronegativ RA: heterogenes Kollektiv, mildere Verlaeufe moeglich. "
            "M05 = hoehere Zuschlaege gerechtfertigt."
        ),
        "style": "warn",
    },
]

CARDS_FAILURE: list[dict] = [
    {
        "q": "Algorithmus lehnt alle F32 ab, egal ob Einzelepisode vor 5 Jahren — welcher Failure Mode?",
        "a": (
            "OVERREACTION (Tier-A Failure Mode).\n\n"
            "Ignoriert zeitlichen Risikoabfall und Episodenzahl. "
            "Einmalige Episode vor >3 Jahren naehert sich Normrisiko an. "
            "Fix: zeitgewichteter Schwellenwert + Episodenzaehler."
        ),
        "style": "danger",
    },
    {
        "q": "Algorithmus wendet Zeitabklingung auf F33 mit 3 Episoden an — was ist falsch?",
        "a": (
            "UNDERESTIMATION (Tier-A Failure Mode).\n\n"
            "Zeitabklingung gilt NICHT fuer rezidivierende Stoerungen (F33). "
            "Jede neue Episode bestaetigt Chronizitaet. "
            "Fix: Episodenzaehler ueberschreibt Zeitabklingung ab Episode 3."
        ),
        "style": "danger",
    },
    {
        "q": "Algorithmus behandelt Z73 gleichwertig mit F41 — Problem?",
        "a": (
            "OVERREACTION (Tier-B Failure Mode).\n\n"
            "Z73 ist ein Kontaktanlasscode, keine Stoerungsdiagnose. "
            "Fix: Z73 ohne begleitenden F-Code erhaelt eigene (niedrigere) Risikoklasse."
        ),
        "style": "warn",
    },
    {
        "q": "F43.2 (Anpassungsstoerung) wird ohne Pruefung frueher F32/F33-Codes akzeptiert — Risiko?",
        "a": (
            "UNDERESTIMATION (Tier-B Failure Mode).\n\n"
            "F43.2 kann 'weichere' Kodierung einer rezidivierenden Depression sein. "
            "Fix: Bei F43.2 immer historische F32/F33-Codes pruefen; "
            "bei >=2 F-Episoden hoeheres Risikoprofil anwenden."
        ),
        "style": "warn",
    },
    {
        "q": "Drei separate Zuschlaege fuer E11 + I10 + E78 werden additiv gestapelt — Problem?",
        "a": (
            "NAIVE LINEAR STACKING (Tier-B Failure Mode).\n\n"
            "Metabolische Komorbiditaeten teilen pathophysiologische Mechanismen (Insulinresistenz). "
            "Additiv-Stapeln ueberschaetzt Unabhaengigkeit. "
            "Fix: Integrierter metabolischer Zuschlag mit Kappungsregel."
        ),
        "style": "warn",
    },
    {
        "q": "Identische ICD-Geschichte traegt gleiches Risiko fuer Physiotherapeut und Softwareentwickler — Problem?",
        "a": (
            "MISSING DATA — Beruf fehlt in der Risikobewertung (Tier-B Failure Mode).\n\n"
            "Muskuloskelettales Risiko ist stark berufsabhaengig. "
            "Fix: Berufsklasse als Pflichtfeld in KTG-Antrag; eigener Feature-Kanal."
        ),
        "style": "warn",
    },
    {
        "q": "Teilzeitarbeit (60%) seit 2 Jahren wird nicht erfasst — welcher Blinde Fleck?",
        "a": (
            "MISSING FUNCTIONAL STATUS (Tier-C Failure Mode).\n\n"
            "ICD-Codes erfassen Arbeitsfaehigkeit nicht. Teilzeit kann bereits adaptierte "
            "Einschraenkung signalisieren. "
            "Fix: Beschaeftigungsgrad als separates Risikosignal, nicht aus ICD ableitbar."
        ),
        "style": "warn",
    },
    {
        "q": "Kein AU-Nachweis bei Selbststaendigem = niedrigeres Risiko — korrekte Interpretation?",
        "a": (
            "NEIN — AU HISTORY GAP (Tier-C Failure Mode).\n\n"
            "Selbststaendige reichen selten AU-Bescheinigungen ein (wirtschaftlicher Anreiz). "
            "Fehlende AU-History = Zahlungsstruktur, nicht Gesundheitsstatus. "
            "Fix: Selbststaendigenstatus als Datenqualitaets-Flag, kein positives Signal."
        ),
        "style": "danger",
    },
]

CARDS_KOMORBIDITAT: list[dict] = [
    {
        "q": "F33 + M79.7 (Depression + Fibromyalgie) — Interaktionstyp und AU-Schaetzung?",
        "a": (
            "SYNERGISTISCH — zentrale Sensibilisierung + serotonerge Dysregulation verstaerken sich.\n\n"
            "AU-Schaetzung: 12-20 Wochen/Jahr (1.5-2x Einzeldiagnose). "
            "Empfehlung: ABLEHNUNG oder Doppelausschluss (psychisch + muskuloskeletal)."
        ),
        "style": "danger",
    },
    {
        "q": "E11 + I10 + E66 (Diabetes + Hypertonie + Adipositas) — wie kalkulieren?",
        "a": (
            "MULTIPLIKATIVES CV-Risiko — nicht additiv!\n\n"
            "Metabolisches Syndrom: gemeinsamer Pathomechanismus (Insulinresistenz). "
            "Integrierter Zuschlag 40-60% genuegt; drei Einzelzuschlaege NICHT stapeln. "
            "Kappungsregel anwenden."
        ),
        "style": "warn",
    },
    {
        "q": "I48 + I10 kontrolliert (Vorhofflimmern + Hypertonie) — Risikobewertung?",
        "a": (
            "UEBERBESTRAFT wenn separates Stapeln.\n\n"
            "I10 ist bekannter AF-Trigger — haeufig kausal zusammenhaengend. "
            "DOAC-Therapie zeigt Schlaganfallrisiko-Management. "
            "Einzelner moderater Zuschlag 25-30% genuegt."
        ),
        "style": "warn",
    },
    {
        "q": "F60.3 + F1x.2 (Borderline-PS + Suchtabhaengigkeit) — KTG-Entscheidung?",
        "a": (
            "SYNERGISTISCH PSYCHIATRISCH — instabilstes Profil.\n\n"
            "Impulsivitaet + Sucht = haeufige Krisen, unvorhersehbare AU-Muster. "
            "Empfehlung: ABLEHNUNG fuer KTG. Kein Zuschlag oder Ausschluss allein ausreichend."
        ),
        "style": "danger",
    },
    {
        "q": "G35 + F33 (MS + Depression) — warum besonders hoch?",
        "a": (
            "NEUROBIOLOGISCHE Komorbidditaet — Depression bei MS ist oft biologisch bedingt "
            "(Laesionen in emotionalen Netzwerken) und therapieresistenter.\n\n"
            "AU-Schaetzung: 16-24+ Wochen/Jahr. "
            "Empfehlung: ABLEHNUNG oder sehr hoher Zuschlag + Doppelausschluss."
        ),
        "style": "danger",
    },
    {
        "q": "E66 Klasse III post-bariatrisch (BMI 43 -> 29) — aktuelle Bewertung?",
        "a": (
            "RISIKO-UMKEHR — historischer ICD-Code E66 spiegelt aktuellen Status NICHT wider.\n\n"
            "Entscheidend: aktueller metabolischer Status (HbA1c, BD, Lipide). "
            "Bei metabolischer Remission: moderater Zuschlag statt Hochrisiko-Einstufung. "
            "Konzeptdrift beachten!"
        ),
        "style": "warn",
    },
    {
        "q": "G43 + F41.1 (Migraene + GAD) — Wechselwirkung?",
        "a": (
            "BIDIREKTIONAL — Angst senkt Schmerzschwelle und erhoelt Attackenfrequenz; "
            "Migraene verstaerkt Angst und Kontrollverlust.\n\n"
            "AU-Schaetzung: 4-8 Wochen/Jahr. "
            "Empfehlung: Moderater Zuschlag 20-30%."
        ),
        "style": "warn",
    },
    {
        "q": "G40 (Epilepsie) + Depression — moegliche Ursache?",
        "a": (
            "IATROGEN — Levetiracetam und Topiramat koennen Stimmungsstoerungen und Depression "
            "als UAW verursachen.\n\n"
            "Wenn Depression separat kodiert: AED-Kausalitaet nicht automatisch erkannt. "
            "Fix: ATC-Code auf AED-UAW-Profil pruefen vor psychiatrischem Risikozuschlag."
        ),
        "style": "warn",
    },
]

CARDS_REGULIERUNG: list[dict] = [
    {
        "q": "Was ist Karenzzeit bei KTG und welche gesetzliche Grundlage?",
        "a": (
            "Wartezeit vor Aktivierung des privaten KTG-Anspruchs.\n\n"
            "Ueblicherweise 42 Tage (6 Wochen Lohnfortzahlung nach §3 EFZG). "
            "Private KTG greift ab Tag 43 der ununterbrochenen AU."
        ),
        "style": "good",
    },
    {
        "q": "Art. 9 DSGVO — Relevanz fuer medizinisches Underwriting?",
        "a": (
            "Gesundheitsdaten sind 'besondere Kategorien' personenbezogener Daten.\n\n"
            "Verarbeitung nur zulaessig mit: ausdruecklicher Einwilligung ODER "
            "versicherungsrechtlicher Grundlage (§22 BDSG). "
            "Jede Risikoentscheidung muss dokumentiert und nachvollziehbar sein."
        ),
        "style": "good",
    },
    {
        "q": "§213 VVG — Was regelt das fuer den Antragsprozess?",
        "a": (
            "Auskunftspflichten bei Versicherungsvertraegen.\n\n"
            "Gesundheitsfragen muessen relevant und verhaeltnismaessig sein. "
            "Unzulaessig: unverhraeltnismaessig tiefe Eingriffe oder nicht-risikoverbundene Fragen. "
            "Relevant fuer Design des KTG-Antragsfragebogens."
        ),
        "style": "good",
    },
    {
        "q": "Was sind die 5 menschlichen Override-Kategorien im Governance-Modell?",
        "a": (
            "1: Faktenfehler (falsche Datenquelle)\n"
            "2: Fehlender klinischer Kontext (z.B. Remission nicht erfasst)\n"
            "3: Interaktionsfehler (Komorbidditaets-Stapeln)\n"
            "4: Schwellenwert-Ermessen (Grenzfall)\n"
            "5: Algorithmus validiert (kein Override notwendig)"
        ),
        "style": "good",
    },
    {
        "q": "Was ist Concept Drift im KTG-Underwriting-Kontext?",
        "a": (
            "Statistische Beziehung zwischen klinischen Features und korrekten Entscheidungen "
            "aendert sich ueber Zeit.\n\n"
            "Beispiel: verbesserte MS-Therapie (Natalizumab) macht historisch hohes G35-Risiko "
            "fuer neue Kohorte zu niedrig. Modell unterschaetzt Risiko der Neuen, ueberschaetzt Alten."
        ),
        "style": "warn",
    },
    {
        "q": "Mindestgroesse einer KTG-Regressionstestsuite vor Modellupdate?",
        "a": (
            ">=200 Faelle vor erstem Produktionseinsatz.\n\n"
            ">=500 laufend nach Go-Live. "
            "Tier-C Failure Modes (fehlende Kontextdaten) sollten >=30% der Suite ausmachen. "
            "Ziel: kein regressiver Fehler bei bekannten Failure Modes."
        ),
        "style": "good",
    },
    {
        "q": "Haeufigkeit unabhaengiger Modellpruefung (Clinical Review)?",
        "a": (
            "Mindestens jaehrlich.\n\n"
            "Zusaetzlich ausgeloest bei: AU-Epidemie oder Pandemie, "
            "Leitlinienupdate (z.B. DGPPN, DGK), "
            "oder >10% Aenderung der Ablehnungsquote durch Regelaenderung."
        ),
        "style": "good",
    },
    {
        "q": "Was ist DQS v2 und welche Tiers gibt es?",
        "a": (
            "Data Quality Score v2 — Composit aus Vollstaendigkeit, Konsistenz, Aktualitaet.\n\n"
            "Tiers:\n"
            "- adequate: DQS > 0.80 (normal processing)\n"
            "- caution: DQS 0.60-0.80 (enhanced review)\n"
            "- insufficient: DQS < 0.60 (manual underwriting required)"
        ),
        "style": "good",
    },
]

ALL_CARD_SETS: dict[str, list[dict]] = {
    "klinisch": CARDS_KLINISCH,
    "icd": CARDS_ICD,
    "failure": CARDS_FAILURE,
    "komorbiditat": CARDS_KOMORBIDITAT,
    "regulierung": CARDS_REGULIERUNG,
}


# ---------------------------------------------------------------------------
# Helper: render a single flashcard
# ---------------------------------------------------------------------------

def _render_card(tab_key: str, idx: int, card: dict) -> None:
    key = _card_key(tab_key, idx)
    revealed = st.session_state.fc_revealed.get(key, False)
    correct = key in st.session_state.fc_correct

    st.markdown(
        f'<div class="fc-question"><span class="category-pill">{idx + 1}</span> {card["q"]}</div>',
        unsafe_allow_html=True,
    )

    if not revealed:
        col_btn, _ = st.columns([1, 4])
        with col_btn:
            if st.button("Antwort anzeigen", key=f"show_{key}"):
                _reveal(key)
                st.rerun()
    else:
        style = card.get("style", "good")
        css_class = {
            "good": "fc-answer",
            "warn": "fc-answer-warn",
            "danger": "fc-answer-danger",
        }.get(style, "fc-answer")

        answer_html = card["a"].replace("\n\n", "<br><br>").replace("\n", "<br>")
        st.markdown(
            f'<div class="{css_class}">{answer_html}</div>',
            unsafe_allow_html=True,
        )

        if not correct:
            col_ok, col_no, _ = st.columns([1, 1, 4])
            with col_ok:
                if st.button("Gewusst", key=f"ok_{key}"):
                    _mark_correct(key)
                    st.rerun()
            with col_no:
                if st.button("Noch lernen", key=f"no_{key}"):
                    # Already seen, just don't mark correct — no state change needed
                    pass
        else:
            st.markdown(
                '<span style="color:#38a169; font-size:0.85rem; font-weight:700;">✓ Gewusst</span>',
                unsafe_allow_html=True,
            )

    st.markdown("<hr style='margin: 10px 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar: score + reset
# ---------------------------------------------------------------------------

def _total_cards() -> int:
    return sum(len(v) for v in ALL_CARD_SETS.values())


with st.sidebar:
    st.markdown("### KTG Domain Reference")
    st.markdown("---")

    total_all = _total_cards()
    total_seen = len(st.session_state.fc_total_seen)
    total_correct = len(st.session_state.fc_correct)

    pct_correct = int(100 * total_correct / total_seen) if total_seen > 0 else 0
    pct_seen = int(100 * total_seen / total_all)

    st.markdown(
        f'<div class="score-badge">Ergebnis: {total_correct} / {total_seen}</div>',
        unsafe_allow_html=True,
    )
    st.caption(f"{pct_seen}% der Karten gesehen — {pct_correct}% gewusst")

    st.markdown("**Fortschritt pro Kategorie:**")
    category_labels = {
        "klinisch": "Klinische Schwellenwerte",
        "icd": "ICD-10 Quiz",
        "failure": "Failure Modes",
        "komorbiditat": "Komorbiditaeten",
        "regulierung": "Regulierung & Prozess",
    }
    for key, label in category_labels.items():
        cards = ALL_CARD_SETS[key]
        n = len(cards)
        n_correct = sum(
            1 for i in range(n) if _card_key(key, i) in st.session_state.fc_correct
        )
        n_seen = sum(
            1 for i in range(n) if _card_key(key, i) in st.session_state.fc_total_seen
        )
        st.markdown(
            f"<small><b>{label}</b>: {n_correct}/{n_seen} "
            f"<span style='color:#718096'>({n} gesamt)</span></small>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    if st.button("Alle zuruecksetzen", use_container_width=True):
        _reset_all()
        st.rerun()

    st.markdown("---")
    st.markdown(
        "<small style='color:#718096'>"
        "Karten: 46 gesamt<br>"
        "Tiers: T1 = Cochrane/Meta-Analyse<br>"
        "T2 = grosse Kohortenstudie"
        "</small>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main page header
# ---------------------------------------------------------------------------

st.markdown("# KTG Underwriting — Interview-Vorbereitung")
st.markdown(
    '<div class="page-subtitle">'
    "46 Flashcards zu klinischen Schwellenwerten, ICD-10-Codes, Failure Modes, "
    "Komorbiditaets-Interaktionen und regulatorischen Grundlagen"
    "</div>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Progress bar (overall)
# ---------------------------------------------------------------------------
seen_frac = total_seen / total_all if total_all > 0 else 0.0
correct_frac = total_correct / total_all if total_all > 0 else 0.0
st.progress(correct_frac, text=f"{total_correct} von {total_all} Karten gewusst")

st.markdown("---")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Klinische Schwellenwerte",
    "ICD-10 Quiz",
    "Failure Modes",
    "Komorbiditaeten",
    "Regulierung & Prozess",
])

with tab1:
    st.markdown(
        '<span class="section-label">Klinische Schwellenwerte</span>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Klinische Grenzwerte, AU-Daten und KTG-spezifische Parameter. "
        "Quellen in eckigen Klammern: [T1] = Tier 1 Evidenz (Meta-Analyse/RCT), "
        "[T2] = Tier 2 (Kohortenstudie)."
    )
    for i, card in enumerate(CARDS_KLINISCH):
        _render_card("klinisch", i, card)

with tab2:
    st.markdown(
        '<span class="section-label">ICD-10 Quiz</span>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Kritische Code-Unterscheidungen, die Underwriting-Entscheidungen veraendern. "
        "Verwechslungen dieser Codes gehoeren zu den haeufigsten systematischen Fehlern."
    )
    for i, card in enumerate(CARDS_ICD):
        _render_card("icd", i, card)

with tab3:
    st.markdown(
        '<span class="section-label">Failure Modes</span>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Typische algorithmische Fehler bei der automatisierten KTG-Risikoklassifikation. "
        "Tier A = kritisch (Kernannahme verletzt), Tier B = signifikant, Tier C = Datenproblem."
    )
    for i, card in enumerate(CARDS_FAILURE):
        _render_card("failure", i, card)

with tab4:
    st.markdown(
        '<span class="section-label">Komorbiditaets-Interaktionen</span>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Wie Diagnosekombinationen die AU-Last veraendern. "
        "Rot = Ablehnung empfohlen. Gelb = integrierte Bewertung noetig. "
        "Additives Stapeln ist meistens falsch."
    )
    for i, card in enumerate(CARDS_KOMORBIDITAT):
        _render_card("komorbiditat", i, card)

with tab5:
    st.markdown(
        '<span class="section-label">Regulierung & Prozess</span>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Gesetzliche Grundlagen (DSGVO, VVG, EFZG), "
        "Governance-Framework und Modellvalidierungsanforderungen."
    )
    for i, card in enumerate(CARDS_REGULIERUNG):
        _render_card("regulierung", i, card)
