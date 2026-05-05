"""Tests for the scoring engine."""

from __future__ import annotations

import pytest

from src.scorer import (
    DimensionScore,
    compute_dimension_scores,
    determine_tier,
    generate_recommendations,
    DIMENSION_WEIGHTS,
)
from src.questionnaire import QUESTIONS, DIMENSIONS, DEMO_ANSWERS


class TestDeterminesTier:
    """Tier assignment from overall score."""

    @pytest.mark.parametrize(
        "score, expected",
        [
            (1.0, "Exploring"),
            (1.5, "Exploring"),
            (1.99, "Exploring"),
            (2.0, "Piloting"),
            (2.5, "Piloting"),
            (2.99, "Piloting"),
            (3.0, "Scaling"),
            (3.5, "Scaling"),
            (3.99, "Scaling"),
            (4.0, "Optimizing"),
            (4.5, "Optimizing"),
            (5.0, "Optimizing"),
        ],
    )
    def test_tier_boundaries(self, score: float, expected: str) -> None:
        assert determine_tier(score) == expected


class TestComputeDimensionScores:
    """Weighted scoring logic."""

    def test_all_ones_gives_score_one(self) -> None:
        answers = [1] * 25
        scores = compute_dimension_scores(answers, QUESTIONS, DIMENSIONS)
        for ds in scores:
            assert ds.score == pytest.approx(1.0, abs=0.01)

    def test_all_fives_gives_score_five(self) -> None:
        answers = [5] * 25
        scores = compute_dimension_scores(answers, QUESTIONS, DIMENSIONS)
        for ds in scores:
            assert ds.score == pytest.approx(5.0, abs=0.01)

    def test_demo_answers_produce_valid_scores(self) -> None:
        scores = compute_dimension_scores(DEMO_ANSWERS, QUESTIONS, DIMENSIONS)
        assert len(scores) == 5
        for ds in scores:
            assert 1.0 <= ds.score <= 5.0

    def test_wrong_answer_count_raises(self) -> None:
        with pytest.raises(ValueError, match="Expected 25"):
            compute_dimension_scores([3] * 10, QUESTIONS, DIMENSIONS)

    def test_out_of_range_answer_raises(self) -> None:
        answers = [3] * 24 + [6]
        with pytest.raises(ValueError, match="Answer must be 1-5"):
            compute_dimension_scores(answers, QUESTIONS, DIMENSIONS)

    def test_weights_sum_to_one(self) -> None:
        for dim, weights in DIMENSION_WEIGHTS.items():
            assert sum(weights) == pytest.approx(1.0, abs=0.001), (
                f"Weights for {dim} sum to {sum(weights)}"
            )

    def test_weighted_calculation_manual(self) -> None:
        """Verify weighted average by hand for the first dimension."""
        answers = [4, 3, 3, 4, 2] + [3] * 20  # first 5 for dim 0
        scores = compute_dimension_scores(answers, QUESTIONS, DIMENSIONS)
        weights = DIMENSION_WEIGHTS[DIMENSIONS[0]]
        expected = sum(a * w for a, w in zip([4, 3, 3, 4, 2], weights))
        assert scores[0].score == pytest.approx(expected, abs=0.01)


class TestGenerateRecommendations:
    """Recommendation generation."""

    def test_returns_at_most_three(self) -> None:
        scores = compute_dimension_scores(DEMO_ANSWERS, QUESTIONS, DIMENSIONS)
        recs = generate_recommendations(scores)
        assert len(recs) <= 3

    def test_recommendations_target_weakest_dimensions(self) -> None:
        scores = compute_dimension_scores(DEMO_ANSWERS, QUESTIONS, DIMENSIONS)
        recs = generate_recommendations(scores)
        sorted_dims = sorted(scores, key=lambda d: d.score)
        weakest_name = sorted_dims[0].name
        assert any(weakest_name in r for r in recs)

    def test_uniform_scores_still_produce_recommendations(self) -> None:
        answers = [3] * 25
        scores = compute_dimension_scores(answers, QUESTIONS, DIMENSIONS)
        recs = generate_recommendations(scores)
        assert len(recs) == 3
