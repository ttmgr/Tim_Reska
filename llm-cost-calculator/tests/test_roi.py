"""Tests for the ROI calculator module."""

from __future__ import annotations

import math

import pytest

from src.pricing import PricingDatabase
from src.roi import ROIResult, calculate_roi


@pytest.fixture()
def db() -> PricingDatabase:
    """Shared pricing database fixture."""
    return PricingDatabase()


class TestROI:
    """Tests for ROI calculation logic."""

    def test_positive_savings(self, db: PricingDatabase) -> None:
        """Expensive manual process with cheap LLM should yield positive savings."""
        result = calculate_roi(
            model_id="mistral-small-latest",
            avg_input_tokens=500,
            avg_output_tokens=200,
            current_manual_cost_per_task=5.0,
            tasks_per_month=30_000,
            human_review_fraction=0.1,
            human_review_cost=5.0,
            db=db,
        )
        assert result.monthly_savings > 0
        assert result.annual_savings > 0
        assert result.annual_roi_percent > 0

    def test_manual_cost_matches_input(self, db: PricingDatabase) -> None:
        """Manual cost should equal cost_per_task * tasks."""
        result = calculate_roi(
            model_id="gpt-4o",
            avg_input_tokens=500,
            avg_output_tokens=200,
            current_manual_cost_per_task=10.0,
            tasks_per_month=1000,
            db=db,
        )
        assert result.current_manual_cost_monthly == pytest.approx(10_000.0)

    def test_human_review_cost_included(self, db: PricingDatabase) -> None:
        """Total augmented cost should include both LLM and human review."""
        result = calculate_roi(
            model_id="mistral-large-latest",
            avg_input_tokens=500,
            avg_output_tokens=200,
            current_manual_cost_per_task=5.0,
            tasks_per_month=30_000,
            human_review_fraction=0.2,
            human_review_cost=10.0,
            db=db,
        )
        expected_review = 30_000 * 0.2 * 10.0
        assert result.human_review_cost_monthly == pytest.approx(expected_review)
        assert result.total_augmented_cost_monthly == pytest.approx(
            result.llm_cost_monthly + result.human_review_cost_monthly
        )

    def test_annual_is_12x_monthly(self, db: PricingDatabase) -> None:
        """Annual savings should be 12x monthly savings."""
        result = calculate_roi(
            model_id="codestral",
            avg_input_tokens=300,
            avg_output_tokens=150,
            current_manual_cost_per_task=3.0,
            tasks_per_month=10_000,
            db=db,
        )
        assert result.annual_savings == pytest.approx(result.monthly_savings * 12)

    def test_negative_savings_when_llm_expensive(self, db: PricingDatabase) -> None:
        """Very cheap manual process should make LLM uneconomical."""
        result = calculate_roi(
            model_id="o3",
            avg_input_tokens=2000,
            avg_output_tokens=1000,
            current_manual_cost_per_task=0.001,
            tasks_per_month=30_000,
            human_review_fraction=0.5,
            human_review_cost=10.0,
            db=db,
        )
        assert result.monthly_savings < 0

    def test_invalid_review_fraction_raises(self, db: PricingDatabase) -> None:
        """Review fraction outside [0, 1] should raise ValueError."""
        with pytest.raises(ValueError, match="human_review_fraction"):
            calculate_roi(
                model_id="gpt-4o-mini",
                avg_input_tokens=100,
                avg_output_tokens=50,
                current_manual_cost_per_task=1.0,
                tasks_per_month=1000,
                human_review_fraction=1.5,
                db=db,
            )

    def test_payback_period_finite_when_saving(self, db: PricingDatabase) -> None:
        """Positive savings should produce a finite payback period."""
        result = calculate_roi(
            model_id="mistral-small-latest",
            avg_input_tokens=200,
            avg_output_tokens=100,
            current_manual_cost_per_task=5.0,
            tasks_per_month=10_000,
            human_review_fraction=0.05,
            human_review_cost=3.0,
            db=db,
        )
        assert result.payback_period_months < float("inf")
        assert result.payback_period_months > 0

    def test_payback_infinite_when_losing(self, db: PricingDatabase) -> None:
        """Negative savings should produce infinite payback."""
        result = calculate_roi(
            model_id="o3",
            avg_input_tokens=5000,
            avg_output_tokens=2000,
            current_manual_cost_per_task=0.001,
            tasks_per_month=30_000,
            human_review_fraction=0.5,
            human_review_cost=10.0,
            db=db,
        )
        assert math.isinf(result.payback_period_months)
