"""SHAP visualization for Streamlit."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st


def shap_bar_chart(feature_names: list[str], importances: list[float], n_top: int = 10) -> None:
    """Render a horizontal bar chart of feature importances."""
    # Sort by absolute importance
    pairs = sorted(zip(feature_names, importances), key=lambda x: abs(x[1]), reverse=True)
    pairs = pairs[:n_top]
    names = [p[0] for p in reversed(pairs)]
    values = [p[1] for p in reversed(pairs)]

    fig, ax = plt.subplots(figsize=(8, 4), facecolor="white")
    ax.set_facecolor("white")
    colors = ["#D00D00" if v > 0 else "#107ACA" for v in values]
    ax.barh(names, values, color=colors, height=0.6)
    ax.set_xlabel("Feature Importance (XGBoost gain)", fontsize=10, color="#2B4660")
    ax.set_title("Top Risk Drivers", fontweight="600", fontsize=12, color="#0D2339")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#C4CDD6")
    ax.spines["bottom"].set_color("#C4CDD6")
    ax.tick_params(colors="#2B4660", labelsize=9)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
