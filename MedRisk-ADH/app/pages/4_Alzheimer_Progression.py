"""MedRisk-ADH -- Alzheimer's Disease Progression Demo.

Interactive exploration of a 7-state CTMC model for Alzheimer's disease
progression, from normal cognition through severe AD to death.
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

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from medrisk.models.disease_configs import ALZHEIMER_CONFIG, build_model

# ---------------------------------------------------------------------------
# Shared page styling (Doctolib Oxygen)
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

    /* Sidebar light override */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div,
    [data-testid="stSidebar"] > div > div {
        background: #f7fafc !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {
        color: #2d3748 !important;
        font-size: 0.85rem;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #1a365d !important;
        font-weight: 700;
    }
    [data-testid="stSidebar"] hr {
        border-color: #e2e8f0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Build AD model
# ---------------------------------------------------------------------------

AD_CONFIG = ALZHEIMER_CONFIG


@st.cache_resource
def get_ad_model(apoe4: bool = False):
    """Build Alzheimer CTMC with optional apoE4 intensity scaling.

    ApoE4 effect is graduated by state: strongest on pre-clinical
    transitions (1.5x), weaker post-diagnosis (1.1-1.3x), neutral
    in severe stages. Based on Suzuki et al. 2020.
    """
    if not apoe4:
        return build_model(AD_CONFIG)

    # Graduated multiplier by source state
    apoe4_by_state = {0: 1.5, 1: 1.5, 2: 1.3, 3: 1.1, 4: 1.0, 5: 1.0}
    scaled = {}
    for (s, d), rate in AD_CONFIG.default_intensities.items():
        scaled[(s, d)] = rate * apoe4_by_state.get(s, 1.0)

    from medrisk.models.multistate import MultistateModel
    model = MultistateModel(
        allowed_transitions=AD_CONFIG.allowed_transitions,
        n_states=AD_CONFIG.n_states,
        absorbing_states=set(AD_CONFIG.absorbing_states),
        state_names=dict(AD_CONFIG.state_names),
    )
    model.set_intensities(scaled)
    return model


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.markdown("### Alzheimer's Disease")
st.sidebar.markdown('<span style="display:inline-block;background:#ebf4ff;color:#2b6cb0;'
                    'font-size:0.68rem;font-weight:700;padding:0.2rem 0.6rem;border-radius:10px;">'
                    'Disease Progression</span>', unsafe_allow_html=True)
st.sidebar.markdown("---")

start_state = st.sidebar.selectbox(
    "Starting state",
    options=list(range(AD_CONFIG.n_states - 1)),  # exclude Death
    format_func=lambda x: AD_CONFIG.state_names[x],
    index=0,
)

time_horizon = st.sidebar.slider("Time horizon (years)", 5, 30, 20)

apoe4 = st.sidebar.toggle("ApoE4 carrier", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown("""
**Clinical Stages**
- **NC**: Normal cognition, no symptoms
- **SCD**: Subjective memory complaints, normal testing
- **MCI**: Measurable cognitive decline, preserved function
- **Mild AD**: Functional impairment, MMSE 20-24
- **Moderate AD**: Dependent for daily activities, MMSE 10-19
- **Severe AD**: Full care dependency, MMSE < 10
""")

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="background:#edf2f7;border:1px solid #e2e8f0;border-radius:6px;padding:0.7rem 0.8rem;">
    <p style="color:#718096;font-size:0.72rem;line-height:1.5;margin:0;">
    Proof of Concept<br>Transition rates from published literature. All patient data is synthetic.
    </p>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------
st.markdown("""
<div style="background:#ffffff;padding:1.5rem 2rem 1rem 2rem;margin:-1rem -1rem 0 -1rem;border-bottom:1px solid #e2e8f0;">
    <h1 style="color:#1a365d;font-size:1.8rem;font-weight:700;margin:0 0 0.3rem 0;">
        Alzheimer's Disease Progression
        <span style="display:inline-block;background:#ebf4ff;color:#2b6cb0;font-size:0.68rem;font-weight:700;padding:0.2rem 0.6rem;border-radius:10px;margin-left:0.5rem;vertical-align:middle;">7-State CTMC</span>
        <span style="display:inline-block;background:#f0fff4;color:#38a169;font-size:0.68rem;font-weight:700;padding:0.2rem 0.6rem;border-radius:10px;margin-left:0.3rem;vertical-align:middle;">Generalizability Proof</span>
    </h1>
    <p style="color:#718096;font-size:0.95rem;margin:0;">
        This page demonstrates that MedRisk-ADH's core validation framework (DQS, Model Router, Reliability Head) generalises beyond cardiovascular risk. New diseases are added as data configurations, not code.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

# Build model
ad_model = get_ad_model(apoe4)

# ---------------------------------------------------------------------------
# State Occupation Chart
# ---------------------------------------------------------------------------
from components.progression_chart import progression_chart

col_chart, col_info = st.columns([3, 1])

with col_chart:
    apoe4_label = " (ApoE4+)" if apoe4 else ""
    progression_chart(
        ad_model,
        start_state=start_state,
        max_time=time_horizon,
        state_names=dict(AD_CONFIG.state_names),
        colors=list(AD_CONFIG.colors),
        line_colors=list(AD_CONFIG.line_colors),
        title=f"Alzheimer's Progression from {AD_CONFIG.state_names[start_state]}{apoe4_label}",
    )

with col_info:
    st.markdown('<div style="color:#1a365d;font-size:0.72rem;font-weight:700;text-transform:uppercase;'
                'letter-spacing:1.5px;margin-bottom:0.5rem;padding-bottom:0.3rem;border-bottom:2px solid #2b6cb0;'
                'display:inline-block;">Mean Sojourn</div>', unsafe_allow_html=True)

    for i in range(AD_CONFIG.n_states):
        sojourn = ad_model.mean_sojourn_time(i)
        name = AD_CONFIG.state_names[i]
        if sojourn == float("inf"):
            val = "Absorbing"
        else:
            val = f"{sojourn:.1f} yr"
        st.markdown(f"**{name}**: {val}")

st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Key Metrics Row
# ---------------------------------------------------------------------------
st.markdown('<div style="color:#1a365d;font-size:0.72rem;font-weight:700;text-transform:uppercase;'
            'letter-spacing:1.5px;margin-bottom:0.8rem;padding-bottom:0.4rem;border-bottom:2px solid #2b6cb0;'
            'display:inline-block;">Key Metrics</div>', unsafe_allow_html=True)

mtta = ad_model.mean_time_to_absorption(start_state)

# Probability of reaching each stage at time_horizon
P_t = ad_model.transition_probability(float(time_horizon))
p_death = P_t[start_state, 6]
p_severe = P_t[start_state, 5]
p_moderate_plus = P_t[start_state, 4] + p_severe + p_death

kpi_cols = st.columns(4)
with kpi_cols[0]:
    st.metric("Mean Time to Death", f"{mtta:.1f} yr")
with kpi_cols[1]:
    st.metric(f"P(Death) at {time_horizon}yr", f"{p_death:.1%}")
with kpi_cols[2]:
    st.metric(f"P(Severe AD) at {time_horizon}yr", f"{p_severe:.1%}")
with kpi_cols[3]:
    st.metric(f"P(Moderate+) at {time_horizon}yr", f"{p_moderate_plus:.1%}")

st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Transition Intensity Table
# ---------------------------------------------------------------------------
col_intensities, col_trajectories = st.columns(2)

with col_intensities:
    st.markdown('<div style="color:#1a365d;font-size:0.72rem;font-weight:700;text-transform:uppercase;'
                'letter-spacing:1.5px;margin-bottom:0.8rem;padding-bottom:0.4rem;border-bottom:2px solid #2b6cb0;'
                'display:inline-block;">Transition Intensities</div>', unsafe_allow_html=True)

    summary = ad_model.get_intensity_summary()
    rows = []
    for transition, rate in summary.items():
        sojourn_contrib = f"{1/rate:.1f}" if rate > 0 else "N/A"
        rows.append({
            "Transition": transition,
            "Rate (per year)": f"{rate:.3f}",
            "Mean time (years)": sojourn_contrib,
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Simulated Trajectories
# ---------------------------------------------------------------------------
with col_trajectories:
    st.markdown('<div style="color:#1a365d;font-size:0.72rem;font-weight:700;text-transform:uppercase;'
                'letter-spacing:1.5px;margin-bottom:0.8rem;padding-bottom:0.4rem;border-bottom:2px solid #2b6cb0;'
                'display:inline-block;">Simulated Trajectories (N=50)</div>', unsafe_allow_html=True)

    rng = np.random.default_rng(42)
    fig_traj = go.Figure()

    for i in range(50):
        traj = ad_model.simulate_trajectory(start_state, float(time_horizon), rng)
        times = [t for t, _ in traj]
        states = [s for _, s in traj]
        # Extend to time_horizon
        times.append(float(time_horizon))
        states.append(states[-1])

        fig_traj.add_trace(go.Scatter(
            x=times, y=states,
            mode="lines",
            line={"width": 0.8, "color": "rgba(43, 108, 176, 0.25)"},
            showlegend=False,
            hoverinfo="skip",
        ))

    fig_traj.update_layout(
        yaxis={
            "tickmode": "array",
            "tickvals": list(range(AD_CONFIG.n_states)),
            "ticktext": [AD_CONFIG.state_names[i] for i in range(AD_CONFIG.n_states)],
            "title": "Stage",
        },
        xaxis_title="Time (years)",
        height=350,
        margin={"t": 10, "b": 40, "l": 140},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font={"family": "Inter, -apple-system, sans-serif", "color": "#2d3748", "size": 11},
    )
    st.plotly_chart(fig_traj, use_container_width=True)

# ---------------------------------------------------------------------------
# Biomarker Reference
# ---------------------------------------------------------------------------
st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

with st.expander("Alzheimer's Biomarker Reference"):
    bio_data = [
        {"Biomarker": "MMSE", "Normal": "24-30", "MCI": "20-24", "Mild AD": "15-20", "Moderate AD": "10-15", "Severe AD": "< 10"},
        {"Biomarker": "MoCA", "Normal": "26-30", "MCI": "18-25", "Mild AD": "12-18", "Moderate AD": "6-12", "Severe AD": "< 6"},
        {"Biomarker": "CSF Amyloid-Beta42", "Normal": "> 600 pg/mL", "MCI": "400-600", "Mild AD": "300-500", "Moderate AD": "200-400", "Severe AD": "< 300"},
        {"Biomarker": "CSF p-tau181", "Normal": "< 40 pg/mL", "MCI": "40-60", "Mild AD": "50-80", "Moderate AD": "60-100", "Severe AD": "> 80"},
        {"Biomarker": "Donepezil", "Normal": "--", "MCI": "Off-label", "Mild AD": "5-10 mg/d", "Moderate AD": "10 mg/d", "Severe AD": "10 mg/d"},
        {"Biomarker": "Memantine", "Normal": "--", "MCI": "--", "Mild AD": "--", "Moderate AD": "10-20 mg/d", "Severe AD": "20 mg/d"},
    ]
    st.dataframe(pd.DataFrame(bio_data), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("""
<div style="margin-top:2rem;padding-top:0.8rem;border-top:1px solid #e2e8f0;display:flex;justify-content:space-between;">
    <p style="color:#718096;font-size:0.75rem;margin:0;"><strong>Tim Reska</strong> &middot; Helmholtz Munich &middot; March 2026</p>
    <p style="color:#718096;font-size:0.7rem;font-style:italic;margin:0;">Transition rates from published literature. All data synthetic.</p>
</div>
""", unsafe_allow_html=True)
