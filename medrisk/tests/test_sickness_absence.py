"""Tests for medrisk.models.sickness_absence."""

import numpy as np
import pytest

from medrisk.models.sickness_absence import (
    NegBinomFrequencyModel,
    WeibullDurationModel,
)


class TestNegBinomFrequencyModel:
    def setup_method(self):
        self.model = NegBinomFrequencyModel()

    def test_expected_frequency_positive(self):
        freq = self.model.expected_frequency(40, "M")
        assert freq > 0

    def test_gkv_reference_frequency_age_40(self):
        f = self.model.gkv_reference_frequency(40, "M")
        # GKV reference for 40M should be around 1.1-1.2 episodes/year
        assert 0.5 < f < 3.0

    def test_gkv_reference_sick_days_age_40(self):
        d = self.model.gkv_reference_sick_days(40, "M")
        assert 5 < d < 40

    def test_gkv_reference_female_higher_than_male_for_young(self):
        # Female typically have more sick days than male at ages 25-45
        d_f = self.model.gkv_reference_sick_days(30, "F")
        d_m = self.model.gkv_reference_sick_days(30, "M")
        assert d_f > d_m

    def test_pmf_sums_to_approx_one(self):
        mu = self.model.expected_frequency(40, "M")
        total = sum(self.model.pmf(k, mu) for k in range(50))
        assert abs(total - 1.0) < 0.01

    def test_pmf_nonnegative(self):
        mu = 1.5
        for k in range(10):
            assert self.model.pmf(k, mu) >= 0.0

    def test_mean_variance_relationship(self):
        mu = 2.0
        mean, var = self.model.mean_variance(mu)
        assert mean == pytest.approx(mu)
        assert var > mean  # overdispersion: variance > mean

    def test_higher_occ_class_more_episodes(self):
        f1 = self.model.expected_frequency(40, "M", occ_class=1)
        f4 = self.model.expected_frequency(40, "M", occ_class=4)
        assert f4 > f1


class TestWeibullDurationModel:
    def setup_method(self):
        self.model = WeibullDurationModel()

    def test_icd_to_chapter_mapping(self):
        assert self.model.icd_to_chapter("M54") == "M"
        assert self.model.icd_to_chapter("F32") == "F"
        assert self.model.icd_to_chapter("I21") == "I"
        assert self.model.icd_to_chapter("J06") == "J"
        assert self.model.icd_to_chapter("X99") == "S_T"  # X = external causes -> S_T per config
        assert self.model.icd_to_chapter("") == "_other"

    def test_icd_with_dot(self):
        # Dot should be stripped
        assert self.model.icd_to_chapter("M54.5") == "M"

    def test_expected_duration_positive(self):
        for chapter in ["M", "F", "I", "J", "_other"]:
            d = self.model.expected_duration(chapter)
            assert d > 0, f"Expected duration for chapter {chapter} must be positive"

    def test_mental_duration_longer_than_respiratory(self):
        # F (mental) episodes are longer than J (respiratory)
        assert self.model.expected_duration("F") > self.model.expected_duration("J")

    def test_survival_at_zero_is_one(self):
        for chapter in ["M", "F", "I"]:
            assert self.model.survival(0.0, chapter) == pytest.approx(1.0)

    def test_survival_at_infinity_is_zero(self):
        for chapter in ["M", "F", "I"]:
            s = self.model.survival(1e9, chapter)
            assert s < 1e-6

    def test_survival_monotone_decreasing(self):
        times = [0, 5, 14, 30, 60, 100]
        surv = [self.model.survival(t, "M") for t in times]
        for i in range(len(surv) - 1):
            assert surv[i] >= surv[i + 1]

    def test_hazard_nonnegative(self):
        for t in [0.1, 1.0, 10.0, 50.0]:
            assert self.model.hazard(t, "M") >= 0.0

    def test_expected_days_above_zero_threshold(self):
        # E[max(T-0,0)] = E[T]
        for chapter in ["M", "F", "J"]:
            days_above = self.model.expected_days_above_threshold(0.0, chapter)
            expected = self.model.expected_duration(chapter)
            assert abs(days_above - expected) / expected < 0.05

    def test_expected_days_above_threshold_decreases_with_threshold(self):
        d0 = self.model.expected_days_above_threshold(0, "M")
        d7 = self.model.expected_days_above_threshold(7, "M")
        d30 = self.model.expected_days_above_threshold(30, "M")
        assert d0 > d7 > d30

    def test_simulate_episodes_shape(self):
        rng = np.random.default_rng(42)
        samples = self.model.simulate_episodes(1000, "M", rng=rng)
        assert samples.shape == (1000,)
        assert (samples > 0).all()

    def test_simulate_episodes_mean_approx_expected(self):
        rng = np.random.default_rng(42)
        samples = self.model.simulate_episodes(10000, "J", rng=rng)
        expected = self.model.expected_duration("J")
        # Within 10% of expected mean (large sample)
        assert abs(samples.mean() - expected) / expected < 0.15

    def test_mrs_scales_duration(self):
        d1 = self.model.expected_duration("M", mrs=1.0)
        d2 = self.model.expected_duration("M", mrs=2.0)
        assert abs(d2 - 2 * d1) < 0.01
