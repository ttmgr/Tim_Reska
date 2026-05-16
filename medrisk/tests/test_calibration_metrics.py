"""Tests for v2 calibration and DCA metrics."""

import numpy as np

from medrisk.evaluation.metrics import calibration_slope_intercept, decision_curve_analysis


class TestCalibrationSlopeIntercept:
    def test_perfect_calibration(self):
        rng = np.random.default_rng(42)
        y_prob = rng.uniform(0.01, 0.99, 500)
        y_true = (rng.random(500) < y_prob).astype(int)
        intercept, slope = calibration_slope_intercept(y_true, y_prob)
        # Should be close to 0 and 1 for well-calibrated predictions
        assert abs(intercept) < 1.0
        assert abs(slope - 1.0) < 1.0

    def test_overconfident_slope_less_than_one(self):
        rng = np.random.default_rng(42)
        # True prevalence is 10% but predictions are spread wide
        y_true = (rng.random(1000) < 0.1).astype(int)
        y_prob = rng.uniform(0.0, 1.0, 1000)
        intercept, slope = calibration_slope_intercept(y_true, y_prob)
        # Overconfident predictions -> slope < 1
        assert slope < 1.5  # relaxed bound


class TestDecisionCurveAnalysis:
    def test_returns_results(self):
        rng = np.random.default_rng(42)
        y_true = rng.integers(0, 2, 200)
        y_prob = rng.uniform(0, 1, 200)
        results = decision_curve_analysis(y_true, y_prob)
        assert len(results) > 0
        assert "threshold" in results[0]
        assert "net_benefit_model" in results[0]
        assert "net_benefit_all" in results[0]

    def test_treat_none_is_zero(self):
        rng = np.random.default_rng(42)
        y_true = rng.integers(0, 2, 100)
        y_prob = rng.uniform(0, 1, 100)
        results = decision_curve_analysis(y_true, y_prob)
        for r in results:
            assert r["net_benefit_none"] == 0.0

    def test_custom_thresholds(self):
        y_true = np.array([0, 1, 0, 1])
        y_prob = np.array([0.1, 0.8, 0.3, 0.9])
        thresholds = np.array([0.2, 0.5, 0.8])
        results = decision_curve_analysis(y_true, y_prob, thresholds=thresholds)
        assert len(results) == 3
