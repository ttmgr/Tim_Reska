"""Krankentagegeld (KTG) pricing and reserving model.

Krankentagegeld is German private daily sickness-benefit insurance that bridges
the gap between GKV Krankengeld (par. 44 SGB V) and the insured's actual income.

GKV chain of coverage:
    Day 1-42  (6 weeks): Employer pays 100 % (Lohnfortzahlung, par. 3 EFZG)
    Day 43-546 (up to 78 weeks): GKV pays Krankengeld
        = min(70 % gross / 30, 90 % net / 30, BBG_daily * 70 %)
    KTG (private): covers gap between Krankengeld and actual income,
        activated after the Karenzzeit (typically 3 days).

Equivalence principle (net premium):
    P * ae_x = sum_t v^t * _tp_x * E[claim_t(age+t)]
    where ae_x = sum_t v^t * _tp_x  and  v = 1/(1+i)

Prospective reserve at time t:
    V_t = PV(future benefits) - PV(future premiums)
    V_0 = 0 by the equivalence principle.

References:
    - par. 44 SGB V (Krankengeld)
    - par. 3 EFZG (Entgeltfortzahlungsgesetz)
    - DAV (Deutsche Aktuarvereinigung): KTG pricing guidelines
    - Bundesministerium fuer Gesundheit: GKV Finanzergebnisse 2024
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from ._config import load_icd_sick_leave, load_insurance_config
from .sickness_absence import NegBinomFrequencyModel, WeibullDurationModel

# ---------------------------------------------------------------------------
# German life table (simplified DAV 2008T excerpt for working-age population)
# Mortality rates q_x (probability of dying in year x) -- illustrative values
# ---------------------------------------------------------------------------

_MORTALITY_QX: dict[int, float] = {
    15: 0.00028,
    20: 0.00040,
    25: 0.00050,
    30: 0.00065,
    35: 0.00085,
    40: 0.00120,
    45: 0.00180,
    50: 0.00290,
    55: 0.00440,
    60: 0.00680,
    65: 0.01000,
    70: 0.01520,
    75: 0.02300,
    80: 0.03600,
    85: 0.06000,
}


def _mortality_qx(age: int) -> float:
    """Annual mortality probability (linear interpolation between table ages)."""
    ages = sorted(_MORTALITY_QX)
    if age <= ages[0]:
        return _MORTALITY_QX[ages[0]]
    if age >= ages[-1]:
        return _MORTALITY_QX[ages[-1]]
    for i in range(len(ages) - 1):
        a0, a1 = ages[i], ages[i + 1]
        if a0 <= age <= a1:
            frac = (age - a0) / (a1 - a0)
            return _MORTALITY_QX[a0] + frac * (_MORTALITY_QX[a1] - _MORTALITY_QX[a0])
    return 0.01  # fallback


class KrankentagegeldModel:
    """KTG net/gross premium and prospective reserve model.

    Parameters
    ----------
    insurance_config : dict
        Loaded from insurance_de.yml.
    icd_config : dict
        Loaded from icd_sick_leave.yml.
    config_dir : Path, optional
        Config directory (used only if configs not supplied directly).
    """

    def __init__(
        self,
        insurance_config: dict[str, Any] | None = None,
        icd_config: dict[str, Any] | None = None,
        config_dir: Path | None = None,
    ) -> None:
        self._ins = insurance_config or load_insurance_config(config_dir)
        self._icd = icd_config or load_icd_sick_leave(config_dir)
        self._freq = NegBinomFrequencyModel(config_dir)
        self._dur = WeibullDurationModel(config_dir)

        stat = self._ins["statutory"]
        self._bbg_monthly: float = float(stat["bbg_monthly_eur"])
        self._kg_pct_gross: float = float(stat["krankengeld_pct_gross"])
        self._kg_pct_net: float = float(stat["krankengeld_pct_net"])
        self._lohnfortzahlung_days: int = int(stat["lohnfortzahlung_weeks"]) * 7

        act = self._ins["actuarial"]
        self._reserve_rate: float = float(act["reserve_interest_rate"])

        occ_cfg = self._ins["occupational_classes"]
        self._occ_factors: dict[int, float] = {
            int(cls): float(v["risk_factor"]) for cls, v in occ_cfg.items()
        }

    @classmethod
    def from_config(cls, config_dir: Path | None = None) -> KrankentagegeldModel:
        """Construct from YAML config files in *config_dir* (or default)."""
        return cls(config_dir=config_dir)

    # ------------------------------------------------------------------
    # GKV Statutory benefit
    # ------------------------------------------------------------------

    def krankengeld_daily(self, gross_monthly: float, net_monthly: float | None = None) -> float:
        """Daily GKV Krankengeld (par. 44 SGB V).

        = min(
            gross_monthly * 0.70 / 30,
            net_monthly  * 0.90 / 30,   [if net provided]
            BBG_daily    * 0.70
          )

        Args:
            gross_monthly: Gross monthly income (EUR).
            net_monthly: Net monthly income (EUR). If None, assumed 80 % of gross.

        Returns:
            Daily Krankengeld amount (EUR/day).
        """
        if net_monthly is None:
            net_monthly = gross_monthly * 0.80  # approximate net after tax/social charges
        bbg_daily = self._bbg_monthly / 30.0
        kg = min(
            gross_monthly * self._kg_pct_gross / 30.0,
            net_monthly * self._kg_pct_net / 30.0,
            bbg_daily * self._kg_pct_gross,
        )
        return max(kg, 0.0)

    def ktg_benefit_above_krankengeld(
        self, insured_daily: float, gross_monthly: float, net_monthly: float | None = None
    ) -> float:
        """Daily KTG benefit net of GKV Krankengeld (i.e. the gap).

        = max(insured_daily - krankengeld_daily, 0)

        Args:
            insured_daily: Contractually insured daily benefit (EUR).
            gross_monthly: Gross monthly income (EUR).
            net_monthly: Net monthly income (EUR).

        Returns:
            Daily KTG benefit above GKV (EUR/day).
        """
        kg = self.krankengeld_daily(gross_monthly, net_monthly)
        return max(insured_daily - kg, 0.0)

    # ------------------------------------------------------------------
    # Risk factors
    # ------------------------------------------------------------------

    def age_sex_factor(self, age: int, sex: str) -> float:
        """Age/sex relative risk factor interpolated from GKV reference table.

        Returns (sick_days/yr at age/sex) / (sick_days/yr at age=35, sex=M).
        """
        ref_days_35m = self._freq.gkv_reference_sick_days(35, "M")
        ref_days = self._freq.gkv_reference_sick_days(age, sex)
        if ref_days_35m <= 0:
            return 1.0
        return ref_days / ref_days_35m

    def occupational_factor(self, occ_class: int) -> float:
        """Occupational risk factor (1.0 - 2.1)."""
        return self._occ_factors.get(occ_class, 1.0)

    # ------------------------------------------------------------------
    # Expected annual claim
    # ------------------------------------------------------------------

    def expected_annual_claim(
        self,
        age: int,
        sex: str,
        occ_class: int,
        insured_daily: float,
        gross_monthly: float,
        net_monthly: float | None = None,
        icd_profile: dict[str, float] | None = None,
        karenzzeit_days: int = 3,
    ) -> float:
        """Expected annual KTG claim amount (EUR).

        E[annual KTG] = frequency * sum_chapters weight_ch * E[benefit_days_ch] * daily_benefit

        where:
            E[benefit_days_ch] = E[max(T_ch - effective_threshold, 0)]
            effective_threshold = karenzzeit_days + lohnfortzahlung_days
            daily_benefit = ktg_benefit_above_krankengeld(...)

        Args:
            age: Insured's age in years.
            sex: "M" or "F".
            occ_class: Occupational risk class 1-4.
            insured_daily: Contractually insured daily benefit (EUR).
            gross_monthly: Gross monthly income (EUR).
            net_monthly: Net monthly income (EUR).
            icd_profile: Dict of {icd_chapter: weight} (weights sum to 1).
                         If None, uses pct_sick_days from icd_sick_leave.yml.
            karenzzeit_days: Private KTG waiting period (days, default 3).

        Returns:
            Expected annual KTG claim (EUR).
        """
        # --- frequency (episodes per year) ---
        of = self.occupational_factor(occ_class)
        base_freq = self._freq.gkv_reference_frequency(age, sex)
        freq = base_freq * of  # occupation-adjusted; MRS left as 1.0 default

        # --- daily benefit above GKV ---
        daily_benefit = self.ktg_benefit_above_krankengeld(
            insured_daily, gross_monthly, net_monthly
        )

        # --- ICD chapter profile ---
        chapters_cfg = self._icd["chapters"]
        if icd_profile is None:
            # Use sick-day shares from config
            icd_profile = {ch: float(v["pct_sick_days"]) for ch, v in chapters_cfg.items()}
            total_w = sum(icd_profile.values())
            if total_w > 0:
                icd_profile = {ch: w / total_w for ch, w in icd_profile.items()}
            else:
                icd_profile = {ch: 1.0 / len(icd_profile) for ch in icd_profile}

        # --- expected benefit days per episode by chapter ---
        # Effective threshold: Karenzzeit for private KTG
        # (Lohnfortzahlung is employer risk, not relevant for private KTG trigger)
        threshold = float(karenzzeit_days)

        claim = 0.0
        for chapter, weight in icd_profile.items():
            if weight <= 0:
                continue
            ch_cfg = chapters_cfg.get(chapter, chapters_cfg.get("_other", {}))
            ktg_rr = float(ch_cfg.get("ktg_rr", 1.0))
            expected_benefit_days = self._dur.expected_days_above_threshold(threshold, chapter)
            claim += weight * ktg_rr * expected_benefit_days

        return freq * claim * daily_benefit

    # ------------------------------------------------------------------
    # Net and gross premium
    # ------------------------------------------------------------------

    def net_premium(
        self,
        age: int,
        sex: str,
        occ_class: int,
        insured_daily: float,
        gross_monthly: float,
        net_monthly: float | None = None,
        **kwargs: Any,
    ) -> float:
        """Single-year net premium = expected annual claim."""
        return self.expected_annual_claim(
            age, sex, occ_class, insured_daily, gross_monthly, net_monthly, **kwargs
        )

    def gross_premium(
        self,
        age: int,
        sex: str,
        occ_class: int,
        insured_daily: float,
        gross_monthly: float,
        net_monthly: float | None = None,
        expense_loading: float = 0.20,
        profit_loading: float = 0.05,
        **kwargs: Any,
    ) -> float:
        """Single-year gross premium with expense and profit loadings.

        gross = net / (1 - expense_loading - profit_loading)
        """
        net = self.net_premium(
            age, sex, occ_class, insured_daily, gross_monthly, net_monthly, **kwargs
        )
        loading = 1.0 - expense_loading - profit_loading
        if loading <= 0:
            raise ValueError("Combined loading factor must leave positive residual.")
        return net / loading

    # ------------------------------------------------------------------
    # Level premium (equivalence principle)
    # ------------------------------------------------------------------

    def level_premium(
        self,
        entry_age: int,
        sex: str,
        occ_class: int,
        insured_daily: float,
        gross_monthly: float,
        net_monthly: float | None = None,
        benefit_period_years: int = 2,
        max_age: int = 67,
        expense_loading: float = 0.20,
        profit_loading: float = 0.05,
        **kwargs: Any,
    ) -> float:
        """Level gross premium based on the equivalence principle.

        P * ae_x = sum_{t=0}^{T-1} v^t * _tp_x * E[claim(entry_age + t)]

        where:
            ae_x = sum_{t=0}^{T-1} v^t * _tp_x       (annuity-due factor)
            v   = 1 / (1 + i)                          (discount factor)
            _tp_x = prod_{k=0}^{t-1} (1 - q_{x+k})   (survival probability)

        The level gross premium adds expense and profit loadings:
            P_gross = P_net / (1 - expense - profit)

        Args:
            entry_age: Age at policy inception.
            sex: "M" or "F".
            occ_class: Occupational risk class 1-4.
            insured_daily: Daily benefit (EUR).
            gross_monthly: Gross monthly income (EUR).
            net_monthly: Net monthly income (EUR).
            benefit_period_years: Maximum KTG benefit period per episode (years).
            max_age: Policy expiry age.
            expense_loading: Expense loading (fraction of gross premium).
            profit_loading: Profit loading (fraction of gross premium).

        Returns:
            Level annual gross premium (EUR/year).
        """
        i = self._reserve_rate
        v = 1.0 / (1.0 + i)
        years = max_age - entry_age
        if years <= 0:
            return 0.0

        pv_benefits = 0.0
        annuity_factor = 0.0
        tpx = 1.0  # survival probability to time t

        for t in range(years):
            current_age = entry_age + t
            discount = v**t
            pv_benefits += (
                discount
                * tpx
                * self.expected_annual_claim(
                    current_age,
                    sex,
                    occ_class,
                    insured_daily,
                    gross_monthly,
                    net_monthly,
                    **kwargs,
                )
            )
            annuity_factor += discount * tpx
            qx = _mortality_qx(current_age)
            tpx *= 1.0 - qx

        if annuity_factor <= 0:
            return 0.0

        net = pv_benefits / annuity_factor
        loading = 1.0 - expense_loading - profit_loading
        return net / max(loading, 1e-9)

    # ------------------------------------------------------------------
    # Prospective reserve
    # ------------------------------------------------------------------

    def prospective_reserve(
        self,
        entry_age: int,
        current_age: int,
        sex: str,
        occ_class: int,
        level_prem: float,
        insured_daily: float,
        gross_monthly: float,
        net_monthly: float | None = None,
        benefit_period_years: int = 2,
        max_age: int = 67,
        **kwargs: Any,
    ) -> float:
        """Prospective reserve at age *current_age*.

        V_t = PV(future benefits | age=current_age)
            - PV(future premiums | age=current_age)

        V_0 = 0 by the equivalence principle (up to rounding).

        Args:
            entry_age: Age at policy inception (used to verify t >= 0).
            current_age: Current age at which to compute reserve.
            sex: "M" or "F".
            occ_class: Occupational risk class 1-4.
            level_prem: Level annual gross premium (EUR/year).
            insured_daily: Daily benefit (EUR).
            gross_monthly: Gross monthly income (EUR).
            net_monthly: Net monthly income (EUR).
            benefit_period_years: Maximum benefit period per episode (years).
            max_age: Policy expiry age.

        Returns:
            Reserve V_t (EUR). Positive = liability; 0 at entry.
        """
        if current_age >= max_age:
            return 0.0
        i = self._reserve_rate
        v = 1.0 / (1.0 + i)
        years_remaining = max_age - current_age

        pv_benefits = 0.0
        pv_premiums = 0.0
        tpx = 1.0

        for t in range(years_remaining):
            age_t = current_age + t
            discount = v**t
            pv_benefits += (
                discount
                * tpx
                * self.expected_annual_claim(
                    age_t, sex, occ_class, insured_daily, gross_monthly, net_monthly, **kwargs
                )
            )
            pv_premiums += discount * tpx * level_prem
            qx = _mortality_qx(age_t)
            tpx *= 1.0 - qx

        return pv_benefits - pv_premiums

    def reserve_profile(
        self,
        entry_age: int,
        sex: str,
        occ_class: int,
        insured_daily: float,
        gross_monthly: float,
        net_monthly: float | None = None,
        benefit_period_years: int = 2,
        max_age: int = 67,
        expense_loading: float = 0.20,
        profit_loading: float = 0.05,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """Reserve profile from entry_age to max_age.

        Returns a DataFrame with columns:
            ``age``, ``reserve``, ``net_premium``, ``gross_premium``.
        """
        lp = self.level_premium(
            entry_age,
            sex,
            occ_class,
            insured_daily,
            gross_monthly,
            net_monthly,
            benefit_period_years,
            max_age,
            expense_loading,
            profit_loading,
            **kwargs,
        )
        rows = []
        for age in range(entry_age, max_age + 1):
            reserve = self.prospective_reserve(
                entry_age,
                age,
                sex,
                occ_class,
                lp,
                insured_daily,
                gross_monthly,
                net_monthly,
                benefit_period_years,
                max_age,
                **kwargs,
            )
            net = self.net_premium(
                age, sex, occ_class, insured_daily, gross_monthly, net_monthly, **kwargs
            )
            gross = self.gross_premium(
                age,
                sex,
                occ_class,
                insured_daily,
                gross_monthly,
                net_monthly,
                expense_loading,
                profit_loading,
                **kwargs,
            )
            rows.append(
                {"age": age, "reserve": reserve, "net_premium": net, "gross_premium": gross}
            )
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Pricing grid
    # ------------------------------------------------------------------

    def pricing_dataframe(
        self,
        ages: list[int],
        sexes: list[str],
        occ_classes: list[int],
        insured_daily: float,
        gross_monthly: float,
        net_monthly: float | None = None,
        expense_loading: float = 0.20,
        profit_loading: float = 0.05,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """Grid of net/gross premiums for all age x sex x occ_class combinations.

        Returns DataFrame with columns:
            ``age``, ``sex``, ``occ_class``, ``net_premium``, ``gross_premium``,
            ``expected_claim``, ``krankengeld_daily``, ``ktg_gap_daily``.
        """
        kg = self.krankengeld_daily(gross_monthly, net_monthly)
        gap = self.ktg_benefit_above_krankengeld(insured_daily, gross_monthly, net_monthly)
        rows = []
        for age in ages:
            for sex in sexes:
                for occ in occ_classes:
                    exp_claim = self.expected_annual_claim(
                        age, sex, occ, insured_daily, gross_monthly, net_monthly, **kwargs
                    )
                    net = self.net_premium(
                        age, sex, occ, insured_daily, gross_monthly, net_monthly, **kwargs
                    )
                    gross = self.gross_premium(
                        age,
                        sex,
                        occ,
                        insured_daily,
                        gross_monthly,
                        net_monthly,
                        expense_loading,
                        profit_loading,
                        **kwargs,
                    )
                    rows.append(
                        {
                            "age": age,
                            "sex": sex,
                            "occ_class": occ,
                            "expected_claim": round(exp_claim, 2),
                            "net_premium": round(net, 2),
                            "gross_premium": round(gross, 2),
                            "krankengeld_daily": round(kg, 2),
                            "ktg_gap_daily": round(gap, 2),
                        }
                    )
        return pd.DataFrame(rows)
