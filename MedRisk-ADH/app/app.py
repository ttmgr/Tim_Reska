"""MedRisk-ADH v2 -- Interactive Underwriting Demo.

Streamlit multi-page app demonstrating AI-augmented medical underwriting
with confidence-calibrated failure mode detection.

Run: streamlit run app/app.py
"""

import streamlit as st

st.set_page_config(
    page_title="MedRisk-ADH",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS -- Doctolib Oxygen-inspired design (light, clean, trustworthy)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* ---------- Global (Doctolib Oxygen) ---------- */
    @import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Nunito Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        -webkit-font-smoothing: antialiased;
    }

    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 2rem;
        max-width: 1100px;
    }

    header[data-testid="stHeader"] { background: transparent; }

    /* ---------- Top header bar ---------- */
    .doc-header {
        background: #ffffff;
        padding: 2rem 2.8rem 1.6rem 2.8rem;
        margin: -1rem -1rem 0 -1rem;
        border-bottom: 1px solid #C4CDD6;
    }

    .doc-header h1 {
        color: #0D2339;
        font-size: 1.9rem;
        font-weight: 700;
        letter-spacing: -0.3px;
        margin: 0 0 0.3rem 0;
        line-height: 1.15;
    }

    .doc-header h1 span { color: #107ACA; }

    .doc-header p {
        color: #61788E;
        font-size: 1rem;
        font-weight: 400;
        margin: 0;
    }

    .doc-header .version-badge {
        display: inline-block;
        background: #E7F4FD;
        color: #107ACA;
        font-size: 0.68rem;
        font-weight: 700;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        margin-left: 0.6rem;
        vertical-align: middle;
    }

    /* ---------- Section headings ---------- */
    .section-label {
        color: #0D2339;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 0.8rem;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #107ACA;
        display: inline-block;
    }

    /* ---------- Navigation cards ---------- */
    .nav-card {
        background: #ffffff;
        border: 1px solid #C4CDD6;
        border-radius: 8px;
        padding: 1.6rem 1.5rem;
        height: 100%;
        transition: box-shadow 0.2s ease, border-color 0.2s ease;
    }

    .nav-card:hover {
        box-shadow: 0 1px 10px rgba(0,0,0,0.13);
        border-color: #107ACA;
    }

    .nav-card-number {
        color: #107ACA;
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 0.5rem;
    }

    .nav-card h3 {
        color: #0D2339;
        font-size: 1.05rem;
        font-weight: 700;
        margin: 0 0 0.5rem 0;
        line-height: 1.3;
    }

    .nav-card p {
        color: #2B4660;
        font-size: 0.88rem;
        line-height: 1.55;
        margin: 0;
    }

    /* ---------- KPI row ---------- */
    .kpi-container { display: flex; gap: 1rem; margin-top: 0.4rem; }

    .kpi-box {
        background: #ffffff;
        border: 1px solid #C4CDD6;
        border-radius: 8px;
        padding: 1.1rem 1.4rem;
        flex: 1;
        text-align: center;
        transition: box-shadow 0.2s ease;
    }

    .kpi-box:hover { box-shadow: 0 1px 10px rgba(0,0,0,0.08); }

    .kpi-value {
        color: #0D2339;
        font-size: 1.65rem;
        font-weight: 700;
        line-height: 1.2;
        margin-bottom: 0.2rem;
    }

    .kpi-value.blue { color: #107ACA; }
    .kpi-value.green { color: #028901; }

    .kpi-label {
        color: #61788E;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* ---------- Architecture diagram ---------- */
    .arch-flow {
        background: #EEF2F7;
        border: 1px solid #C4CDD6;
        border-radius: 8px;
        padding: 1.4rem 1.6rem;
        font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
        font-size: 0.8rem;
        color: #2B4660;
        line-height: 1.7;
        overflow-x: auto;
    }

    .arch-flow span.stage { color: #107ACA; font-weight: 700; }
    .arch-flow span.arrow { color: #C4CDD6; }
    .arch-flow span.detail { color: #61788E; font-size: 0.72rem; }

    /* ---------- Footer ---------- */
    .doc-footer {
        margin-top: 2.5rem;
        padding-top: 1rem;
        border-top: 1px solid #C4CDD6;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .doc-footer p { color: #61788E; font-size: 0.75rem; margin: 0; }
    .doc-footer .disclaimer { color: #61788E; font-size: 0.7rem; font-style: italic; }

    /* ---------- Force light backgrounds everywhere ---------- */
    .stApp, .main, [data-testid="stAppViewContainer"],
    [data-testid="stAppViewBlockContainer"],
    .stApp > header, section[data-testid="stSidebar"] > div,
    [data-testid="stBottomBlockContainer"] {
        background-color: #ffffff !important;
        color: #0D2339 !important;
    }

    /* ---------- Sidebar (light, Doctolib-style) ---------- */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div,
    [data-testid="stSidebar"] > div > div,
    [data-testid="stSidebar"] > div > div > div {
        background: #F8FAFB !important;
        background-color: #F8FAFB !important;
        border-right: 1px solid #C4CDD6 !important;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdown"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdown"] li,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {
        color: #2B4660 !important;
        font-size: 0.85rem;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdown"] h1,
    [data-testid="stSidebar"] [data-testid="stMarkdown"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdown"] h3,
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #0D2339 !important;
        font-weight: 700;
    }

    [data-testid="stSidebar"] hr {
        border-color: #C4CDD6 !important;
    }

    /* ---------- Force all text dark on main area ---------- */
    h1, h2, h3, h4, h5, h6 { color: #0D2339 !important; }
    p, li, span, label, div { color: #2B4660; }
    .stMarkdown p, .stMarkdown li { color: #2B4660 !important; }

    /* ---------- Streamlit widgets light override ---------- */
    [data-testid="stSelectbox"] label,
    [data-testid="stSlider"] label,
    [data-testid="stNumberInput"] label,
    [data-testid="stTextInput"] label {
        color: #0D2339 !important;
    }

    .stSelectbox > div > div,
    .stSlider > div > div,
    [data-baseweb="select"] {
        background-color: #ffffff !important;
        color: #0D2339 !important;
    }

    /* Expander */
    [data-testid="stExpander"] {
        background-color: #ffffff !important;
        border-color: #C4CDD6 !important;
    }

    /* Dataframes */
    [data-testid="stDataFrame"] {
        background-color: #ffffff !important;
    }

    .sidebar-badge {
        display: inline-block;
        background: #E7F4FD;
        color: #107ACA;
        font-size: 0.68rem;
        font-weight: 700;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        letter-spacing: 0.5px;
    }

    .sidebar-disclaimer {
        background: #EEF2F7;
        border: 1px solid #C4CDD6;
        border-radius: 8px;
        padding: 0.7rem 0.8rem;
        margin-top: 0.5rem;
    }

    .sidebar-disclaimer p {
        color: #61788E !important;
        font-size: 0.72rem !important;
        line-height: 1.5;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="doc-header">
    <h1>MedRisk-<span>ADH</span> <span class="version-badge">v2.0</span></h1>
    <p>AI-Augmented Medical Underwriting with Confidence-Calibrated Failure Mode Detection</p>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height: 1.6rem'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Navigation cards
# ---------------------------------------------------------------------------
st.markdown('<div class="section-label">Application Views</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    st.markdown("""
    <div class="nav-card">
        <div class="nav-card-number">View 01</div>
        <h3>Patient Assessment</h3>
        <p>Score an individual patient through the full v2 pipeline -- from data profiling through DQS to cost-optimal decision.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="nav-card">
        <div class="nav-card-number">View 02</div>
        <h3>PBW Comparison</h3>
        <p>Side-by-side analysis showing how data quality shifts the reliability of identical risk predictions.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="nav-card">
        <div class="nav-card-number">View 03</div>
        <h3>Portfolio Dashboard</h3>
        <p>Aggregate view across the full synthetic cohort -- risk distributions, failure modes, and market-level KPIs.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 1.4rem'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Key metrics
# ---------------------------------------------------------------------------
st.markdown('<div class="section-label">Key Figures</div>', unsafe_allow_html=True)

st.markdown("""
<div class="kpi-container">
    <div class="kpi-box">
        <div class="kpi-value">4,000</div>
        <div class="kpi-label">Synthetic Patients</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-value">4</div>
        <div class="kpi-label">European Markets</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-value green">192</div>
        <div class="kpi-label">Tests Passing</div>
    </div>
    <div class="kpi-box">
        <div class="kpi-value blue">3</div>
        <div class="kpi-label">Model Stages</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height: 1.4rem'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Architecture
# ---------------------------------------------------------------------------
st.markdown('<div class="section-label">Pipeline Architecture</div>', unsafe_allow_html=True)

st.markdown("""
<div class="arch-flow">
<span class="stage">Patient Record</span> <span class="arrow">--></span> <span class="stage">Data Profile</span> <span class="arrow">--></span> <span class="stage">DQS v2</span> <span class="arrow">--></span> <span class="stage">Model Router</span> <span class="arrow">--></span> <span class="stage">Reliability Head</span> <span class="arrow">--></span> <span class="stage">Decision</span><br>
<span class="detail">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;what data&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;how good&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;right model&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;P(wrong) +&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;accept /</span><br>
<span class="detail">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;is available?&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;is it?&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;for this data&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;cost-optimal&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;review /</span><br>
<span class="detail">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;reject</span>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Why AI?
# ---------------------------------------------------------------------------
st.markdown("<div style='height: 1.4rem'></div>", unsafe_allow_html=True)
st.markdown('<div class="section-label">Why AI-Driven Underwriting</div>', unsafe_allow_html=True)

st.markdown("""
<div style="border:1px solid #C4CDD6; border-radius:8px; overflow:hidden; margin-bottom:1rem;">
<table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
  <thead>
    <tr style="background:#EEF2F7;">
      <th style="padding:0.55rem 0.8rem; text-align:left; font-size:0.7rem; color:#0D2339; text-transform:uppercase; letter-spacing:0.5px; font-weight:700;">Capability</th>
      <th style="padding:0.55rem 0.8rem; text-align:center; font-size:0.7rem; color:#0D2339; text-transform:uppercase; letter-spacing:0.5px; font-weight:700;">Rules / Actuarial</th>
      <th style="padding:0.55rem 0.8rem; text-align:center; font-size:0.7rem; color:#0D2339; text-transform:uppercase; letter-spacing:0.5px; font-weight:700;">Basic ML</th>
      <th style="padding:0.55rem 0.8rem; text-align:center; font-size:0.7rem; color:#0D2339; text-transform:uppercase; letter-spacing:0.5px; font-weight:700;">MedRisk-ADH</th>
    </tr>
  </thead>
  <tbody>
    <tr><td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EEF2F7; color:#2B4660;">Per-case reliability</td>
        <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EEF2F7; text-align:center; color:#61788E;">No</td>
        <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EEF2F7; text-align:center; color:#61788E;">No</td>
        <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EEF2F7; text-align:center; color:#028901; font-weight:600;">DQS + P(wrong)</td></tr>
    <tr style="background:#FAFBFC;"><td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EEF2F7; color:#2B4660;">Handles missing data</td>
        <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EEF2F7; text-align:center; color:#61788E;">Reject case</td>
        <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EEF2F7; text-align:center; color:#D00D00;">Impute (PBW risk)</td>
        <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EEF2F7; text-align:center; color:#028901; font-weight:600;">Route to right model</td></tr>
    <tr><td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EEF2F7; color:#2B4660;">Individual risk drivers</td>
        <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EEF2F7; text-align:center; color:#61788E;">No</td>
        <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EEF2F7; text-align:center; color:#61788E;">Limited</td>
        <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EEF2F7; text-align:center; color:#028901; font-weight:600;">SHAP per patient</td></tr>
    <tr style="background:#FAFBFC;"><td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EEF2F7; color:#2B4660;">Disease progression</td>
        <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EEF2F7; text-align:center; color:#61788E;">Static tables</td>
        <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EEF2F7; text-align:center; color:#61788E;">No</td>
        <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EEF2F7; text-align:center; color:#028901; font-weight:600;">CTMC (any disease)</td></tr>
    <tr><td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EEF2F7; color:#2B4660;">Confidence estimation</td>
        <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EEF2F7; text-align:center; color:#61788E;">No</td>
        <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EEF2F7; text-align:center; color:#61788E;">Uncalibrated</td>
        <td style="padding:0.5rem 0.8rem; border-bottom:1px solid #EEF2F7; text-align:center; color:#028901; font-weight:600;">Cost-optimal decisions</td></tr>
    <tr style="background:#FAFBFC;"><td style="padding:0.5rem 0.8rem; color:#2B4660;">EU AI Act compliance</td>
        <td style="padding:0.5rem 0.8rem; text-align:center; color:#61788E;">Partial</td>
        <td style="padding:0.5rem 0.8rem; text-align:center; color:#D00D00;">Difficult</td>
        <td style="padding:0.5rem 0.8rem; text-align:center; color:#028901; font-weight:600;">Built-in (Art. 14, 15)</td></tr>
  </tbody>
</table>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height: 0.6rem'></div>", unsafe_allow_html=True)
st.markdown('<div class="section-label">LLM Extension (Phase 3 Vision)</div>', unsafe_allow_html=True)

col_llm1, col_llm2 = st.columns(2, gap="medium")

with col_llm1:
    st.markdown("""
    <div class="nav-card">
        <div class="nav-card-number">Extraction</div>
        <h3>Unstructured Records</h3>
        <p>LLMs read doctor notes, discharge summaries, and lab reports in DE/FR/ES/EN -- extracting structured data for the pipeline automatically.</p>
    </div>
    """, unsafe_allow_html=True)

with col_llm2:
    st.markdown("""
    <div class="nav-card">
        <div class="nav-card-number">Explanation</div>
        <h3>Natural Language Risk Narratives</h3>
        <p>Instead of "SHAP: age +0.12", generate: "This patient's age (78) places them in the highest risk quartile, contributing 12% to the risk score."</p>
    </div>
    """, unsafe_allow_html=True)

col_llm3, col_llm4 = st.columns(2, gap="medium")

with col_llm3:
    st.markdown("""
    <div class="nav-card">
        <div class="nav-card-number">Calibration</div>
        <h3>Literature-Verified Parameters</h3>
        <p>LLM agents query PubMed for systematic reviews and verify CTMC transition rates against published data -- already demonstrated in this PoC.</p>
    </div>
    """, unsafe_allow_html=True)

with col_llm4:
    st.markdown("""
    <div class="nav-card">
        <div class="nav-card-number">Monitoring</div>
        <h3>Continuous Updates</h3>
        <p>Flag when new publications change recommended clinical parameters, triggering automated model recalibration with full audit trail.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 1.4rem'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("""
<div class="doc-footer">
    <p><strong>Tim Reska</strong> &middot; Helmholtz Munich &middot; Proof of Concept &middot; March 2026</p>
    <p class="disclaimer">All data is synthetic (GDPR-safe). No real patient information is used.</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar (light Doctolib style)
# ---------------------------------------------------------------------------
st.sidebar.markdown("### MedRisk-ADH")
st.sidebar.markdown('<span class="sidebar-badge">v2.0</span>', unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown("**Tim Reska**")
st.sidebar.markdown("PhD Researcher")
st.sidebar.markdown("Helmholtz Munich & TU Munich")
st.sidebar.markdown("[github.com/ttmgr](https://github.com/ttmgr)")
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div class="sidebar-disclaimer">
    <p><strong>Background</strong><br>
    "Plausible but Wrong" coined in my own LLM evaluation research (ISME Communications 2024).
    22 LLMs evaluated over 36 months. 8 publications incl. Nature Communications.
    Built this system in ~48 hours with Claude.</p>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div class="sidebar-disclaimer">
    <p>Proof of Concept<br>All patient data is synthetic and GDPR-safe. No real health records are used.</p>
</div>
""", unsafe_allow_html=True)
