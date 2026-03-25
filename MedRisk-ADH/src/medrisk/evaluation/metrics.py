"""Discrimination, calibration, and evaluation metrics.

Standard metrics for evaluating risk models in a medical underwriting context.
"""

from __future__ import annotations

import logging

import numpy as np
from sklearn.metrics import (
    brier_score_loss,
    roc_auc_score,
)

logger = logging.getLogger(__name__)


def concordance_index(
    event_times: np.ndarray,
    predicted_risk: np.ndarray,
    event_observed: np.ndarray,
) -> float:
    """Compute Harrell's concordance index.

    For each concordant pair where the patient with shorter survival has
    higher predicted risk, the pair is concordant.

    Args:
        event_times: Array of observed times.
        predicted_risk: Array of predicted risk scores (higher = worse).
        event_observed: Binary array (1=event, 0=censored).

    Returns:
        C-index in [0, 1]. 0.5 = random, 1.0 = perfect.
    """
    n = len(event_times)
    concordant = 0
    discordant = 0
    tied = 0

    for i in range(n):
        if not event_observed[i]:
            continue
        for j in range(n):
            if i == j:
                continue
            if event_times[i] < event_times[j]:
                # i had event before j — i should have higher risk
                if predicted_risk[i] > predicted_risk[j]:
                    concordant += 1
                elif predicted_risk[i] < predicted_risk[j]:
                    discordant += 1
                else:
                    tied += 1

    total = concordant + discordant + tied
    if total == 0:
        return 0.5

    return (concordant + 0.5 * tied) / total


def auc_roc(
    y_true: np.ndarray,
    y_score: np.ndarray,
) -> float:
    """Compute area under the ROC curve.

    Args:
        y_true: Binary true labels.
        y_score: Predicted probabilities or scores.

    Returns:
        AUC-ROC score.
    """
    if len(np.unique(y_true)) < 2:
        logger.warning("Only one class present in y_true, AUC-ROC undefined")
        return 0.5
    return float(roc_auc_score(y_true, y_score))


def brier_score(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> float:
    """Compute Brier score (mean squared error of probabilities).

    Lower is better. 0.0 = perfect, 0.25 = no skill.

    Args:
        y_true: Binary true labels.
        y_prob: Predicted probabilities.

    Returns:
        Brier score.
    """
    return float(brier_score_loss(y_true, y_prob))


def calibration_error(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10,
) -> tuple[float, list[tuple[float, float, int]]]:
    """Compute expected calibration error (ECE) and per-bin statistics.

    Args:
        y_true: Binary true labels.
        y_prob: Predicted probabilities.
        n_bins: Number of calibration bins.

    Returns:
        Tuple of (ECE, list of (mean_predicted, fraction_positive, bin_count)).
    """
    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    bin_stats: list[tuple[float, float, int]] = []

    for i in range(n_bins):
        mask = (y_prob >= bin_edges[i]) & (y_prob < bin_edges[i + 1])
        if i == n_bins - 1:
            mask = mask | (y_prob == bin_edges[i + 1])

        count = mask.sum()
        if count == 0:
            bin_stats.append((0.0, 0.0, 0))
            continue

        mean_pred = y_prob[mask].mean()
        frac_pos = y_true[mask].mean()
        ece += count * abs(mean_pred - frac_pos)
        bin_stats.append((float(mean_pred), float(frac_pos), int(count)))

    ece /= len(y_true) if len(y_true) > 0 else 1
    return float(ece), bin_stats


# ============================================================================
# v2: Calibration slope/intercept + Decision Curve Analysis
# ============================================================================


def calibration_slope_intercept(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> tuple[float, float]:
    """Compute calibration slope and intercept (Cox method).

    Fits logit(y) ~ a + b * logit(p). Perfect calibration: a=0, b=1.
    Slope < 1 means overconfident, slope > 1 means underconfident.

    Args:
        y_true: Binary true labels.
        y_prob: Predicted probabilities.

    Returns:
        Tuple of (intercept, slope).
    """
    from sklearn.linear_model import LogisticRegression

    # Clip to avoid log(0)
    eps = 1e-7
    p_clipped = np.clip(y_prob, eps, 1.0 - eps)
    logit_p = np.log(p_clipped / (1.0 - p_clipped))

    lr = LogisticRegression(penalty=None, max_iter=1000)
    lr.fit(logit_p.reshape(-1, 1), y_true)

    intercept = float(lr.intercept_[0])
    slope = float(lr.coef_[0, 0])

    logger.info("Calibration: intercept=%.4f, slope=%.4f", intercept, slope)
    return intercept, slope


def decision_curve_analysis(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    thresholds: np.ndarray | None = None,
) -> list[dict[str, float]]:
    """Compute net benefit at each threshold for Decision Curve Analysis.

    Net benefit = (TP/N) - (FP/N) * (pt / (1-pt))
    where pt is the threshold probability.

    Args:
        y_true: Binary true labels.
        y_prob: Predicted probabilities.
        thresholds: Array of threshold values to evaluate.

    Returns:
        List of dicts with keys: threshold, net_benefit_model,
        net_benefit_all, net_benefit_none.
    """

    if thresholds is None:
        thresholds = np.arange(0.01, 0.99, 0.01)

    n = len(y_true)
    prevalence = y_true.mean()
    results = []

    for pt in thresholds:
        # Model strategy
        pred_pos = y_prob >= pt
        tp = ((pred_pos) & (y_true == 1)).sum()
        fp = ((pred_pos) & (y_true == 0)).sum()

        odds = pt / (1.0 - pt) if pt < 1.0 else float("inf")
        nb_model = (tp / n) - (fp / n) * odds

        # Treat all strategy
        nb_all = prevalence - (1.0 - prevalence) * odds

        # Treat none strategy
        nb_none = 0.0

        results.append(
            {
                "threshold": round(float(pt), 4),
                "net_benefit_model": round(float(nb_model), 6),
                "net_benefit_all": round(float(nb_all), 6),
                "net_benefit_none": nb_none,
            }
        )

    return results
