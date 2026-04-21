"""Subgroup-level evaluation for fairness and robustness.

Computes discrimination and calibration metrics per subgroup (market,
DQS tier, data profile, etc.) to identify populations where the model
performs poorly or is miscalibrated.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, roc_auc_score

from medrisk.evaluation.metrics import calibration_error, calibration_slope_intercept

logger = logging.getLogger(__name__)


@dataclass
class SubgroupMetrics:
    """Evaluation metrics for a single subgroup.

    Attributes:
        group_name: Identifier for this subgroup.
        n_samples: Number of samples in this subgroup.
        n_events: Number of positive events.
        auc: AUC-ROC (None if only one class).
        brier: Brier score.
        ece: Expected Calibration Error.
        cal_intercept: Calibration intercept (None if insufficient data).
        cal_slope: Calibration slope (None if insufficient data).
    """

    group_name: str
    n_samples: int
    n_events: int
    auc: float | None
    brier: float
    ece: float
    cal_intercept: float | None = None
    cal_slope: float | None = None


def subgroup_calibration(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    groups: pd.Series,
    n_bins: int = 10,
) -> dict[str, SubgroupMetrics]:
    """Compute per-subgroup discrimination and calibration.

    Args:
        y_true: Binary true labels.
        y_prob: Predicted probabilities.
        groups: Group assignment per record (e.g., market, DQS tier).
        n_bins: Number of bins for ECE.

    Returns:
        Dict mapping group value to SubgroupMetrics.
    """
    results = {}

    for group_val in sorted(groups.unique()):
        mask = groups == group_val
        y_t = y_true[mask]
        y_p = y_prob[mask]
        n = len(y_t)
        n_ev = int(y_t.sum())

        # AUC
        auc = None
        if len(np.unique(y_t)) >= 2:
            auc = float(roc_auc_score(y_t, y_p))

        # Brier
        brier = float(brier_score_loss(y_t, y_p))

        # ECE
        ece, _ = calibration_error(y_t, y_p, n_bins=n_bins)

        # Calibration slope/intercept (need sufficient data and both classes)
        cal_int = None
        cal_slope = None
        if n >= 50 and len(np.unique(y_t)) >= 2:
            try:
                cal_int, cal_slope = calibration_slope_intercept(y_t, y_p)
            except Exception:
                logger.warning("Calibration slope failed for group %s", group_val)

        results[str(group_val)] = SubgroupMetrics(
            group_name=str(group_val),
            n_samples=n,
            n_events=n_ev,
            auc=auc,
            brier=brier,
            ece=ece,
            cal_intercept=cal_int,
            cal_slope=cal_slope,
        )

    return results


def error_analysis_by_group(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
    groups: pd.Series,
) -> pd.DataFrame:
    """Detailed error breakdown per subgroup.

    Args:
        y_true: Binary true labels.
        y_pred: Binary predicted labels.
        y_prob: Predicted probabilities.
        groups: Group assignment per record.

    Returns:
        DataFrame with per-group TP, FP, TN, FN, precision, recall, F1,
        mean probability for errors.
    """
    rows = []

    for group_val in sorted(groups.unique()):
        mask = groups == group_val
        yt = y_true[mask]
        yp = y_pred[mask]
        ypr = y_prob[mask]

        tp = int(((yp == 1) & (yt == 1)).sum())
        fp = int(((yp == 1) & (yt == 0)).sum())
        tn = int(((yp == 0) & (yt == 0)).sum())
        fn = int(((yp == 0) & (yt == 1)).sum())

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        errors_mask = yp != yt
        mean_prob_errors = float(ypr[errors_mask].mean()) if errors_mask.any() else 0.0

        rows.append(
            {
                "group": str(group_val),
                "n": int(mask.sum()),
                "TP": tp,
                "FP": fp,
                "TN": tn,
                "FN": fn,
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "mean_prob_errors": round(mean_prob_errors, 4),
            }
        )

    return pd.DataFrame(rows)
