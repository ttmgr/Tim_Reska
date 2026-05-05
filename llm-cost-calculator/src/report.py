"""Generate text and Markdown reports from cost analysis results."""

from __future__ import annotations

import logging
from typing import Optional

from src.calculator import CostEstimate
from src.roi import ROIResult
from src.sensitivity import SensitivityResult

logger = logging.getLogger(__name__)


def cost_report_markdown(
    estimates: list[CostEstimate],
    sensitivity: Optional[SensitivityResult] = None,
    roi: Optional[ROIResult] = None,
) -> str:
    """Generate a Markdown report combining cost estimates, sensitivity, and ROI."""
    sections: list[str] = []

    # Header
    sections.append("# LLM Cost Analysis Report\n")

    # Cost comparison table
    if estimates:
        sections.append("## Cost Estimates\n")
        sections.append(
            "| Model | Provider | Monthly Cost | Daily Cost | Cost/Request |"
        )
        sections.append(
            "|-------|----------|-------------:|-----------:|-------------:|"
        )
        for est in estimates:
            sections.append(
                f"| {est.display_name} | {est.provider} "
                f"| ${est.monthly_cost_usd:,.2f} "
                f"| ${est.daily_cost_usd:,.2f} "
                f"| ${est.cost_per_request_usd:.6f} |"
            )
        sections.append("")

        # Workload summary from first estimate
        first = estimates[0]
        sections.append("### Workload Parameters\n")
        sections.append(f"- Monthly requests: {first.monthly_requests:,}")
        sections.append(f"- Input tokens per request: {first.monthly_input_tokens // first.monthly_requests:,}")
        sections.append(f"- Output tokens per request: {first.monthly_output_tokens // first.monthly_requests:,}")
        sections.append("")

    # Sensitivity section
    if sensitivity is not None:
        sections.append("## Sensitivity Analysis\n")
        sections.append(f"Monte Carlo simulation with {sensitivity.n_simulations:,} runs.\n")
        sections.append("| Percentile | Monthly Cost |")
        sections.append("|------------|-------------:|")
        sections.append(f"| P10 (optimistic) | ${sensitivity.p10_cost:,.2f} |")
        sections.append(f"| P50 (median) | ${sensitivity.p50_cost:,.2f} |")
        sections.append(f"| P90 (pessimistic) | ${sensitivity.p90_cost:,.2f} |")
        sections.append("")
        sections.append(
            f"Mean: ${sensitivity.mean_cost:,.2f} "
            f"(std: ${sensitivity.std_cost:,.2f})"
        )
        sections.append("")

    # ROI section
    if roi is not None:
        sections.append("## ROI Analysis\n")
        sections.append("| Metric | Value |")
        sections.append("|--------|------:|")
        sections.append(f"| Manual cost/month | ${roi.current_manual_cost_monthly:,.2f} |")
        sections.append(f"| LLM cost/month | ${roi.llm_cost_monthly:,.2f} |")
        sections.append(f"| Human review/month | ${roi.human_review_cost_monthly:,.2f} |")
        sections.append(f"| Total augmented/month | ${roi.total_augmented_cost_monthly:,.2f} |")
        sections.append(f"| Monthly savings | ${roi.monthly_savings:,.2f} |")
        sections.append(f"| Annual savings | ${roi.annual_savings:,.2f} |")
        sections.append(f"| Annual ROI | {roi.annual_roi_percent:.1f}% |")
        payback = (
            "Never"
            if roi.payback_period_months == float("inf")
            else f"{roi.payback_period_months:.1f} months"
        )
        sections.append(f"| Payback period | {payback} |")
        sections.append("")

    return "\n".join(sections)


def cost_report_text(
    estimates: list[CostEstimate],
    sensitivity: Optional[SensitivityResult] = None,
    roi: Optional[ROIResult] = None,
) -> str:
    """Generate a plain-text report combining cost estimates, sensitivity, and ROI."""
    sections: list[str] = []

    sections.append("LLM COST ANALYSIS REPORT")
    sections.append("=" * 60)
    sections.append("")

    if estimates:
        sections.append("COST ESTIMATES")
        sections.append("-" * 60)
        header = f"{'Model':<30} {'Provider':<15} {'Monthly':>12}"
        sections.append(header)
        sections.append("-" * len(header))
        for est in estimates:
            sections.append(
                f"{est.display_name:<30} {est.provider:<15} "
                f"${est.monthly_cost_usd:>10,.2f}"
            )
        sections.append("")

    if sensitivity is not None:
        sections.append("SENSITIVITY ANALYSIS")
        sections.append("-" * 60)
        sections.append(f"Simulations: {sensitivity.n_simulations:,}")
        sections.append(f"  P10:  ${sensitivity.p10_cost:>12,.2f}")
        sections.append(f"  P50:  ${sensitivity.p50_cost:>12,.2f}")
        sections.append(f"  P90:  ${sensitivity.p90_cost:>12,.2f}")
        sections.append("")

    if roi is not None:
        sections.append("ROI ANALYSIS")
        sections.append("-" * 60)
        sections.append(f"Manual cost/month:     ${roi.current_manual_cost_monthly:>12,.2f}")
        sections.append(f"Augmented cost/month:  ${roi.total_augmented_cost_monthly:>12,.2f}")
        sections.append(f"Monthly savings:       ${roi.monthly_savings:>12,.2f}")
        sections.append(f"Annual ROI:            {roi.annual_roi_percent:>11.1f}%")
        sections.append("")

    return "\n".join(sections)
