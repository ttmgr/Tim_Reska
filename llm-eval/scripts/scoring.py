"""Shared scoring taxonomy and model registry for the LLM evaluation.

Single source of truth for the four things that were previously re-declared
(and drifting) across every ``generate_*.py`` / ``aggregate_scores.py`` script:

1. The **scoring taxonomy** — how a per-dimension letter grade maps to a number
   (``SCORE_MAP``), which dimensions exist (``DIMENSIONS``), and which letter
   means "fully correct" (``FULLY_CORRECT``).
2. The **canonical model registry** — family order, the chronological version
   order within each family, and human-readable family / model labels.
3. The **pipeline metadata** — expected step counts and display labels.
4. The genuinely-shared **pure helpers** — numeric mapping, model ordering,
   label lookup, slugification, and the "is this step fully correct?" predicate.

Deliberately *not* centralised, because they are real per-script choices, not
duplication:
- Each figure script keeps its own *compact* model-label map (axis labels need
  shorter strings than the markdown summary).
- The **composite policy** differs by design: the markdown/stats paths take a
  NaN-skipping mean over present dimensions, while the heatmap/radar paths treat
  a row as scorable only when *every* dimension is present. Unifying these would
  change edge-case behaviour on incomplete rows, so each loader keeps its own.

This module has no third-party dependencies, so the scoring logic is unit
testable without pandas, matplotlib, or any file I/O.
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Scoring taxonomy
# ---------------------------------------------------------------------------

# Per-dimension letter-grade -> numeric score. Dimensions have different valid
# letters and scales (output_compatibility is binary; the rest have a 0.5 mid).
SCORE_MAP: dict[str, dict[str, float]] = {
    "tool_selection": {"C": 1.0, "A": 0.5, "I": 0.0},
    "parameter_accuracy": {"C": 1.0, "P": 0.5, "I": 0.0},
    "output_compatibility": {"P": 1.0, "F": 0.0},
    "scientific_validity": {"S": 1.0, "Q": 0.5, "I": 0.0},
    "executability": {"R": 1.0, "M": 0.5, "N": 0.0},
}

DIMENSIONS: list[str] = list(SCORE_MAP.keys())

# The letter that counts as "fully correct" for each dimension.
FULLY_CORRECT: dict[str, str] = {
    "tool_selection": "C",
    "parameter_accuracy": "C",
    "output_compatibility": "P",
    "scientific_validity": "S",
    "executability": "R",
}

# ---------------------------------------------------------------------------
# Pipeline metadata
# ---------------------------------------------------------------------------

PIPELINE_STEP_COUNTS: dict[str, int] = {"aerobiome": 7, "wetland": 10}
PIPELINE_LABELS: dict[str, str] = {"aerobiome": "Aerobiome", "wetland": "Wetland"}

# ---------------------------------------------------------------------------
# Canonical model registry — family order, chronological versions, labels
# ---------------------------------------------------------------------------

FAMILY_ORDER: list[str] = ["openai", "claude", "gemini", "google", "deepseek", "zhipu"]

# Chronological version order within each family (canonical, full set).
MODEL_VERSION_ORDER: dict[str, list[str]] = {
    "openai": [
        "gpt4o",
        "o1_preview",
        "o1_mini",
        "o1",
        "o1_pro",
        "o3_mini",
        "o3_high",
        "o4_mini",
        "gpt5",
        "chatgpt_deep_research",
    ],
    "claude": [
        "sonnet_3.5",
        "sonnet_4",
        "sonnet_4.5",
        "haiku_4.5",
        "opus_4.5",
        "opus_4.6",
        "sonnet_4.6",
        "deep_research",
    ],
    "gemini": [
        "2.0_flash",
        "2.5_pro_preview",
        "2.5_flash",
        "2.5_pro_stable",
        "3_pro",
        "3_flash",
        "3.1_pro",
    ],
    "google": ["gemini_deep_research"],
    "deepseek": ["v3"],
    "zhipu": ["glm_5"],
}

FAMILY_LABELS: dict[str, str] = {
    "openai": "OpenAI",
    "claude": "Claude",
    "gemini": "Gemini",
    "google": "Google",
    "deepseek": "DeepSeek",
    "zhipu": "Zhipu",
}

# Canonical, full-length model labels (the markdown summary uses these). Figure
# scripts keep their own compact variants for axis labels.
MODEL_LABELS: dict[tuple[str, str], str] = {
    ("openai", "gpt4o"): "GPT-4o",
    ("openai", "o1_preview"): "o1-preview",
    ("openai", "o1_mini"): "o1-mini",
    ("openai", "o1"): "o1",
    ("openai", "o1_pro"): "o1-pro",
    ("openai", "o3_mini"): "o3-mini",
    ("openai", "o3_high"): "o3 (high reasoning)",
    ("openai", "o4_mini"): "o4-mini",
    ("openai", "gpt5"): "GPT-5",
    ("openai", "chatgpt_deep_research"): "ChatGPT Deep Research",
    ("claude", "sonnet_3.5"): "Sonnet 3.5",
    ("claude", "sonnet_4"): "Sonnet 4",
    ("claude", "sonnet_4.5"): "Sonnet 4.5",
    ("claude", "haiku_4.5"): "Haiku 4.5",
    ("claude", "opus_4.5"): "Opus 4.5",
    ("claude", "opus_4.6"): "Opus 4.6",
    ("claude", "sonnet_4.6"): "Sonnet 4.6",
    ("claude", "deep_research"): "Claude Deep Research",
    ("gemini", "2.0_flash"): "Gemini 2.0 Flash",
    ("gemini", "2.5_pro_preview"): "Gemini 2.5 Pro Preview",
    ("gemini", "2.5_flash"): "Gemini 2.5 Flash",
    ("gemini", "2.5_pro_stable"): "Gemini 2.5 Pro",
    ("gemini", "3_pro"): "Gemini 3 Pro",
    ("gemini", "3_flash"): "Gemini 3 Flash",
    ("gemini", "3.1_pro"): "Gemini 3.1 Pro",
    ("google", "gemini_deep_research"): "Gemini Deep Research",
    ("deepseek", "v3"): "DeepSeek V3",
    ("zhipu", "glm_5"): "GLM-5",
}

# ---------------------------------------------------------------------------
# Shared pure helpers
# ---------------------------------------------------------------------------


def add_numeric_scores(df: Any) -> Any:
    """Add a ``{dim}_num`` column for each dimension via ``SCORE_MAP``.

    Unmappable / missing letters become NaN (pandas ``Series.map`` default).
    Mutates and returns ``df`` for convenience.
    """
    for dim in DIMENSIONS:
        df[f"{dim}_num"] = df[dim].map(SCORE_MAP[dim])
    return df


def ordered_models(
    df: Any,
    version_order: dict[str, list[str]] | None = None,
    family_order: list[str] | None = None,
) -> list[tuple[str, str]]:
    """Return the (family, version) pairs present in ``df`` in canonical order.

    Models are ordered by ``family_order`` then by the chronological
    ``version_order`` within each family; any present pair not covered by the
    registry is appended in sorted order so nothing is silently dropped.
    """
    version_order = MODEL_VERSION_ORDER if version_order is None else version_order
    family_order = FAMILY_ORDER if family_order is None else family_order

    present = set(zip(df["model_family"], df["model_version"]))
    ordered: list[tuple[str, str]] = []
    for family in family_order:
        for version in version_order.get(family, []):
            key = (family, version)
            if key in present:
                ordered.append(key)
    ordered.extend(sorted(present - set(ordered)))
    return ordered


def family_label(family: str) -> str:
    """Human-readable family name, falling back to a title-cased key."""
    return FAMILY_LABELS.get(family, family.title())


def model_label(
    family: str,
    version: str,
    labels: dict[tuple[str, str], str] | None = None,
) -> str:
    """Human-readable model name. Pass ``labels`` to use a compact map."""
    labels = MODEL_LABELS if labels is None else labels
    return labels.get((family, version), f"{family}/{version}")


def is_step_fully_correct(row: Any) -> bool:
    """True when every dimension in ``row`` carries its fully-correct letter."""
    return all(row[dim] == expected for dim, expected in FULLY_CORRECT.items())


def slugify(text: str) -> str:
    """Lowercase, collapse non-alphanumerics to underscores, trim edges."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")
