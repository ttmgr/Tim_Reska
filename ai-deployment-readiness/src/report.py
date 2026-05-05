"""Markdown report generator for AI deployment readiness results."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.scorer import generate_recommendations

if TYPE_CHECKING:
    from src.benchmarks import SectorBenchmark
    from src.scorer import DimensionScore


def _bar(score: float, width: int = 20) -> str:
    """Render a simple text progress bar."""
    filled = round(score / 5.0 * width)
    return f"[{'#' * filled}{'.' * (width - filled)}] {score:.2f}/5.00"


def generate_report(
    dim_scores: list[DimensionScore],
    overall: float,
    tier: str,
    benchmark: SectorBenchmark | None = None,
    sector: str | None = None,
) -> str:
    """Generate a markdown-formatted readiness report."""
    lines: list[str] = []

    lines.append("")
    lines.append("# AI Deployment Readiness Report")
    lines.append("")
    lines.append(f"**Overall Score: {overall:.2f} / 5.00**")
    lines.append(f"**Maturity Tier: {tier}**")
    lines.append("")

    # Dimension breakdown
    lines.append("## Dimension Scores")
    lines.append("")
    for ds in dim_scores:
        lines.append(f"  {ds.name:<45s} {_bar(ds.score)}")
    lines.append("")

    # Benchmark comparison (optional)
    if benchmark and sector:
        lines.append(f"## Benchmark Comparison ({sector})")
        lines.append("")
        lines.append(f"  {'Dimension':<45s} {'You':>8s}  {'Sector':>8s}  {'Delta':>8s}")
        lines.append(f"  {'─' * 45} {'─' * 8}  {'─' * 8}  {'─' * 8}")
        for ds in dim_scores:
            bm_score = benchmark.scores.get(ds.name, 0.0)
            delta = ds.score - bm_score
            sign = "+" if delta >= 0 else ""
            lines.append(
                f"  {ds.name:<45s} {ds.score:>8.2f}  {bm_score:>8.2f}  {sign}{delta:>7.2f}"
            )
        lines.append("")
        bm_delta = overall - benchmark.overall
        bm_sign = "+" if bm_delta >= 0 else ""
        lines.append(
            f"  Overall: {overall:.2f} vs sector average {benchmark.overall:.2f} "
            f"({bm_sign}{bm_delta:.2f})"
        )
        lines.append("")

    # Recommendations
    recs = generate_recommendations(dim_scores)
    if recs:
        lines.append("## Prioritised Recommendations")
        lines.append("")
        for i, rec in enumerate(recs, 1):
            lines.append(f"  {i}. {rec}")
        lines.append("")

    # Tier explanations
    lines.append("## Maturity Tier Definitions")
    lines.append("")
    lines.append("  1.0-2.0  Exploring   — AI interest exists but no structured capability.")
    lines.append("  2.0-3.0  Piloting    — Isolated experiments; not yet embedded in operations.")
    lines.append("  3.0-4.0  Scaling     — AI in production for select use cases; governance emerging.")
    lines.append("  4.0-5.0  Optimizing  — AI integrated across the organisation with mature governance.")
    lines.append("")

    # Attribution
    lines.append("---")
    lines.append(
        "Assessment framework based on publicly available maturity models: "
        "Gartner AI Maturity Model (2023), Stanford HAI AI Index Report (2024), "
        "McKinsey 'The State of AI' (2023)."
    )
    lines.append("")
    lines.append(
        "For comprehensive AI deployment due diligence with governance mapping "
        "and implementation roadmaps, engage a specialist firm."
    )
    lines.append("")

    return "\n".join(lines)
