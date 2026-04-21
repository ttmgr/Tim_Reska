"""Tests for survival analysis metric calculations.

Validates C-index, Brier score, and AUC computations using
known synthetic scenarios (perfect predictions, random predictions,
tied predictions).
"""

import numpy as np
import pytest
from lifelines.utils import concordance_index


# ── C-index tests ───────────────────────────────────────────────────────────

class TestConcordanceIndex:
    """Test C-index with known orderings."""

    def test_perfect_concordance(self) -> None:
        """Perfect risk ordering should yield C-index = 1.0."""
        event_times = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        predicted_risk = np.array([5.0, 4.0, 3.0, 2.0, 1.0])  # higher risk = shorter survival
        events = np.array([1, 1, 1, 1, 1])

        ci = concordance_index(event_times, predicted_risk, events)
        assert ci == pytest.approx(1.0, abs=1e-6), (
            f"Perfect concordance expected C-index=1.0, got {ci}"
        )

    def test_inverse_concordance(self) -> None:
        """Perfectly inverted risk ordering should yield C-index = 0.0."""
        event_times = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        predicted_risk = np.array([1.0, 2.0, 3.0, 4.0, 5.0])  # inverted
        events = np.array([1, 1, 1, 1, 1])

        ci = concordance_index(event_times, predicted_risk, events)
        assert ci == pytest.approx(0.0, abs=1e-6), (
            f"Inverse concordance expected C-index=0.0, got {ci}"
        )

    def test_random_concordance_approximately_half(self) -> None:
        """Random predictions should yield C-index approximately 0.5."""
        np.random.seed(42)
        n = 5000
        event_times = np.random.exponential(5, n)
        predicted_risk = np.random.randn(n)
        events = np.ones(n)

        ci = concordance_index(event_times, predicted_risk, events)
        assert 0.45 <= ci <= 0.55, (
            f"Random predictions expected C-index near 0.5, got {ci}"
        )

    def test_cindex_with_censoring(self) -> None:
        """C-index should handle censored observations correctly."""
        event_times = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        predicted_risk = np.array([5.0, 4.0, 3.0, 2.0, 1.0])
        events = np.array([1, 0, 1, 0, 1])  # some censored

        ci = concordance_index(event_times, predicted_risk, events)
        # With censoring, C-index should still be high for correct ordering
        assert ci >= 0.8, (
            f"Expected high C-index with correct ordering despite censoring, got {ci}"
        )

    def test_cindex_all_censored(self) -> None:
        """C-index with all censored observations should return 0.0 (no comparable pairs)."""
        event_times = np.array([1.0, 2.0, 3.0])
        predicted_risk = np.array([3.0, 2.0, 1.0])
        events = np.array([0, 0, 0])

        # lifelines returns 0.0 when there are no comparable pairs
        ci = concordance_index(event_times, predicted_risk, events)
        # No events means no concordant pairs can be formed
        assert ci == pytest.approx(0.0, abs=1e-6) or np.isnan(ci)

    def test_cindex_ties(self) -> None:
        """C-index should handle tied predictions appropriately."""
        event_times = np.array([1.0, 2.0, 3.0, 4.0])
        predicted_risk = np.array([3.0, 3.0, 1.0, 1.0])  # ties
        events = np.array([1, 1, 1, 1])

        ci = concordance_index(event_times, predicted_risk, events)
        # Tied predictions contribute 0.5 to concordance
        assert 0.0 <= ci <= 1.0, f"C-index out of bounds: {ci}"

    def test_cindex_bounded(self) -> None:
        """C-index must always be between 0 and 1."""
        np.random.seed(123)
        for _ in range(20):
            n = np.random.randint(10, 100)
            event_times = np.random.exponential(5, n)
            predicted_risk = np.random.randn(n)
            events = np.random.binomial(1, 0.5, n)

            if events.sum() == 0:
                continue  # skip if no events

            ci = concordance_index(event_times, predicted_risk, events)
            assert 0.0 <= ci <= 1.0, f"C-index out of [0, 1]: {ci}"


# ── Brier score tests ──────────────────────────────────────────────────────

class TestBrierScore:
    """Test Brier score bounds and properties."""

    @staticmethod
    def _brier_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Simple Brier score calculation (without censoring adjustment)."""
        return np.mean((y_true - y_pred) ** 2)

    def test_perfect_predictions(self) -> None:
        """Perfect predictions should have Brier score = 0."""
        y_true = np.array([0, 1, 0, 1, 1])
        y_pred = np.array([0.0, 1.0, 0.0, 1.0, 1.0])
        bs = self._brier_score(y_true, y_pred)
        assert bs == pytest.approx(0.0, abs=1e-10)

    def test_worst_predictions(self) -> None:
        """Perfectly wrong predictions should have Brier score = 1."""
        y_true = np.array([0, 1, 0, 1, 1])
        y_pred = np.array([1.0, 0.0, 1.0, 0.0, 0.0])
        bs = self._brier_score(y_true, y_pred)
        assert bs == pytest.approx(1.0, abs=1e-10)

    def test_brier_score_bounded(self) -> None:
        """Brier score must be between 0 and 1 for valid probability predictions."""
        np.random.seed(42)
        for _ in range(50):
            n = np.random.randint(10, 200)
            y_true = np.random.binomial(1, 0.3, n).astype(float)
            y_pred = np.random.uniform(0, 1, n)
            bs = self._brier_score(y_true, y_pred)
            assert 0.0 <= bs <= 1.0, f"Brier score out of [0, 1]: {bs}"

    def test_random_predictions_brier(self) -> None:
        """Random 0.5 predictions on balanced data should give Brier ~ 0.25."""
        np.random.seed(42)
        n = 10000
        y_true = np.random.binomial(1, 0.5, n).astype(float)
        y_pred = np.full(n, 0.5)
        bs = self._brier_score(y_true, y_pred)
        assert 0.20 <= bs <= 0.30, (
            f"Random predictions Brier expected ~0.25, got {bs:.4f}"
        )

    def test_brier_score_monotonicity(self) -> None:
        """Better predictions should have lower Brier score."""
        y_true = np.array([0, 0, 1, 1, 1, 0, 1, 0])
        y_good = np.array([0.1, 0.2, 0.8, 0.9, 0.7, 0.1, 0.85, 0.15])
        y_bad = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])

        bs_good = self._brier_score(y_true, y_good)
        bs_bad = self._brier_score(y_true, y_bad)
        assert bs_good < bs_bad, (
            f"Good predictions ({bs_good:.4f}) should have lower Brier than "
            f"uninformative ({bs_bad:.4f})"
        )


# ── AUC tests ──────────────────────────────────────────────────────────────

class TestAUC:
    """Test AUC with perfect and random predictions."""

    @staticmethod
    def _simple_auc(y_true: np.ndarray, y_scores: np.ndarray) -> float:
        """Compute AUC using the Wilcoxon-Mann-Whitney statistic."""
        pos = y_scores[y_true == 1]
        neg = y_scores[y_true == 0]
        if len(pos) == 0 or len(neg) == 0:
            return np.nan
        concordant = sum(
            (p > n) + 0.5 * (p == n)
            for p in pos
            for n in neg
        )
        return concordant / (len(pos) * len(neg))

    def test_perfect_auc(self) -> None:
        """Perfect separation should give AUC = 1.0."""
        y_true = np.array([0, 0, 0, 1, 1, 1])
        y_scores = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])
        auc = self._simple_auc(y_true, y_scores)
        assert auc == pytest.approx(1.0, abs=1e-10)

    def test_inverse_auc(self) -> None:
        """Perfectly inverted predictions should give AUC = 0.0."""
        y_true = np.array([0, 0, 0, 1, 1, 1])
        y_scores = np.array([0.9, 0.8, 0.7, 0.3, 0.2, 0.1])
        auc = self._simple_auc(y_true, y_scores)
        assert auc == pytest.approx(0.0, abs=1e-10)

    def test_random_auc_approximately_half(self) -> None:
        """Random predictions should give AUC approximately 0.5."""
        np.random.seed(42)
        n = 2000
        y_true = np.random.binomial(1, 0.5, n)
        y_scores = np.random.uniform(0, 1, n)
        auc = self._simple_auc(y_true, y_scores)
        assert 0.45 <= auc <= 0.55, (
            f"Random AUC expected ~0.5, got {auc:.4f}"
        )

    def test_auc_bounded(self) -> None:
        """AUC must be between 0 and 1."""
        np.random.seed(42)
        for _ in range(20):
            n = np.random.randint(20, 200)
            y_true = np.random.binomial(1, 0.3, n)
            y_scores = np.random.uniform(0, 1, n)
            if y_true.sum() == 0 or y_true.sum() == n:
                continue
            auc = self._simple_auc(y_true, y_scores)
            assert 0.0 <= auc <= 1.0, f"AUC out of [0, 1]: {auc}"

    def test_auc_invariant_to_monotone_transform(self) -> None:
        """AUC should be invariant to monotone transformations of scores."""
        y_true = np.array([0, 0, 1, 1, 0, 1])
        y_scores = np.array([0.2, 0.3, 0.7, 0.8, 0.4, 0.9])
        auc_original = self._simple_auc(y_true, y_scores)
        auc_log = self._simple_auc(y_true, np.log(y_scores + 1))
        auc_squared = self._simple_auc(y_true, y_scores ** 2)

        assert auc_original == pytest.approx(auc_log, abs=1e-10), (
            "AUC should be invariant to log transform"
        )
        assert auc_original == pytest.approx(auc_squared, abs=1e-10), (
            "AUC should be invariant to square transform"
        )

    def test_auc_with_all_positive(self) -> None:
        """AUC with all positive labels should be NaN."""
        y_true = np.ones(10)
        y_scores = np.random.uniform(0, 1, 10)
        auc = self._simple_auc(y_true, y_scores)
        assert np.isnan(auc), "AUC with all positive labels should be NaN"

    def test_auc_with_all_negative(self) -> None:
        """AUC with all negative labels should be NaN."""
        y_true = np.zeros(10)
        y_scores = np.random.uniform(0, 1, 10)
        auc = self._simple_auc(y_true, y_scores)
        assert np.isnan(auc), "AUC with all negative labels should be NaN"
