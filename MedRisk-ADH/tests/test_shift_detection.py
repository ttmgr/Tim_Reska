"""Tests for distribution shift detection."""

import numpy as np
import pandas as pd

from medrisk.validation.shift_detection import (
    compute_js_divergence,
    compute_psi,
    detect_shift,
)


class TestComputePSI:
    def test_identical_distributions(self):
        rng = np.random.default_rng(42)
        data = rng.normal(0, 1, 1000)
        psi = compute_psi(data, data)
        assert psi < 0.05

    def test_shifted_distribution(self):
        rng = np.random.default_rng(42)
        ref = rng.normal(0, 1, 1000)
        cur = rng.normal(2, 1, 1000)  # shifted mean
        psi = compute_psi(ref, cur)
        assert psi > 0.25  # significant shift

    def test_non_negative(self):
        rng = np.random.default_rng(42)
        ref = rng.normal(0, 1, 500)
        cur = rng.normal(0.5, 1.5, 500)
        assert compute_psi(ref, cur) >= 0


class TestComputeJSDivergence:
    def test_identical_zero(self):
        rng = np.random.default_rng(42)
        data = rng.normal(0, 1, 1000)
        js = compute_js_divergence(data, data)
        assert js < 0.01

    def test_different_positive(self):
        rng = np.random.default_rng(42)
        ref = rng.normal(0, 1, 1000)
        cur = rng.normal(3, 1, 1000)
        js = compute_js_divergence(ref, cur)
        assert js > 0.1

    def test_bounded(self):
        rng = np.random.default_rng(42)
        ref = rng.normal(0, 1, 500)
        cur = rng.normal(5, 0.1, 500)
        js = compute_js_divergence(ref, cur)
        assert 0 <= js <= np.log(2) + 0.01  # bounded by ln(2)


class TestDetectShift:
    def test_no_shift(self):
        rng = np.random.default_rng(42)
        df = pd.DataFrame({"f1": rng.normal(0, 1, 500), "f2": rng.normal(5, 2, 500)})
        report = detect_shift(df, df, ["f1", "f2"])
        assert not report.shift_detected
        assert len(report.flagged_features) == 0

    def test_shift_detected(self):
        rng = np.random.default_rng(42)
        ref = pd.DataFrame({"f1": rng.normal(0, 1, 500)})
        cur = pd.DataFrame({"f1": rng.normal(3, 1, 500)})
        report = detect_shift(ref, cur, ["f1"])
        assert report.shift_detected
        assert "f1" in report.flagged_features

    def test_missing_column_handled(self):
        ref = pd.DataFrame({"f1": [1, 2, 3]})
        cur = pd.DataFrame({"f2": [1, 2, 3]})
        report = detect_shift(ref, cur, ["f1"])
        assert not report.shift_detected
