"""Tests for Cox PH survival model."""

import numpy as np
import pandas as pd
import pytest

from medrisk.models.cox_ph import CoxPHModel, fit_kaplan_meier


@pytest.fixture
def survival_data():
    """Small synthetic survival dataset."""
    rng = np.random.default_rng(42)
    n = 200
    df = pd.DataFrame(
        {
            "age": rng.normal(60, 10, n),
            "bmi": rng.normal(27, 4, n),
            "risk_score": rng.normal(0, 1, n),
            "time_to_event": np.abs(rng.exponential(5, n)) + 0.01,
            "event_occurred": rng.binomial(1, 0.3, n),
        }
    )
    return df


class TestCoxPHModel:
    def test_fit(self, survival_data) -> None:
        model = CoxPHModel()
        model.fit(survival_data, feature_cols=["age", "bmi", "risk_score"])
        assert model.concordance_index > 0.0
        assert model.concordance_index < 1.0

    def test_predict_risk(self, survival_data) -> None:
        model = CoxPHModel()
        model.fit(survival_data, feature_cols=["age", "bmi", "risk_score"])
        risk = model.predict_risk(survival_data)
        assert risk.shape == (len(survival_data),)

    def test_predict_survival_function(self, survival_data) -> None:
        model = CoxPHModel()
        model.fit(survival_data, feature_cols=["age", "bmi", "risk_score"])
        sf = model.predict_survival_function(survival_data.head(5))
        assert sf.shape[1] == 5
        # Survival probabilities should be in [0, 1]
        assert sf.min().min() >= 0.0
        assert sf.max().max() <= 1.0

    def test_survival_monotonically_nonincreasing(self, survival_data) -> None:
        model = CoxPHModel()
        model.fit(survival_data, feature_cols=["age", "bmi", "risk_score"])
        sf = model.predict_survival_function(survival_data.head(1))
        diffs = sf.diff().dropna()
        assert (diffs <= 1e-10).all().all(), "Survival function should be non-increasing"

    def test_summary_has_correct_covariates(self, survival_data) -> None:
        model = CoxPHModel()
        model.fit(survival_data, feature_cols=["age", "bmi", "risk_score"])
        assert len(model.summary) == 3

    def test_hazard_ratios(self, survival_data) -> None:
        model = CoxPHModel()
        model.fit(survival_data, feature_cols=["age", "bmi", "risk_score"])
        hr = model.hazard_ratios()
        assert len(hr) == 3
        assert (hr > 0).all()


class TestKaplanMeier:
    def test_fit_km(self, survival_data) -> None:
        kmf = fit_kaplan_meier(
            survival_data["time_to_event"].values,
            survival_data["event_occurred"].values,
        )
        assert kmf.median_survival_time_ > 0
