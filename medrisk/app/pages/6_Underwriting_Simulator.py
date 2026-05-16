"""MedRisk-ADH -- Underwriting Simulator (Interactive Quiz).

Interview prep tool: presents KTG underwriting case studies as an interactive
quiz.  The user plays the role of a medical underwriter reviewing algorithm
outputs and submits their own decision before the expert answer is revealed.
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

import pandas as pd
import streamlit as st

from medrisk.underwriting.profiles import CaseStudy, load_case_studies

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Underwriting Simulator | MedRisk-ADH",
    page_icon="🩺",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Page styling (Doctolib Oxygen — identical to page 5)
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
    .algo-box-decline {
        background: #fff5f5; border: 2px solid #fc8181;
        border-radius: 8px; padding: 16px 20px; margin-bottom: 8px;
    }
    .algo-box-loading {
        background: #fffff0; border: 2px solid #f6e05e;
        border-radius: 8px; padding: 16px 20px; margin-bottom: 8px;
    }
    .algo-box-accept {
        background: #f0fff4; border: 2px solid #68d391;
        border-radius: 8px; padding: 16px 20px; margin-bottom: 8px;
    }
    .algo-box-review {
        background: #ebf8ff; border: 2px solid #63b3ed;
        border-radius: 8px; padding: 16px 20px; margin-bottom: 8px;
    }
    .decision-col {
        border-radius: 8px; padding: 16px; text-align: center;
    }
    .decision-algo  { background: #edf2f7; }
    .decision-user-correct { background: #f0fff4; border: 2px solid #38a169; }
    .decision-user-wrong   { background: #fff5f5; border: 2px solid #e53e3e; }
    .decision-manual { background: #ebf8ff; border: 2px solid #3182ce; }
    .badge {
        display: inline-block; padding: 4px 12px; border-radius: 12px;
        font-size: 0.72rem; font-weight: 700; letter-spacing: 0.5px;
    }
    .badge-failure-overreaction      { background: #fed7d7; color: #c53030; }
    .badge-failure-underestimation   { background: #feebc8; color: #c05621; }
    .badge-failure-correct           { background: #c6f6d5; color: #276749; }
    .badge-failure-missing_data      { background: #bee3f8; color: #2b6cb0; }
    .badge-failure-premature_decline { background: #e9d8fd; color: #6b46c1; }
    .badge-failure-naive_linear_stacking { background: #fefcbf; color: #975a16; }
    .badge-failure-missing_functional_status { background: #fed7d7; color: #9b2c2c; }
    .badge-failure-au_history_gap    { background: #e2e8f0; color: #2d3748; }
    .badge-failure-ignoring_trend    { background: #fefcbf; color: #744210; }
    .badge-difficulty-easy     { background: #c6f6d5; color: #276749; }
    .badge-difficulty-moderate { background: #feebc8; color: #c05621; }
    .badge-difficulty-hard     { background: #fed7d7; color: #c53030; }
    .badge-evidence            { background: #ebf8ff; color: #2b6cb0; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
if "quiz_score" not in st.session_state:
    st.session_state.quiz_score: dict = {"correct": 0, "total": 0, "seen": set()}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _load_cases() -> list[CaseStudy]:
    return load_case_studies()


try:
    cases: list[CaseStudy] = _load_cases()
except Exception as exc:
    st.error(f"Fehler beim Laden der Fallstudien: {exc}")
    st.stop()

case_map: dict[int, CaseStudy] = {c.id: c for c in cases}


# ---------------------------------------------------------------------------
# Decision mappings
# ---------------------------------------------------------------------------
DECISION_DE_TO_EN: dict[str, str] = {
    "Annehmen":                 "accept",
    "Annehmen mit Zuschlag":    "accept_with_loading",
    "Annehmen mit Ausschluss":  "accept_with_exclusion",
    "Zurueckstellen":           "postpone",
    "Ablehnen":                 "decline",
}

DECISION_EN_TO_DE: dict[str, str] = {v: k for k, v in DECISION_DE_TO_EN.items()}

# Some case studies use combined keys — map to the closest German label
_NORMALISE_DECISION: dict[str, str] = {
    "accept":                          "Annehmen",
    "accept_with_loading":             "Annehmen mit Zuschlag",
    "accept_with_loading_and_exclusion": "Annehmen mit Zuschlag",
    "accept_with_exclusion":           "Annehmen mit Ausschluss",
    "accept_with_exclusion_and_loading": "Annehmen mit Zuschlag",
    "expert_review_required":          "Zurueckstellen",
    "manual_review":                   "Zurueckstellen",
    "postpone":                        "Zurueckstellen",
    "decline":                         "Ablehnen",
}

FAILURE_MODE_LABELS: dict[str, str] = {
    "overreaction":              "Ueberreaktion",
    "underestimation":           "Unterschaetzung",
    "correct":                   "Korrekt",
    "missing_data":              "Fehlende Daten",
    "premature_decline":         "Vorzeitige Ablehnung",
    "naive_linear_stacking":     "Lineares Stacking",
    "missing_functional_status": "Fehlender Funktionsstatus",
    "au_history_gap":            "AU-Luecke (Selbst.)",
    "ignoring_trend":            "Trend ignoriert",
}

ALGO_DECISION_DE: dict[str, str] = {
    "decline":                   "Ablehnen",
    "manual_review":             "Manuelle Pruefung",
    "accept_with_loading":       "Zuschlag",
    "accept_with_exclusion":     "Ausschluss",
    "accept_with_exclusion_and_loading": "Ausschluss + Zuschlag",
    "accept":                    "Annehmen",
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _failure_badge(failure_mode: str, revealed: bool = True) -> str:
    css_key = f"badge-failure-{failure_mode}"
    label = FAILURE_MODE_LABELS.get(failure_mode, failure_mode)
    if not revealed:
        return '<span class="badge" style="background:#e2e8f0;color:#a0aec0;">Verborgen</span>'
    return f'<span class="badge {css_key}">Failure Mode: {label}</span>'


def _difficulty_badge(difficulty: str) -> str:
    label_map = {"easy": "Einfach", "moderate": "Mittel", "hard": "Schwer"}
    label = label_map.get(difficulty, difficulty)
    return f'<span class="badge badge-difficulty-{difficulty}">{label}</span>'


def _evidence_badge(evidence_tier: str) -> str:
    return f'<span class="badge badge-evidence">Evidenz: {evidence_tier}</span>'


def _algo_box_class(decision: str) -> str:
    if "decline" in decision:
        return "algo-box-decline"
    if "loading" in decision or "exclusion" in decision:
        return "algo-box-loading"
    if "review" in decision:
        return "algo-box-review"
    return "algo-box-accept"


def _normalise_correct_decision(raw: str) -> str:
    """Map a case study decision key to the closest German display label."""
    return _NORMALISE_DECISION.get(raw, raw)


def _au_weeks_display(au_weeks) -> str:
    """Render au_weeks (int, float, list, or None) as a readable string."""
    if au_weeks is None:
        return "—"
    if isinstance(au_weeks, list):
        parts = [str(int(w)) if w is not None else "?" for w in au_weeks]
        return f"{' – '.join(parts)} Wochen"
    val = int(au_weeks) if float(au_weeks) == int(float(au_weeks)) else au_weeks
    return f"{val} Wochen" if val > 0 else "Keine AU"


def _score_submission(case: CaseStudy, user_de: str) -> bool:
    """Return True if the user's German decision matches the correct decision."""
    correct_en = case.correct_decision.decision
    correct_de = _normalise_correct_decision(correct_en)
    return user_de == correct_de


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.header("Fallauswahl")

case_options = [f"Fall {c.id}: {c.title}" for c in cases]
selected_label = st.sidebar.selectbox(
    "Fallstudie auswaehlen:",
    case_options,
    index=0,
    key="case_selector",
)
selected_index = case_options.index(selected_label)
active_case: CaseStudy = cases[selected_index]

st.sidebar.divider()
st.sidebar.markdown('<p class="section-label">Ergebnis</p>', unsafe_allow_html=True)

score = st.session_state.quiz_score
st.sidebar.metric("Richtige Antworten", f"{score['correct']} / {score['total']}")

if score["total"] > 0:
    pct = int(100 * score["correct"] / score["total"])
    st.sidebar.progress(pct / 100, text=f"{pct}% korrekt")

st.sidebar.divider()
st.sidebar.markdown(
    '<p class="section-label">Ueber dieses Tool</p>',
    unsafe_allow_html=True,
)
st.sidebar.caption(
    "Interaktives Trainingstool fuer KTG-Underwriter. "
    "Jede Fallstudie zeigt einen Algorithmus-Output — "
    "treffen Sie Ihre eigene Entscheidung, bevor die "
    "Expertenloesung aufgedeckt wird."
)

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.title("Underwriting Simulator")
st.markdown(
    '<p class="page-subtitle">'
    "KTG-Fallstudien — Trainingstool fuer medizinische Underwriter"
    "</p>",
    unsafe_allow_html=True,
)

case = active_case
case_key = f"submitted_{case.id}"
already_submitted = st.session_state.get(case_key, False)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_fall, tab_entscheidung, tab_analyse = st.tabs([
    "Fallpraesentation",
    "Ihre Entscheidung",
    "Analyse",
])


# ===========================================================================
# TAB 1: FALLPRAESENTATION
# ===========================================================================
with tab_fall:
    # Title row with difficulty and failure mode badges
    col_title, col_badges = st.columns([3, 2])
    with col_title:
        st.subheader(f"Fall {case.id}: {case.title}")
    with col_badges:
        st.markdown(
            _difficulty_badge(case.difficulty) + "&nbsp;&nbsp;" +
            _failure_badge(case.failure_mode, revealed=already_submitted),
            unsafe_allow_html=True,
        )

    st.divider()

    # --- Applicant metrics ---
    st.markdown('<p class="section-label">Antragsteller</p>', unsafe_allow_html=True)
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Alter", f"{case.applicant.age} Jahre")
    mc2.metric("Beruf", case.applicant.occupation)
    mc3.metric("Berufsklasse", f"Klasse {case.applicant.occupation_class}")
    mc4.metric("KTG Tagessatz", f"EUR {case.applicant.ktg_daily}")

    st.divider()

    # --- ICD history table ---
    st.markdown('<p class="section-label">ICD-Anamnese</p>', unsafe_allow_html=True)

    icd_rows = []
    for entry in case.icd_history:
        icd_rows.append({
            "Code": entry.code,
            "Datum": entry.date or "—",
            "AU-Dauer": _au_weeks_display(entry.au_weeks),
            "Behandlung": entry.treatment or "—",
        })

    icd_df = pd.DataFrame(icd_rows)
    st.dataframe(
        icd_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Code":        st.column_config.TextColumn("Code", width="small"),
            "Datum":       st.column_config.TextColumn("Datum", width="small"),
            "AU-Dauer":    st.column_config.TextColumn("AU-Dauer", width="medium"),
            "Behandlung":  st.column_config.TextColumn("Behandlung", width="large"),
        },
    )

    # --- Additional clinical info ---
    if case.additional_info:
        st.markdown(
            '<p class="section-label">Zusaetzliche klinische Informationen</p>',
            unsafe_allow_html=True,
        )
        for item in case.additional_info:
            st.markdown(f"- {item}")

    st.divider()

    # --- Algorithm output ---
    st.markdown(
        '<p class="section-label">Algorithmus-Output</p>',
        unsafe_allow_html=True,
    )

    algo_decision_raw = case.algorithm_output.decision
    algo_box_cls = _algo_box_class(algo_decision_raw)
    algo_decision_label = ALGO_DECISION_DE.get(algo_decision_raw, algo_decision_raw.upper())
    algo_loading_str = (
        f"&nbsp;&nbsp;<strong>Zuschlag:</strong> {case.algorithm_output.loading_pct}%"
        if case.algorithm_output.loading_pct is not None
        else ""
    )

    st.markdown(
        f"""
        <div class="{algo_box_cls}">
          <div style="font-size:0.75rem;color:#718096;text-transform:uppercase;
                      letter-spacing:1px;margin-bottom:6px;">Algorithmus-Entscheidung</div>
          <div style="font-size:1.3rem;font-weight:700;color:#1a365d;">
            {algo_decision_label}{algo_loading_str}
          </div>
          <div style="margin-top:8px;font-size:0.85rem;color:#4a5568;">
            <strong>Regel:</strong> {case.algorithm_output.rule}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ===========================================================================
# TAB 2: IHRE ENTSCHEIDUNG
# ===========================================================================
with tab_entscheidung:
    if already_submitted:
        st.success(
            "Sie haben fuer diesen Fall bereits eine Entscheidung abgegeben. "
            "Wechseln Sie zum Tab 'Analyse' fuer die Auswertung."
        )
    else:
        st.subheader("Ihre Underwriting-Entscheidung")
        st.caption(
            "Analysieren Sie den Algorithmus-Output und die klinischen Daten. "
            "Treffen Sie Ihre eigene Entscheidung."
        )
        st.divider()

        decision_options = [
            "Annehmen",
            "Annehmen mit Zuschlag",
            "Annehmen mit Ausschluss",
            "Zurueckstellen",
            "Ablehnen",
        ]

        user_decision = st.radio(
            "Ihre Underwriting-Entscheidung:",
            decision_options,
            key=f"decision_{case.id}",
            horizontal=False,
        )

        # Conditional fields
        user_loading_pct: int | None = None
        user_exclusion_type: str | None = None

        if user_decision == "Annehmen mit Zuschlag":
            user_loading_pct = st.slider(
                "Zuschlag (%)",
                min_value=5,
                max_value=100,
                value=25,
                step=5,
                key=f"loading_{case.id}",
            )

        if user_decision == "Annehmen mit Ausschluss":
            user_exclusion_type = st.selectbox(
                "Ausschlusstyp:",
                [
                    "Psychiatrisch",
                    "Muskuloskelettal",
                    "Metabolisch",
                    "Kardiovaskulaer",
                    "Neurologisch",
                ],
                key=f"exclusion_{case.id}",
            )

        user_reasoning = st.text_area(
            "Begruendung (optional):",
            height=100,
            placeholder="Begruenden Sie Ihre Entscheidung ...",
            key=f"reasoning_{case.id}",
        )

        st.divider()

        if st.button("Entscheidung abgeben", type="primary", key=f"submit_{case.id}"):
            # Record submission
            st.session_state[case_key] = True
            st.session_state[f"user_decision_{case.id}"] = user_decision
            st.session_state[f"user_loading_{case.id}"] = user_loading_pct
            st.session_state[f"user_exclusion_{case.id}"] = user_exclusion_type
            st.session_state[f"user_reasoning_{case.id}"] = user_reasoning

            # Score tracking — only count each case once
            if case.id not in st.session_state.quiz_score["seen"]:
                st.session_state.quiz_score["total"] += 1
                st.session_state.quiz_score["seen"].add(case.id)
                if _score_submission(case, user_decision):
                    st.session_state.quiz_score["correct"] += 1

            st.rerun()


# ===========================================================================
# TAB 3: ANALYSE
# ===========================================================================
with tab_analyse:
    if not already_submitted:
        st.info(
            "Bitte geben Sie zuerst Ihre Entscheidung im Tab "
            "'Ihre Entscheidung' ab. Die Analyse wird danach aufgedeckt."
        )
    else:
        # Retrieve stored user inputs
        user_decision_stored: str = st.session_state.get(
            f"user_decision_{case.id}", "—"
        )
        user_loading_stored: int | None = st.session_state.get(
            f"user_loading_{case.id}", None
        )
        user_reasoning_stored: str = st.session_state.get(
            f"user_reasoning_{case.id}", ""
        )

        correct_decision_raw = case.correct_decision.decision
        correct_decision_de = _normalise_correct_decision(correct_decision_raw)
        is_correct = (user_decision_stored == correct_decision_de)

        # --- 3-column comparison ---
        st.subheader("Entscheidungsvergleich")
        col_algo, col_user, col_manual = st.columns(3)

        algo_label_display = ALGO_DECISION_DE.get(
            case.algorithm_output.decision,
            case.algorithm_output.decision.upper(),
        )

        with col_algo:
            st.markdown(
                f"""
                <div class="decision-col decision-algo">
                  <div style="font-size:0.7rem;color:#718096;text-transform:uppercase;
                              letter-spacing:1px;margin-bottom:6px;">Algorithmus</div>
                  <div style="font-size:1.15rem;font-weight:700;color:#1a365d;">
                    {algo_label_display}
                  </div>
                  {"<div style='font-size:0.8rem;color:#718096;margin-top:6px;'>"
                   + f"Zuschlag: {case.algorithm_output.loading_pct}%"
                   + "</div>" if case.algorithm_output.loading_pct is not None else ""}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_user:
            user_col_cls = (
                "decision-col decision-user-correct"
                if is_correct
                else "decision-col decision-user-wrong"
            )
            user_extra = ""
            if user_loading_stored is not None:
                user_extra = (
                    f"<div style='font-size:0.8rem;color:#4a5568;margin-top:6px;'>"
                    f"Zuschlag: {user_loading_stored}%</div>"
                )
            st.markdown(
                f"""
                <div class="{user_col_cls}">
                  <div style="font-size:0.7rem;color:#718096;text-transform:uppercase;
                              letter-spacing:1px;margin-bottom:6px;">Ihre Entscheidung</div>
                  <div style="font-size:1.15rem;font-weight:700;color:#1a365d;">
                    {user_decision_stored}
                  </div>
                  {user_extra}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_manual:
            # Build correct decision detail string
            correct_loading = case.correct_decision.loading_pct
            correct_exclusion = case.correct_decision.exclusion
            correct_extra_parts = []
            if correct_loading is not None:
                if isinstance(correct_loading, list):
                    correct_extra_parts.append(
                        f"Zuschlag: {correct_loading[0]}-{correct_loading[1]}%"
                    )
                else:
                    correct_extra_parts.append(f"Zuschlag: {correct_loading}%")
            if correct_exclusion:
                correct_extra_parts.append(f"Ausschluss: {correct_exclusion}")
            correct_extra_html = "".join(
                f"<div style='font-size:0.75rem;color:#2b6cb0;margin-top:4px;'>{p}</div>"
                for p in correct_extra_parts
            )

            st.markdown(
                f"""
                <div class="decision-col decision-manual">
                  <div style="font-size:0.7rem;color:#718096;text-transform:uppercase;
                              letter-spacing:1px;margin-bottom:6px;">Handbuch-Loesung</div>
                  <div style="font-size:1.15rem;font-weight:700;color:#1a365d;">
                    {correct_decision_de}
                  </div>
                  {correct_extra_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # --- Match indicator ---
        if is_correct:
            st.success(
                "Ihre Entscheidung stimmt mit der Handbuch-Loesung ueberein."
            )
        else:
            st.warning(
                f"Ihre Entscheidung weicht ab. "
                f"Handbuch-Loesung: **{correct_decision_de}**."
            )

        # Optional: duration note
        duration_note = getattr(case.correct_decision, "duration_note", None)
        if duration_note:
            st.caption(f"Hinweis: {duration_note}")

        st.divider()

        # --- Full explanation ---
        st.markdown(
            '<p class="section-label">Erklaerung</p>',
            unsafe_allow_html=True,
        )
        st.markdown(case.explanation)

        # --- Key learning ---
        st.info(f"**Kernaussage:** {case.key_learning}")

        st.divider()

        # --- Badges row ---
        st.markdown(
            _failure_badge(case.failure_mode, revealed=True)
            + "&nbsp;&nbsp;"
            + _difficulty_badge(case.difficulty)
            + "&nbsp;&nbsp;"
            + _evidence_badge(case.evidence_tier),
            unsafe_allow_html=True,
        )

        # --- User reasoning (if provided) ---
        if user_reasoning_stored.strip():
            st.divider()
            st.markdown(
                '<p class="section-label">Ihre Begruendung</p>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="background:#f7fafc;border-left:3px solid #a0aec0;'
                f'padding:12px 16px;border-radius:4px;color:#4a5568;">'
                f'{user_reasoning_stored}</div>',
                unsafe_allow_html=True,
            )
