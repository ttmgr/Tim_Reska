"""Cox Proportional Hazards survival model.

Thin wrapper around lifelines.CoxPHFitter with a standardised interface
for the MedRisk pipeline.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter

logger = logging.getLogger(__name__)


class CoxPHModel:
    """Cox PH survival model wrapper.

    Attributes:
        model: The underlying lifelines CoxPHFitter.
        duration_col: Name of the time-to-event column.
        event_col: Name of the event indicator column.
    """

    def __init__(
        self,
        penalizer: float = 0.01,
        l1_ratio: float = 0.0,
        duration_col: str = "time_to_event",
        event_col: str = "event_occurred",
    ) -> None:
        self.model = CoxPHFitter(penalizer=penalizer, l1_ratio=l1_ratio)
        self.duration_col = duration_col
        self.event_col = event_col
        self.feature_names: list[str] = []

    def fit(
        self,
        df: pd.DataFrame,
        feature_cols: list[str],
    ) -> CoxPHModel:
        """Fit the Cox PH model.

        Args:
            df: DataFrame containing features, duration, and event columns.
            feature_cols: List of feature column names to use as covariates.

        Returns:
            self for method chaining.
        """
        self.feature_names = list(feature_cols)
        cols = feature_cols + [self.duration_col, self.event_col]
        fit_df = df[cols].copy()

        # Ensure minimum time > 0
        fit_df[self.duration_col] = fit_df[self.duration_col].clip(lower=0.001)

        self.model.fit(
            fit_df,
            duration_col=self.duration_col,
            event_col=self.event_col,
        )
        logger.info(
            "Cox PH fitted: %d covariates, concordance=%.4f",
            len(feature_cols),
            self.model.concordance_index_,
        )
        return self

    def predict_risk(self, X: pd.DataFrame) -> np.ndarray:
        """Predict log partial hazard for each patient.

        Higher values indicate higher risk.

        Args:
            X: Feature DataFrame (must contain feature_names columns).

        Returns:
            Array of log partial hazard values.
        """
        return self.model.predict_log_partial_hazard(X[self.feature_names]).values.ravel()

    def predict_survival_function(
        self,
        X: pd.DataFrame,
        times: np.ndarray | None = None,
    ) -> pd.DataFrame:
        """Predict survival function S(t) for each patient.

        Args:
            X: Feature DataFrame.
            times: Specific time points to evaluate. If None, uses training times.

        Returns:
            DataFrame with survival probabilities (rows=times, columns=patients).
        """
        sf = self.model.predict_survival_function(X[self.feature_names])
        if times is not None:
            # Reindex to requested times
            sf = sf.reindex(times, method="ffill")
        return sf

    def predict_median_survival(self, X: pd.DataFrame) -> np.ndarray:
        """Predict median survival time for each patient.

        Args:
            X: Feature DataFrame.

        Returns:
            Array of median survival times.
        """
        return self.model.predict_median(X[self.feature_names]).values.ravel()

    @property
    def concordance_index(self) -> float:
        """Return the concordance index from the fitted model."""
        return self.model.concordance_index_

    @property
    def summary(self) -> pd.DataFrame:
        """Return the model summary table."""
        return self.model.summary

    def hazard_ratios(self) -> pd.Series:
        """Return exponentiated coefficients (hazard ratios)."""
        return np.exp(self.model.params_)


def fit_kaplan_meier(
    durations: np.ndarray,
    events: np.ndarray,
    label: str = "KM",
) -> KaplanMeierFitter:
    """Fit a Kaplan-Meier estimator.

    Args:
        durations: Time-to-event array.
        events: Event indicator array (1=event, 0=censored).
        label: Label for the estimator.

    Returns:
        Fitted KaplanMeierFitter.
    """
    kmf = KaplanMeierFitter()
    kmf.fit(durations, event_observed=events, label=label)
    return kmf
