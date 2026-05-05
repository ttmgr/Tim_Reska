"""Monte Carlo sensitivity analysis for LLM cost projections."""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

from src.pricing import (
    APIModelPricing,
    PricingDatabase,
    SelfHostedModelPricing,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SensitivityResult:
    """Distribution summary from a Monte Carlo cost simulation."""

    model_id: str
    display_name: str
    n_simulations: int
    p10_cost: float
    p50_cost: float
    p90_cost: float
    mean_cost: float
    std_cost: float
    min_cost: float
    max_cost: float


def run_sensitivity(
    model_id: str,
    avg_input_tokens: int,
    avg_output_tokens: int,
    requests_per_day: int,
    days_per_month: int = 30,
    n_simulations: int = 1000,
    volume_variation: float = 0.50,
    token_variation: float = 0.30,
    price_variation: float = 0.20,
    seed: Optional[int] = None,
    db: Optional[PricingDatabase] = None,
) -> SensitivityResult:
    """Run Monte Carlo simulation over request volume, token length, and pricing."""
    if db is None:
        db = PricingDatabase()

    pricing = db.get(model_id)
    rng = np.random.default_rng(seed)

    # Sample multipliers from uniform distributions centered on 1.0
    volume_mult = rng.uniform(1 - volume_variation, 1 + volume_variation, n_simulations)
    input_tok_mult = rng.uniform(1 - token_variation, 1 + token_variation, n_simulations)
    output_tok_mult = rng.uniform(1 - token_variation, 1 + token_variation, n_simulations)
    price_mult = rng.uniform(1 - price_variation, 1 + price_variation, n_simulations)

    sim_requests = requests_per_day * days_per_month * volume_mult
    sim_input_tokens = sim_requests * avg_input_tokens * input_tok_mult
    sim_output_tokens = sim_requests * avg_output_tokens * output_tok_mult

    if isinstance(pricing, APIModelPricing):
        input_cost = (sim_input_tokens / 1_000_000) * pricing.input_per_1m * price_mult
        output_cost = (sim_output_tokens / 1_000_000) * pricing.output_per_1m * price_mult
        costs = input_cost + output_cost
    elif isinstance(pricing, SelfHostedModelPricing):
        total_tokens = sim_input_tokens + sim_output_tokens
        seconds_needed = total_tokens / pricing.tokens_per_second
        hours_needed = seconds_needed / 3600
        base_cost = hours_needed * pricing.gpu_cost_per_hour * price_mult
        costs = base_cost * (1 + pricing.overhead_fraction)
    else:
        raise TypeError(f"Unsupported pricing type: {type(pricing)}")

    return SensitivityResult(
        model_id=model_id,
        display_name=pricing.display_name,
        n_simulations=n_simulations,
        p10_cost=float(np.percentile(costs, 10)),
        p50_cost=float(np.percentile(costs, 50)),
        p90_cost=float(np.percentile(costs, 90)),
        mean_cost=float(np.mean(costs)),
        std_cost=float(np.std(costs)),
        min_cost=float(np.min(costs)),
        max_cost=float(np.max(costs)),
    )


def _format_result(result: SensitivityResult) -> str:
    """Format sensitivity analysis for terminal output."""
    lines = [
        f"Sensitivity Analysis: {result.display_name}",
        f"Simulations: {result.n_simulations:,}",
        "",
        f"  P10 (optimistic):  ${result.p10_cost:>12,.2f}",
        f"  P50 (median):      ${result.p50_cost:>12,.2f}",
        f"  P90 (pessimistic): ${result.p90_cost:>12,.2f}",
        "",
        f"  Mean:              ${result.mean_cost:>12,.2f}",
        f"  Std dev:           ${result.std_cost:>12,.2f}",
        f"  Range:             ${result.min_cost:>12,.2f} — ${result.max_cost:>12,.2f}",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    """CLI entry point for sensitivity analysis."""
    parser = argparse.ArgumentParser(
        description="Monte Carlo sensitivity analysis for LLM costs.",
    )
    parser.add_argument("--model", type=str, required=True, help="Model identifier.")
    parser.add_argument("--input-tokens", type=int, required=True, help="Average input tokens per request.")
    parser.add_argument("--output-tokens", type=int, required=True, help="Average output tokens per request.")
    parser.add_argument("--requests-per-day", type=int, required=True, help="Requests per day.")
    parser.add_argument("--days-per-month", type=int, default=30, help="Days per month.")
    parser.add_argument("--simulations", type=int, default=1000, help="Number of Monte Carlo runs.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility.")

    args = parser.parse_args(argv)

    result = run_sensitivity(
        model_id=args.model,
        avg_input_tokens=args.input_tokens,
        avg_output_tokens=args.output_tokens,
        requests_per_day=args.requests_per_day,
        days_per_month=args.days_per_month,
        n_simulations=args.simulations,
        seed=args.seed,
    )
    print(_format_result(result))


if __name__ == "__main__":
    main()
