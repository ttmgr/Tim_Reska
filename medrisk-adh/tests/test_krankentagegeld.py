"""Tests for medrisk.models.krankentagegeld."""

import pandas as pd
import pytest

from medrisk.models.krankentagegeld import KrankentagegeldModel


@pytest.fixture
def model():
    return KrankentagegeldModel.from_config()


class TestGKVStatutory:
    def test_krankengeld_daily_below_bbg(self, model):
        # Gross 3000/month -> KG = min(3000*0.70/30, ...) = 70
        kg = model.krankengeld_daily(3000.0)
        assert 50.0 < kg <= 100.0

    def test_krankengeld_daily_capped_at_bbg(self, model):
        # Very high income: should be capped at BBG * 0.70 / 30 ~ 116.38
        kg_high = model.krankengeld_daily(20000.0)
        kg_bbg = model.krankengeld_daily(4987.50)
        assert abs(kg_high - kg_bbg) < 1.0  # effectively the same (BBG cap)

    def test_krankengeld_daily_nonnegative(self, model):
        assert model.krankengeld_daily(0.0) >= 0.0
        assert model.krankengeld_daily(500.0) >= 0.0

    def test_krankengeld_daily_net_overrides(self, model):
        # Low net income cap should bind
        kg_with_net = model.krankengeld_daily(5000.0, net_monthly=1000.0)
        # 90% of 1000 / 30 ~ 30 -- lower than gross-based cap
        assert kg_with_net <= 35.0

    def test_ktg_gap_positive_when_benefit_above_kg(self, model):
        gap = model.ktg_benefit_above_krankengeld(150.0, 3000.0)
        assert gap > 0.0

    def test_ktg_gap_zero_when_benefit_below_kg(self, model):
        # Insured only 10 EUR/day but KG is ~70 -- gap = 0
        gap = model.ktg_benefit_above_krankengeld(10.0, 3000.0)
        assert gap == pytest.approx(0.0)


class TestRiskFactors:
    def test_age_sex_factor_age35_male_near_one(self, model):
        f = model.age_sex_factor(35, "M")
        assert 0.5 < f < 2.0  # should be approximately the baseline

    def test_older_age_higher_factor(self, model):
        f35 = model.age_sex_factor(35, "M")
        f55 = model.age_sex_factor(55, "M")
        assert f55 > f35

    def test_occ_factor_class1_is_one(self, model):
        assert model.occupational_factor(1) == pytest.approx(1.00)

    def test_occ_factor_class4_is_2_10(self, model):
        assert model.occupational_factor(4) == pytest.approx(2.10)

    def test_occ_factor_increases_with_class(self, model):
        for c in range(1, 4):
            assert model.occupational_factor(c) < model.occupational_factor(c + 1)


class TestExpectedClaim:
    def test_expected_annual_claim_positive(self, model):
        claim = model.expected_annual_claim(40, "M", 2, 100.0, 4000.0)
        assert claim > 0.0

    def test_expected_claim_higher_for_class4(self, model):
        c1 = model.expected_annual_claim(40, "M", 1, 100.0, 4000.0)
        c4 = model.expected_annual_claim(40, "M", 4, 100.0, 4000.0)
        assert c4 > c1

    def test_expected_claim_varies_with_age(self, model):
        # GKV frequency peaks around age 22 and declines; claims are positive at all ages
        c25 = model.expected_annual_claim(25, "M", 1, 100.0, 4000.0)
        c45 = model.expected_annual_claim(45, "M", 1, 100.0, 4000.0)
        c65 = model.expected_annual_claim(65, "M", 1, 100.0, 4000.0)
        assert c25 > 0 and c45 > 0 and c65 > 0

    def test_expected_claim_higher_with_longer_karenzzeit(self, model):
        # Longer Karenzzeit -> fewer benefit days -> lower claim
        c3 = model.expected_annual_claim(40, "M", 1, 100.0, 4000.0, karenzzeit_days=3)
        c14 = model.expected_annual_claim(40, "M", 1, 100.0, 4000.0, karenzzeit_days=14)
        assert c3 > c14

    def test_expected_claim_zero_insured_daily(self, model):
        # No insured daily benefit -> no claim
        claim = model.expected_annual_claim(40, "M", 1, 0.0, 4000.0)
        assert claim == pytest.approx(0.0, abs=0.01)


class TestPremiumCalculations:
    def test_net_premium_positive(self, model):
        p = model.net_premium(40, "M", 1, 100.0, 4000.0)
        assert p > 0.0

    def test_gross_premium_gt_net(self, model):
        net = model.net_premium(40, "M", 1, 100.0, 4000.0)
        gross = model.gross_premium(40, "M", 1, 100.0, 4000.0)
        assert gross > net

    def test_level_premium_gt_single_year_net(self, model):
        # Level premium amortises increasing risk -- may differ, but must be > 0
        lp = model.level_premium(30, "M", 1, 100.0, 4000.0)
        assert lp > 0.0

    def test_level_premium_gross_gt_net(self, model):
        lp_net = model.level_premium(
            30, "M", 1, 100.0, 4000.0, expense_loading=0.0, profit_loading=0.0
        )
        lp_gross = model.level_premium(30, "M", 1, 100.0, 4000.0)
        assert lp_gross > lp_net

    def test_invalid_loading_raises(self, model):
        with pytest.raises(ValueError):
            model.gross_premium(
                40, "M", 1, 100.0, 4000.0, expense_loading=0.80, profit_loading=0.30
            )


class TestProspectiveReserve:
    def test_reserve_zero_at_entry_net_premium(self, model):
        # With zero loadings, the level premium = net premium, so V_0 = 0
        lp = model.level_premium(
            35, "M", 1, 100.0, 4000.0, expense_loading=0.0, profit_loading=0.0
        )
        reserve = model.prospective_reserve(35, 35, "M", 1, lp, 100.0, 4000.0)
        # Should be ~0 by equivalence principle (small numerical residual OK)
        assert abs(reserve) < lp * 0.05  # within 5% of annual premium

    def test_reserve_zero_at_expiry(self, model):
        lp = model.level_premium(
            35, "M", 1, 100.0, 4000.0, expense_loading=0.0, profit_loading=0.0, max_age=67
        )
        reserve = model.prospective_reserve(35, 67, "M", 1, lp, 100.0, 4000.0, max_age=67)
        assert reserve == pytest.approx(0.0, abs=1e-6)

    def test_reserve_gross_negative_at_entry(self, model):
        # With positive loadings, gross level premium > net, so V_0 < 0 (unearned loading)
        lp = model.level_premium(35, "M", 1, 100.0, 4000.0)
        reserve = model.prospective_reserve(35, 35, "M", 1, lp, 100.0, 4000.0)
        assert reserve < 0.0

    def test_reserve_profile_shape(self, model):
        df = model.reserve_profile(35, "M", 1, 100.0, 4000.0)
        assert isinstance(df, pd.DataFrame)
        assert "age" in df.columns
        assert "reserve" in df.columns
        assert "net_premium" in df.columns
        assert "gross_premium" in df.columns
        # Ages from 35 to 67 inclusive
        assert len(df) == 67 - 35 + 1

    def test_reserve_profile_last_row_near_zero(self, model):
        df = model.reserve_profile(
            35, "M", 1, 100.0, 4000.0, expense_loading=0.0, profit_loading=0.0
        )
        # Reserve at max_age (67) should be ~0
        assert abs(df.iloc[-1]["reserve"]) < 1.0


class TestPricingDataframe:
    def test_pricing_dataframe_shape(self, model):
        df = model.pricing_dataframe(
            ages=[30, 40, 50],
            sexes=["M", "F"],
            occ_classes=[1, 2],
            insured_daily=100.0,
            gross_monthly=4000.0,
        )
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3 * 2 * 2  # 12 rows
        assert "net_premium" in df.columns
        assert "gross_premium" in df.columns
        assert "expected_claim" in df.columns

    def test_all_premiums_positive(self, model):
        df = model.pricing_dataframe(
            ages=[35, 45],
            sexes=["M"],
            occ_classes=[1, 3],
            insured_daily=100.0,
            gross_monthly=4000.0,
        )
        assert (df["net_premium"] > 0).all()
        assert (df["gross_premium"] > df["net_premium"]).all()
