"""Page 2: Plausible-but-Wrong comparison -- clean vs flagged patient."""

import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st  # noqa: E402

from app.components.dqs_gauge import dqs_components_bar, dqs_gauge  # noqa: E402
from app.components.metrics_cards import decision_badge, dqs_tier_badge, metric_card  # noqa: E402
from app.data_cache import load_app_data  # noqa: E402

st.markdown("""
<style>
    .block-container { max-width: 1100px; }
    .stApp, .main, [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
    }
    .section-label {
        color: #0D2339; font-size: 0.72rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 1.5px;
        margin-bottom: 0.8rem; padding-bottom: 0.4rem;
        border-bottom: 2px solid #107ACA; display: inline-block;
    }
    .page-subtitle {
        color: #2B4660; font-size: 0.95rem; margin-top: -0.5rem; margin-bottom: 1.2rem;
    }
    .vs-badge {
        display: inline-block; background: #EEF2F7; border: 1px solid #C4CDD6;
        border-radius: 50%; width: 48px; height: 48px; line-height: 48px;
        text-align: center; font-size: 1rem; font-weight: 700; color: #0D2339;
    }
    h1, h2, h3, h4 { color: #0D2339 !important; }
    p, li { color: #2B4660 !important; }
</style>
""", unsafe_allow_html=True)

st.title("Plausible-but-Wrong Detection")
st.markdown(
    '<p class="page-subtitle"><strong>Same demographics, different data quality</strong> -- '
    "how the DQS and Reliability Head catch predictions that look confident but aren't "
    "supported by evidence.</p>",
    unsafe_allow_html=True,
)

# Load data
data = load_app_data(n_per_market=1000)
cohort = data["cohort"]
df = data["df"]
dqs_results = data["dqs_results"]
decisions = data["decisions"]
predictions = data["predictions"]

# Find a good DE patient (high DQS) and INT patient (low DQS) with similar age
de_indices = df[df["market"] == "DE"].index.tolist()
int_indices = df[df["market"] == "INT"].index.tolist()

# Sort by DQS
de_by_dqs = sorted(de_indices, key=lambda i: dqs_results[i].dqs, reverse=True)
int_by_dqs = sorted(int_indices, key=lambda i: dqs_results[i].dqs)

# Pick a high-DQS DE and low-DQS INT patient
de_idx = de_by_dqs[0]
int_idx = int_by_dqs[0]

# Allow user to browse
st.sidebar.header("Patient Selection")
de_selection = st.sidebar.slider("DE patient rank (by DQS, best first)", 0, min(50, len(de_by_dqs) - 1), 0)
int_selection = st.sidebar.slider("INT patient rank (by DQS, worst first)", 0, min(50, len(int_by_dqs) - 1), 0)
de_idx = de_by_dqs[de_selection]
int_idx = int_by_dqs[int_selection]

de_patient = cohort[de_idx]
int_patient = cohort[int_idx]
de_dqs = dqs_results[de_idx]
int_dqs = dqs_results[int_idx]
de_decision = decisions[de_idx]
int_decision = decisions[int_idx]
de_pred = predictions[de_idx]
int_pred = predictions[int_idx]

# Two columns
col_de, col_divider, col_int = st.columns([5, 1, 5])

with col_de:
    st.markdown("### Germany (DE) -- Clean Case")
    st.markdown(f"Age {de_patient.age} | {de_patient.sex.value} | BMI {de_patient.bmi:.1f}")

    dqs_gauge(de_dqs)
    dqs_components_bar(de_dqs)

    st.divider()
    m1, m2 = st.columns(2)
    with m1:
        metric_card("Risk Score", f"{de_pred:.1%}", color="#107ACA")
    with m2:
        metric_card("P(wrong)", f"{de_decision.p_wrong:.2%}",
                    color="#028901" if de_decision.p_wrong < 0.3 else "#D00D00")

    st.markdown(decision_badge(de_decision.decision), unsafe_allow_html=True)

    st.divider()
    st.markdown(f"""
    | Data Available | Count |
    |---|---|
    | Diagnoses | **{len(de_patient.diagnoses)}** |
    | Lab results | **{len(de_patient.lab_results)}** |
    | Medications | **{len(de_patient.medications)}** |
    """)

with col_divider:
    st.markdown(
        '<div style="text-align:center; padding-top:180px;">'
        '<span class="vs-badge">vs</span></div>',
        unsafe_allow_html=True,
    )

with col_int:
    st.markdown("### International (INT) -- Flagged Case")
    st.markdown(f"Age {int_patient.age} | {int_patient.sex.value} | BMI {int_patient.bmi:.1f}")

    dqs_gauge(int_dqs)
    dqs_components_bar(int_dqs)

    st.divider()
    m1, m2 = st.columns(2)
    with m1:
        metric_card("Risk Score", f"{int_pred:.1%}", color="#107ACA")
    with m2:
        metric_card("P(wrong)", f"{int_decision.p_wrong:.2%}",
                    color="#028901" if int_decision.p_wrong < 0.3 else "#D00D00")

    st.markdown(decision_badge(int_decision.decision), unsafe_allow_html=True)

    st.divider()
    st.markdown(f"""
    | Data Available | Count |
    |---|---|
    | Diagnoses | **{len(int_patient.diagnoses)}** |
    | Lab results | **{len(int_patient.lab_results)}** |
    | Medications | **{len(int_patient.medications)}** |
    """)

# Insight box
st.divider()
st.info(f"""
**Key Insight:** Both patients receive a similar-looking risk score
(DE: {de_pred:.1%} vs INT: {int_pred:.1%}), but the reliability is fundamentally different:

- **DE patient** has {len(de_patient.diagnoses)} diagnoses, {len(de_patient.lab_results)} labs,
  {len(de_patient.medications)} medications -- the prediction is evidence-based.
- **INT patient** has {len(int_patient.diagnoses)} diagnoses, {len(int_patient.lab_results)} labs,
  {len(int_patient.medications)} medications -- the model is filling gaps with population priors.

The Reliability Head estimates P(wrong) = {de_decision.p_wrong:.0%} for DE
vs {int_decision.p_wrong:.0%} for INT. Without MedRisk-ADH, both would be treated identically.
""")

if int_dqs.missingness_types:
    st.warning(f"**INT missingness pattern:** {int_dqs.missingness_types}")
