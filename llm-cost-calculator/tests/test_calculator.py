"""Tests for the cost calculator module."""

from __future__ import annotations

import pytest

from src.calculator import compare_models, estimate_monthly_cost
from src.pricing import PricingDatabase


@pytest.fixture()
def db() -> PricingDatabase:
    """Shared pricing database fixture."""
    return PricingDatabase()


class TestEstimateMonthlyCost:
    """Tests for single-model cost estimation."""

    def test_api_model_basic(self, db: PricingDatabase) -> None:
        """Mistral Large with known inputs should produce correct cost."""
        est = estimate_monthly_cost(
            model_id="mistral-large-latest",
            avg_input_tokens=500,
            avg_output_tokens=200,
            requests_per_day=1000,
            days_per_month=30,
            db=db,
        )
        # 30,000 requests * 500 input = 15M input tokens
        # 15M / 1M * $2.0 = $30.00 input cost
        # 30,000 requests * 200 output = 6M output tokens
        # 6M / 1M * $6.0 = $36.00 output cost
        # Total = $66.00
        assert est.monthly_cost_usd == pytest.approx(66.0, abs=0.01)
        assert est.monthly_requests == 30_000
        assert est.monthly_input_tokens == 15_000_000
        assert est.monthly_output_tokens == 6_000_000

    def test_api_model_cost_per_request(self, db: PricingDatabase) -> None:
        """Cost per request should equal monthly / requests."""
        est = estimate_monthly_cost(
            model_id="gpt-4o",
            avg_input_tokens=1000,
            avg_output_tokens=500,
            requests_per_day=100,
            db=db,
        )
        expected_per_request = est.monthly_cost_usd / est.monthly_requests
        assert est.cost_per_request_usd == pytest.approx(expected_per_request, rel=1e-6)

    def test_self_hosted_model(self, db: PricingDatabase) -> None:
        """Self-hosted Llama should factor in GPU hours and overhead."""
        est = estimate_monthly_cost(
            model_id="llama-3.1-70b-a100",
            avg_input_tokens=500,
            avg_output_tokens=200,
            requests_per_day=1000,
            days_per_month=30,
            db=db,
        )
        # 30,000 requests * (500 + 200) = 21M tokens
        # 21M / 500 tps = 42,000 seconds = 11.667 hours
        # 11.667 * $2/hr = $23.333
        # With 20% overhead: $23.333 * 1.2 = $28.00
        assert est.monthly_cost_usd == pytest.approx(28.0, abs=0.01)

    def test_unknown_model_raises(self, db: PricingDatabase) -> None:
        """Requesting a nonexistent model should raise KeyError."""
        with pytest.raises(KeyError, match="nonexistent-model"):
            estimate_monthly_cost(
                model_id="nonexistent-model",
                avg_input_tokens=100,
                avg_output_tokens=50,
                requests_per_day=10,
                db=db,
            )

    def test_daily_cost(self, db: PricingDatabase) -> None:
        """Daily cost should be monthly cost divided by days."""
        est = estimate_monthly_cost(
            model_id="mistral-small-latest",
            avg_input_tokens=200,
            avg_output_tokens=100,
            requests_per_day=500,
            days_per_month=30,
            db=db,
        )
        assert est.daily_cost_usd == pytest.approx(est.monthly_cost_usd / 30, rel=1e-6)

    def test_zero_requests(self, db: PricingDatabase) -> None:
        """Zero requests should produce zero cost."""
        est = estimate_monthly_cost(
            model_id="gpt-4o-mini",
            avg_input_tokens=100,
            avg_output_tokens=50,
            requests_per_day=0,
            db=db,
        )
        assert est.monthly_cost_usd == 0.0
        assert est.cost_per_request_usd == 0.0


class TestCompareModels:
    """Tests for multi-model comparison."""

    def test_sorted_by_cost(self, db: PricingDatabase) -> None:
        """Results should be sorted ascending by monthly cost."""
        estimates = compare_models(
            model_ids=["mistral-large-latest", "gpt-4o", "gpt-4o-mini"],
            avg_input_tokens=500,
            avg_output_tokens=200,
            requests_per_day=1000,
            db=db,
        )
        costs = [e.monthly_cost_usd for e in estimates]
        assert costs == sorted(costs)

    def test_comparison_returns_all_models(self, db: PricingDatabase) -> None:
        """Comparison should return one estimate per model."""
        model_ids = ["mistral-small-latest", "mistral-large-latest", "codestral"]
        estimates = compare_models(
            model_ids=model_ids,
            avg_input_tokens=300,
            avg_output_tokens=150,
            requests_per_day=500,
            db=db,
        )
        assert len(estimates) == len(model_ids)
        returned_ids = {e.model_id for e in estimates}
        assert returned_ids == set(model_ids)

    def test_cheaper_model_ranks_first(self, db: PricingDatabase) -> None:
        """GPT-4o Mini should be cheaper than GPT-4o for same workload."""
        estimates = compare_models(
            model_ids=["gpt-4o", "gpt-4o-mini"],
            avg_input_tokens=500,
            avg_output_tokens=200,
            requests_per_day=1000,
            db=db,
        )
        assert estimates[0].model_id == "gpt-4o-mini"
