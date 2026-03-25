"""Distribution shift detection for monitoring data drift.

Computes Population Stability Index (PSI) and Jensen-Shannon divergence
between reference (training) and incoming distributions. Used to flag
when the input data has shifted enough to warrant model recalibration.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ShiftReport:
    """Result of distribution shift detection.

    Attributes:
        per_feature_psi: PSI value per feature.
        aggregate_psi: Mean PSI across all features.
        shift_detected: True if aggregate PSI exceeds threshold.
        flagged_features: Features with PSI above threshold.
    """

    per_feature_psi: dict[str, float] = field(default_factory=dict)
    aggregate_psi: float = 0.0
    shift_detected: bool = False
    flagged_features: list[str] = field(default_factory=list)


def compute_psi(
    reference: np.ndarray,
    current: np.ndarray,
    n_bins: int = 10,
) -> float:
    """Compute Population Stability Index between two distributions.

    PSI < 0.10: no significant shift
    PSI 0.10-0.25: moderate shift
    PSI > 0.25: significant shift

    Args:
        reference: Reference (training) distribution.
        current: Current (incoming) distribution.
        n_bins: Number of bins.

    Returns:
        PSI value (>= 0).
    """
    eps = 1e-6

    # Use reference quantiles as bin edges for robustness
    bin_edges = np.percentile(reference, np.linspace(0, 100, n_bins + 1))
    bin_edges[0] = -np.inf
    bin_edges[-1] = np.inf

    ref_counts = np.histogram(reference, bins=bin_edges)[0]
    cur_counts = np.histogram(current, bins=bin_edges)[0]

    ref_pct = ref_counts / len(reference) + eps
    cur_pct = cur_counts / len(current) + eps

    psi = float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))
    return max(0.0, psi)


def compute_js_divergence(
    reference: np.ndarray,
    current: np.ndarray,
    n_bins: int = 50,
) -> float:
    """Compute Jensen-Shannon divergence between two distributions.

    JS divergence is symmetric and bounded [0, ln(2)].

    Args:
        reference: Reference distribution.
        current: Current distribution.
        n_bins: Number of bins.

    Returns:
        JS divergence value in [0, ln(2)].
    """
    eps = 1e-10

    all_data = np.concatenate([reference, current])
    bin_edges = np.histogram_bin_edges(all_data, bins=n_bins)

    p = np.histogram(reference, bins=bin_edges)[0].astype(float)
    q = np.histogram(current, bins=bin_edges)[0].astype(float)

    p = p / p.sum() + eps
    q = q / q.sum() + eps

    m = 0.5 * (p + q)

    kl_pm = float(np.sum(p * np.log(p / m)))
    kl_qm = float(np.sum(q * np.log(q / m)))

    return 0.5 * kl_pm + 0.5 * kl_qm


def detect_shift(
    training_df: pd.DataFrame,
    incoming_df: pd.DataFrame,
    feature_cols: list[str],
    psi_threshold: float = 0.20,
) -> ShiftReport:
    """Detect distribution shift between training and incoming data.

    Args:
        training_df: Reference (training) DataFrame.
        incoming_df: Incoming (production) DataFrame.
        feature_cols: Feature columns to check.
        psi_threshold: PSI threshold for flagging a feature.

    Returns:
        ShiftReport with per-feature PSI and aggregate assessment.
    """
    per_feature: dict[str, float] = {}
    flagged: list[str] = []

    for col in feature_cols:
        if col not in training_df.columns or col not in incoming_df.columns:
            continue

        ref = training_df[col].dropna().values
        cur = incoming_df[col].dropna().values

        if len(ref) < 10 or len(cur) < 10:
            continue

        psi = compute_psi(ref, cur)
        per_feature[col] = round(psi, 4)

        if psi > psi_threshold:
            flagged.append(col)

    agg_psi = float(np.mean(list(per_feature.values()))) if per_feature else 0.0

    return ShiftReport(
        per_feature_psi=per_feature,
        aggregate_psi=round(agg_psi, 4),
        shift_detected=len(flagged) > 0,
        flagged_features=flagged,
    )
