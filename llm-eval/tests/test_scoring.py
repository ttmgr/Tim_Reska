"""Tests for the shared scoring taxonomy and model registry.

The scoring logic *is* the product of this evaluation, so it gets a unit-test
safety net independent of the figure/markdown rendering. These tests also act
as drift guards: a typo'd model version or an unlabeled model now fails CI
instead of silently mismatching grouping/labels across scripts.
"""

import pandas as pd
import pytest

from scoring import (
    DIMENSIONS,
    FAMILY_LABELS,
    FAMILY_ORDER,
    FULLY_CORRECT,
    MODEL_LABELS,
    MODEL_VERSION_ORDER,
    SCORE_MAP,
    add_numeric_scores,
    family_label,
    is_step_fully_correct,
    model_label,
    ordered_models,
    slugify,
)

# ---------------------------------------------------------------------------
# Scoring taxonomy
# ---------------------------------------------------------------------------


def test_dimensions_match_score_map() -> None:
    assert DIMENSIONS == list(SCORE_MAP.keys())


def test_fully_correct_covers_every_dimension() -> None:
    assert set(FULLY_CORRECT) == set(DIMENSIONS)


def test_fully_correct_letter_scores_one() -> None:
    for dim, letter in FULLY_CORRECT.items():
        assert SCORE_MAP[dim][letter] == 1.0


def test_all_scores_in_unit_range() -> None:
    for mapping in SCORE_MAP.values():
        assert all(0.0 <= v <= 1.0 for v in mapping.values())


# ---------------------------------------------------------------------------
# Model registry consistency (drift guards)
# ---------------------------------------------------------------------------


def test_every_ordered_model_has_a_label() -> None:
    for family, versions in MODEL_VERSION_ORDER.items():
        for version in versions:
            assert (family, version) in MODEL_LABELS, f"missing label for {family}/{version}"


def test_no_orphan_labels() -> None:
    for family, version in MODEL_LABELS:
        assert family in MODEL_VERSION_ORDER, f"label family {family} not in registry"
        assert version in MODEL_VERSION_ORDER[family], f"label {family}/{version} not in order"


def test_families_consistent_across_registry() -> None:
    assert set(MODEL_VERSION_ORDER) <= set(FAMILY_ORDER)
    for family in MODEL_VERSION_ORDER:
        assert family in FAMILY_LABELS


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def test_add_numeric_scores_maps_letters() -> None:
    df = pd.DataFrame(
        {
            "tool_selection": ["C", "A", "I"],
            "parameter_accuracy": ["C", "P", "I"],
            "output_compatibility": ["P", "F", "P"],
            "scientific_validity": ["S", "Q", "I"],
            "executability": ["R", "M", "N"],
        }
    )
    add_numeric_scores(df)
    assert list(df["tool_selection_num"]) == [1.0, 0.5, 0.0]
    assert list(df["output_compatibility_num"]) == [1.0, 0.0, 1.0]
    assert list(df["executability_num"]) == [1.0, 0.5, 0.0]


def test_add_numeric_scores_unmapped_letter_is_nan() -> None:
    df = pd.DataFrame(
        {
            "tool_selection": ["Z"],
            "parameter_accuracy": ["C"],
            "output_compatibility": ["P"],
            "scientific_validity": ["S"],
            "executability": ["R"],
        }
    )
    add_numeric_scores(df)
    assert pd.isna(df["tool_selection_num"].iloc[0])


def test_ordered_models_canonical_order_with_extras() -> None:
    df = pd.DataFrame(
        {
            "model_family": ["gemini", "openai", "openai", "newco"],
            "model_version": ["3_pro", "gpt5", "gpt4o", "x1"],
        }
    )
    # openai (gpt4o before gpt5 per registry), then gemini, then unknown extra appended.
    assert ordered_models(df) == [
        ("openai", "gpt4o"),
        ("openai", "gpt5"),
        ("gemini", "3_pro"),
        ("newco", "x1"),
    ]


def test_ordered_models_only_returns_present() -> None:
    df = pd.DataFrame({"model_family": ["claude"], "model_version": ["opus_4.6"]})
    assert ordered_models(df) == [("claude", "opus_4.6")]


def test_is_step_fully_correct() -> None:
    good = {
        "tool_selection": "C",
        "parameter_accuracy": "C",
        "output_compatibility": "P",
        "scientific_validity": "S",
        "executability": "R",
    }
    assert is_step_fully_correct(good)
    assert not is_step_fully_correct({**good, "executability": "N"})


def test_labels_known_and_fallback() -> None:
    assert family_label("openai") == "OpenAI"
    assert family_label("unknown_co") == "Unknown_Co"
    assert model_label("openai", "gpt5") == "GPT-5"
    assert model_label("xyz", "v9") == "xyz/v9"
    # A compact override map is honoured.
    assert model_label("openai", "gpt5", labels={("openai", "gpt5"): "G5"}) == "G5"


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Host Depletion", "host_depletion"),
        ("AMR/Vir/Plasmid", "amr_vir_plasmid"),
        ("  Trimmed  ", "trimmed"),
    ],
)
def test_slugify(raw: str, expected: str) -> None:
    assert slugify(raw) == expected
