"""Scoring engine: weighted dimension scores, maturity tiers, recommendations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from src.questionnaire import Question

# ---------------------------------------------------------------------------
# Per-dimension question weights
# ---------------------------------------------------------------------------
# Within each dimension the five questions are not equally important.
# Weights are normalised per dimension so they sum to 1.0.
# Rationale draws on publicly available frameworks:
#   - Gartner AI Maturity Model emphasises governance and data foundations
#   - McKinsey "State of AI" (2023) highlights talent and executive buy-in
#     as top differentiators between AI leaders and laggards

DIMENSION_WEIGHTS: Final[dict[str, list[float]]] = {
    "Data Infrastructure & Quality": [0.25, 0.25, 0.20, 0.15, 0.15],
    "Process Maturity & Documentation": [0.25, 0.20, 0.20, 0.15, 0.20],
    "Governance & Compliance Readiness": [0.20, 0.25, 0.20, 0.20, 0.15],
    "AI Talent & Skills": [0.25, 0.20, 0.20, 0.20, 0.15],
    "Executive Sponsorship & Change Management": [0.25, 0.25, 0.15, 0.20, 0.15],
}


# ---------------------------------------------------------------------------
# Maturity tiers
# ---------------------------------------------------------------------------

TIER_THRESHOLDS: Final[list[tuple[float, float, str]]] = [
    (1.0, 2.0, "Exploring"),
    (2.0, 3.0, "Piloting"),
    (3.0, 4.0, "Scaling"),
    (4.0, 5.0, "Optimizing"),
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DimensionScore:
    """Aggregated score for one assessment dimension."""

    name: str
    score: float
    question_scores: list[int]


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------


def compute_dimension_scores(
    answers: list[int],
    questions: list[Question],
    dimensions: list[str],
) -> list[DimensionScore]:
    """Compute weighted score for each dimension."""
    if len(answers) != len(questions):
        raise ValueError(
            f"Expected {len(questions)} answers, got {len(answers)}"
        )

    dim_answers: dict[str, list[int]] = {d: [] for d in dimensions}
    for ans, q in zip(answers, questions):
        if ans < 1 or ans > 5:
            raise ValueError(f"Answer must be 1-5, got {ans}")
        dim_answers[q.dimension].append(ans)

    scores: list[DimensionScore] = []
    for dim in dimensions:
        raw = dim_answers[dim]
        weights = DIMENSION_WEIGHTS[dim]
        weighted = sum(a * w for a, w in zip(raw, weights))
        scores.append(DimensionScore(name=dim, score=round(weighted, 2), question_scores=raw))

    return scores


def determine_tier(overall_score: float) -> str:
    """Map an overall score (1.0-5.0) to a maturity tier label."""
    for low, high, label in TIER_THRESHOLDS:
        if low <= overall_score < high:
            return label
    # Score of exactly 5.0
    return "Optimizing"


def generate_recommendations(dim_scores: list[DimensionScore]) -> list[str]:
    """Return up to 3 prioritised recommendations for the lowest-scoring dimensions."""
    _recs: dict[str, list[str]] = {
        "Data Infrastructure & Quality": [
            "Establish a governed data catalogue covering your top-20 production "
            "datasets, with ownership, freshness SLAs, and automated quality checks.",
            "Invest in a self-service data platform so analysts can access clean "
            "datasets without IT bottlenecks.",
        ],
        "Process Maturity & Documentation": [
            "Document your 10 highest-headcount processes with swim-lane diagrams "
            "and baseline cycle-time and error-rate metrics before automating.",
            "Introduce a lightweight intake process (scoring rubric + business case "
            "template) for evaluating AI/automation proposals.",
        ],
        "Governance & Compliance Readiness": [
            "Draft and ratify an AI-use policy covering acceptable use, prohibited "
            "applications, and an escalation path for edge cases.",
            "Build a model registry that tracks every production model, its owner, "
            "validation date, and regulatory risk classification.",
        ],
        "AI Talent & Skills": [
            "Run a structured AI literacy programme for non-technical staff, "
            "focusing on realistic capabilities, limitations, and responsible use.",
            "Hire or upskill at least one ML engineer with production deployment "
            "experience (containers, endpoints, monitoring).",
        ],
        "Executive Sponsorship & Change Management": [
            "Appoint a named executive sponsor with board-level accountability "
            "and OKRs tied to measurable AI outcomes.",
            "Communicate AI strategy to all employees with a clear explanation "
            "of why, what changes, and what support is available.",
        ],
    }

    sorted_dims = sorted(dim_scores, key=lambda d: d.score)
    recommendations: list[str] = []
    for dim in sorted_dims:
        for rec in _recs.get(dim.name, []):
            if len(recommendations) >= 3:
                break
            recommendations.append(f"[{dim.name}] {rec}")
        if len(recommendations) >= 3:
            break

    return recommendations
