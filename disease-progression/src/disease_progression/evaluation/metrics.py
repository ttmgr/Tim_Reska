"""
disease_progression.evaluation.metrics - Survival analysis evaluation metrics.

Provides a comprehensive suite of discrimination and calibration metrics
for survival / competing-risk models:

    **Discrimination**
    - Harrell's concordance index (C-index)
    - Uno's concordance index (IPCW-weighted, more robust under censoring)
    - Time-dependent AUC (cumulative/dynamic via inverse-probability
      weighting)

    **Calibration**
    - Integrated Brier score (IBS) over a time grid
    - CIF calibration: observed vs. predicted cumulative incidence in
      decile groups (Hosmer-Lemeshow style)

All functions accept numpy arrays and return plain floats or DataFrames
for easy integration into evaluation pipelines and model cards.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ===================================================================
# Concordance index (Harrell's)
# ===================================================================

def concordance_index(
    event_times: np.ndarray,
    predicted_risk: np.ndarray,
    event_observed: np.ndarray,
) -> float:
    """Compute Harrell's concordance index.

    The C-index measures the probability that, for a randomly selected
    pair of subjects where one has a shorter event time, the model
    assigns a higher risk score to that subject.

    Parameters
    ----------
    event_times : ndarray (n,)
        Observed follow-up times.
    predicted_risk : ndarray (n,)
        Model-predicted risk scores (higher = more risky).
    event_observed : ndarray (n,)
        Binary event indicator (1 = event, 0 = censored).

    Returns
    -------
    float
        Concordance index in [0, 1].  0.5 = random, 1.0 = perfect.
    """
    n = len(event_times)
    concordant = 0
    discordant = 0
    tied_risk = 0
    comparable = 0

    for i in range(n):
        if not event_observed[i]:
            continue
        for j in range(n):
            if i == j:
                continue
            if event_times[i] >= event_times[j] and event_observed[j]:
                continue  # Not a valid pair
            if event_times[i] < event_times[j] or (event_times[j] >= event_times[i] and not event_observed[j]):
                comparable += 1
                if predicted_risk[i] > predicted_risk[j]:
                    concordant += 1
                elif predicted_risk[i] < predicted_risk[j]:
                    discordant += 1
                else:
                    tied_risk += 1

    if comparable == 0:
        logger.warning("No comparable pairs for C-index computation.")
        return 0.5

    return (concordant + 0.5 * tied_risk) / comparable


def concordance_index_lifelines(
    event_times: np.ndarray,
    predicted_risk: np.ndarray,
    event_observed: np.ndarray,
) -> float:
    """C-index via lifelines (more efficient for large datasets).

    Falls back to the manual implementation if lifelines is unavailable.
    """
    try:
        from lifelines.utils import concordance_index as _ci
        return _ci(event_times, -predicted_risk, event_observed)
    except ImportError:
        return concordance_index(event_times, predicted_risk, event_observed)


def concordance_index_ipcw(
    event_times_train: np.ndarray,
    event_observed_train: np.ndarray,
    event_times_test: np.ndarray,
    event_observed_test: np.ndarray,
    predicted_risk: np.ndarray,
    tau: Optional[float] = None,
) -> float:
    """Uno's IPCW concordance index.

    Weights concordant/discordant pairs by the inverse probability of
    censoring to correct for informative censoring bias.

    Uses sksurv if available, otherwise falls back to Harrell's.
    """
    try:
        from sksurv.metrics import concordance_index_ipcw as _ci_ipcw

        # sksurv expects structured arrays
        def _make_structured(t: np.ndarray, e: np.ndarray) -> np.ndarray:
            dt = np.dtype([("event", bool), ("time", float)])
            arr = np.empty(len(t), dtype=dt)
            arr["event"] = e.astype(bool)
            arr["time"] = t.astype(float)
            return arr

        train_y = _make_structured(event_times_train, event_observed_train)
        test_y = _make_structured(event_times_test, event_observed_test)

        if tau is None:
            tau = min(event_times_test[event_observed_test > 0].max(), event_times_train.max())

        c_idx, _, _, _, _ = _ci_ipcw(train_y, test_y, predicted_risk, tau=tau)
        return float(c_idx)
    except ImportError:
        logger.warning("sksurv not available; falling back to Harrell's C-index.")
        return concordance_index(event_times_test, predicted_risk, event_observed_test)


# ===================================================================
# Time-dependent AUC
# ===================================================================

def time_dependent_auc(
    event_times: np.ndarray,
    event_observed: np.ndarray,
    predicted_risk: np.ndarray,
    times: np.ndarray,
) -> pd.DataFrame:
    """Compute time-dependent AUC (cumulative/dynamic definition).

    At each evaluation time t, subjects are classified as:
    - Cases: experienced the event before or at t (T_i <= t, delta_i = 1)
    - Controls: event-free beyond t (T_i > t)

    The AUC is the probability that a randomly selected case has a
    higher predicted risk than a randomly selected control.

    Parameters
    ----------
    event_times : ndarray (n,)
    event_observed : ndarray (n,)
    predicted_risk : ndarray (n,)
        Higher values = higher predicted risk.
    times : ndarray (k,)
        Time points at which to evaluate AUC.

    Returns
    -------
    pd.DataFrame
        Columns: time, auc, n_cases, n_controls.
    """
    try:
        from sksurv.metrics import cumulative_dynamic_auc as _cdauc

        dt = np.dtype([("event", bool), ("time", float)])
        y = np.empty(len(event_times), dtype=dt)
        y["event"] = event_observed.astype(bool)
        y["time"] = event_times.astype(float)

        aucs, mean_auc = _cdauc(y, y, predicted_risk, times)
        results = []
        for t_val, auc_val in zip(times, aucs):
            n_cases = int(((event_times <= t_val) & (event_observed > 0)).sum())
            n_controls = int((event_times > t_val).sum())
            results.append({"time": t_val, "auc": float(auc_val), "n_cases": n_cases, "n_controls": n_controls})

        df = pd.DataFrame(results)
        df.attrs["mean_auc"] = float(mean_auc)
        return df

    except ImportError:
        logger.info("sksurv not available; computing AUC manually.")

    results: List[Dict[str, Any]] = []
    for t in times:
        cases = (event_times <= t) & (event_observed > 0)
        controls = event_times > t
        n_cases = int(cases.sum())
        n_controls = int(controls.sum())

        if n_cases == 0 or n_controls == 0:
            results.append({"time": t, "auc": np.nan, "n_cases": n_cases, "n_controls": n_controls})
            continue

        risk_cases = predicted_risk[cases]
        risk_controls = predicted_risk[controls]

        concordant = 0
        total = 0
        for rc in risk_cases:
            concordant += (rc > risk_controls).sum()
            concordant += 0.5 * (rc == risk_controls).sum()
            total += len(risk_controls)

        auc = concordant / total if total > 0 else 0.5
        results.append({"time": t, "auc": float(auc), "n_cases": n_cases, "n_controls": n_controls})

    return pd.DataFrame(results)


# ===================================================================
# Integrated Brier score
# ===================================================================

def brier_score(
    event_times: np.ndarray,
    event_observed: np.ndarray,
    predicted_survival: np.ndarray,
    eval_time: float,
) -> float:
    """Brier score at a single time point.

    BS(t) = (1/n) * sum_i [
        S(t|x_i)^2 * I(T_i <= t, delta_i=1) / G(T_i)
        + (1 - S(t|x_i))^2 * I(T_i > t) / G(t)
    ]

    where G is the Kaplan-Meier estimate of the censoring distribution.

    Parameters
    ----------
    event_times : (n,)
    event_observed : (n,)
    predicted_survival : (n,)
        Predicted S(t|x_i) at ``eval_time``.
    eval_time : float

    Returns
    -------
    float
    """
    n = len(event_times)

    # Estimate censoring distribution G(t) via reverse KM
    censor_times = event_times.copy()
    censor_events = 1 - event_observed  # Censoring is the "event" for G
    sorted_idx = np.argsort(censor_times)
    sorted_times = censor_times[sorted_idx]
    sorted_events = censor_events[sorted_idx]

    # KM for censoring
    g_values = np.ones(n)
    at_risk = n
    surv = 1.0
    km_times = []
    km_surv = []
    for i in range(n):
        if sorted_events[i]:
            surv *= (at_risk - 1) / at_risk
        km_times.append(sorted_times[i])
        km_surv.append(surv)
        at_risk -= 1

    km_times_arr = np.array(km_times)
    km_surv_arr = np.array(km_surv)

    def _get_G(t: float) -> float:
        idx = np.searchsorted(km_times_arr, t, side="right") - 1
        if idx < 0:
            return 1.0
        return max(km_surv_arr[idx], 1e-8)

    bs = 0.0
    for i in range(n):
        s_hat = predicted_survival[i]
        if event_times[i] <= eval_time and event_observed[i]:
            w = 1.0 / _get_G(event_times[i])
            bs += w * s_hat ** 2
        elif event_times[i] > eval_time:
            w = 1.0 / _get_G(eval_time)
            bs += w * (1 - s_hat) ** 2

    return bs / n


def integrated_brier_score(
    event_times: np.ndarray,
    event_observed: np.ndarray,
    predicted_survival_fn: np.ndarray,
    eval_times: np.ndarray,
) -> float:
    """Integrated Brier score over a time grid.

    IBS = (1 / (t_max - t_min)) * integral BS(t) dt

    Approximated via the trapezoidal rule over ``eval_times``.

    Parameters
    ----------
    event_times : (n,)
    event_observed : (n,)
    predicted_survival_fn : (n, len(eval_times))
        Predicted survival probabilities S(t|x_i) for each subject
        and each time in eval_times.
    eval_times : (k,)
        Ordered time points for evaluation.

    Returns
    -------
    float
        Integrated Brier score (lower is better).
    """
    bs_values = []
    for j, t in enumerate(eval_times):
        bs = brier_score(event_times, event_observed, predicted_survival_fn[:, j], t)
        bs_values.append(bs)

    bs_arr = np.array(bs_values)
    t_range = eval_times[-1] - eval_times[0]
    if t_range <= 0:
        return float(bs_arr.mean())

    # Trapezoidal integration
    ibs = float(np.trapz(bs_arr, eval_times) / t_range)
    return ibs


# ===================================================================
# CIF Calibration
# ===================================================================

def cif_calibration(
    event_times: np.ndarray,
    event_observed: np.ndarray,
    predicted_cif: np.ndarray,
    eval_time: float,
    n_groups: int = 10,
) -> pd.DataFrame:
    """Calibration assessment for cumulative incidence predictions.

    Splits subjects into ``n_groups`` by predicted CIF, then compares
    the predicted mean CIF in each group against the Kaplan-Meier-based
    observed incidence.

    Parameters
    ----------
    event_times : (n,)
    event_observed : (n,)
    predicted_cif : (n,)
        Predicted CIF at ``eval_time``.
    eval_time : float
    n_groups : int
        Number of calibration groups (deciles by default).

    Returns
    -------
    pd.DataFrame
        Columns: group, n, predicted_mean, observed_rate, diff, abs_diff.
    """
    n = len(event_times)
    # Assign groups based on predicted CIF quantiles
    try:
        groups = pd.qcut(predicted_cif, n_groups, labels=False, duplicates="drop")
    except ValueError:
        groups = pd.cut(predicted_cif, n_groups, labels=False)

    rows: List[Dict[str, Any]] = []
    for g in sorted(np.unique(groups)):
        mask = groups == g
        group_n = int(mask.sum())
        pred_mean = float(predicted_cif[mask].mean())

        # Observed: KM estimate of CIF at eval_time
        g_times = event_times[mask]
        g_events = event_observed[mask]

        # Simple observed rate: fraction who had event before eval_time
        observed = float(((g_times <= eval_time) & (g_events > 0)).sum() / max(group_n, 1))

        rows.append({
            "group": int(g),
            "n": group_n,
            "predicted_mean": pred_mean,
            "observed_rate": observed,
            "diff": pred_mean - observed,
            "abs_diff": abs(pred_mean - observed),
        })

    result = pd.DataFrame(rows)
    cal_error = float(result["abs_diff"].mean())
    result.attrs["mean_calibration_error"] = cal_error
    logger.info("CIF calibration at t=%.1f: mean |diff| = %.4f", eval_time, cal_error)
    return result


# ===================================================================
# Summary evaluation
# ===================================================================

def evaluate_survival_model(
    event_times: np.ndarray,
    event_observed: np.ndarray,
    predicted_risk: np.ndarray,
    predicted_survival_fn: Optional[np.ndarray] = None,
    eval_times: Optional[np.ndarray] = None,
    predicted_cif: Optional[np.ndarray] = None,
    cif_eval_time: Optional[float] = None,
) -> Dict[str, Any]:
    """Run a comprehensive evaluation suite and return a summary dict.

    Parameters
    ----------
    event_times : (n,)
    event_observed : (n,)
    predicted_risk : (n,)
    predicted_survival_fn : (n, k), optional
        Survival function evaluated at ``eval_times``.
    eval_times : (k,), optional
        Times for AUC and Brier score.
    predicted_cif : (n,), optional
        CIF at a single time for calibration.
    cif_eval_time : float, optional
        The time at which ``predicted_cif`` is evaluated.

    Returns
    -------
    dict
        Keys: c_index, td_auc (DataFrame), ibs, cif_calibration (DataFrame).
    """
    results: Dict[str, Any] = {}

    # C-index
    results["c_index"] = concordance_index(event_times, predicted_risk, event_observed)

    # Time-dependent AUC
    if eval_times is not None:
        td_auc_df = time_dependent_auc(event_times, event_observed, predicted_risk, eval_times)
        results["td_auc"] = td_auc_df
        results["mean_td_auc"] = float(td_auc_df["auc"].dropna().mean())

    # Integrated Brier score
    if predicted_survival_fn is not None and eval_times is not None:
        results["ibs"] = integrated_brier_score(
            event_times, event_observed, predicted_survival_fn, eval_times
        )

    # CIF calibration
    if predicted_cif is not None and cif_eval_time is not None:
        results["cif_calibration"] = cif_calibration(
            event_times, event_observed, predicted_cif, cif_eval_time
        )
        results["mean_calibration_error"] = results["cif_calibration"].attrs.get("mean_calibration_error", np.nan)

    logger.info("Evaluation summary: %s", {k: v for k, v in results.items() if not isinstance(v, pd.DataFrame)})
    return results
