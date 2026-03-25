"""Continuous-time Markov chain for multi-state disease progression.

Implements a CTMC with maximum likelihood estimation of transition intensities,
matrix exponential for transition probabilities, and Gillespie simulation
for individual trajectory generation.

States for the underwriting model:
    0: Healthy / low risk
    1: Risk factors present (hypertension, prediabetes, dyslipidemia)
    2: Diagnosed chronic condition (T2D, CHD, CKD stage 3+)
    3: Complication (MI, stroke, HF, CKD stage 4+)
    4: Major event / absorbing (death, ESRD)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
from scipy.linalg import expm
from scipy.optimize import minimize

logger = logging.getLogger(__name__)

N_STATES = 5
ABSORBING_STATES = {4}
STATE_NAMES = {
    0: "Healthy",
    1: "Risk factors",
    2: "Chronic condition",
    3: "Complication",
    4: "Major event",
}


@dataclass
class TransitionData:
    """Observed transitions for MLE fitting.

    Attributes:
        from_state: Array of origin states.
        to_state: Array of destination states.
        time_in_state: Array of sojourn times before transition.
    """

    from_state: np.ndarray
    to_state: np.ndarray
    time_in_state: np.ndarray

    def __post_init__(self) -> None:
        assert len(self.from_state) == len(self.to_state) == len(self.time_in_state)


class MultistateModel:
    """Continuous-time Markov chain for disease progression.

    Attributes:
        n_states: Number of states in the model.
        Q: Transition intensity matrix (n_states x n_states).
        allowed_transitions: Set of (from, to) pairs that are allowed.
    """

    def __init__(
        self,
        allowed_transitions: list[tuple[int, int]] | None = None,
        n_states: int | None = None,
        absorbing_states: set[int] | None = None,
        state_names: dict[int, str] | None = None,
    ) -> None:
        self.n_states = n_states if n_states is not None else N_STATES
        self.absorbing_states = absorbing_states if absorbing_states is not None else ABSORBING_STATES
        self.state_names = state_names if state_names is not None else STATE_NAMES

        if allowed_transitions is None:
            # Default underwriting topology
            self.allowed_transitions = [
                (0, 1),
                (1, 0),
                (1, 2),
                (2, 3),
                (2, 4),
                (3, 4),
            ]
        else:
            self.allowed_transitions = list(allowed_transitions)

        self.Q: np.ndarray = np.zeros((self.n_states, self.n_states))
        self._fitted = False

    def _params_to_Q(self, params: np.ndarray) -> np.ndarray:
        """Convert a flat parameter vector to a valid intensity matrix Q.

        Off-diagonal entries q_ij > 0 are set from params (exponentiated
        to ensure positivity). Diagonal entries are set so rows sum to 0.
        """
        Q = np.zeros((self.n_states, self.n_states))
        for idx, (i, j) in enumerate(self.allowed_transitions):
            Q[i, j] = np.exp(params[idx])

        # Diagonal: negative row sum
        for i in range(self.n_states):
            Q[i, i] = -np.sum(Q[i, :])

        return Q

    def _neg_log_likelihood(self, params: np.ndarray, data: TransitionData) -> float:
        """Negative log-likelihood for the CTMC.

        For each observed transition (s -> s') with sojourn time t:
            L_i = q_{s,s'} * exp(q_{s,s} * t)  if s != s' (transition)
            L_i = exp(q_{s,s} * t)              if censored (same state)
        """
        Q = self._params_to_Q(params)
        nll = 0.0

        for k in range(len(data.from_state)):
            s = data.from_state[k]
            d = data.to_state[k]
            t = data.time_in_state[k]

            if s in self.absorbing_states:
                continue

            q_ss = Q[s, s]

            if s == d:
                # Censored: stayed in state s for time t
                nll -= q_ss * t
            else:
                # Transition: moved from s to d after time t
                q_sd = Q[s, d]
                if q_sd <= 0:
                    nll += 1e10  # penalty for impossible transition
                else:
                    nll -= np.log(q_sd) + q_ss * t

        return nll

    def fit(
        self,
        data: TransitionData,
        max_iter: int = 500,
        tol: float = 1e-6,
    ) -> MultistateModel:
        """Fit transition intensities via maximum likelihood estimation.

        Args:
            data: Observed transition data.
            max_iter: Maximum optimisation iterations.
            tol: Convergence tolerance.

        Returns:
            self for method chaining.
        """
        n_params = len(self.allowed_transitions)
        x0 = np.log(np.full(n_params, 0.05))

        result = minimize(
            self._neg_log_likelihood,
            x0,
            args=(data,),
            method="L-BFGS-B",
            options={"maxiter": max_iter, "ftol": tol},
        )

        if not result.success:
            logger.warning("MLE optimisation did not converge: %s", result.message)

        self.Q = self._params_to_Q(result.x)
        self._fitted = True

        logger.info("CTMC fitted: %d transitions, NLL=%.4f", n_params, result.fun)
        return self

    def set_intensities(self, intensities: dict[tuple[int, int], float]) -> MultistateModel:
        """Manually set transition intensities.

        Args:
            intensities: Dictionary mapping (from, to) pairs to intensity values.

        Returns:
            self for method chaining.
        """
        self.Q = np.zeros((self.n_states, self.n_states))
        for (i, j), rate in intensities.items():
            self.Q[i, j] = rate
            if (i, j) not in self.allowed_transitions:
                self.allowed_transitions.append((i, j))

        for i in range(self.n_states):
            self.Q[i, i] = -np.sum(self.Q[i, :])

        self._fitted = True
        return self

    def transition_probability(self, t: float) -> np.ndarray:
        """Compute P(t) = expm(Qt), the transition probability matrix at time t.

        Args:
            t: Time horizon.

        Returns:
            n_states x n_states matrix where P[i,j] = P(X(t)=j | X(0)=i).
        """
        return expm(self.Q * t)

    def state_occupation_probabilities(
        self,
        initial_state: int,
        times: np.ndarray,
    ) -> np.ndarray:
        """Compute state occupation probabilities over time.

        Args:
            initial_state: Starting state.
            times: Array of time points.

        Returns:
            Array of shape (len(times), n_states) with P(state j at time t).
        """
        probs = np.zeros((len(times), self.n_states))
        for idx, t in enumerate(times):
            P = self.transition_probability(t)
            probs[idx, :] = P[initial_state, :]
        return probs

    def mean_sojourn_time(self, state: int) -> float:
        """Expected time spent in a state before transitioning.

        Args:
            state: State index.

        Returns:
            Mean sojourn time (1 / |q_ii|). Returns inf for absorbing states.
        """
        q_ii = self.Q[state, state]
        if q_ii >= 0:
            return float("inf")
        return -1.0 / q_ii

    def mean_time_to_absorption(self, initial_state: int) -> float:
        """Expected time to reach an absorbing state.

        Uses the fundamental matrix N = (I - T)^{-1} where T is the
        transient-to-transient submatrix of the embedded chain.

        Args:
            initial_state: Starting state.

        Returns:
            Expected time to absorption. Returns 0 for absorbing states.
        """
        if initial_state in self.absorbing_states:
            return 0.0

        transient = [i for i in range(self.n_states) if i not in self.absorbing_states]
        n_transient = len(transient)

        # Sub-intensity matrix for transient states
        Q_T = np.zeros((n_transient, n_transient))
        for i_idx, i in enumerate(transient):
            for j_idx, j in enumerate(transient):
                Q_T[i_idx, j_idx] = self.Q[i, j]

        # Mean time = -Q_T^{-1} * 1
        try:
            N = np.linalg.solve(-Q_T, np.ones(n_transient))
            state_idx = transient.index(initial_state)
            return float(N[state_idx])
        except np.linalg.LinAlgError:
            logger.warning("Singular sub-intensity matrix, returning inf")
            return float("inf")

    def simulate_trajectory(
        self,
        initial_state: int,
        max_time: float,
        rng: np.random.Generator | None = None,
    ) -> list[tuple[float, int]]:
        """Simulate a single trajectory using the Gillespie algorithm.

        Args:
            initial_state: Starting state.
            max_time: Maximum simulation time.
            rng: Random generator for reproducibility.

        Returns:
            List of (time, state) tuples representing the trajectory.
        """
        if rng is None:
            rng = np.random.default_rng()

        trajectory = [(0.0, initial_state)]
        current_state = initial_state
        elapsed = 0.0

        while elapsed < max_time and current_state not in self.absorbing_states:
            rate = -self.Q[current_state, current_state]
            if rate <= 0:
                break

            dt = rng.exponential(1.0 / rate)
            elapsed += dt
            if elapsed > max_time:
                break

            # Choose destination
            probs = self.Q[current_state, :].copy()
            probs[current_state] = 0
            probs = probs / probs.sum()

            next_state = rng.choice(self.n_states, p=probs)
            current_state = next_state
            trajectory.append((elapsed, current_state))

        return trajectory

    def get_intensity_summary(self) -> dict[str, float]:
        """Return a human-readable summary of transition intensities.

        Returns:
            Dictionary mapping "state_i -> state_j" to intensity values.
        """
        summary = {}
        for i, j in self.allowed_transitions:
            key = f"{self.state_names.get(i, str(i))} -> {self.state_names.get(j, str(j))}"
            summary[key] = self.Q[i, j]
        return summary
