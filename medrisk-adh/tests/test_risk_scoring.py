"""Tests for medrisk.models.risk_scoring."""

from medrisk.models.risk_scoring import (
    CharlsonIndex,
    ElixhauserScore,
    MorbidityRiskScorer,
)


class TestCharlsonIndex:
    def setup_method(self):
        self.cci = CharlsonIndex()

    def test_empty_codes_returns_zero(self):
        assert self.cci.score([]) == 0

    def test_single_mi(self):
        # I21 = Myocardial infarction, weight 1
        assert self.cci.score(["I21"]) == 1

    def test_single_chf(self):
        # I50 = CHF, weight 1
        assert self.cci.score(["I50"]) == 1

    def test_ckd_weight_2(self):
        # N18 = CKD moderate-severe, weight 2
        assert self.cci.score(["N18"]) == 2

    def test_multiple_conditions_sum(self):
        # E11.9 (DM uncomplicated, w=1) + I50 (CHF, w=1) + N18 (CKD, w=2) -> 4
        result = self.cci.score(["E11.9", "I50", "N18"])
        assert result == 4

    def test_metastatic_weight_6(self):
        # C77 = metastatic solid tumour, weight 6
        assert self.cci.score(["C77"]) == 6

    def test_dm_mutual_exclusion(self):
        # E11.2 (DM complicated, w=2) should suppress E11.9 (uncomplicated, w=1)
        score_complicated = self.cci.score(["E11.2"])
        score_both = self.cci.score(["E11.9", "E11.2"])
        assert score_complicated == 2
        assert score_both == 2  # not 3

    def test_metastatic_suppresses_solid_tumour(self):
        # Metastatic (w=6) should suppress solid tumour (w=2)
        score = self.cci.score(["C50", "C77"])
        assert score == 6  # not 8

    def test_survival_10yr_zero_cci(self):
        # S10 = 0.983^exp(0*0.9) = 0.983^1 = 0.983
        s = self.cci.survival_10yr(0)
        assert abs(s - 0.983) < 1e-6

    def test_survival_10yr_decreases_with_cci(self):
        assert self.cci.survival_10yr(0) > self.cci.survival_10yr(2)
        assert self.cci.survival_10yr(2) > self.cci.survival_10yr(5)

    def test_survival_10yr_bounded(self):
        for cci in [0, 1, 3, 6, 10]:
            s = self.cci.survival_10yr(cci)
            assert 0.0 < s <= 1.0

    def test_icd_with_dot_normalised(self):
        # "I21.0" should match same as "I21"
        assert self.cci.score(["I21.0"]) == 1

    def test_hiv_weight_6(self):
        assert self.cci.score(["B20"]) == 6


class TestElixhauserScore:
    def setup_method(self):
        self.eli = ElixhauserScore()

    def test_empty_codes_returns_zero(self):
        assert self.eli.score([]) == 0

    def test_chf_weight_7(self):
        assert self.eli.score(["I50"]) == 7

    def test_metastatic_weight_12(self):
        assert self.eli.score(["C77"]) == 12

    def test_hypertension_weight_negative(self):
        # I10 = uncomplicated hypertension, weight -1
        assert self.eli.score(["I10"]) == -1

    def test_multiple_additive(self):
        # CHF (7) + metastatic (12) = 19
        assert self.eli.score(["I50", "C77"]) == 19


class TestMorbidityRiskScorer:
    def setup_method(self):
        self.mrs = MorbidityRiskScorer()

    def test_baseline_rr_approximately_one(self):
        # No diagnoses, age 35 male, occ class 1 -> should be close to 1.0
        rr = self.mrs.relative_risk([], age=35, sex="M", occ_class=1)
        assert 0.8 <= rr <= 1.5

    def test_higher_occ_class_increases_rr(self):
        rr1 = self.mrs.relative_risk([], 40, "M", occ_class=1)
        rr4 = self.mrs.relative_risk([], 40, "M", occ_class=4)
        assert rr4 > rr1

    def test_higher_cci_increases_rr(self):
        rr_healthy = self.mrs.relative_risk([], 40, "M", 1)
        rr_sick = self.mrs.relative_risk(["I50", "N18", "E11.2"], 40, "M", 1)
        assert rr_sick > rr_healthy

    def test_older_age_increases_rr(self):
        # age 25 -> band 25 (RR 0.90), age 65 -> band 65 (RR 1.70)
        rr_young = self.mrs.relative_risk([], 25, "M", 1)
        rr_old = self.mrs.relative_risk([], 65, "M", 1)
        assert rr_old > rr_young

    def test_age_band_clamps(self):
        # Ages below 15 and above 69 should return valid RR
        rr_low = self.mrs.relative_risk([], 10, "M", 1)
        rr_high = self.mrs.relative_risk([], 80, "M", 1)
        assert rr_low > 0
        assert rr_high > 0
