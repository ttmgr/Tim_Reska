"""XGBoost risk classifier for binary underwriting decisions.

Wraps xgboost.XGBClassifier with calibration support and standardised
predict/explain interface used by the validation layer.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.calibration import CalibratedClassifierCV

logger = logging.getLogger(__name__)


@dataclass
class RiskClassifierConfig:
    """Configuration for the XGBoost risk classifier."""

    n_estimators: int = 200
    max_depth: int = 6
    learning_rate: float = 0.05
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    eval_metric: str = "logloss"
    random_state: int = 42
    early_stopping_rounds: int = 20


class RiskClassifier:
    """XGBoost binary risk classifier with optional Platt calibration.

    Attributes:
        model: The underlying XGBClassifier.
        calibrated_model: Platt-calibrated version (fit after calibrate()).
        feature_names: Feature names from training.
        is_calibrated: Whether calibrate() has been called.
    """

    def __init__(
        self, config: RiskClassifierConfig | None = None, model_id: str = "xgb_default"
    ) -> None:
        self.config = config or RiskClassifierConfig()
        self.model_id = model_id
        self.model = xgb.XGBClassifier(
            n_estimators=self.config.n_estimators,
            max_depth=self.config.max_depth,
            learning_rate=self.config.learning_rate,
            subsample=self.config.subsample,
            colsample_bytree=self.config.colsample_bytree,
            eval_metric=self.config.eval_metric,
            random_state=self.config.random_state,
        )
        self.calibrated_model: CalibratedClassifierCV | None = None
        self.feature_names: list[str] = []
        self.is_calibrated: bool = False

    def fit(
        self,
        X: pd.DataFrame | np.ndarray,
        y: np.ndarray,
        X_val: pd.DataFrame | np.ndarray | None = None,
        y_val: np.ndarray | None = None,
    ) -> RiskClassifier:
        """Train the classifier.

        Args:
            X: Training features.
            y: Binary target (0/1).
            X_val: Optional validation set for early stopping.
            y_val: Optional validation targets.

        Returns:
            self for method chaining.
        """
        if isinstance(X, pd.DataFrame):
            self.feature_names = list(X.columns)

        fit_params: dict = {}
        if X_val is not None and y_val is not None:
            fit_params["eval_set"] = [(X_val, y_val)]
            fit_params["verbose"] = False

        self.model.fit(X, y, **fit_params)
        logger.info(
            "XGBoost trained: %d estimators, %d features",
            self.model.n_estimators,
            X.shape[1],
        )
        return self

    def predict_proba(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Predict raw (uncalibrated) probability of high risk.

        Args:
            X: Feature matrix.

        Returns:
            Array of P(high_risk) for each sample.
        """
        return self.model.predict_proba(X)[:, 1]

    def predict_proba_calibrated(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Predict calibrated probability of high risk.

        Falls back to raw probabilities if not calibrated.

        Args:
            X: Feature matrix.

        Returns:
            Array of calibrated P(high_risk) for each sample.
        """
        if self.calibrated_model is not None:
            return self.calibrated_model.predict_proba(X)[:, 1]
        logger.warning("Model not calibrated, returning raw probabilities")
        return self.predict_proba(X)

    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        """Predict binary risk class.

        Args:
            X: Feature matrix.

        Returns:
            Array of 0/1 predictions.
        """
        return self.model.predict(X)

    def calibrate(
        self,
        X: pd.DataFrame | np.ndarray,
        y: np.ndarray,
        method: str = "sigmoid",
        cv: int = 3,
    ) -> RiskClassifier:
        """Fit Platt scaling (or isotonic) calibration on held-out data.

        Args:
            X: Calibration features.
            y: Calibration targets.
            method: "sigmoid" (Platt) or "isotonic".
            cv: Number of cross-validation folds.

        Returns:
            self for method chaining.
        """
        self.calibrated_model = CalibratedClassifierCV(
            estimator=self.model,
            method=method,
            cv=cv,
        )
        self.calibrated_model.fit(X, y)
        self.is_calibrated = True
        logger.info("Calibration fitted: method=%s, cv=%d", method, cv)
        return self

    def get_feature_importance(self) -> dict[str, float]:
        """Return feature importance scores from the trained model.

        Returns:
            Dictionary mapping feature names to importance scores.
        """
        importances = self.model.feature_importances_
        if self.feature_names:
            return dict(zip(self.feature_names, importances, strict=True))
        return {f"f{i}": v for i, v in enumerate(importances)}
