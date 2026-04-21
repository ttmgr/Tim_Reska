"""Page 1: Individual patient assessment through full v2 pipeline."""

import sys
from pathlib import Path

# Ensure project root and app dir are on path before any local imports
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
_APP_DIR = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

import streamlit as st  # noqa: E402

from components.dqs_gauge import dqs_components_bar, dqs_gauge  # noqa: E402
from components.metrics_cards import decision_badge, dqs_tier_badge, metric_card  # noqa: E402
from components.progression_chart import progression_chart  # noqa: E402
from components.shap_chart import shap_bar_chart  # noqa: E402
from data_cache import load_app_data  # noqa: E402

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
</style>
""", unsafe_allow_html=True)

st.title("Patient Assessment")
st.markdown('<p class="page-subtitle">Score an individual patient through the full MedRisk-ADH v2 pipeline.</p>', unsafe_allow_html=True)

# Load cached data
data = load_app_data(n_per_market=1000)
cohort = data["cohort"]
df = data["df"]
dqs_results = data["dqs_results"]
decisions = data["decisions"]
predictions = data["predictions"]
model_ids = data["model_ids"]

# Sidebar: patient selection
st.sidebar.header("Select Patient")
markets = sorted(df["market"].unique())
selected_market = st.sidebar.selectbox("Market", markets, index=0)

market_mask = df["market"] == selected_market
market_indices = df[market_mask].index.tolist()

# Patient dropdown (show index + age + sex for quick identification)
patient_options = []
for idx in market_indices[:100]:  # limit for performance
    p = cohort[idx]
    patient_options.append(f"{idx}: Age {p.age}, {p.sex.value}, CCI {len(p.diagnoses)} dx")

selected_patient_str = st.sidebar.selectbox("Patient", patient_options, index=0)
patient_idx = int(selected_patient_str.split(":")[0])

# Get patient data
patient = cohort[patient_idx]
dqs = dqs_results[patient_idx]
decision = decisions[patient_idx]
pred = predictions[patient_idx]
mid = model_ids[patient_idx]

# --- Main layout ---

# Row 1: Demographics + DQS
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Demographics")
    st.markdown(f"""
    | | |
    |---|---|
    | **Age** | {patient.age} |
    | **Sex** | {patient.sex.value} |
    | **BMI** | {patient.bmi:.1f} |
    | **Smoking** | {patient.smoking_status.value} |
    | **Diagnoses** | {len(patient.diagnoses)} |
    | **Lab results** | {len(patient.lab_results)} |
    | **Medications** | {len(patient.medications)} |
    | **Market** | {patient.market.value} |
    """)

with col2:
    st.markdown('<div class="section-label">Data Quality Score</div>', unsafe_allow_html=True)
    gcol1, gcol_spacer, gcol2 = st.columns([5, 1, 6])
    with gcol1:
        dqs_gauge(dqs)
    with gcol2:
        dqs_components_bar(dqs)
        if dqs.missingness_types:
            st.markdown(
                '<div style="margin-top:0.6rem; font-size:0.7rem; color:#1a365d; '
                'text-transform:uppercase; letter-spacing:1.5px; font-weight:600;">'
                'Missing Data</div>',
                unsafe_allow_html=True,
            )
            for cat, mtype in dqs.missingness_types.items():
                st.markdown(f"- {cat}: `{mtype}`")

st.divider()

# Row 2: Decision
st.subheader("Underwriting Decision")
dcol1, dcol2, dcol3, dcol4 = st.columns(4)

with dcol1:
    metric_card("Risk Score", f"{pred:.1%}", f"Model: {mid}")
with dcol2:
    metric_card("P(wrong)", f"{decision.p_wrong:.2%}",
                f"Cost accept: {decision.expected_cost_accept:.3f}",
                color="#e53e3e" if decision.p_wrong > 0.3 else "#38a169")
with dcol3:
    st.markdown('<div class="section-label">Decision</div>', unsafe_allow_html=True)
    st.markdown(decision_badge(decision.decision), unsafe_allow_html=True)
    st.markdown(f"<br>{dqs_tier_badge(dqs.tier)}", unsafe_allow_html=True)
with dcol4:
    metric_card("Profile", str(data["profiles"].iloc[patient_idx]).upper(),
                f"Features: {len(data['router'].feature_sets.get(data['profiles'].iloc[patient_idx], []))}")

st.info(decision.explanation)

st.divider()

# Row 3: SHAP + Progression
scol1, scol2 = st.columns(2)

with scol1:
    st.subheader("Risk Drivers (Global Feature Importance)")
    # Get feature importance from router's model
    profile = data["profiles"].iloc[patient_idx]
    if profile in data["router"].models:
        clf = data["router"].models[profile]
        imp = clf.get_feature_importance()
        names = list(imp.keys())
        values = list(imp.values())
        shap_bar_chart(names, values, n_top=10)
    else:
        st.warning("No model available for this profile.")

with scol2:
    st.subheader("Disease Progression")
    # Determine start state based on patient's conditions
    has_risk = len(patient.diagnoses) > 0
    start = 1 if has_risk else 0
    progression_chart(data["msm"], start_state=start)

st.divider()

# Row 4: Audit entry
with st.expander("Audit Trail Entry (JSON)"):
    import json
    audit_data = {
        "patient_id": patient.patient_id,
        "market": patient.market.value,
        "data_profile": str(data["profiles"].iloc[patient_idx]),
        "model_id": mid,
        "dqs": {"score": dqs.dqs, "tier": dqs.tier,
                "completeness": dqs.completeness, "consistency": dqs.consistency,
                "recency": dqs.recency, "range_score": dqs.range_score},
        "missingness": dqs.missingness_types,
        "predicted_probability": round(float(pred), 4),
        "reliability": {"p_wrong": decision.p_wrong, "decision": decision.decision,
                        "cost_accept": decision.expected_cost_accept,
                        "cost_reject": decision.expected_cost_reject,
                        "cost_review": decision.expected_cost_review},
    }
    st.json(audit_data)
