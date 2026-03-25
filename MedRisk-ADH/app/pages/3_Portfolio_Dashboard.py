"""Page 3: Portfolio dashboard -- aggregate C-level view."""

import sys
from collections import Counter
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import plotly.express as px  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from app.components.metrics_cards import metric_card  # noqa: E402
from app.data_cache import load_app_data  # noqa: E402
from medrisk.evaluation.metrics import auc_roc, brier_score  # noqa: E402

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
    h1, h2, h3, h4 { color: #0D2339 !important; }
    p, li { color: #2B4660 !important; }
</style>
""", unsafe_allow_html=True)

st.title("Portfolio Dashboard")
st.markdown('<p class="page-subtitle">Aggregate view across all markets and patients.</p>', unsafe_allow_html=True)

# Shared Plotly layout defaults
_PLOTLY_LAYOUT = dict(
    font=dict(family="Nunito Sans, Inter, sans-serif", color="#2B4660"),
    paper_bgcolor="#ffffff",
    plot_bgcolor="#ffffff",
    title_font=dict(size=13, color="#0D2339", family="Nunito Sans, Inter, sans-serif"),
)

MARKET_COLORS = {"DE": "#107ACA", "FR": "#4299e1", "ES": "#F97C00", "INT": "#D00D00"}

# Load data
data = load_app_data(n_per_market=1000)
df = data["df"]
dqs_results = data["dqs_results"]
decisions = data["decisions"]
predictions = data["predictions"]
events = data["events"]

n_total = len(df)

# KPI Cards
st.subheader("Key Metrics")
k1, k2, k3, k4 = st.columns(4)

auc = auc_roc(events, predictions)
brier = brier_score(events, predictions)
n_accept = sum(1 for d in decisions if d.decision == "accept")
n_review = sum(1 for d in decisions if d.decision == "human_review")
n_reject = sum(1 for d in decisions if d.decision == "reject")

with k1:
    metric_card("AUC-ROC", f"{auc:.3f}", f"{n_total:,} patients")
with k2:
    metric_card("Brier Score", f"{brier:.4f}", "Lower is better", color="#028901")
with k3:
    metric_card("Auto-Accept Rate", f"{n_accept/n_total:.0%}",
                f"{n_accept:,} of {n_total:,}", color="#028901")
with k4:
    metric_card("Review + Reject", f"{(n_review+n_reject)/n_total:.0%}",
                f"Review: {n_review:,} | Reject: {n_reject:,}", color="#D00D00")

st.divider()

# Charts
row1_col1, row1_col2 = st.columns(2)

# DQS Distribution by Market
with row1_col1:
    st.subheader("DQS Distribution by Market")
    dqs_df = pd.DataFrame({
        "market": df["market"].values,
        "dqs": [d.dqs for d in dqs_results],
    })
    fig = px.box(dqs_df, x="market", y="dqs", color="market",
                 color_discrete_map=MARKET_COLORS,
                 category_orders={"market": ["DE", "FR", "ES", "INT"]})
    fig.add_hline(y=0.80, line_dash="dash", line_color="#028901", annotation_text="Adequate")
    fig.add_hline(y=0.60, line_dash="dash", line_color="#F97C00", annotation_text="Caution")
    fig.update_layout(**_PLOTLY_LAYOUT, height=350, showlegend=False, yaxis_title="DQS")
    st.plotly_chart(fig, use_container_width=True)

# Decision Breakdown by Market
with row1_col2:
    st.subheader("Decision Breakdown by Market")
    dec_data = []
    for i, d in enumerate(decisions):
        dec_data.append({"market": df.iloc[i]["market"], "decision": d.decision})
    dec_df = pd.DataFrame(dec_data)
    dec_counts = dec_df.groupby(["market", "decision"]).size().reset_index(name="count")
    fig = px.bar(dec_counts, x="market", y="count", color="decision",
                 color_discrete_map={"accept": "#028901", "human_review": "#F97C00", "reject": "#D00D00"},
                 category_orders={"market": ["DE", "FR", "ES", "INT"],
                                  "decision": ["accept", "human_review", "reject"]},
                 barmode="stack")
    fig.update_layout(**_PLOTLY_LAYOUT, height=350, yaxis_title="Patients")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

row2_col1, row2_col2 = st.columns(2)

# Confidence vs DQS Scatter
with row2_col1:
    st.subheader("Confidence vs Data Quality")
    scatter_df = pd.DataFrame({
        "dqs": [d.dqs for d in dqs_results],
        "confidence": [max(p, 1 - p) for p in predictions],
        "market": df["market"].values,
        "decision": [d.decision for d in decisions],
    })
    fig = px.scatter(scatter_df, x="dqs", y="confidence", color="market",
                     color_discrete_map=MARKET_COLORS,
                     opacity=0.4, size_max=5)
    # PBW zone
    fig.add_shape(type="rect", x0=0, x1=0.6, y0=0.8, y1=1.02,
                  fillcolor="#D00D00", opacity=0.08, line_width=0)
    fig.add_annotation(x=0.3, y=0.9, text="PBW Zone", showarrow=False,
                       font={"color": "#D00D00", "size": 11, "family": "Inter, sans-serif"})
    fig.update_layout(**_PLOTLY_LAYOUT, height=400, xaxis_title="DQS", yaxis_title="Effective Confidence")
    st.plotly_chart(fig, use_container_width=True)

# P(wrong) Distribution
with row2_col2:
    st.subheader("P(wrong) Distribution by Market")
    pwrong_df = pd.DataFrame({
        "p_wrong": [d.p_wrong for d in decisions],
        "market": df["market"].values,
    })
    fig = px.histogram(pwrong_df, x="p_wrong", color="market", nbins=30,
                       color_discrete_map=MARKET_COLORS,
                       barmode="overlay", opacity=0.6)
    fig.update_layout(**_PLOTLY_LAYOUT, height=400, xaxis_title="P(wrong)", yaxis_title="Count")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# Reliability Head Coefficients
st.markdown('<div class="section-label">Reliability Head -- Interpretable Coefficients</div>', unsafe_allow_html=True)
st.markdown('<p style="color:#61788E; font-size:0.85rem; margin-top:-0.3rem;">What predicts model error? Logistic regression coefficients show the relationship.</p>', unsafe_allow_html=True)
rhead = data["reliability_head"]
coeff_table = rhead.get_coefficient_table()
if len(coeff_table) > 0:
    fig = px.bar(coeff_table.head(10), x="coefficient", y="feature", orientation="h",
                 color="coefficient",
                 color_continuous_scale=["#4299e1", "#e2e8f0", "#D00D00"],
                 color_continuous_midpoint=0)
    fig.update_layout(**_PLOTLY_LAYOUT, height=350,
                      yaxis={"categoryorder": "total ascending"},
                      xaxis_title="Coefficient (positive = increases P(wrong))",
                      coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

# Market summary table
st.subheader("Market Summary")
market_stats = []
for market in ["DE", "FR", "ES", "INT"]:
    mask = df["market"] == market
    indices = df[mask].index.tolist()
    m_dqs = [dqs_results[i].dqs for i in indices]
    m_dec = Counter(decisions[i].decision for i in indices)
    m_pw = [decisions[i].p_wrong for i in indices]
    market_stats.append({
        "Market": market,
        "N": mask.sum(),
        "Mean DQS": f"{np.mean(m_dqs):.3f}",
        "Accept": m_dec.get("accept", 0),
        "Review": m_dec.get("human_review", 0),
        "Reject": m_dec.get("reject", 0),
        "Accept %": f"{m_dec.get('accept', 0) / mask.sum() * 100:.1f}%",
        "Mean P(wrong)": f"{np.mean(m_pw):.3f}",
    })
st.dataframe(pd.DataFrame(market_stats), use_container_width=True, hide_index=True)
