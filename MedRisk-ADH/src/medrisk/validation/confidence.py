"""Confidence calibration and epistemic uncertainty estimation.

Provides tools for assessing whether model confidence is warranted:
- Calibration-Confidence Mismatch (CCM): raw vs calibrated probability gap
- Epistemic Prediction Uncertainty (EPU): disagreement across model ensemble
- Risk decile mapping for cross-model comparison
"""

from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)


def compute_ccm(
    raw_proba: np.ndarray,
    calibrated_proba: np.ndarray,
) -> np.ndarray:
    """Compute Calibration-Confidence Mismatch per sample.

    CCM_i = |P_raw(high_risk) - P_calibrated(high_risk)|

    A high CCM indicates the model is overconfident or underconfident
    relative to its calibrated estimate.

    Args:
        raw_proba: Raw predicted probabilities.
        calibrated_proba: Platt-calibrated probabilities.

    Returns:
        Array of CCM values per sample.
    """
    return np.abs(raw_proba - calibrated_proba)


def probability_to_risk_decile(proba: np.ndarray) -> np.ndarray:
    """Map probabilities to risk deciles (1-10).

    Uses quantile binning on the input distribution.

    Args:
        proba: Array of probabilities or risk scores.

    Returns:
        Array of decile assignments (1 = lowest risk, 10 = highest).
    """
    # Handle edge case of constant predictions
    if np.std(proba) < 1e-10:
        return np.full(len(proba), 5, dtype=int)

    percentiles = np.percentile(proba, np.arange(10, 100, 10))
    return np.searchsorted(percentiles, proba, side="right").astype(int) + 1


def compute_epu(
    risk_deciles: list[np.ndarray],
) -> np.ndarray:
    """Compute Epistemic Prediction Uncertainty from model ensemble.

    EPU_i = max(decile) - min(decile) across models for sample i.

    A high EPU means the models disagree substantially about risk.

    Args:
        risk_deciles: List of decile arrays, one per model.

    Returns:
        Array of EPU values per sample.
    """
    stacked = np.stack(risk_deciles, axis=0)  # (n_models, n_samples)
    return np.max(stacked, axis=0) - np.min(stacked, axis=0)


def hazard_to_risk_score(
    log_partial_hazard: np.ndarray,
) -> np.ndarray:
    """Convert Cox PH log partial hazard to a [0, 1] risk score.

    Uses a sigmoid transformation centred on the median hazard.

    Args:
        log_partial_hazard: Array of log partial hazard values.

    Returns:
        Array of risk scores in [0, 1].
    """
    centred = log_partial_hazard - np.median(log_partial_hazard)
    return 1.0 / (1.0 + np.exp(-centred))
