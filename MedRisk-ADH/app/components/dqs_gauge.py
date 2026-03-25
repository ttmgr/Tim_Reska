"""DQS visualization components."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from medrisk.validation.data_quality import DQSv2Result


def dqs_gauge(dqs: DQSv2Result) -> None:
    """Render DQS as a gauge chart with component bars."""
    # Gauge
    tier_colors = {"adequate": "#028901", "caution": "#F97C00", "insufficient": "#D00D00"}
    color = tier_colors.get(dqs.tier, "#718096")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=dqs.dqs,
        number={"font": {"size": 32, "color": "#0D2339", "family": "Nunito Sans, Inter, sans-serif"},
                "valueformat": ".2f"},
        gauge={
            "axis": {"range": [0, 1], "tickvals": [0, 0.6, 0.8, 1.0],
                     "tickfont": {"size": 10, "color": "#61788E"}},
            "bar": {"color": color, "thickness": 0.75},
            "bgcolor": "#f7fafc",
            "bordercolor": "#e2e8f0",
            "borderwidth": 1,
            "steps": [
                {"range": [0, 0.6], "color": "#fff5f5"},
                {"range": [0.6, 0.8], "color": "#fffff0"},
                {"range": [0.8, 1.0], "color": "#f0fff4"},
            ],
            "threshold": {"line": {"color": color, "width": 2}, "value": dqs.dqs},
        },
        title={"text": f"DQS: {dqs.tier.upper()}",
               "font": {"size": 11, "color": "#61788E", "family": "Nunito Sans, Inter, sans-serif"}},
    ))
    fig.update_layout(
        height=200,
        margin={"t": 40, "b": 5, "l": 25, "r": 25},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font={"family": "Nunito Sans, Inter, sans-serif", "color": "#2B4660"},
    )
    st.plotly_chart(fig, use_container_width=True)


def dqs_components_bar(dqs: DQSv2Result) -> None:
    """Render DQS component breakdown as horizontal bars."""
    components = [
        ("Completeness (0.40)", dqs.completeness, "#107ACA"),
        ("Consistency (0.35)", dqs.consistency, "#028901"),
        ("Recency (0.25)", dqs.recency, "#F97C00"),
        ("Range Score", dqs.range_score, "#2B4660"),
    ]

    for label, value, color in components:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(
                f'<div style="font-size:0.7rem; color:#61788E; text-transform:uppercase; '
                f'letter-spacing:1px; margin-bottom:2px;">{label}</div>'
                f'<div style="background:#EEF2F7; border-radius:3px; height:10px; width:100%; '
                f'border:1px solid #C4CDD6;">'
                f'<div style="background:{color}; border-radius:3px; height:100%; '
                f'width:{value*100:.0f}%;"></div></div>',
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f'<div style="font-size:0.85rem; font-weight:600; color:#0D2339; '
                f'text-align:right; padding-top:14px;">{value:.2f}</div>',
                unsafe_allow_html=True,
            )
