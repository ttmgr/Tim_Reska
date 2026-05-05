"""Tests for the questionnaire module and benchmark lookups."""

from __future__ import annotations

import pytest

from src.questionnaire import QUESTIONS, DIMENSIONS, DEMO_ANSWERS, Question
from src.benchmarks import get_benchmark, list_sectors, SECTOR_NAMES, DIMENSION_NAMES


class TestQuestionBank:
    """Validate the question bank structure."""

    def test_exactly_25_questions(self) -> None:
        assert len(QUESTIONS) == 25

    def test_five_questions_per_dimension(self) -> None:
        for dim in DIMENSIONS:
            count = sum(1 for q in QUESTIONS if q.dimension == dim)
            assert count == 5, f"{dim} has {count} questions, expected 5"

    def test_all_questions_have_anchors(self) -> None:
        for q in QUESTIONS:
            assert len(q.anchors) == 2
            assert q.anchors[0] != q.anchors[1]

    def test_demo_answers_match_question_count(self) -> None:
        assert len(DEMO_ANSWERS) == len(QUESTIONS)

    def test_demo_answers_in_range(self) -> None:
        for ans in DEMO_ANSWERS:
            assert 1 <= ans <= 5

    def test_dimensions_match_benchmark_dimensions(self) -> None:
        assert DIMENSIONS == DIMENSION_NAMES


class TestBenchmarks:
    """Benchmark lookup and data integrity."""

    def test_all_sectors_retrievable(self) -> None:
        for sector in SECTOR_NAMES:
            bm = get_benchmark(sector)
            assert bm is not None
            assert bm.sector == sector

    def test_case_insensitive_lookup(self) -> None:
        bm = get_benchmark("financial services")
        assert bm is not None
        assert bm.sector == "Financial Services"

    def test_unknown_sector_returns_none(self) -> None:
        assert get_benchmark("Aerospace") is None

    def test_benchmark_scores_in_valid_range(self) -> None:
        for sector in SECTOR_NAMES:
            bm = get_benchmark(sector)
            assert bm is not None
            for dim, score in bm.scores.items():
                assert 1.0 <= score <= 5.0, f"{sector}/{dim} score {score} out of range"
            assert 1.0 <= bm.overall <= 5.0

    def test_benchmark_covers_all_dimensions(self) -> None:
        for sector in SECTOR_NAMES:
            bm = get_benchmark(sector)
            assert bm is not None
            for dim in DIMENSION_NAMES:
                assert dim in bm.scores, f"{sector} missing dimension {dim}"

    def test_list_sectors_returns_all(self) -> None:
        assert list_sectors() == SECTOR_NAMES
