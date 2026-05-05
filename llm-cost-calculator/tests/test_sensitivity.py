"""Tests for the Monte Carlo sensitivity analysis module."""

from __future__ import annotations

import pytest

from src.pricing import PricingDatabase
from src.sensitivity import run_sensitivity


@pytest.fixture()
def db() -> PricingDatabase:
    """Shared pricing database fixture."""
    return PricingDatabase()


class TestSensitivity:
    """Tests for Monte Carlo sensitivity analysis."""

    def test_percentile_ordering(self, db: PricingDatabase) -> None:
        """P10 <= P50 <= P90 must hold."""
        result = run_sensitivity(
            model_id="mistral-large-latest",
            avg_input_tokens=500,
            avg_output_tokens=200,
            requests_per_day=1000,
            seed=42,
            db=db,
        )
        assert result.p10_cost <= result.p50_cost <= result.p90_cost

    def test_deterministic_with_seed(self, db: PricingDatabase) -> None:
        """Same seed should produce identical results."""
        kwargs = dict(
            model_id="gpt-4o",
            avg_input_tokens=500,
            avg_output_tokens=200,
            requests_per_day=1000,
            seed=123,
            db=db,
        )
        r1 = run_sensitivity(**kwargs)
        r2 = run_sensitivity(**kwargs)
        assert r1.p50_cost == r2.p50_cost
        assert r1.p90_cost == r2.p90_cost

    def test_simulation_count(self, db: PricingDatabase) -> None:
        """Result should report the requested number of simulations."""
        result = run_sensitivity(
            model_id="mistral-small-latest",
            avg_input_tokens=200,
            avg_output_tokens=100,
            requests_per_day=500,
            n_simulations=500,
            seed=1,
            db=db,
        )
        assert result.n_simulations == 500

    def test_p50_near_deterministic_estimate(self, db: PricingDatabase) -> None:
        """Median should be close to the deterministic estimate."""
        from src.calculator import estimate_monthly_cost

        det = estimate_monthly_cost(
            model_id="mistral-large-latest",
            avg_input_tokens=500,
            avg_output_tokens=200,
            requests_per_day=1000,
            db=db,
        )
        mc = run_sensitivity(
            model_id="mistral-large-latest",
            avg_input_tokens=500,
            avg_output_tokens=200,
            requests_per_day=1000,
            n_simulations=10_000,
            seed=42,
            db=db,
        )
        # Median should be within 15% of deterministic for uniform distributions
        assert mc.p50_cost == pytest.approx(det.monthly_cost_usd, rel=0.15)

    def test_wider_variation_increases_spread(self, db: PricingDatabase) -> None:
        """Larger variation parameters should widen P10-P90 range."""
        narrow = run_sensitivity(
            model_id="gpt-4o",
            avg_input_tokens=500,
            avg_output_tokens=200,
            requests_per_day=1000,
            volume_variation=0.10,
            token_variation=0.10,
            price_variation=0.05,
            n_simulations=5000,
            seed=42,
            db=db,
        )
        wide = run_sensitivity(
            model_id="gpt-4o",
            avg_input_tokens=500,
            avg_output_tokens=200,
            requests_per_day=1000,
            volume_variation=0.50,
            token_variation=0.30,
            price_variation=0.20,
            n_simulations=5000,
            seed=42,
            db=db,
        )
        narrow_range = narrow.p90_cost - narrow.p10_cost
        wide_range = wide.p90_cost - wide.p10_cost
        assert wide_range > narrow_range

    def test_self_hosted_model(self, db: PricingDatabase) -> None:
        """Sensitivity analysis should work for self-hosted models."""
        result = run_sensitivity(
            model_id="llama-3.1-70b-a100",
            avg_input_tokens=500,
            avg_output_tokens=200,
            requests_per_day=1000,
            seed=42,
            db=db,
        )
        assert result.p50_cost > 0
        assert result.p10_cost <= result.p50_cost <= result.p90_cost
