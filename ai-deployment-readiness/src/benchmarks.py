"""Synthetic sector benchmarks derived from public AI maturity surveys.

Sources (all publicly available):
  - McKinsey & Company, "The State of AI in 2023", global survey (n=1,684).
    Financial services and technology lead in AI adoption; manufacturing
    and public sector trail.  https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai-in-2023-generative-ais-breakout-year
  - Stanford HAI, "AI Index Report 2024", Chapter 6 (Economy & Education).
    Reports sector-level AI investment and talent distribution.
    https://aiindex.stanford.edu/report/
  - Gartner, "AI Maturity Model" (2023 update). Places most enterprises
    at Level 2-3 of a 5-level maturity scale, with sector variance.
    https://www.gartner.com/en/articles/the-4-trends-that-prevail-on-the-gartner-hype-cycle-for-ai-2023

Benchmark values are synthetic approximations that reflect the relative
ordering and rough magnitude reported in these sources. They are NOT raw
data from any proprietary survey.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

DIMENSION_NAMES: Final[list[str]] = [
    "Data Infrastructure & Quality",
    "Process Maturity & Documentation",
    "Governance & Compliance Readiness",
    "AI Talent & Skills",
    "Executive Sponsorship & Change Management",
]

SECTOR_NAMES: Final[list[str]] = [
    "Financial Services",
    "Healthcare",
    "Manufacturing",
    "Public Sector",
    "Technology",
]


@dataclass(frozen=True, slots=True)
class SectorBenchmark:
    """Benchmark scores for a single industry sector."""

    sector: str
    scores: dict[str, float]  # dimension name -> typical score (1.0-5.0)
    overall: float


# Synthetic benchmarks.  See module docstring for source rationale.
_BENCHMARKS: Final[dict[str, SectorBenchmark]] = {
    "Financial Services": SectorBenchmark(
        sector="Financial Services",
        scores={
            "Data Infrastructure & Quality": 3.6,
            "Process Maturity & Documentation": 3.4,
            "Governance & Compliance Readiness": 3.8,
            "AI Talent & Skills": 3.2,
            "Executive Sponsorship & Change Management": 3.5,
        },
        overall=3.5,
    ),
    "Healthcare": SectorBenchmark(
        sector="Healthcare",
        scores={
            "Data Infrastructure & Quality": 2.8,
            "Process Maturity & Documentation": 2.6,
            "Governance & Compliance Readiness": 3.2,
            "AI Talent & Skills": 2.4,
            "Executive Sponsorship & Change Management": 2.5,
        },
        overall=2.7,
    ),
    "Manufacturing": SectorBenchmark(
        sector="Manufacturing",
        scores={
            "Data Infrastructure & Quality": 2.5,
            "Process Maturity & Documentation": 3.0,
            "Governance & Compliance Readiness": 2.3,
            "AI Talent & Skills": 2.1,
            "Executive Sponsorship & Change Management": 2.6,
        },
        overall=2.5,
    ),
    "Public Sector": SectorBenchmark(
        sector="Public Sector",
        scores={
            "Data Infrastructure & Quality": 2.2,
            "Process Maturity & Documentation": 2.8,
            "Governance & Compliance Readiness": 2.9,
            "AI Talent & Skills": 1.9,
            "Executive Sponsorship & Change Management": 2.3,
        },
        overall=2.4,
    ),
    "Technology": SectorBenchmark(
        sector="Technology",
        scores={
            "Data Infrastructure & Quality": 3.9,
            "Process Maturity & Documentation": 3.2,
            "Governance & Compliance Readiness": 3.0,
            "AI Talent & Skills": 4.0,
            "Executive Sponsorship & Change Management": 3.6,
        },
        overall=3.5,
    ),
}


def get_benchmark(sector: str) -> SectorBenchmark | None:
    """Look up synthetic benchmark for a sector (case-insensitive)."""
    for key, bm in _BENCHMARKS.items():
        if key.lower() == sector.lower():
            return bm
    return None


def list_sectors() -> list[str]:
    """Return all available sector names."""
    return list(_BENCHMARKS.keys())
