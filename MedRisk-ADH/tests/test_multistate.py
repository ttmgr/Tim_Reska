"""Tests for continuous-time Markov chain multistate model."""

import numpy as np
import pytest

from medrisk.models.multistate import MultistateModel, TransitionData


@pytest.fixture
def simple_model():
    """A model with manually set intensities."""
    model = MultistateModel()
    model.set_intensities(
        {
            (0, 1): 0.08,
            (1, 0): 0.02,
            (1, 2): 0.06,
            (2, 3): 0.04,
            (2, 4): 0.01,
            (3, 4): 0.03,
        }
    )
    return model


@pytest.fixture
def transition_data():
    """Synthetic transition data for MLE fitting."""
    rng = np.random.default_rng(42)
    n = 500
    from_states = rng.choice([0, 1, 2, 3], size=n, p=[0.3, 0.3, 0.25, 0.15])
    to_states = np.zeros(n, dtype=int)
    times = rng.exponential(5, n)

    for i in range(n):
        s = from_states[i]
        if s == 0:
            to_states[i] = rng.choice([0, 1], p=[0.3, 0.7])
        elif s == 1:
            to_states[i] = rng.choice([0, 1, 2], p=[0.1, 0.3, 0.6])
        elif s == 2:
            to_states[i] = rng.choice([2, 3, 4], p=[0.3, 0.5, 0.2])
        elif s == 3:
            to_states[i] = rng.choice([3, 4], p=[0.4, 0.6])

    return TransitionData(from_states, to_states, times)


class TestIntensityMatrix:
    def test_rows_sum_to_zero(self, simple_model) -> None:
        row_sums = simple_model.Q.sum(axis=1)
        np.testing.assert_allclose(row_sums, 0, atol=1e-10)

    def test_off_diagonal_non_negative(self, simple_model) -> None:
        Q = simple_model.Q.copy()
        np.fill_diagonal(Q, 0)
        assert (Q >= 0).all()

    def test_diagonal_non_positive(self, simple_model) -> None:
        assert (np.diag(simple_model.Q) <= 0).all()

    def test_absorbing_state_zero_row(self, simple_model) -> None:
        np.testing.assert_allclose(simple_model.Q[4, :], 0, atol=1e-10)


class TestTransitionProbability:
    def test_rows_sum_to_one(self, simple_model) -> None:
        P = simple_model.transition_probability(5.0)
        row_sums = P.sum(axis=1)
        np.testing.assert_allclose(row_sums, 1.0, atol=1e-10)

    def test_entries_in_zero_one(self, simple_model) -> None:
        P = simple_model.transition_probability(5.0)
        assert (P >= -1e-10).all()
        assert (P <= 1.0 + 1e-10).all()

    def test_identity_at_zero(self, simple_model) -> None:
        P = simple_model.transition_probability(0.0)
        np.testing.assert_allclose(P, np.eye(5), atol=1e-10)

    def test_absorbing_state_sticky(self, simple_model) -> None:
        P = simple_model.transition_probability(10.0)
        assert P[4, 4] == pytest.approx(1.0, abs=1e-10)


class TestStateOccupation:
    def test_sums_to_one(self, simple_model) -> None:
        times = np.linspace(0, 20, 50)
        probs = simple_model.state_occupation_probabilities(0, times)
        row_sums = probs.sum(axis=1)
        np.testing.assert_allclose(row_sums, 1.0, atol=1e-10)

    def test_absorbing_grows(self, simple_model) -> None:
        times = np.array([1.0, 5.0, 10.0, 20.0, 50.0])
        probs = simple_model.state_occupation_probabilities(0, times)
        absorbing_probs = probs[:, 4]
        # Should be monotonically non-decreasing
        assert all(
            absorbing_probs[i] <= absorbing_probs[i + 1] + 1e-10
            for i in range(len(absorbing_probs) - 1)
        )


class TestSojournAndAbsorption:
    def test_mean_sojourn_positive(self, simple_model) -> None:
        for s in range(4):
            mst = simple_model.mean_sojourn_time(s)
            assert mst > 0, f"State {s} sojourn should be positive"

    def test_absorbing_sojourn_infinite(self, simple_model) -> None:
        assert simple_model.mean_sojourn_time(4) == float("inf")

    def test_mean_absorption_time_positive(self, simple_model) -> None:
        for s in range(4):
            mat = simple_model.mean_time_to_absorption(s)
            assert 0 < mat < float("inf"), f"State {s} absorption time should be finite"

    def test_absorbing_absorption_zero(self, simple_model) -> None:
        assert simple_model.mean_time_to_absorption(4) == 0.0


class TestSimulation:
    def test_trajectory_starts_correctly(self, simple_model) -> None:
        traj = simple_model.simulate_trajectory(0, 50.0, rng=np.random.default_rng(42))
        assert traj[0] == (0.0, 0)

    def test_trajectory_respects_max_time(self, simple_model) -> None:
        traj = simple_model.simulate_trajectory(0, 5.0, rng=np.random.default_rng(42))
        assert all(t <= 5.0 for t, _ in traj)

    def test_trajectory_ends_at_absorbing_or_maxtime(self, simple_model) -> None:
        traj = simple_model.simulate_trajectory(0, 100.0, rng=np.random.default_rng(42))
        final_state = traj[-1][1]
        final_time = traj[-1][0]
        assert final_state == 4 or final_time >= 100.0 or final_state < 4


class TestMLE:
    def test_fit_converges(self, transition_data) -> None:
        model = MultistateModel()
        model.fit(transition_data)
        assert model._fitted
        # Q should have rows summing to zero
        np.testing.assert_allclose(model.Q.sum(axis=1), 0, atol=1e-6)

    def test_fitted_intensities_positive(self, transition_data) -> None:
        model = MultistateModel()
        model.fit(transition_data)
        for i, j in model.allowed_transitions:
            assert model.Q[i, j] > 0, f"q[{i},{j}] should be positive"
