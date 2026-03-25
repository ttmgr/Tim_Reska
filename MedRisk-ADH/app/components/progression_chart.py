"""Disease progression chart for Streamlit."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from medrisk.models.multistate import STATE_NAMES, MultistateModel

# Default colors (cardiovascular model)
_DEFAULT_COLORS = [
    "rgba(2, 137, 1, 0.5)",       # green — healthy
    "rgba(16, 122, 202, 0.5)",    # blue — risk factors
    "rgba(249, 124, 0, 0.5)",     # orange — chronic
    "rgba(208, 13, 0, 0.5)",      # red — complication
    "rgba(13, 35, 57, 0.5)",      # dark navy — major event
]
_DEFAULT_LINE_COLORS = ["#028901", "#107ACA", "#F97C00", "#D00D00", "#0D2339"]


def progression_chart(
    msm: MultistateModel,
    start_state: int = 0,
    max_time: float = 30,
    state_names: dict[int, str] | None = None,
    colors: list[str] | None = None,
    line_colors: list[str] | None = None,
    title: str = "Disease Progression (CTMC State Occupation)",
) -> None:
    """Render CTMC state occupation probabilities as stacked area chart.

    Args:
        msm: Fitted MultistateModel.
        start_state: Initial state index.
        max_time: Time horizon in years.
        state_names: Override state names. Falls back to msm.state_names.
        colors: RGBA fill colors (one per state).
        line_colors: Hex line colors (one per state).
        title: Chart title.
    """
    names = state_names or getattr(msm, "state_names", STATE_NAMES)
    n = msm.n_states

    if colors is None:
        colors = _DEFAULT_COLORS[:n] if n <= len(_DEFAULT_COLORS) else [
            f"rgba({(i * 60) % 255}, {(i * 90 + 80) % 255}, {(i * 40 + 120) % 255}, 0.5)"
            for i in range(n)
        ]
    if line_colors is None:
        line_colors = _DEFAULT_LINE_COLORS[:n] if n <= len(_DEFAULT_LINE_COLORS) else [
            f"#{(i * 60) % 255:02x}{(i * 90 + 80) % 255:02x}{(i * 40 + 120) % 255:02x}"
            for i in range(n)
        ]

    times = np.linspace(0, max_time, 200)
    probs = msm.state_occupation_probabilities(start_state, times)

    fig = go.Figure()
    for i in range(n):
        fig.add_trace(go.Scatter(
            x=times, y=probs[:, i],
            name=names.get(i, f"State {i}"),
            mode="lines",
            stackgroup="one",
            fillcolor=colors[i],
            line={"color": line_colors[i], "width": 0.5},
        ))

    fig.update_layout(
        title={"text": title,
               "font": {"size": 13, "color": "#0D2339", "family": "Nunito Sans, Inter, sans-serif"}},
        xaxis_title="Time (years)",
        yaxis_title="Probability",
        yaxis={"range": [0, 1]},
        height=350,
        margin={"t": 40, "b": 40},
        legend={"orientation": "h", "y": -0.15, "font": {"size": 10, "color": "#2B4660"}},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font={"family": "Nunito Sans, Inter, sans-serif", "color": "#2B4660"},
    )
    st.plotly_chart(fig, use_container_width=True)
