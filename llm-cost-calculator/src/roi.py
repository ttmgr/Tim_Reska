"""ROI calculator comparing manual process costs to LLM-augmented workflows."""

from __future__ import annotations

import argparse
import logging
import math
from dataclasses import dataclass
from typing import Optional

from src.calculator import estimate_monthly_cost
from src.pricing import PricingDatabase

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ROIResult:
    """Return on investment analysis for LLM deployment vs manual process."""

    model_id: str
    tasks_per_month: int
    current_manual_cost_monthly: float
    llm_cost_monthly: float
    human_review_cost_monthly: float
    total_augmented_cost_monthly: float
    monthly_savings: float
    annual_savings: float
    annual_roi_percent: float
    breakeven_tasks_per_month: int
    payback_period_months: float


def calculate_roi(
    model_id: str,
    avg_input_tokens: int,
    avg_output_tokens: int,
    current_manual_cost_per_task: float,
    tasks_per_month: int,
    human_review_fraction: float = 0.1,
    human_review_cost: float = 5.0,
    days_per_month: int = 30,
    db: Optional[PricingDatabase] = None,
) -> ROIResult:
    """Compare manual cost to LLM-augmented cost and compute ROI metrics."""
    if not 0.0 <= human_review_fraction <= 1.0:
        raise ValueError(f"human_review_fraction must be in [0, 1], got {human_review_fraction}")

    if db is None:
        db = PricingDatabase()

    # Derive requests_per_day from tasks_per_month
    requests_per_day = max(1, tasks_per_month // days_per_month)

    est = estimate_monthly_cost(
        model_id=model_id,
        avg_input_tokens=avg_input_tokens,
        avg_output_tokens=avg_output_tokens,
        requests_per_day=requests_per_day,
        days_per_month=days_per_month,
        db=db,
    )

    current_manual_cost_monthly = current_manual_cost_per_task * tasks_per_month
    llm_cost_monthly = est.monthly_cost_usd
    reviewed_tasks = tasks_per_month * human_review_fraction
    human_review_cost_monthly = reviewed_tasks * human_review_cost
    total_augmented = llm_cost_monthly + human_review_cost_monthly

    monthly_savings = current_manual_cost_monthly - total_augmented
    annual_savings = monthly_savings * 12

    if total_augmented > 0:
        annual_roi_percent = (annual_savings / (total_augmented * 12)) * 100
    else:
        annual_roi_percent = float("inf") if annual_savings > 0 else 0.0

    # Breakeven: find task volume where manual cost = augmented cost
    # manual_cost_per_task * N = llm_cost_per_task * N + review_frac * review_cost * N
    # Solve for N where total_augmented scales linearly:
    cost_per_task_augmented = total_augmented / tasks_per_month if tasks_per_month > 0 else 0.0
    if current_manual_cost_per_task > cost_per_task_augmented and cost_per_task_augmented > 0:
        # Already profitable at any volume; breakeven is effectively 0
        # But we report the minimum volume that covers fixed-ish LLM costs
        breakeven_tasks = 0
    elif cost_per_task_augmented >= current_manual_cost_per_task:
        # LLM is more expensive per task; breakeven is never reached
        breakeven_tasks = -1  # sentinel for "never"
    else:
        breakeven_tasks = 0

    # More useful breakeven: at what volume does the LLM option pay for itself
    # relative to zero automation (assuming the LLM has some base cost)?
    # Since API pricing is purely variable, breakeven_tasks = 0 when per-task
    # LLM cost < manual cost. We report this directly.
    if cost_per_task_augmented > 0 and cost_per_task_augmented < current_manual_cost_per_task:
        breakeven_tasks = 0
    elif cost_per_task_augmented >= current_manual_cost_per_task:
        breakeven_tasks = -1

    # Payback period: months until cumulative savings cover initial month investment
    if monthly_savings > 0:
        payback_months = total_augmented / monthly_savings
    else:
        payback_months = float("inf")

    return ROIResult(
        model_id=model_id,
        tasks_per_month=tasks_per_month,
        current_manual_cost_monthly=current_manual_cost_monthly,
        llm_cost_monthly=llm_cost_monthly,
        human_review_cost_monthly=human_review_cost_monthly,
        total_augmented_cost_monthly=total_augmented,
        monthly_savings=monthly_savings,
        annual_savings=annual_savings,
        annual_roi_percent=annual_roi_percent,
        breakeven_tasks_per_month=breakeven_tasks,
        payback_period_months=payback_months,
    )


def _format_result(result: ROIResult) -> str:
    """Format ROI analysis for terminal output."""
    breakeven_str = (
        "N/A (LLM more expensive per task)"
        if result.breakeven_tasks_per_month < 0
        else f"{result.breakeven_tasks_per_month:,} tasks/month"
    )
    payback_str = (
        "Never (negative savings)"
        if math.isinf(result.payback_period_months)
        else f"{result.payback_period_months:.1f} months"
    )

    lines = [
        f"ROI Analysis: {result.model_id}",
        f"Tasks per month: {result.tasks_per_month:,}",
        "",
        "Current state:",
        f"  Manual cost/month:    ${result.current_manual_cost_monthly:>12,.2f}",
        "",
        "LLM-augmented state:",
        f"  LLM API cost/month:   ${result.llm_cost_monthly:>12,.2f}",
        f"  Human review/month:   ${result.human_review_cost_monthly:>12,.2f}",
        f"  Total augmented/month:${result.total_augmented_cost_monthly:>12,.2f}",
        "",
        "Impact:",
        f"  Monthly savings:      ${result.monthly_savings:>12,.2f}",
        f"  Annual savings:       ${result.annual_savings:>12,.2f}",
        f"  Annual ROI:           {result.annual_roi_percent:>11.1f}%",
        f"  Breakeven volume:     {breakeven_str}",
        f"  Payback period:       {payback_str}",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    """CLI entry point for ROI calculation."""
    parser = argparse.ArgumentParser(
        description="ROI calculator: manual cost vs LLM-augmented workflow.",
    )
    parser.add_argument("--model", type=str, required=True, help="Model identifier.")
    parser.add_argument("--input-tokens", type=int, required=True, help="Average input tokens per request.")
    parser.add_argument("--output-tokens", type=int, required=True, help="Average output tokens per request.")
    parser.add_argument("--requests-per-day", type=int, default=None, help="Requests per day (overrides tasks-per-month / 30).")
    parser.add_argument("--manual-cost", type=float, required=True, help="Current manual cost per task (USD).")
    parser.add_argument("--tasks-per-month", type=int, required=True, help="Number of tasks per month.")
    parser.add_argument("--review-fraction", type=float, default=0.1, help="Fraction of outputs needing human review (0-1).")
    parser.add_argument("--review-cost", type=float, default=5.0, help="Cost per human-reviewed item (USD).")

    args = parser.parse_args(argv)

    result = calculate_roi(
        model_id=args.model,
        avg_input_tokens=args.input_tokens,
        avg_output_tokens=args.output_tokens,
        current_manual_cost_per_task=args.manual_cost,
        tasks_per_month=args.tasks_per_month,
        human_review_fraction=args.review_fraction,
        human_review_cost=args.review_cost,
    )
    print(_format_result(result))


if __name__ == "__main__":
    main()
