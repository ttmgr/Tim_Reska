"""KPI metric card components for Streamlit."""

from __future__ import annotations

import streamlit as st


def metric_card(label: str, value: str, delta: str = "", color: str = "#107ACA") -> None:
    """Render a styled metric card."""
    st.markdown(
        f"""
        <div style="background: #ffffff; border: 1px solid #C4CDD6;
                    border-left: 4px solid {color}; padding: 14px 16px;
                    border-radius: 8px; margin-bottom: 8px;
                    transition: box-shadow 0.2s ease;">
            <div style="font-size: 0.7rem; color: #61788E; text-transform: uppercase;
                        letter-spacing: 1.5px; font-weight: 600;">{label}</div>
            <div style="font-size: 1.65rem; font-weight: 700; color: {color};
                        margin: 4px 0; line-height: 1.2;">{value}</div>
            {f'<div style="font-size: 0.7rem; color: #61788E; margin-top: 2px;">{delta}</div>' if delta else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def decision_badge(decision: str) -> str:
    """Return colored HTML badge for a decision."""
    colors = {
        "accept": ("#028901", "#f0fff4"),
        "human_review": ("#F97C00", "#fffff0"),
        "reject": ("#D00D00", "#fff5f5"),
    }
    fg, bg = colors.get(decision, ("#718096", "#f7fafc"))
    label = decision.upper().replace("_", " ")
    return (
        f'<span style="background:{bg}; color:{fg}; border:1px solid {fg}33; padding:5px 14px; '
        f'border-radius:4px; font-weight:700; font-size:0.8rem; letter-spacing:0.5px;">{label}</span>'
    )


def dqs_tier_badge(tier: str) -> str:
    """Return colored HTML badge for DQS tier."""
    colors = {
        "adequate": ("#028901", "#f0fff4"),
        "caution": ("#F97C00", "#fffff0"),
        "insufficient": ("#D00D00", "#fff5f5"),
    }
    fg, bg = colors.get(tier, ("#718096", "#f7fafc"))
    return (
        f'<span style="background:{bg}; color:{fg}; border:1px solid {fg}33; padding:3px 10px; '
        f'border-radius:4px; font-weight:600; font-size:0.7rem; letter-spacing:0.5px;">'
        f'{tier.upper()}</span>'
    )
