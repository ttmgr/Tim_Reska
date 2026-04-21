"""Classical actuarial methods: aggregate claims, IBNR reserving.

Aggregate claims (compound distribution):
    S = X_1 + X_2 + ... + X_N
    N ~ NegBin(r, p)  [Panjer (a,b,0) class]
    X_i ~ discretised severity distribution

Panjer recursion (for (a,b,0) class):
    g_0 = P_N(0)
    g_k = (1/k) * sum_{j=1}^{k} (a + b*j/k) * p_j * g_{k-j}    k >= 1

where p_j = P(X = j*h) are severity PMF probabilities on a grid of step h.

NegBin parameters:
    a = beta/(1+beta),  b = (r-1)*beta/(1+beta)
    where mu = r*beta,  variance = mu + mu^2/r = mu(1+beta)

Chain Ladder / Bornhuetter-Ferguson:
    Triangle: rows = origin years, columns = development years (cumulative).
    Missing entries (upper right) are the IBNR reserves.

References:
    - Panjer HH (1981). ASTIN Bulletin 12(1):22-26.
    - England PD & Verrall RJ (2002). British Actuarial Journal 8(3):443-544.
    - Mack T (1993). ASTIN Bulletin 23(2):213-225.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Chain-Ladder
# ---------------------------------------------------------------------------


def chain_ladder(triangle: np.ndarray) -> dict[str, Any]:
    """Chain-Ladder IBNR reserve estimate.

    Args:
        triangle: 2-D array of shape (n_origins, n_dev_years).
                  Lower-right entries should be NaN (unreported).
                  Cumulative losses expected (convert incurred -> cumulative
                  before calling).

    Returns:
        dict with keys:
            ``factors``    -- development factors f_1, ..., f_{n-1}
            ``ultimates``  -- estimated ultimate loss for each origin year
            ``reserves``   -- IBNR reserve = ultimate - latest diagonal
            ``triangle``   -- completed triangle (NaN filled)
    """
    tri = np.array(triangle, dtype=float)
    n_orig, n_dev = tri.shape

    # Development factors: f_k = sum_i C[i,k+1] / sum_i C[i,k]  (weighted average)
    factors = np.ones(n_dev - 1)
    for k in range(n_dev - 1):
        col_k = tri[:, k]
        col_k1 = tri[:, k + 1]
        mask = ~(np.isnan(col_k) | np.isnan(col_k1))
        if mask.sum() > 0:
            factors[k] = col_k1[mask].sum() / col_k[mask].sum()

    # Latest diagonal (most recent cumulative for each origin year)
    latest = np.array(
        [
            tri[i, ~np.isnan(tri[i, :])][-1] if (~np.isnan(tri[i, :])).any() else np.nan
            for i in range(n_orig)
        ]
    )
    latest_col = np.array(
        [
            int(np.where(~np.isnan(tri[i, :]))[0][-1]) if (~np.isnan(tri[i, :])).any() else -1
            for i in range(n_orig)
        ]
    )

    # Project to ultimate
    ultimates = latest.copy()
    for i in range(n_orig):
        col = latest_col[i]
        if col < 0:
            continue
        for k in range(col, n_dev - 1):
            ultimates[i] *= factors[k]

    reserves = ultimates - latest

    # Fill completed triangle
    tri_completed = tri.copy()
    for i in range(n_orig):
        col = latest_col[i]
        if col < 0:
            continue
        cumulative = latest[i]
        for k in range(col + 1, n_dev):
            cumulative *= factors[k - 1]
            tri_completed[i, k] = cumulative

    return {
        "factors": factors,
        "ultimates": ultimates,
        "reserves": np.where(np.isnan(reserves), 0.0, reserves),
        "triangle": tri_completed,
    }


def bornhuetter_ferguson(triangle: np.ndarray, prior_ultimates: np.ndarray) -> dict[str, Any]:
    """Bornhuetter-Ferguson IBNR reserve estimate.

    BF mixes reported losses with prior (a priori) ultimates:
        BF_ultimate_i = reported_i + prior_i * (1 - 1/CDF_i)

    where CDF_i is the cumulative development factor to ultimate for origin year i.

    Args:
        triangle: Cumulative loss triangle (NaN = unreported).
        prior_ultimates: A priori ultimate estimate for each origin year.

    Returns:
        dict with same keys as ``chain_ladder`` plus:
            ``cl_ultimates``  -- chain-ladder ultimates (for comparison)
            ``bf_ultimates``  -- BF ultimates
            ``bf_reserves``   -- BF IBNR reserves
    """
    cl_result = chain_ladder(triangle)
    cl_factors = cl_result["factors"]
    latest = np.array(
        [
            triangle[i][~np.isnan(np.array(triangle[i], dtype=float))][-1]
            if any(not np.isnan(x) for x in triangle[i])
            else np.nan
            for i in range(len(triangle))
        ],
        dtype=float,
    )
    latest_col = np.array(
        [
            int(np.where(~np.isnan(np.array(triangle[i], dtype=float)))[0][-1])
            if any(not np.isnan(x) for x in triangle[i])
            else -1
            for i in range(len(triangle))
        ]
    )

    n_dev = len(cl_factors) + 1
    prior = np.asarray(prior_ultimates, dtype=float)
    bf_ultimates = np.zeros(len(triangle))
    for i, (lat, col) in enumerate(zip(latest, latest_col, strict=False)):
        if col < 0 or np.isnan(lat):
            bf_ultimates[i] = prior[i]
            continue
        # CDF from col to ultimate = product of remaining factors
        cdf = 1.0
        for k in range(col, n_dev - 1):
            cdf *= cl_factors[k]
        expected_unreported = prior[i] * (1.0 - 1.0 / max(cdf, 1e-9))
        bf_ultimates[i] = lat + expected_unreported

    bf_reserves = bf_ultimates - np.where(np.isnan(latest), 0.0, latest)

    return {
        **cl_result,
        "cl_ultimates": cl_result["ultimates"],
        "bf_ultimates": bf_ultimates,
        "bf_reserves": bf_reserves,
    }


# ---------------------------------------------------------------------------
# Aggregate Claims Model (Panjer recursion)
# ---------------------------------------------------------------------------


@dataclass
class AggregateClaimsModel:
    """Compound frequency-severity model for aggregate sick-leave claims.

    Attributes
    ----------
    freq_distribution : str
        Frequency distribution family. Only ``"negbin"`` is currently supported.
    freq_params : dict
        Parameters for the frequency distribution:
            - ``"negbin"``: {"r": float, "beta": float}
              where mu = r*beta, Var = mu*(1+beta)
    severity_pmf : np.ndarray or None
        Discretised severity PMF on grid [0, h, 2h, ..., m*h].
        Set by calling ``discretise_severity()`` or directly.
    h : float
        Severity grid step size (default 1.0 = one day).
    """

    freq_distribution: str = "negbin"
    freq_params: dict[str, float] = field(default_factory=lambda: {"r": 5.0, "beta": 2.0})
    severity_pmf: np.ndarray | None = None
    h: float = 1.0
    _aggregate_pmf: np.ndarray | None = field(default=None, init=False, repr=False)

    # ------------------------------------------------------------------
    # Severity discretisation
    # ------------------------------------------------------------------

    def discretise_severity(
        self,
        dist: Any,  # scipy.stats frozen distribution
        h: float = 1.0,
        m: int = 500,
    ) -> np.ndarray:
        """Discretise a continuous severity distribution via method of rounding.

        p_0 = F(h/2)
        p_k = F((k+0.5)h) - F((k-0.5)h)  for k = 1, ..., m-1
        p_m = 1 - F((m-0.5)h)

        Args:
            dist: scipy.stats frozen distribution (e.g. ``scipy.stats.weibull_min(c, scale=lam)``).
            h: Grid step size.
            m: Number of grid points (grid = {0, h, 2h, ..., m*h}).

        Returns:
            PMF array of length m+1.
        """
        self.h = h
        pmf = np.zeros(m + 1)
        pmf[0] = dist.cdf(0.5 * h)
        for k in range(1, m):
            pmf[k] = dist.cdf((k + 0.5) * h) - dist.cdf((k - 0.5) * h)
        pmf[m] = 1.0 - dist.cdf((m - 0.5) * h)
        # Normalise to 1 to remove numerical error
        pmf /= pmf.sum()
        self.severity_pmf = pmf
        self._aggregate_pmf = None  # invalidate cache
        return pmf

    # ------------------------------------------------------------------
    # Panjer recursion
    # ------------------------------------------------------------------

    def panjer_recursion(
        self,
        freq_params: dict[str, float] | None = None,
        severity_pmf: np.ndarray | None = None,
    ) -> np.ndarray:
        """Compute aggregate PMF via Panjer recursion.

        For NegBin(r, beta):
            a = beta / (1 + beta)
            b = (r - 1) * beta / (1 + beta)

        Recursion:
            g_0 = P_N(0) = (1/(1+beta))^r
            g_k = (1/k) * sum_{j=1}^{k} (a + b*j/k) * p_j * g_{k-j}

        Args:
            freq_params: Override instance freq_params if provided.
            severity_pmf: Override instance severity_pmf if provided.

        Returns:
            Aggregate PMF array (same length as severity_pmf).
        """
        if self._aggregate_pmf is not None and freq_params is None and severity_pmf is None:
            return self._aggregate_pmf

        fp = freq_params if freq_params is not None else self.freq_params
        sp = severity_pmf if severity_pmf is not None else self.severity_pmf
        if sp is None:
            raise ValueError("severity_pmf must be set before calling panjer_recursion.")

        if self.freq_distribution == "negbin":
            r = fp["r"]
            beta = fp["beta"]
            a = beta / (1.0 + beta)
            b = (r - 1.0) * beta / (1.0 + beta)
            # g_0 = P(N=0) = (1/(1+beta))^r
            g0 = (1.0 / (1.0 + beta)) ** r
        else:
            raise NotImplementedError(
                f"Panjer recursion not implemented for '{self.freq_distribution}'."
            )

        m = len(sp)
        g = np.zeros(m)
        g[0] = g0
        for k in range(1, m):
            s = 0.0
            for j in range(1, k + 1):
                if j < m:
                    s += (a + b * j / k) * sp[j] * g[k - j]
            g[k] = s
        # Normalise (small rounding errors accumulate)
        total = g.sum()
        if total > 0:
            g /= total

        if freq_params is None and severity_pmf is None:
            self._aggregate_pmf = g
        return g

    # ------------------------------------------------------------------
    # Summary statistics
    # ------------------------------------------------------------------

    def expected_aggregate(self) -> float:
        """E[S] = E[N] * E[X]."""
        fp = self.freq_params
        if self.freq_distribution == "negbin":
            en = fp["r"] * fp["beta"]
        else:
            raise NotImplementedError
        sp = self.severity_pmf
        if sp is None:
            raise ValueError("severity_pmf not set.")
        m = len(sp)
        ex = float(np.sum(np.arange(m) * self.h * sp))
        return en * ex

    def var(self, alpha: float = 0.99) -> float:
        """Value-at-Risk at level alpha (quantile of aggregate distribution).

        Args:
            alpha: Confidence level in (0, 1).

        Returns:
            VaR_alpha(S) in the same units as severity_pmf * h.
        """
        g = self.panjer_recursion()
        cumulative = np.cumsum(g)
        idx = int(np.searchsorted(cumulative, alpha))
        return idx * self.h

    def cte(self, alpha: float = 0.99) -> float:
        """Conditional Tail Expectation (CVaR) at level alpha.

        CTE_alpha = E[S | S > VaR_alpha(S)]
        """
        g = self.panjer_recursion()
        m = len(g)
        var_idx = int(np.searchsorted(np.cumsum(g), alpha))
        tail_values = np.arange(var_idx + 1, m) * self.h
        tail_probs = g[var_idx + 1 :]
        tail_prob_total = tail_probs.sum()
        if tail_prob_total <= 0:
            return var_idx * self.h
        return float(np.sum(tail_values * tail_probs) / tail_prob_total)

    def full_distribution(self) -> pd.DataFrame:
        """Return full aggregate PMF as a DataFrame.

        Columns: ``claim_amount``, ``pmf``, ``cdf``.
        """
        g = self.panjer_recursion()
        m = len(g)
        amounts = np.arange(m) * self.h
        return pd.DataFrame(
            {
                "claim_amount": amounts,
                "pmf": g,
                "cdf": np.cumsum(g),
            }
        )
