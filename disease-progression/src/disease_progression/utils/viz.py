"""
disease_progression.utils.viz - Visualization utilities for survival analysis.

Publication-quality plots for disease progression models:

    - **Kaplan-Meier curves**: Stratified survival curves with confidence
      bands, at-risk tables, and log-rank p-values.
    - **Calibration plots**: Predicted vs. observed event rates with
      perfect-calibration reference line.
    - **Attention heatmaps**: Visualize transformer self-attention weights
      over EHR token sequences for interpretability.
    - **State occupation plots**: Stacked area charts showing the expected
      proportion of a cohort in each disease state over time (for
      multistate models).
    - **CIF plots**: Cumulative incidence function curves for competing
      risks.
    - **Forest plots**: Hazard ratio plots from Cox regression.

All functions return ``matplotlib.figure.Figure`` objects that can be
saved, embedded, or displayed interactively.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.figure import Figure

logger = logging.getLogger(__name__)

# Consistent style
PALETTE = ["#2196F3", "#F44336", "#4CAF50", "#FF9800", "#9C27B0", "#607D8B", "#E91E63", "#00BCD4"]


def _apply_style() -> None:
    """Apply a clean publication style."""
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
    })


# ===================================================================
# Kaplan-Meier curves
# ===================================================================

def plot_kaplan_meier(
    event_times: np.ndarray,
    event_observed: np.ndarray,
    groups: Optional[np.ndarray] = None,
    group_labels: Optional[List[str]] = None,
    title: str = "Kaplan-Meier Survival Estimate",
    xlabel: str = "Time",
    ylabel: str = "Survival Probability",
    confidence: bool = True,
    at_risk_table: bool = True,
    figsize: Tuple[float, float] = (10, 7),
) -> Figure:
    """Plot Kaplan-Meier survival curves, optionally stratified by group.

    Parameters
    ----------
    event_times : ndarray (n,)
    event_observed : ndarray (n,)
    groups : ndarray (n,), optional
        Group labels for stratification.
    group_labels : list of str, optional
        Display names for each group.
    title : str
    xlabel, ylabel : str
    confidence : bool
        Show 95% confidence intervals (Greenwood formula).
    at_risk_table : bool
        Display number-at-risk below the plot.
    figsize : tuple

    Returns
    -------
    Figure
    """
    _apply_style()

    if at_risk_table:
        fig, (ax_km, ax_risk) = plt.subplots(
            2, 1, figsize=figsize, gridspec_kw={"height_ratios": [4, 1]}, sharex=True
        )
    else:
        fig, ax_km = plt.subplots(figsize=figsize)
        ax_risk = None

    if groups is None:
        groups = np.zeros(len(event_times), dtype=int)
        group_labels = group_labels or ["All"]

    unique_groups = np.unique(groups)
    if group_labels is None:
        group_labels = [str(g) for g in unique_groups]

    risk_table_data: Dict[str, List[Tuple[float, int]]] = {}

    for idx, (g, label) in enumerate(zip(unique_groups, group_labels)):
        mask = groups == g
        t = event_times[mask]
        e = event_observed[mask]

        km_times, km_surv, km_lower, km_upper, n_at_risk = _kaplan_meier_estimator(t, e)

        color = PALETTE[idx % len(PALETTE)]
        ax_km.step(km_times, km_surv, where="post", color=color, linewidth=2, label=label)

        if confidence:
            ax_km.fill_between(
                km_times, km_lower, km_upper,
                step="post", alpha=0.15, color=color,
            )

        risk_table_data[label] = n_at_risk

    ax_km.set_ylabel(ylabel)
    ax_km.set_title(title)
    ax_km.legend(loc="best", frameon=True, framealpha=0.9)
    ax_km.set_ylim(-0.02, 1.05)

    if at_risk_table and ax_risk is not None:
        _draw_risk_table(ax_risk, risk_table_data, xlabel)

    ax_km.set_xlabel(xlabel if not at_risk_table else "")
    fig.tight_layout()
    return fig


def _kaplan_meier_estimator(
    times: np.ndarray,
    events: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[Tuple[float, int]]]:
    """Compute KM estimate with Greenwood CI and at-risk counts."""
    n = len(times)
    order = np.argsort(times)
    sorted_t = times[order]
    sorted_e = events[order]

    unique_times = np.unique(sorted_t)
    surv = 1.0
    var_sum = 0.0

    km_t = [0.0]
    km_s = [1.0]
    km_lo = [1.0]
    km_hi = [1.0]
    at_risk_list: List[Tuple[float, int]] = [(0.0, n)]

    remaining = n
    pos = 0
    for ut in unique_times:
        # Count events and censorings at this time
        d = 0
        c = 0
        while pos < n and sorted_t[pos] == ut:
            if sorted_e[pos]:
                d += 1
            else:
                c += 1
            pos += 1

        if remaining > 0 and d > 0:
            surv *= (remaining - d) / remaining
            if remaining > d:
                var_sum += d / (remaining * (remaining - d))

        remaining -= (d + c)

        se = surv * np.sqrt(var_sum) if var_sum > 0 else 0.0
        km_t.append(ut)
        km_s.append(surv)
        km_lo.append(max(0, surv - 1.96 * se))
        km_hi.append(min(1, surv + 1.96 * se))
        at_risk_list.append((ut, max(remaining, 0)))

    return np.array(km_t), np.array(km_s), np.array(km_lo), np.array(km_hi), at_risk_list


def _draw_risk_table(
    ax: plt.Axes,
    risk_data: Dict[str, List[Tuple[float, int]]],
    xlabel: str,
) -> None:
    """Draw number-at-risk table below KM plot."""
    ax.set_xlabel(xlabel)
    ax.set_yticks(range(len(risk_data)))
    ax.set_yticklabels(list(risk_data.keys()), fontsize=10)
    ax.tick_params(axis="x", which="both", bottom=True)
    ax.grid(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)

    for idx, (label, nar) in enumerate(risk_data.items()):
        # Sample a few time points for display
        times = [t for t, _ in nar]
        counts = [c for _, c in nar]
        if len(times) > 8:
            display_idx = np.linspace(0, len(times) - 1, 8, dtype=int)
        else:
            display_idx = np.arange(len(times))
        for di in display_idx:
            ax.text(
                times[di], idx, str(counts[di]),
                ha="center", va="center", fontsize=9,
                color=PALETTE[idx % len(PALETTE)],
            )


# ===================================================================
# Calibration plot
# ===================================================================

def plot_calibration(
    predicted: np.ndarray,
    observed: np.ndarray,
    n_groups: int = 10,
    title: str = "Calibration Plot",
    xlabel: str = "Predicted Probability",
    ylabel: str = "Observed Proportion",
    figsize: Tuple[float, float] = (7, 7),
) -> Figure:
    """Plot predicted vs. observed event rates (calibration).

    Parameters
    ----------
    predicted : ndarray (n,)
        Predicted event probabilities.
    observed : ndarray (n,)
        Binary event indicators.
    n_groups : int
        Number of calibration bins.
    title, xlabel, ylabel : str
    figsize : tuple

    Returns
    -------
    Figure
    """
    _apply_style()
    fig, ax = plt.subplots(figsize=figsize)

    # Bin by predicted probability
    try:
        bins = pd.qcut(predicted, n_groups, labels=False, duplicates="drop")
    except ValueError:
        bins = pd.cut(predicted, n_groups, labels=False)

    pred_means = []
    obs_means = []
    sizes = []

    for b in sorted(np.unique(bins)):
        mask = bins == b
        pred_means.append(float(predicted[mask].mean()))
        obs_means.append(float(observed[mask].mean()))
        sizes.append(int(mask.sum()))

    pred_means = np.array(pred_means)
    obs_means = np.array(obs_means)
    sizes = np.array(sizes)

    # Perfect calibration line
    ax.plot([0, 1], [0, 1], "k--", linewidth=1, alpha=0.6, label="Perfect calibration")

    # Calibration points
    scatter = ax.scatter(
        pred_means, obs_means, s=sizes * 2, c=PALETTE[0],
        edgecolors="white", linewidth=1.5, zorder=5, alpha=0.85,
    )
    ax.plot(pred_means, obs_means, color=PALETTE[0], linewidth=1.5, alpha=0.5)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect("equal")
    ax.legend(loc="lower right")

    # Annotate mean calibration error
    mce = float(np.abs(pred_means - obs_means).mean())
    ax.text(
        0.05, 0.92, f"Mean |pred - obs| = {mce:.4f}",
        transform=ax.transAxes, fontsize=10,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.8),
    )

    fig.tight_layout()
    return fig


# ===================================================================
# Attention heatmap
# ===================================================================

def plot_attention_heatmap(
    attention_weights: np.ndarray,
    token_labels: Optional[List[str]] = None,
    layer: int = -1,
    head: int = 0,
    title: str = "Self-Attention Weights",
    figsize: Tuple[float, float] = (12, 10),
    max_tokens: int = 50,
) -> Figure:
    """Plot a heatmap of transformer self-attention weights.

    Parameters
    ----------
    attention_weights : ndarray
        Shape (n_layers, batch, n_heads, seq_len, seq_len) or
        (batch, n_heads, seq_len, seq_len) for a single layer.
    token_labels : list of str, optional
        Human-readable labels for token positions.
    layer : int
        Which layer to visualize (-1 = last).
    head : int
        Which attention head.
    title : str
    figsize : tuple
    max_tokens : int
        Truncate display to this many tokens for readability.

    Returns
    -------
    Figure
    """
    _apply_style()

    if isinstance(attention_weights, list):
        # List of per-layer arrays
        attn = attention_weights[layer]
    elif attention_weights.ndim == 5:
        attn = attention_weights[layer]
    else:
        attn = attention_weights

    # Take first sample in batch, specified head
    if attn.ndim == 4:
        attn_matrix = attn[0, head, :max_tokens, :max_tokens]
    elif attn.ndim == 3:
        attn_matrix = attn[head, :max_tokens, :max_tokens]
    else:
        attn_matrix = attn[:max_tokens, :max_tokens]

    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(attn_matrix, cmap="YlOrRd", aspect="auto", vmin=0)
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Attention Weight")

    if token_labels is not None:
        labels = token_labels[:max_tokens]
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=90, fontsize=8)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=8)

    ax.set_xlabel("Key Position")
    ax.set_ylabel("Query Position")
    ax.set_title(f"{title} (Layer {layer}, Head {head})")
    fig.tight_layout()
    return fig


# ===================================================================
# State occupation plot (multistate models)
# ===================================================================

def plot_state_occupation(
    state_probs: pd.DataFrame,
    title: str = "State Occupation Probabilities",
    xlabel: str = "Time (years)",
    ylabel: str = "Probability",
    figsize: Tuple[float, float] = (10, 6),
    stacked: bool = True,
) -> Figure:
    """Plot state occupation probabilities from a multistate model.

    Parameters
    ----------
    state_probs : pd.DataFrame
        Index = time, columns = state names, values = probabilities.
    title, xlabel, ylabel : str
    figsize : tuple
    stacked : bool
        If True, use stacked area chart. Otherwise, line plot.

    Returns
    -------
    Figure
    """
    _apply_style()
    fig, ax = plt.subplots(figsize=figsize)

    times = state_probs.index.values
    states = state_probs.columns.tolist()
    colors = PALETTE[: len(states)]

    if stacked:
        ax.stackplot(
            times,
            *[state_probs[s].values for s in states],
            labels=states,
            colors=colors,
            alpha=0.8,
        )
    else:
        for i, state in enumerate(states):
            ax.plot(
                times, state_probs[state].values,
                color=colors[i], linewidth=2, label=state,
            )

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(loc="center right", frameon=True, framealpha=0.9)
    ax.set_ylim(0, 1.02)
    ax.set_xlim(times[0], times[-1])
    fig.tight_layout()
    return fig


# ===================================================================
# CIF plot (competing risks)
# ===================================================================

def plot_cumulative_incidence(
    times: np.ndarray,
    cif_curves: Dict[str, np.ndarray],
    title: str = "Cumulative Incidence Functions",
    xlabel: str = "Time",
    ylabel: str = "Cumulative Incidence",
    figsize: Tuple[float, float] = (10, 6),
) -> Figure:
    """Plot cumulative incidence functions for competing risks.

    Parameters
    ----------
    times : ndarray (k,)
        Time grid.
    cif_curves : dict mapping str -> ndarray (k,)
        CIF values for each cause.
    title, xlabel, ylabel : str
    figsize : tuple

    Returns
    -------
    Figure
    """
    _apply_style()
    fig, ax = plt.subplots(figsize=figsize)

    for i, (cause, cif) in enumerate(cif_curves.items()):
        color = PALETTE[i % len(PALETTE)]
        ax.plot(times, cif, color=color, linewidth=2, label=cause)
        ax.fill_between(times, 0, cif, color=color, alpha=0.1)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(loc="upper left", frameon=True)
    ax.set_ylim(0, 1.02)
    fig.tight_layout()
    return fig


# ===================================================================
# Forest plot (hazard ratios)
# ===================================================================

def plot_forest(
    labels: List[str],
    hazard_ratios: np.ndarray,
    ci_lower: np.ndarray,
    ci_upper: np.ndarray,
    title: str = "Forest Plot: Hazard Ratios",
    figsize: Tuple[float, float] = (8, None),
) -> Figure:
    """Forest plot for Cox regression hazard ratios.

    Parameters
    ----------
    labels : list of str
        Covariate names.
    hazard_ratios : ndarray
    ci_lower, ci_upper : ndarray
        95% confidence interval bounds.
    title : str
    figsize : tuple
        Height is auto-calculated if None.

    Returns
    -------
    Figure
    """
    _apply_style()
    n = len(labels)
    height = figsize[1] if figsize[1] is not None else max(4, n * 0.4 + 2)
    fig, ax = plt.subplots(figsize=(figsize[0], height))

    y_pos = np.arange(n)
    xerr_lower = hazard_ratios - ci_lower
    xerr_upper = ci_upper - hazard_ratios

    ax.errorbar(
        hazard_ratios, y_pos,
        xerr=[xerr_lower, xerr_upper],
        fmt="o", color=PALETTE[0], markersize=6,
        capsize=4, elinewidth=1.5, capthick=1.5,
    )
    ax.axvline(1.0, color="gray", linestyle="--", linewidth=1, alpha=0.7)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Hazard Ratio (95% CI)")
    ax.set_title(title)
    ax.invert_yaxis()

    # Log scale for x-axis
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))

    fig.tight_layout()
    return fig


# ===================================================================
# Model comparison radar chart
# ===================================================================

def plot_model_comparison(
    model_names: List[str],
    metrics_dict: Dict[str, List[float]],
    title: str = "Model Comparison",
    figsize: Tuple[float, float] = (8, 8),
) -> Figure:
    """Radar chart comparing multiple models across metrics.

    Parameters
    ----------
    model_names : list of str
    metrics_dict : dict mapping metric_name -> list of values
        Each list must have len == len(model_names).
    title : str
    figsize : tuple

    Returns
    -------
    Figure
    """
    _apply_style()
    metric_names = list(metrics_dict.keys())
    n_metrics = len(metric_names)
    angles = np.linspace(0, 2 * np.pi, n_metrics, endpoint=False).tolist()
    angles += angles[:1]  # Close the polygon

    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))

    for i, name in enumerate(model_names):
        values = [metrics_dict[m][i] for m in metric_names]
        values += values[:1]
        color = PALETTE[i % len(PALETTE)]
        ax.plot(angles, values, "o-", linewidth=2, label=name, color=color)
        ax.fill(angles, values, alpha=0.1, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metric_names, fontsize=10)
    ax.set_title(title, pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    fig.tight_layout()
    return fig
