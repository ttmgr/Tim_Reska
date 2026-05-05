"""Interactive CLI questionnaire for AI deployment readiness assessment."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Final

from src.scorer import DimensionScore, compute_dimension_scores, determine_tier
from src.report import generate_report
from src.benchmarks import get_benchmark, SECTOR_NAMES

# ---------------------------------------------------------------------------
# Question definitions
# ---------------------------------------------------------------------------

DIMENSIONS: Final[list[str]] = [
    "Data Infrastructure & Quality",
    "Process Maturity & Documentation",
    "Governance & Compliance Readiness",
    "AI Talent & Skills",
    "Executive Sponsorship & Change Management",
]


@dataclass(frozen=True, slots=True)
class Question:
    """A single Likert-scale assessment question."""

    dimension: str
    text: str
    anchors: tuple[str, str]  # (low-anchor, high-anchor)


# Each question is concrete and actionable, grounded in publicly available
# maturity-model literature:
#   - Gartner AI Maturity Model (2023)
#   - Stanford HAI AI Index Report (2024)
#   - McKinsey "The State of AI" global survey (2023)
QUESTIONS: Final[list[Question]] = [
    # ── Dimension 1: Data Infrastructure & Quality ────────────────────────
    Question(
        dimension=DIMENSIONS[0],
        text=(
            "Do you maintain a documented data dictionary covering >80%% of "
            "your production datasets?"
        ),
        anchors=("No dictionary exists", "Comprehensive, auto-updated dictionary"),
    ),
    Question(
        dimension=DIMENSIONS[0],
        text=(
            "Are your core analytical datasets available through a central "
            "data platform (warehouse, lake, or lakehouse) with governed access?"
        ),
        anchors=("Siloed spreadsheets/local DBs", "Unified platform with RBAC"),
    ),
    Question(
        dimension=DIMENSIONS[0],
        text=(
            "Do you run automated data-quality checks (completeness, freshness, "
            "schema drift) on ingestion pipelines?"
        ),
        anchors=("No automated checks", "Full pipeline observability"),
    ),
    Question(
        dimension=DIMENSIONS[0],
        text=(
            "Can analysts self-serve access to cleaned, documented datasets "
            "without filing IT tickets?"
        ),
        anchors=("All access requires IT", "Fully self-service with audit trail"),
    ),
    Question(
        dimension=DIMENSIONS[0],
        text=(
            "Do you have version control or lineage tracking for datasets used "
            "in analytical or ML workflows?"
        ),
        anchors=("No versioning", "Full lineage from source to model"),
    ),
    # ── Dimension 2: Process Maturity & Documentation ─────────────────────
    Question(
        dimension=DIMENSIONS[1],
        text=(
            "Are your core business processes (top 10 by headcount) documented "
            "in a format accessible to non-experts?"
        ),
        anchors=("Tribal knowledge only", "Documented with process maps"),
    ),
    Question(
        dimension=DIMENSIONS[1],
        text=(
            "Do you measure cycle time and error rates for the processes most "
            "likely to be augmented by AI?"
        ),
        anchors=("No process metrics", "KPIs tracked and reviewed monthly"),
    ),
    Question(
        dimension=DIMENSIONS[1],
        text=(
            "Is there a structured intake process for evaluating new technology "
            "or automation proposals?"
        ),
        anchors=("Ad-hoc requests", "Stage-gated evaluation with criteria"),
    ),
    Question(
        dimension=DIMENSIONS[1],
        text=(
            "Do process owners have the authority and budget to implement "
            "approved changes within their domain?"
        ),
        anchors=("All changes require C-suite", "Delegated authority with guardrails"),
    ),
    Question(
        dimension=DIMENSIONS[1],
        text=(
            "Have you identified which tasks within key processes are "
            "repetitive, rule-based, and high-volume (automation candidates)?"
        ),
        anchors=("No task-level analysis", "Task taxonomy with volume estimates"),
    ),
    # ── Dimension 3: Governance & Compliance Readiness ────────────────────
    Question(
        dimension=DIMENSIONS[2],
        text=(
            "Does your organization have a written AI-use policy that covers "
            "acceptable use, prohibited use, and escalation paths?"
        ),
        anchors=("No AI policy", "Board-approved policy, reviewed annually"),
    ),
    Question(
        dimension=DIMENSIONS[2],
        text=(
            "Is there a defined process for reviewing AI outputs for bias, "
            "fairness, and accuracy before deployment?"
        ),
        anchors=("No review process", "Formal pre-deployment audit checklist"),
    ),
    Question(
        dimension=DIMENSIONS[2],
        text=(
            "Do you track which AI models are in production, who owns them, "
            "and when they were last validated?"
        ),
        anchors=("No model inventory", "Live registry with ownership and refresh dates"),
    ),
    Question(
        dimension=DIMENSIONS[2],
        text=(
            "Have you assessed regulatory requirements (e.g., EU AI Act risk "
            "tiers, GDPR Art. 22) that apply to your planned AI use cases?"
        ),
        anchors=("No regulatory mapping", "Use-case-level risk classification done"),
    ),
    Question(
        dimension=DIMENSIONS[2],
        text=(
            "Is there a clear incident-response procedure if an AI system "
            "produces harmful or incorrect outputs in production?"
        ),
        anchors=("No procedure", "Documented runbook with escalation and rollback"),
    ),
    # ── Dimension 4: AI Talent & Skills ───────────────────────────────────
    Question(
        dimension=DIMENSIONS[3],
        text=(
            "Do you have at least one team member with hands-on experience "
            "deploying ML/AI models to production (not just prototyping)?"
        ),
        anchors=("No in-house ML experience", "Dedicated MLOps/ML engineering team"),
    ),
    Question(
        dimension=DIMENSIONS[3],
        text=(
            "Have non-technical staff (e.g., operations, finance, HR) received "
            "structured training on what AI can and cannot do?"
        ),
        anchors=("No AI literacy training", "Role-specific AI fluency programme"),
    ),
    Question(
        dimension=DIMENSIONS[3],
        text=(
            "Can your IT/engineering team integrate third-party APIs and "
            "manage model serving infrastructure (containers, endpoints)?"
        ),
        anchors=("No API/infra skills", "Production-grade serving experience"),
    ),
    Question(
        dimension=DIMENSIONS[3],
        text=(
            "Do you have access to domain experts who can define success "
            "criteria and validate AI outputs in their area?"
        ),
        anchors=("No domain-expert involvement", "Embedded domain experts in AI projects"),
    ),
    Question(
        dimension=DIMENSIONS[3],
        text=(
            "Is there a retention or upskilling plan for employees whose roles "
            "will be significantly changed by AI adoption?"
        ),
        anchors=("No plan", "Formal reskilling roadmap with timelines"),
    ),
    # ── Dimension 5: Executive Sponsorship & Change Management ────────────
    Question(
        dimension=DIMENSIONS[4],
        text=(
            "Is there a named executive sponsor (C-level or VP) accountable "
            "for AI strategy and its business outcomes?"
        ),
        anchors=("No sponsor", "Named sponsor with OKRs tied to AI outcomes"),
    ),
    Question(
        dimension=DIMENSIONS[4],
        text=(
            "Has the leadership team allocated a ring-fenced budget for AI "
            "experimentation and deployment (not just IT capex)?"
        ),
        anchors=("No dedicated budget", "Multi-year ring-fenced AI budget"),
    ),
    Question(
        dimension=DIMENSIONS[4],
        text=(
            "Do you have a communication plan that explains to employees why "
            "AI is being introduced and how it affects their work?"
        ),
        anchors=("No communication", "Structured change-comms with feedback loops"),
    ),
    Question(
        dimension=DIMENSIONS[4],
        text=(
            "Has the organization run at least one end-to-end AI pilot with "
            "measured business impact (not just a proof of concept)?"
        ),
        anchors=("No pilots", "Multiple pilots with documented ROI"),
    ),
    Question(
        dimension=DIMENSIONS[4],
        text=(
            "Are AI initiative results (successes and failures) shared "
            "transparently across the organization?"
        ),
        anchors=("Results stay in project team", "Regular cross-functional AI reviews"),
    ),
]


# ---------------------------------------------------------------------------
# Demo answers (a mid-maturity technology company)
# ---------------------------------------------------------------------------

DEMO_ANSWERS: Final[list[int]] = [
    # Data Infrastructure & Quality
    4, 3, 3, 4, 2,
    # Process Maturity & Documentation
    3, 2, 3, 3, 2,
    # Governance & Compliance Readiness
    2, 2, 1, 2, 1,
    # AI Talent & Skills
    4, 3, 4, 3, 2,
    # Executive Sponsorship & Change Management
    4, 3, 2, 3, 2,
]


# ---------------------------------------------------------------------------
# CLI interaction
# ---------------------------------------------------------------------------


def _prompt_answer(question: Question, index: int, total: int) -> int:
    """Prompt the user for a Likert-scale answer (1-5)."""
    print(f"\n{'─' * 60}")
    print(f"  [{index}/{total}]  {question.dimension}")
    print(f"  {question.text}")
    print(f"    1 = {question.anchors[0]}")
    print(f"    5 = {question.anchors[1]}")

    while True:
        raw = input("  Your answer (1-5): ").strip()
        if raw in {"1", "2", "3", "4", "5"}:
            return int(raw)
        print("  Please enter a number between 1 and 5.")


def _prompt_sector() -> str | None:
    """Prompt user to select a sector for benchmarking (optional)."""
    print(f"\n{'─' * 60}")
    print("  Optional: select a sector for benchmark comparison.")
    for i, name in enumerate(SECTOR_NAMES, 1):
        print(f"    {i} = {name}")
    print(f"    0 = Skip benchmarks")

    while True:
        raw = input("  Your choice (0-5): ").strip()
        if raw == "0":
            return None
        if raw in {"1", "2", "3", "4", "5"}:
            return SECTOR_NAMES[int(raw) - 1]
        print("  Please enter a number between 0 and 5.")


def run_interactive() -> None:
    """Run the full interactive questionnaire and print the report."""
    print("=" * 60)
    print("  AI Deployment Readiness Assessment")
    print("  -----------------------------------")
    print("  Answer each question on a scale of 1 (lowest) to 5 (highest).")
    print("  25 questions across 5 dimensions. Takes ~10 minutes.")
    print("=" * 60)

    answers: list[int] = []
    total = len(QUESTIONS)
    for i, q in enumerate(QUESTIONS, 1):
        answers.append(_prompt_answer(q, i, total))

    sector = _prompt_sector()
    _display_results(answers, sector)


def run_demo() -> None:
    """Run the questionnaire with pre-filled demo answers."""
    print("=" * 60)
    print("  AI Deployment Readiness Assessment — DEMO MODE")
    print("  Using example answers for a mid-maturity technology company.")
    print("=" * 60)

    _display_results(DEMO_ANSWERS, sector="Technology")


def _display_results(answers: list[int], sector: str | None) -> None:
    """Score the answers and print the markdown report."""
    dim_scores = compute_dimension_scores(answers, QUESTIONS, DIMENSIONS)
    overall = sum(s.score for s in dim_scores) / len(dim_scores)
    tier = determine_tier(overall)

    benchmark = get_benchmark(sector) if sector else None
    report = generate_report(dim_scores, overall, tier, benchmark, sector)
    print(report)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Parse CLI arguments and dispatch."""
    parser = argparse.ArgumentParser(
        description="AI Deployment Readiness Assessment CLI",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run with pre-filled example answers",
    )
    args = parser.parse_args()

    if args.demo:
        run_demo()
    else:
        run_interactive()


if __name__ == "__main__":
    main()
