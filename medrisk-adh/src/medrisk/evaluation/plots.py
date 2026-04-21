"""Evaluation visualization for calibration, DCA, and reliability.

Generates publication-quality plots for model assessment reports.
All functions return BytesIO PNG buffers for embedding in PDFs/notebooks.
"""

from __future__ import annotations

import logging
from io import BytesIO

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.calibration import calibration_curve

from medrisk.evaluation.subgroup_eval import SubgroupMetrics

logger = logging.getLogger(__name__)

_STYLE = {
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "figure.facecolor": "white",
}


def plot_calibration_curve(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10,
    title: str = "Calibration Plot",
    ax: plt.Axes | None = None,
) -> BytesIO:
    """Calibration plot showing predicted vs. observed probability.

    Args:
        y_true: Binary true labels.
        y_prob: Predicted probabilities.
        n_bins: Number of calibration bins.
        title: Plot title.
        ax: Optional matplotlib axes.

    Returns:
        BytesIO containing the plot as PNG.
    """
    plt.rcParams.update(_STYLE)
    own_fig = ax is None
    if own_fig:
        fig, ax = plt.subplots(figsize=(6, 6), dpi=150)

    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="uniform")

    ax.plot(prob_pred, prob_true, "o-", color="#2b6cb0", label="Model", markersize=5)
    ax.plot([0, 1], [0, 1], "--", color="#a0aec0", label="Perfect calibration")
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Fraction of positives")
    ax.set_title(title, fontweight="bold")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(fontsize=8)
    ax.set_aspect("equal")

    buf = BytesIO()
    if own_fig:
        fig.tight_layout()
        fig.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)
    buf.seek(0)
    return buf


def plot_dca(
    dca_results: list[dict[str, float]],
    title: str = "Decision Curve Analysis",
    ax: plt.Axes | None = None,
) -> BytesIO:
    """Decision Curve Analysis plot.

    Args:
        dca_results: Output from metrics.decision_curve_analysis().
        title: Plot title.
        ax: Optional matplotlib axes.

    Returns:
        BytesIO containing the plot as PNG.
    """
    plt.rcParams.update(_STYLE)
    own_fig = ax is None
    if own_fig:
        fig, ax = plt.subplots(figsize=(8, 5), dpi=150)

    thresholds = [r["threshold"] for r in dca_results]
    nb_model = [r["net_benefit_model"] for r in dca_results]
    nb_all = [r["net_benefit_all"] for r in dca_results]

    ax.plot(thresholds, nb_model, "-", color="#2b6cb0", label="Model", linewidth=1.5)
    ax.plot(thresholds, nb_all, "--", color="#e53e3e", label="Treat all", linewidth=1)
    ax.axhline(0, color="#a0aec0", linestyle=":", linewidth=0.8, label="Treat none")
    ax.set_xlabel("Threshold probability")
    ax.set_ylabel("Net benefit")
    ax.set_title(title, fontweight="bold")
    ax.set_xlim(0, max(thresholds))
    ax.legend(fontsize=8)

    buf = BytesIO()
    if own_fig:
        fig.tight_layout()
        fig.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)
    buf.seek(0)
    return buf


def plot_reliability_diagram(
    p_wrong: np.ndarray,
    actual_errors: np.ndarray,
    n_bins: int = 10,
    title: str = "Reliability Head Calibration",
    ax: plt.Axes | None = None,
) -> BytesIO:
    """Calibration plot for the ReliabilityHead itself.

    Shows whether P(wrong) estimates are well-calibrated.

    Args:
        p_wrong: Estimated P(wrong) from ReliabilityHead.
        actual_errors: Binary array (1 = model was actually wrong).
        n_bins: Number of bins.
        title: Plot title.
        ax: Optional matplotlib axes.

    Returns:
        BytesIO containing the plot as PNG.
    """
    plt.rcParams.update(_STYLE)
    own_fig = ax is None
    if own_fig:
        fig, ax = plt.subplots(figsize=(6, 6), dpi=150)

    if len(np.unique(actual_errors)) >= 2:
        prob_true, prob_pred = calibration_curve(
            actual_errors,
            p_wrong,
            n_bins=n_bins,
            strategy="uniform",
        )
        ax.plot(prob_pred, prob_true, "o-", color="#e53e3e", label="ReliabilityHead", markersize=5)

    ax.plot([0, 1], [0, 1], "--", color="#a0aec0", label="Perfect")
    ax.set_xlabel("Predicted P(wrong)")
    ax.set_ylabel("Actual error rate")
    ax.set_title(title, fontweight="bold")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(fontsize=8)
    ax.set_aspect("equal")

    buf = BytesIO()
    if own_fig:
        fig.tight_layout()
        fig.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)
    buf.seek(0)
    return buf


def plot_subgroup_calibration(
    subgroup_metrics: dict[str, SubgroupMetrics],
    title: str = "Subgroup Calibration Comparison",
) -> BytesIO:
    """Bar chart comparing AUC, ECE, and Brier across subgroups.

    Args:
        subgroup_metrics: Dict from subgroup_calibration().
        title: Plot title.

    Returns:
        BytesIO containing the plot as PNG.
    """
    plt.rcParams.update(_STYLE)
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), dpi=150)

    groups = list(subgroup_metrics.keys())
    aucs = [m.auc if m.auc is not None else 0 for m in subgroup_metrics.values()]
    briers = [m.brier for m in subgroup_metrics.values()]
    eces = [m.ece for m in subgroup_metrics.values()]

    colors = ["#2b6cb0", "#4299e1", "#ed8936", "#e53e3e"][: len(groups)]

    axes[0].bar(groups, aucs, color=colors, alpha=0.8)
    axes[0].set_title("AUC-ROC", fontweight="bold")
    axes[0].set_ylim(0.4, 1.0)
    axes[0].axhline(0.5, color="#a0aec0", linestyle=":", linewidth=0.8)

    axes[1].bar(groups, briers, color=colors, alpha=0.8)
    axes[1].set_title("Brier Score", fontweight="bold")

    axes[2].bar(groups, eces, color=colors, alpha=0.8)
    axes[2].set_title("ECE", fontweight="bold")

    fig.suptitle(title, fontweight="bold", fontsize=12, y=1.02)
    fig.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf
