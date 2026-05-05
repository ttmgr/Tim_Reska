"""Cost calculation engine for LLM deployments."""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from typing import Optional

from src.pricing import (
    APIModelPricing,
    PricingDatabase,
    SelfHostedModelPricing,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CostEstimate:
    """Monthly cost estimate for a single model deployment."""

    model_id: str
    display_name: str
    provider: str
    monthly_requests: int
    monthly_input_tokens: int
    monthly_output_tokens: int
    monthly_cost_usd: float
    cost_per_request_usd: float
    daily_cost_usd: float


def estimate_monthly_cost(
    model_id: str,
    avg_input_tokens: int,
    avg_output_tokens: int,
    requests_per_day: int,
    days_per_month: int = 30,
    db: Optional[PricingDatabase] = None,
) -> CostEstimate:
    """Compute the projected monthly cost for a given workload and model."""
    if db is None:
        db = PricingDatabase()

    pricing = db.get(model_id)
    monthly_requests = requests_per_day * days_per_month
    monthly_input_tokens = monthly_requests * avg_input_tokens
    monthly_output_tokens = monthly_requests * avg_output_tokens

    if isinstance(pricing, APIModelPricing):
        input_cost = (monthly_input_tokens / 1_000_000) * pricing.input_per_1m
        output_cost = (monthly_output_tokens / 1_000_000) * pricing.output_per_1m
        monthly_cost = input_cost + output_cost
    elif isinstance(pricing, SelfHostedModelPricing):
        total_tokens = monthly_input_tokens + monthly_output_tokens
        seconds_needed = total_tokens / pricing.tokens_per_second
        hours_needed = seconds_needed / 3600
        base_cost = hours_needed * pricing.gpu_cost_per_hour
        monthly_cost = base_cost * (1 + pricing.overhead_fraction)
    else:
        raise TypeError(f"Unsupported pricing type: {type(pricing)}")

    cost_per_request = monthly_cost / monthly_requests if monthly_requests > 0 else 0.0
    daily_cost = monthly_cost / days_per_month if days_per_month > 0 else 0.0

    return CostEstimate(
        model_id=model_id,
        display_name=pricing.display_name,
        provider=pricing.provider,
        monthly_requests=monthly_requests,
        monthly_input_tokens=monthly_input_tokens,
        monthly_output_tokens=monthly_output_tokens,
        monthly_cost_usd=monthly_cost,
        cost_per_request_usd=cost_per_request,
        daily_cost_usd=daily_cost,
    )


def compare_models(
    model_ids: list[str],
    avg_input_tokens: int,
    avg_output_tokens: int,
    requests_per_day: int,
    days_per_month: int = 30,
    db: Optional[PricingDatabase] = None,
) -> list[CostEstimate]:
    """Estimate costs for multiple models and return sorted by monthly cost."""
    if db is None:
        db = PricingDatabase()

    estimates = [
        estimate_monthly_cost(
            model_id=mid,
            avg_input_tokens=avg_input_tokens,
            avg_output_tokens=avg_output_tokens,
            requests_per_day=requests_per_day,
            days_per_month=days_per_month,
            db=db,
        )
        for mid in model_ids
    ]
    return sorted(estimates, key=lambda e: e.monthly_cost_usd)


def _format_single(est: CostEstimate) -> str:
    """Format a single cost estimate for terminal output."""
    lines = [
        f"Model:            {est.display_name} ({est.provider})",
        f"Monthly requests: {est.monthly_requests:,}",
        f"Input tokens/mo:  {est.monthly_input_tokens:,}",
        f"Output tokens/mo: {est.monthly_output_tokens:,}",
        f"Monthly cost:     ${est.monthly_cost_usd:,.2f}",
        f"Daily cost:       ${est.daily_cost_usd:,.2f}",
        f"Cost per request: ${est.cost_per_request_usd:.6f}",
    ]
    return "\n".join(lines)


def _format_comparison(estimates: list[CostEstimate]) -> str:
    """Format a comparison table for terminal output."""
    header = f"{'Model':<30} {'Provider':<15} {'Monthly Cost':>14} {'Per Request':>14}"
    sep = "-" * len(header)
    rows = [header, sep]
    for est in estimates:
        rows.append(
            f"{est.display_name:<30} {est.provider:<15} "
            f"${est.monthly_cost_usd:>12,.2f} ${est.cost_per_request_usd:>12.6f}"
        )
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> None:
    """CLI entry point for cost estimation."""
    parser = argparse.ArgumentParser(
        description="Estimate monthly LLM deployment costs.",
    )
    parser.add_argument("--model", type=str, help="Single model identifier.")
    parser.add_argument(
        "--compare",
        type=str,
        help="Comma-separated model identifiers for comparison.",
    )
    parser.add_argument("--input-tokens", type=int, required=True, help="Average input tokens per request.")
    parser.add_argument("--output-tokens", type=int, required=True, help="Average output tokens per request.")
    parser.add_argument("--requests-per-day", type=int, required=True, help="Requests per day.")
    parser.add_argument("--days-per-month", type=int, default=30, help="Days per month (default: 30).")
    parser.add_argument("--list-models", action="store_true", help="List available models and exit.")

    args = parser.parse_args(argv)
    db = PricingDatabase()

    if args.list_models:
        print("Available models:")
        for mid in db.list_models():
            print(f"  {mid}")
        return

    if args.compare:
        model_ids = [m.strip() for m in args.compare.split(",")]
        estimates = compare_models(
            model_ids=model_ids,
            avg_input_tokens=args.input_tokens,
            avg_output_tokens=args.output_tokens,
            requests_per_day=args.requests_per_day,
            days_per_month=args.days_per_month,
            db=db,
        )
        print(_format_comparison(estimates))
    elif args.model:
        est = estimate_monthly_cost(
            model_id=args.model,
            avg_input_tokens=args.input_tokens,
            avg_output_tokens=args.output_tokens,
            requests_per_day=args.requests_per_day,
            days_per_month=args.days_per_month,
            db=db,
        )
        print(_format_single(est))
    else:
        parser.error("Provide --model or --compare.")


if __name__ == "__main__":
    main()
