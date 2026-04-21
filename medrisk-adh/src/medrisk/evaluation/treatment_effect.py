"""Treatment effect estimation via inverse propensity weighting (IPW).

Estimates the Average Treatment Effect (ATE) of a binary treatment
(e.g., medication compliance) on an outcome (e.g., work disability).
Uses IPW with propensity scores from logistic regression.

Based on Hernan & Robins (2020) "Causal Inference: What If" and
the doubly robust estimator of Chernozhukov et al. (2018).

Usage:
    result = estimate_ate(X, treatment, outcome)
    print(f"ATE = {result['ate']:.3f} ({result['ci_lower']:.3f}, {result['ci_upper']:.3f})")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression

logger = logging.getLogger(__name__)


@dataclass
class ATEResult:
    """Result of average treatment effect estimation."""

    ate: float
    ci_lower: float
    ci_upper: float
    se: float
    treated_mean: float
    control_mean: float
    n_treated: int
    n_control: int
    propensity_mean: float


def estimate_ate(
    X: np.ndarray,
    treatment: np.ndarray,
    outcome: np.ndarray,
    n_bootstrap: int = 200,
    clip_propensity: float = 0.05,
    seed: int = 42,
) -> ATEResult:
    """Estimate ATE using inverse propensity weighting.

    Args:
        X: Covariates (confounders), shape (n, p).
        treatment: Binary treatment indicator (0/1).
        outcome: Continuous or binary outcome.
        n_bootstrap: Number of bootstrap samples for CI.
        clip_propensity: Min/max propensity score to avoid extreme weights.
        seed: Random seed.

    Returns:
        ATEResult with ATE, 95% CI, and descriptive statistics.
    """
    rng = np.random.RandomState(seed)
    treatment = np.asarray(treatment, dtype=int)
    outcome = np.asarray(outcome, dtype=float)
    X = np.asarray(X, dtype=float)

    n = len(outcome)
    n_treated = treatment.sum()
    n_control = n - n_treated

    # Fit propensity score model
    ps_model = LogisticRegression(max_iter=500, random_state=seed)
    ps_model.fit(X, treatment)
    propensity = ps_model.predict_proba(X)[:, 1]
    propensity = np.clip(propensity, clip_propensity, 1 - clip_propensity)

    # IPW estimator: ATE = E[Y*T/e(X)] - E[Y*(1-T)/(1-e(X))]
    def _ipw_ate(idx: np.ndarray) -> float:
        t = treatment[idx]
        y = outcome[idx]
        e = propensity[idx]
        treated_term = np.mean(y * t / e)
        control_term = np.mean(y * (1 - t) / (1 - e))
        return treated_term - control_term

    ate = _ipw_ate(np.arange(n))

    # Bootstrap CI
    boot_ates = []
    for _ in range(n_bootstrap):
        idx = rng.choice(n, size=n, replace=True)
        boot_ates.append(_ipw_ate(idx))

    se = np.std(boot_ates, ddof=1)
    ci_lower = np.percentile(boot_ates, 2.5)
    ci_upper = np.percentile(boot_ates, 97.5)

    logger.info(
        "ATE = %.4f (95%% CI: %.4f, %.4f), n_treated=%d, n_control=%d",
        ate,
        ci_lower,
        ci_upper,
        n_treated,
        n_control,
    )

    return ATEResult(
        ate=ate,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        se=se,
        treated_mean=outcome[treatment == 1].mean(),
        control_mean=outcome[treatment == 0].mean(),
        n_treated=int(n_treated),
        n_control=int(n_control),
        propensity_mean=float(propensity.mean()),
    )
