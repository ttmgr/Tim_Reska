"""Sick-leave frequency and duration models for KTG pricing.

Frequency model:
    Y ~ NegBin(mu, alpha)
    log(mu) = beta0 + beta1*age + beta2*(sex=="M") + beta3*MRS + beta4*occ_risk_factor

Duration model (Weibull AFT):
    log(T) = mu + sigma*epsilon,  epsilon ~ Gumbel(0,1)
    => T ~ Weibull with scale lambda = exp(mu),  shape k = 1/sigma
    S(t) = exp(-(t/lambda)^k)
    h(t) = (k/lambda) * (t/lambda)^(k-1)
    E[T] = lambda * Gamma(1 + sigma)  [since k = 1/sigma -> Gamma(1 + 1/k) = Gamma(1 + sigma)]

References:
    - BAuA sick-leave statistics 2022
    - Techniker Krankenkasse Gesundheitsreport 2023
    - Cameron & Trivedi (1998) Regression Analysis of Count Data
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np

from ._config import load_icd_sick_leave, load_insurance_config


class NegBinomFrequencyModel:
    """Negative Binomial sick-leave frequency model.

    Expected episodes per year:
        log(mu) = beta0 + beta1*age + beta2*male_indicator
                 + beta3*morbidity_risk_score + beta4*log(occ_risk_factor)

    Regression coefficients are calibrated to GKV reference table entries.
    The NegBin overdispersion parameter alpha is loaded from insurance_de.yml.

    Parameters
    ----------
    config_dir : Path, optional
        Directory containing insurance_de.yml. Defaults to repo configs/.
    """

    def __init__(self, config_dir: Path | None = None) -> None:
        cfg = load_insurance_config(config_dir)
        self._alpha: float = cfg["actuarial"]["nb_overdispersion_alpha"]
        # Reference table: list of [age_mid, sex, episodes/yr, sick_days/yr]
        self._ref_table: list[list] = cfg["gkv_reference_table"]

        # Default OLS-calibrated coefficients (population baseline, log scale)
        # Derived by regressing log(episodes) on age/sex from GKV reference table
        self._beta: dict[str, float] = {
            "intercept": 0.30,
            "age": -0.004,
            "male": -0.08,
            "mrs": 0.12,
            "log_occ_rf": 0.18,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit(
        self,
        ages: np.ndarray,
        is_male: np.ndarray,
        mrs_values: np.ndarray,
        occ_risk_factors: np.ndarray,
        y: np.ndarray,
    ) -> None:
        """Fit regression coefficients via statsmodels NegBin MLE.

        Falls back gracefully if statsmodels is not installed.
        """
        try:
            import statsmodels.api as sm

            X = _build_design(ages, is_male, mrs_values, occ_risk_factors)
            model = sm.NegativeBinomial(y, X)
            result = model.fit(disp=False)
            b = result.params
            keys = ["intercept", "age", "male", "mrs", "log_occ_rf"]
            self._beta = dict(zip(keys, b, strict=False))
            self._alpha = result.params.get("alpha", self._alpha)
        except ImportError:
            pass  # keep default coefficients

    def expected_frequency(
        self,
        age: int,
        sex: str,
        mrs: float = 1.0,
        occ_class: int = 1,
    ) -> float:
        """Expected sick-leave episodes per year.

        Args:
            age: Age in years.
            sex: "M" or "F".
            mrs: Morbidity risk score (multiplicative; use 1.0 for population).
            occ_class: Occupational risk class 1-4.
        """
        occ_risk_factor = {1: 1.00, 2: 1.25, 3: 1.60, 4: 2.10}.get(occ_class, 1.00)
        male = 1.0 if sex.upper().startswith("M") else 0.0
        log_mu = (
            self._beta["intercept"]
            + self._beta["age"] * age
            + self._beta["male"] * male
            + self._beta["mrs"] * math.log(max(mrs, 1e-9))
            + self._beta["log_occ_rf"] * math.log(max(occ_risk_factor, 1e-9))
        )
        return math.exp(log_mu)

    def gkv_reference_frequency(self, age: int, sex: str) -> float:
        """Interpolated episodes/year from GKV reference table (linear)."""
        return _interpolate_ref(self._ref_table, age, sex, col=2)

    def gkv_reference_sick_days(self, age: int, sex: str) -> float:
        """Interpolated sick days/year from GKV reference table (linear)."""
        return _interpolate_ref(self._ref_table, age, sex, col=3)

    def pmf(self, k: int, mu: float) -> float:
        """Negative Binomial PMF P(Y=k) with mean mu and overdispersion alpha.

        NegBin(r, p) parameterisation: r = 1/alpha, p = 1/(1+alpha*mu)
        """
        from scipy.stats import nbinom  # type: ignore[import-untyped]

        r = 1.0 / self._alpha
        p = 1.0 / (1.0 + self._alpha * mu)
        return float(nbinom.pmf(k, r, p))

    def mean_variance(self, mu: float) -> tuple[float, float]:
        """Return (mean, variance) = (mu, mu + alpha*mu^2) for NegBin."""
        return mu, mu + self._alpha * mu**2


# ---------------------------------------------------------------------------
# Weibull AFT Duration Model
# ---------------------------------------------------------------------------


class WeibullDurationModel:
    """Weibull Accelerated Failure Time model for sick-leave episode duration.

    Parameterisation:
        log(T) = mu + sigma*epsilon,  epsilon ~ Gumbel(0,1)
        T ~ Weibull(scale=lambda, shape=k)  where lambda=exp(mu), k=1/sigma

    Mean duration:
        E[T] = lambda * Gamma(1 + 1/k) = exp(mu) * Gamma(1 + sigma)

    Survival:
        S(t; chapter) = exp(-(t / lambda)^k)

    Hazard:
        h(t; chapter) = (k / lambda) * (t / lambda)^(k-1)

    Expected days above threshold d:
        E[max(T-d, 0)] = integral_d^inf S(t) dt
    using the complementary incomplete gamma function.
    """

    def __init__(self, config_dir: Path | None = None) -> None:
        cfg = load_icd_sick_leave(config_dir)
        self._chapters: dict[str, dict[str, Any]] = cfg["chapters"]
        self._chapter_map: dict[str, str] = cfg["icd_chapter_map"]

    # ------------------------------------------------------------------
    # ICD-10 -> chapter
    # ------------------------------------------------------------------

    def icd_to_chapter(self, icd10: str) -> str:
        """Map an ICD-10 code to the configured chapter key.

        Uses the first character of the code for the lookup.
        Returns "_other" if no match.
        """
        code = icd10.strip().upper().replace(".", "")
        if not code:
            return "_other"
        first = code[0]
        return self._chapter_map.get(first, "_other")

    # ------------------------------------------------------------------
    # Weibull helpers
    # ------------------------------------------------------------------

    def _params(self, icd_chapter: str) -> tuple[float, float]:
        """Return (scale lambda, shape k) for the given chapter."""
        ch = self._chapters.get(icd_chapter, self._chapters["_other"])
        mu = ch["mu"]
        sigma = ch["sigma"]
        lam = math.exp(mu)  # scale
        k = 1.0 / sigma  # shape
        return lam, k

    def expected_duration(self, icd_chapter: str, mrs: float = 1.0) -> float:
        """Expected episode duration in days, optionally scaled by MRS.

        E[T] = lambda * Gamma(1 + 1/k) * mrs
        """
        lam, k = self._params(icd_chapter)
        mean = lam * math.gamma(1.0 + 1.0 / k)
        return mean * max(mrs, 0.0)

    def survival(self, t: float, icd_chapter: str) -> float:
        """Survival function S(t) = exp(-(t/lambda)^k)."""
        if t <= 0.0:
            return 1.0
        lam, k = self._params(icd_chapter)
        return math.exp(-((t / lam) ** k))

    def hazard(self, t: float, icd_chapter: str) -> float:
        """Hazard function h(t) = (k/lambda) * (t/lambda)^(k-1)."""
        if t <= 0.0:
            return 0.0
        lam, k = self._params(icd_chapter)
        return (k / lam) * ((t / lam) ** (k - 1.0))

    def expected_days_above_threshold(self, threshold_days: float, icd_chapter: str) -> float:
        """E[max(T - threshold, 0)] = integral_{threshold}^{inf} S(t) dt.

        Computed via the upper incomplete gamma function:
            integral_d^inf exp(-(t/lambda)^k) dt = (lambda/k) * Gamma(1/k, (d/lambda)^k)
        where Gamma(a, x) is the upper incomplete gamma function.

        Args:
            threshold_days: Minimum days before counting (e.g. Karenzzeit + 42).
            icd_chapter: ICD chapter key.

        Returns:
            Expected benefit days (>= 0).
        """
        if threshold_days <= 0.0:
            lam, k = self._params(icd_chapter)
            return lam * math.gamma(1.0 + 1.0 / k)

        lam, k = self._params(icd_chapter)
        a = 1.0 / k
        x = (threshold_days / lam) ** k  # lower limit of upper incomplete gamma

        # scipy.special.gammaincc(a, x) = Gamma(a, x) / Gamma(a)  (regularised)
        from scipy.special import gammaincc  # type: ignore[import-untyped]

        upper_reg = float(gammaincc(a, x))
        # Gamma(a, x) = upper_reg * Gamma(a)
        result = (lam / k) * upper_reg * math.gamma(a)
        return max(result, 0.0)

    def simulate_episodes(
        self,
        n: int,
        icd_chapter: str,
        mrs: float = 1.0,
        rng: np.random.Generator | None = None,
    ) -> np.ndarray:
        """Simulate n episode durations (days) from Weibull distribution.

        Args:
            n: Number of samples.
            icd_chapter: ICD chapter key.
            mrs: Morbidity risk scale factor applied to the scale parameter lambda.
            rng: NumPy random generator (created if None).

        Returns:
            Array of shape (n,) with simulated durations in days.
        """
        if rng is None:
            rng = np.random.default_rng()
        lam, k = self._params(icd_chapter)
        lam = lam * max(mrs, 1e-9)
        # Weibull: T = lambda * (-log(U))^(1/k),  U ~ Uniform(0,1)
        u = rng.uniform(0.0, 1.0, size=n)
        return lam * (-np.log(u + 1e-300)) ** (1.0 / k)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _interpolate_ref(table: list[list], age: int, sex: str, col: int) -> float:
    """Linear interpolation over the GKV reference table for a given age/sex."""
    sex_key = sex.upper()[:1]
    rows = [(row[0], row[col]) for row in table if str(row[1]) == sex_key]
    if not rows:
        rows = [(row[0], row[col]) for row in table if str(row[1]).upper() == "M"]
    rows.sort(key=lambda r: r[0])
    if age <= rows[0][0]:
        return float(rows[0][1])
    if age >= rows[-1][0]:
        return float(rows[-1][1])
    for i in range(len(rows) - 1):
        a0, v0 = rows[i]
        a1, v1 = rows[i + 1]
        if a0 <= age <= a1:
            frac = (age - a0) / (a1 - a0)
            return float(v0 + frac * (v1 - v0))
    return float(rows[-1][1])


def _build_design(
    ages: np.ndarray,
    is_male: np.ndarray,
    mrs: np.ndarray,
    occ_rf: np.ndarray,
) -> np.ndarray:
    """Build design matrix [intercept, age, male, log(mrs), log(occ_rf)]."""
    n = len(ages)
    X = np.column_stack(
        [
            np.ones(n),
            ages.astype(float),
            is_male.astype(float),
            np.log(np.maximum(mrs, 1e-9)),
            np.log(np.maximum(occ_rf, 1e-9)),
        ]
    )
    return X
