"""Tests for subgroup evaluation."""

import numpy as np
import pandas as pd

from medrisk.evaluation.subgroup_eval import (
    SubgroupMetrics,
    error_analysis_by_group,
    subgroup_calibration,
)


class TestSubgroupCalibration:
    def test_returns_per_group_metrics(self):
        rng = np.random.default_rng(42)
        y_true = rng.integers(0, 2, 200)
        y_prob = rng.uniform(0, 1, 200)
        groups = pd.Series(["A"] * 100 + ["B"] * 100)
        result = subgroup_calibration(y_true, y_prob, groups)
        assert "A" in result
        assert "B" in result
        assert isinstance(result["A"], SubgroupMetrics)

    def test_metrics_bounded(self):
        rng = np.random.default_rng(42)
        y_true = rng.integers(0, 2, 300)
        y_prob = rng.uniform(0, 1, 300)
        groups = pd.Series(["X"] * 150 + ["Y"] * 150)
        result = subgroup_calibration(y_true, y_prob, groups)
        for m in result.values():
            assert 0 <= m.brier <= 1
            assert 0 <= m.ece <= 1
            if m.auc is not None:
                assert 0 <= m.auc <= 1

    def test_single_class_no_auc(self):
        y_true = np.zeros(50)
        y_prob = np.random.default_rng(42).uniform(0, 0.5, 50)
        groups = pd.Series(["only_neg"] * 50)
        result = subgroup_calibration(y_true, y_prob, groups)
        assert result["only_neg"].auc is None


class TestErrorAnalysisByGroup:
    def test_returns_dataframe(self):
        y_true = np.array([0, 1, 0, 1, 0, 1])
        y_pred = np.array([0, 1, 1, 1, 0, 0])
        y_prob = np.array([0.1, 0.9, 0.6, 0.8, 0.2, 0.4])
        groups = pd.Series(["A", "A", "A", "B", "B", "B"])
        df = error_analysis_by_group(y_true, y_pred, y_prob, groups)
        assert isinstance(df, pd.DataFrame)
        assert set(df.columns) >= {"group", "n", "TP", "FP", "TN", "FN"}
        assert len(df) == 2

    def test_counts_sum_to_n(self):
        rng = np.random.default_rng(42)
        y_true = rng.integers(0, 2, 100)
        y_pred = rng.integers(0, 2, 100)
        y_prob = rng.uniform(0, 1, 100)
        groups = pd.Series(["G"] * 100)
        df = error_analysis_by_group(y_true, y_pred, y_prob, groups)
        row = df.iloc[0]
        assert row["TP"] + row["FP"] + row["TN"] + row["FN"] == 100
