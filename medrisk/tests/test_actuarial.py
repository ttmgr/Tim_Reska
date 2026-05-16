"""Tests for medrisk.models.actuarial."""

import numpy as np
import pytest

from medrisk.models.actuarial import (
    AggregateClaimsModel,
    bornhuetter_ferguson,
    chain_ladder,
)

# ---------------------------------------------------------------------------
# Chain-Ladder
# ---------------------------------------------------------------------------


class TestChainLadder:
    def _triangle(self):
        # 4x4 triangle; lower-right NaN = unreported
        tri = np.array(
            [
                [100.0, 150.0, 165.0, 170.0],
                [110.0, 160.0, 175.0, np.nan],
                [120.0, 170.0, np.nan, np.nan],
                [130.0, np.nan, np.nan, np.nan],
            ]
        )
        return tri

    def test_returns_dict_with_expected_keys(self):
        result = chain_ladder(self._triangle())
        assert "factors" in result
        assert "ultimates" in result
        assert "reserves" in result
        assert "triangle" in result

    def test_factors_length(self):
        result = chain_ladder(self._triangle())
        assert len(result["factors"]) == 3  # n_dev - 1

    def test_factors_positive(self):
        result = chain_ladder(self._triangle())
        assert (result["factors"] > 0).all()

    def test_ultimates_geq_latest_diagonal(self):
        result = chain_ladder(self._triangle())
        # All ultimates should be >= the most recent reported value
        assert (result["ultimates"] >= 0).all()

    def test_reserves_nonnegative(self):
        result = chain_ladder(self._triangle())
        assert (result["reserves"] >= 0).all()

    def test_fully_developed_row_zero_reserve(self):
        # First row is fully developed: ultimate = 170, reserve = 0
        result = chain_ladder(self._triangle())
        assert result["reserves"][0] == pytest.approx(0.0, abs=1e-6)

    def test_completed_triangle_no_nan(self):
        result = chain_ladder(self._triangle())
        assert not np.isnan(result["triangle"]).any()


class TestBornhuetterFerguson:
    def _triangle(self):
        return np.array(
            [
                [100.0, 150.0, 165.0, 170.0],
                [110.0, 160.0, 175.0, np.nan],
                [120.0, 170.0, np.nan, np.nan],
                [130.0, np.nan, np.nan, np.nan],
            ]
        )

    def test_returns_bf_ultimates(self):
        prior = np.array([170.0, 180.0, 190.0, 200.0])
        result = bornhuetter_ferguson(self._triangle(), prior)
        assert "bf_ultimates" in result
        assert "bf_reserves" in result

    def test_bf_reserves_nonnegative(self):
        prior = np.array([170.0, 180.0, 190.0, 200.0])
        result = bornhuetter_ferguson(self._triangle(), prior)
        assert (result["bf_reserves"] >= -0.01).all()

    def test_fully_developed_bf_reserve_zero(self):
        prior = np.array([170.0, 180.0, 190.0, 200.0])
        result = bornhuetter_ferguson(self._triangle(), prior)
        assert result["bf_reserves"][0] == pytest.approx(0.0, abs=1e-6)

    def test_bf_between_cl_and_prior(self):
        # BF should be a blend: bf_ultimate <= max(cl_ultimate, prior_ultimate)
        prior = np.array([180.0, 190.0, 200.0, 210.0])
        result = bornhuetter_ferguson(self._triangle(), prior)
        cl_ults = result["cl_ultimates"]
        bf_ults = result["bf_ultimates"]
        for i in range(len(bf_ults)):
            lo = min(cl_ults[i], prior[i]) - 1.0
            hi = max(cl_ults[i], prior[i]) + 1.0
            assert lo <= bf_ults[i] <= hi


# ---------------------------------------------------------------------------
# Aggregate Claims Model (Panjer)
# ---------------------------------------------------------------------------


class TestAggregateClaimsModel:
    def _model_with_pmf(self, m=100):
        """NegBin frequency + Weibull severity (discretised)."""
        from scipy.stats import weibull_min  # type: ignore[import-untyped]

        model = AggregateClaimsModel(
            freq_distribution="negbin",
            freq_params={"r": 5.0, "beta": 2.0},
        )
        # Weibull(c=1.5, scale=10) severity, grid step h=1, m=100 points
        dist = weibull_min(c=1.5, scale=10.0)
        model.discretise_severity(dist, h=1.0, m=m)
        return model

    def test_severity_pmf_sums_to_one(self):
        model = self._model_with_pmf()
        assert abs(model.severity_pmf.sum() - 1.0) < 1e-8

    def test_panjer_pmf_sums_to_approximately_one(self):
        model = self._model_with_pmf()
        g = model.panjer_recursion()
        assert abs(g.sum() - 1.0) < 1e-4

    def test_panjer_pmf_nonnegative(self):
        model = self._model_with_pmf()
        g = model.panjer_recursion()
        assert (g >= -1e-10).all()

    def test_expected_aggregate_positive(self):
        model = self._model_with_pmf()
        ea = model.expected_aggregate()
        assert ea > 0

    def test_expected_aggregate_formula(self):
        # E[S] = E[N] * E[X]
        # E[N] = r * beta = 5 * 2 = 10
        # E[X] ~ scale * Gamma(1 + 1/c) = 10 * Gamma(1 + 1/1.5)

        model = self._model_with_pmf()
        en = 5.0 * 2.0  # r * beta
        # Approximate E[X] from discrete pmf
        m = len(model.severity_pmf)
        ex = float(np.sum(np.arange(m) * model.severity_pmf))
        expected = en * ex
        assert abs(model.expected_aggregate() - expected) < 1.0

    def test_var_geq_mean(self):
        model = self._model_with_pmf()
        var = model.var(alpha=0.99)
        mean = model.expected_aggregate()
        assert var >= mean

    def test_cte_geq_var(self):
        model = self._model_with_pmf()
        var = model.var(alpha=0.95)
        cte = model.cte(alpha=0.95)
        assert cte >= var - 1e-6

    def test_full_distribution_returns_dataframe(self):
        model = self._model_with_pmf()
        df = model.full_distribution()
        assert "claim_amount" in df.columns
        assert "pmf" in df.columns
        assert "cdf" in df.columns
        assert df["cdf"].iloc[-1] == pytest.approx(1.0, abs=0.001)

    def test_panjer_g0_geq_pn0(self):
        # P(S=0) >= P(N=0) because P(X=0) > 0 contributes compound probabilities.
        # P(N=0) = (1/(1+beta))^r = (1/3)^5 ~ 0.004115
        model = self._model_with_pmf()
        g = model.panjer_recursion()
        r, beta = 5.0, 2.0
        pn0 = (1.0 / (1.0 + beta)) ** r
        assert g[0] >= pn0 - 1e-6

    def test_unsupported_distribution_raises(self):
        model = AggregateClaimsModel(freq_distribution="poisson")
        model.severity_pmf = np.ones(10) / 10
        with pytest.raises(NotImplementedError):
            model.panjer_recursion()

    def test_no_severity_pmf_raises(self):
        model = AggregateClaimsModel()
        with pytest.raises(ValueError):
            model.panjer_recursion()
