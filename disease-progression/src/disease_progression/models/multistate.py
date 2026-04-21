"""
disease_progression.models.multistate - Continuous-time Markov multistate model.

Implements a multi-state model (MSM) for disease progression where patients
transition between clinically defined states (e.g. Healthy -> Diagnosed ->
Complication -> Death) via a continuous-time Markov chain (CTMC).

Key concepts:
    - **States**: Discrete disease stages (e.g. "no_disease", "stable_chd",
      "heart_failure", "post_mi", "dead").
    - **Transitions**: Permitted state-to-state moves, each governed by a
      transition intensity (hazard rate) q_rs.
    - **Intensity matrix Q**: Off-diagonal entries q_rs >= 0 represent
      instantaneous transition rates; rows sum to zero.
    - **Transition probability matrix P(t)**: P(t) = expm(Q * t) gives
      the probability of being in state s at time t, conditional on the
      state at time 0.
    - **State occupation probabilities**: Expected proportion of time
      spent in each state over a horizon.
    - **Covariate effects**: Proportional-intensities regression allows
      covariates to modulate transition rates via log-linear models.

The implementation uses scipy's matrix exponential for P(t) computation
and maximum likelihood estimation for the intensity parameters.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.linalg import expm
from scipy.optimize import minimize

from disease_progression.models.registry import auto_register

logger = logging.getLogger(__name__)


# ===================================================================
# State and transition specification
# ===================================================================

@dataclass
class StateSpec:
    """Specification of a single state in the multistate model.

    Attributes
    ----------
    name : str
        Human-readable state label.
    absorbing : bool
        If True, the state has no outgoing transitions (e.g. death).
    """
    name: str
    absorbing: bool = False


@dataclass
class TransitionSpec:
    """Specification of a permitted transition.

    Attributes
    ----------
    from_state : str
        Origin state name.
    to_state : str
        Destination state name.
    initial_rate : float
        Initial estimate of the transition intensity q_rs.
    """
    from_state: str
    to_state: str
    initial_rate: float = 0.01


# ===================================================================
# Predefined multistate topologies
# ===================================================================

def cvd_progression_states() -> Tuple[List[StateSpec], List[TransitionSpec]]:
    """Standard CVD progression multistate model.

    States: healthy -> stable_chd -> post_mi -> heart_failure -> dead
    Plus direct transitions healthy -> dead, stable_chd -> dead, etc.
    """
    states = [
        StateSpec("healthy"),
        StateSpec("stable_chd"),
        StateSpec("post_mi"),
        StateSpec("heart_failure"),
        StateSpec("dead", absorbing=True),
    ]
    transitions = [
        TransitionSpec("healthy", "stable_chd", 0.02),
        TransitionSpec("healthy", "dead", 0.005),
        TransitionSpec("stable_chd", "post_mi", 0.03),
        TransitionSpec("stable_chd", "heart_failure", 0.015),
        TransitionSpec("stable_chd", "dead", 0.01),
        TransitionSpec("post_mi", "heart_failure", 0.04),
        TransitionSpec("post_mi", "dead", 0.025),
        TransitionSpec("heart_failure", "dead", 0.05),
    ]
    return states, transitions


def diabetes_progression_states() -> Tuple[List[StateSpec], List[TransitionSpec]]:
    """Diabetes progression multistate model.

    States: prediabetes -> diabetes_controlled -> diabetes_uncontrolled
            -> nephropathy -> esrd -> dead
    """
    states = [
        StateSpec("prediabetes"),
        StateSpec("diabetes_controlled"),
        StateSpec("diabetes_uncontrolled"),
        StateSpec("nephropathy"),
        StateSpec("esrd"),
        StateSpec("dead", absorbing=True),
    ]
    transitions = [
        TransitionSpec("prediabetes", "diabetes_controlled", 0.05),
        TransitionSpec("prediabetes", "dead", 0.003),
        TransitionSpec("diabetes_controlled", "diabetes_uncontrolled", 0.03),
        TransitionSpec("diabetes_controlled", "nephropathy", 0.01),
        TransitionSpec("diabetes_controlled", "dead", 0.008),
        TransitionSpec("diabetes_uncontrolled", "nephropathy", 0.04),
        TransitionSpec("diabetes_uncontrolled", "dead", 0.015),
        TransitionSpec("nephropathy", "esrd", 0.02),
        TransitionSpec("nephropathy", "dead", 0.025),
        TransitionSpec("esrd", "dead", 0.08),
    ]
    return states, transitions


# ===================================================================
# Multi-state model
# ===================================================================

@auto_register(
    "multistate",
    description="Continuous-time Markov multistate model for disease progression",
    default_params={"topology": "cvd"},
)
class MultiStateModel:
    """Continuous-time Markov multi-state model.

    Parameters
    ----------
    states : list of StateSpec
        State definitions.
    transitions : list of TransitionSpec
        Permitted transitions with initial intensity estimates.
    topology : str, optional
        Shorthand for predefined topologies (``"cvd"`` or ``"diabetes"``).
        Overridden if ``states`` and ``transitions`` are provided.
    """

    def __init__(
        self,
        states: Optional[List[StateSpec]] = None,
        transitions: Optional[List[TransitionSpec]] = None,
        topology: str = "cvd",
    ) -> None:
        if states is None or transitions is None:
            if topology == "diabetes":
                states, transitions = diabetes_progression_states()
            else:
                states, transitions = cvd_progression_states()

        self.states = states
        self.transitions = transitions
        self.state_names = [s.name for s in states]
        self.n_states = len(states)
        self._state_idx = {s.name: i for i, s in enumerate(states)}

        # Build transition mask and initial Q
        self._trans_mask = np.zeros((self.n_states, self.n_states), dtype=bool)
        self._initial_rates: Dict[Tuple[int, int], float] = {}
        for t in transitions:
            i, j = self._state_idx[t.from_state], self._state_idx[t.to_state]
            self._trans_mask[i, j] = True
            self._initial_rates[(i, j)] = t.initial_rate

        self._Q: Optional[np.ndarray] = None
        self._fitted = False
        self._covariate_effects: Optional[np.ndarray] = None

    # ------------------------------------------------------------------
    # Intensity matrix construction
    # ------------------------------------------------------------------

    def _build_Q(self, log_rates: np.ndarray) -> np.ndarray:
        """Construct the intensity matrix Q from a vector of log-rates.

        Off-diagonal entries are exp(log_rate) to ensure positivity.
        Diagonal entries are set so each row sums to zero.
        """
        Q = np.zeros((self.n_states, self.n_states))
        idx = 0
        for i in range(self.n_states):
            for j in range(self.n_states):
                if self._trans_mask[i, j]:
                    Q[i, j] = np.exp(log_rates[idx])
                    idx += 1
        # Set diagonal so rows sum to 0
        np.fill_diagonal(Q, 0.0)
        np.fill_diagonal(Q, -Q.sum(axis=1))
        return Q

    def _n_params(self) -> int:
        """Number of free transition intensity parameters."""
        return int(self._trans_mask.sum())

    def _initial_log_rates(self) -> np.ndarray:
        """Initial parameter vector (log-transformed rates)."""
        params = []
        for i in range(self.n_states):
            for j in range(self.n_states):
                if self._trans_mask[i, j]:
                    rate = self._initial_rates.get((i, j), 0.01)
                    params.append(np.log(rate))
        return np.array(params)

    # ------------------------------------------------------------------
    # Transition probability matrix
    # ------------------------------------------------------------------

    def transition_probability(self, t: float, Q: Optional[np.ndarray] = None) -> np.ndarray:
        """Compute P(t) = expm(Q * t).

        Parameters
        ----------
        t : float
            Time horizon.
        Q : ndarray, optional
            Intensity matrix.  Uses the fitted Q if not provided.

        Returns
        -------
        ndarray of shape (n_states, n_states)
            P[i, j] = P(X(t) = j | X(0) = i).
        """
        if Q is None:
            if self._Q is None:
                raise RuntimeError("Model not fitted and no Q provided.")
            Q = self._Q
        return expm(Q * t)

    # ------------------------------------------------------------------
    # MLE fitting
    # ------------------------------------------------------------------

    def fit(
        self,
        transition_data: pd.DataFrame,
        max_iter: int = 500,
    ) -> "MultiStateModel":
        """Fit transition intensities via maximum likelihood.

        Parameters
        ----------
        transition_data : pd.DataFrame
            Must contain columns: ``patient_id``, ``from_state``,
            ``to_state``, ``time`` (sojourn time in the origin state).
            Censored observations use ``to_state = from_state`` (i.e.
            the patient was still in the origin state at last follow-up).

        Returns self.
        """
        # Aggregate sufficient statistics
        n_trans = np.zeros((self.n_states, self.n_states))
        total_time = np.zeros(self.n_states)

        for _, row in transition_data.iterrows():
            i = self._state_idx.get(row["from_state"])
            j = self._state_idx.get(row["to_state"])
            if i is None or j is None:
                continue
            sojourn = float(row["time"])
            total_time[i] += sojourn
            if i != j:
                n_trans[i, j] += 1

        def neg_log_lik(log_rates: np.ndarray) -> float:
            Q = self._build_Q(log_rates)
            nll = 0.0
            idx = 0
            for i in range(self.n_states):
                for j in range(self.n_states):
                    if self._trans_mask[i, j]:
                        rate = np.exp(log_rates[idx])
                        # Log-lik contribution: n_ij * log(q_ij) - q_ij * T_i
                        if n_trans[i, j] > 0:
                            nll -= n_trans[i, j] * np.log(rate + 1e-15)
                        nll += rate * total_time[i]
                        idx += 1
            return nll

        x0 = self._initial_log_rates()
        result = minimize(neg_log_lik, x0, method="L-BFGS-B", options={"maxiter": max_iter})

        self._Q = self._build_Q(result.x)
        self._fitted = True

        logger.info("Multistate MLE converged: %s, nll=%.2f", result.success, result.fun)
        logger.info("Intensity matrix Q:\n%s", self.intensity_matrix_df())
        return self

    def fit_from_panel(
        self,
        panel: pd.DataFrame,
        patient_col: str = "patient_id",
        state_col: str = "state",
        time_col: str = "time",
    ) -> "MultiStateModel":
        """Fit from a panel (long-format) dataset.

        Converts panel observations into pairwise transitions, then
        calls ``fit()``.
        """
        panel = panel.sort_values([patient_col, time_col])
        rows: List[Dict[str, Any]] = []

        for pid, group in panel.groupby(patient_col):
            states_seq = group[state_col].values
            times_seq = group[time_col].values
            for k in range(len(states_seq) - 1):
                rows.append({
                    "patient_id": pid,
                    "from_state": states_seq[k],
                    "to_state": states_seq[k + 1],
                    "time": float(times_seq[k + 1] - times_seq[k]),
                })
            # Last observation is right-censored (self-transition)
            if len(states_seq) >= 1:
                rows.append({
                    "patient_id": pid,
                    "from_state": states_seq[-1],
                    "to_state": states_seq[-1],
                    "time": 1.0,  # Nominal censoring contribution
                })

        return self.fit(pd.DataFrame(rows))

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def state_occupation_probabilities(
        self,
        initial_state: str,
        times: np.ndarray,
    ) -> pd.DataFrame:
        """Compute state occupation probabilities over a time grid.

        Parameters
        ----------
        initial_state : str
            Starting state name.
        times : ndarray
            Time points at which to evaluate P(t).

        Returns
        -------
        pd.DataFrame
            Rows = time points, columns = state names.
        """
        if self._Q is None:
            raise RuntimeError("Model not fitted.")
        i = self._state_idx[initial_state]
        probs = np.zeros((len(times), self.n_states))
        for k, t in enumerate(times):
            P = self.transition_probability(t)
            probs[k, :] = P[i, :]
        return pd.DataFrame(probs, index=times, columns=self.state_names)

    def expected_sojourn_time(self) -> pd.Series:
        """Expected sojourn time in each transient state = -1/q_ii."""
        if self._Q is None:
            raise RuntimeError("Model not fitted.")
        diag = np.diag(self._Q)
        sojourn = np.where(diag < 0, -1.0 / diag, np.inf)
        return pd.Series(sojourn, index=self.state_names, name="expected_sojourn_time")

    def mean_time_to_absorption(self, initial_state: str) -> float:
        """Mean time to reach any absorbing state from ``initial_state``.

        Uses the fundamental matrix N = (I - T_sub)^{-1} of the
        transient sub-chain, where T_sub is the transient-to-transient
        block of the embedded jump chain.

        For a CTMC, mean absorption time from state i is
        -sum_j (Q_T^{-1})_{ij} where Q_T is the transient sub-block of Q.
        """
        if self._Q is None:
            raise RuntimeError("Model not fitted.")

        transient_idx = [i for i, s in enumerate(self.states) if not s.absorbing]
        if not transient_idx:
            return 0.0

        Q_T = self._Q[np.ix_(transient_idx, transient_idx)]
        try:
            inv_QT = np.linalg.inv(Q_T)
        except np.linalg.LinAlgError:
            return np.inf

        i_in_transient = transient_idx.index(self._state_idx[initial_state])
        return float(-inv_QT[i_in_transient, :].sum())

    def simulate(
        self,
        initial_state: str,
        max_time: float = 20.0,
        n_trajectories: int = 1000,
        seed: int = 42,
    ) -> pd.DataFrame:
        """Simulate trajectories from the fitted CTMC via Gillespie algorithm.

        Parameters
        ----------
        initial_state : str
        max_time : float
            Maximum simulation time.
        n_trajectories : int
            Number of independent trajectories.
        seed : int

        Returns
        -------
        pd.DataFrame
            Columns: trajectory_id, time, state.
        """
        if self._Q is None:
            raise RuntimeError("Model not fitted.")

        rng = np.random.default_rng(seed)
        records: List[Dict[str, Any]] = []
        absorbing = {i for i, s in enumerate(self.states) if s.absorbing}

        for traj in range(n_trajectories):
            current = self._state_idx[initial_state]
            t = 0.0
            records.append({"trajectory_id": traj, "time": t, "state": self.state_names[current]})

            while t < max_time and current not in absorbing:
                rate_out = -self._Q[current, current]
                if rate_out <= 0:
                    break
                # Sojourn time ~ Exp(rate_out)
                dt = rng.exponential(1.0 / rate_out)
                t += dt
                if t > max_time:
                    break
                # Choose destination state
                dest_rates = self._Q[current, :].copy()
                dest_rates[current] = 0.0
                probs = dest_rates / dest_rates.sum()
                current = int(rng.choice(self.n_states, p=probs))
                records.append({"trajectory_id": traj, "time": t, "state": self.state_names[current]})

        return pd.DataFrame(records)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def intensity_matrix_df(self) -> pd.DataFrame:
        """Return Q as a labelled DataFrame."""
        if self._Q is None:
            raise RuntimeError("Model not fitted.")
        return pd.DataFrame(self._Q, index=self.state_names, columns=self.state_names)

    def transition_rates(self) -> pd.DataFrame:
        """Return non-zero transition rates as a tidy DataFrame."""
        if self._Q is None:
            raise RuntimeError("Model not fitted.")
        rows = []
        for i in range(self.n_states):
            for j in range(self.n_states):
                if self._trans_mask[i, j]:
                    rows.append({
                        "from_state": self.state_names[i],
                        "to_state": self.state_names[j],
                        "intensity": self._Q[i, j],
                        "expected_wait": -1.0 / self._Q[i, i] if self._Q[i, i] < 0 else np.inf,
                    })
        return pd.DataFrame(rows)
