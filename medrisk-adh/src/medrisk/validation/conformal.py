"""Split-conformal prediction intervals.

Provides distribution-free, finite-sample coverage guarantees for
any point predictor. Based on Vovk et al. (2005) and the modern
treatment by Angelopoulos & Bates (2023).

Usage:
    cp = ConformalPredictor()
    cp.calibrate(y_cal, y_hat_cal)
    lower, upper = cp.predict_interval(y_hat_new, alpha=0.10)
"""

from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)


class ConformalPredictor:
    """Split-conformal prediction intervals for regression.

    After calibration on a held-out set, produces prediction intervals
    with guaranteed 1-alpha coverage (finite-sample, distribution-free).
    """

    def __init__(self) -> None:
        self.scores_: np.ndarray | None = None

    def calibrate(self, y_true: np.ndarray, y_hat: np.ndarray) -> None:
        """Compute nonconformity scores on calibration set.

        Args:
            y_true: True values (calibration set).
            y_hat: Predicted values (calibration set).
        """
        y_true = np.asarray(y_true, dtype=float)
        y_hat = np.asarray(y_hat, dtype=float)
        self.scores_ = np.abs(y_true - y_hat)
        logger.info(
            "Conformal calibration: %d samples, median score %.3f",
            len(self.scores_),
            np.median(self.scores_),
        )

    def predict_interval(
        self,
        y_hat: float | np.ndarray,
        alpha: float = 0.10,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Compute prediction interval with 1-alpha coverage.

        Args:
            y_hat: Point predictions for new data.
            alpha: Miscoverage rate (0.10 = 90% coverage).

        Returns:
            (lower, upper) bounds with guaranteed coverage.
        """
        if self.scores_ is None:
            raise RuntimeError("Call calibrate() first.")

        n = len(self.scores_)
        # Finite-sample correction: ceil((n+1)(1-alpha))/n quantile
        q_level = min(np.ceil((n + 1) * (1 - alpha)) / n, 1.0)
        q_hat = np.quantile(self.scores_, q_level)

        y_hat = np.asarray(y_hat, dtype=float)
        return y_hat - q_hat, y_hat + q_hat

    @property
    def is_calibrated(self) -> bool:
        return self.scores_ is not None
