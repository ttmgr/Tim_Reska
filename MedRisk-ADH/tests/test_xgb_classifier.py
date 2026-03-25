"""Tests for XGBoost risk classifier."""

import numpy as np
import pytest

from medrisk.models.xgb_classifier import RiskClassifier, RiskClassifierConfig


@pytest.fixture
def simple_data():
    """Small synthetic dataset for classifier tests."""
    rng = np.random.default_rng(42)
    n = 200
    X = rng.standard_normal((n, 10))
    # Target correlated with first two features
    logit = 0.5 * X[:, 0] + 0.3 * X[:, 1] + rng.standard_normal(n) * 0.5
    y = (logit > 0).astype(int)
    return X, y


class TestRiskClassifier:
    def test_fit_and_predict(self, simple_data) -> None:
        X, y = simple_data
        clf = RiskClassifier(RiskClassifierConfig(n_estimators=20, max_depth=3))
        clf.fit(X, y)
        proba = clf.predict_proba(X)
        assert proba.shape == (len(X),)
        assert np.all((proba >= 0) & (proba <= 1))

    def test_predict_binary(self, simple_data) -> None:
        X, y = simple_data
        clf = RiskClassifier(RiskClassifierConfig(n_estimators=20, max_depth=3))
        clf.fit(X, y)
        preds = clf.predict(X)
        assert set(np.unique(preds)).issubset({0, 1})

    def test_feature_importance(self, simple_data) -> None:
        X, y = simple_data
        clf = RiskClassifier(RiskClassifierConfig(n_estimators=20, max_depth=3))
        clf.fit(X, y)
        importance = clf.get_feature_importance()
        assert len(importance) == 10

    def test_calibration(self, simple_data) -> None:
        X, y = simple_data
        clf = RiskClassifier(RiskClassifierConfig(n_estimators=20, max_depth=3))
        clf.fit(X[:150], y[:150])
        clf.calibrate(X[:150], y[:150], cv=2)
        assert clf.is_calibrated
        proba = clf.predict_proba_calibrated(X[150:])
        assert np.all((proba >= 0) & (proba <= 1))

    def test_uncalibrated_fallback(self, simple_data) -> None:
        X, y = simple_data
        clf = RiskClassifier(RiskClassifierConfig(n_estimators=20, max_depth=3))
        clf.fit(X, y)
        assert not clf.is_calibrated
        # Should fall back to raw proba
        proba = clf.predict_proba_calibrated(X)
        assert proba.shape == (len(X),)

    def test_with_validation_set(self, simple_data) -> None:
        X, y = simple_data
        clf = RiskClassifier(RiskClassifierConfig(n_estimators=50, max_depth=3))
        clf.fit(X[:150], y[:150], X_val=X[150:], y_val=y[150:])
        proba = clf.predict_proba(X)
        assert proba.shape == (len(X),)
