"""Tests for disease configuration registry and Alzheimer CTMC model."""

import numpy as np
import pytest

from medrisk.models.disease_configs import (
    ALZHEIMER_CONFIG,
    CARDIOVASCULAR_CONFIG,
    DISEASE_REGISTRY,
    build_model,
)
from medrisk.models.multistate import (
    ABSORBING_STATES,
    N_STATES,
    STATE_NAMES,
    MultistateModel,
)

# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------


class TestDiseaseRegistry:
    def test_registry_contains_cardiovascular(self):
        assert "cardiovascular" in DISEASE_REGISTRY

    def test_registry_contains_alzheimer(self):
        assert "alzheimer" in DISEASE_REGISTRY

    def test_cardiovascular_matches_legacy_n_states(self):
        assert CARDIOVASCULAR_CONFIG.n_states == N_STATES

    def test_cardiovascular_matches_legacy_absorbing(self):
        assert set(CARDIOVASCULAR_CONFIG.absorbing_states) == ABSORBING_STATES

    def test_cardiovascular_matches_legacy_state_names(self):
        assert dict(CARDIOVASCULAR_CONFIG.state_names) == STATE_NAMES

    def test_build_model_returns_fitted(self):
        model = build_model(CARDIOVASCULAR_CONFIG)
        assert isinstance(model, MultistateModel)
        assert model._fitted

    def test_build_model_alzheimer_returns_fitted(self):
        model = build_model(ALZHEIMER_CONFIG)
        assert isinstance(model, MultistateModel)
        assert model._fitted
        assert model.n_states == 7


# ---------------------------------------------------------------------------
# MultistateModel parameterization tests
# ---------------------------------------------------------------------------


class TestMultistateParameterization:
    def test_default_backward_compatible(self):
        model = MultistateModel()
        assert model.n_states == N_STATES
        assert model.absorbing_states == ABSORBING_STATES
        assert model.state_names == STATE_NAMES

    def test_custom_n_states(self):
        model = MultistateModel(n_states=7, absorbing_states={6}, state_names={0: "A"})
        assert model.n_states == 7

    def test_custom_absorbing_states(self):
        model = MultistateModel(n_states=3, absorbing_states={2})
        assert model.absorbing_states == {2}

    def test_custom_state_names_in_summary(self):
        names = {0: "Start", 1: "Middle", 2: "End"}
        model = MultistateModel(
            n_states=3,
            absorbing_states={2},
            state_names=names,
            allowed_transitions=[(0, 1), (1, 2)],
        )
        model.set_intensities({(0, 1): 0.1, (1, 2): 0.2})
        summary = model.get_intensity_summary()
        assert "Start -> Middle" in summary
        assert "Middle -> End" in summary


# ---------------------------------------------------------------------------
# Alzheimer CTMC model tests
# ---------------------------------------------------------------------------


class TestAlzheimerModel:
    @pytest.fixture
    def ad_model(self):
        return build_model(ALZHEIMER_CONFIG)

    def test_n_states(self, ad_model):
        assert ad_model.n_states == 7

    def test_absorbing_state_6(self, ad_model):
        # Row 6 of Q should be all zeros (absorbing)
        assert np.allclose(ad_model.Q[6, :], 0.0)

    def test_q_matrix_rows_sum_to_zero(self, ad_model):
        row_sums = ad_model.Q.sum(axis=1)
        np.testing.assert_allclose(row_sums, 0.0, atol=1e-12)

    def test_transition_probability_rows_sum_to_one(self, ad_model):
        P = ad_model.transition_probability(5.0)
        row_sums = P.sum(axis=1)
        np.testing.assert_allclose(row_sums, 1.0, atol=1e-10)

    def test_state_occupation_sums_to_one(self, ad_model):
        times = np.linspace(0, 20, 50)
        probs = ad_model.state_occupation_probabilities(0, times)
        row_sums = probs.sum(axis=1)
        np.testing.assert_allclose(row_sums, 1.0, atol=1e-10)

    def test_death_probability_increases(self, ad_model):
        times = np.linspace(0, 30, 100)
        probs = ad_model.state_occupation_probabilities(0, times)
        death_probs = probs[:, 6]
        # Death probability should be monotonically non-decreasing
        diffs = np.diff(death_probs)
        assert np.all(diffs >= -1e-10)

    def test_mean_sojourn_mci_clinically_plausible(self, ad_model):
        # MCI (state 2): sojourn should be ~4-7 years
        sojourn = ad_model.mean_sojourn_time(2)
        assert 3.0 <= sojourn <= 10.0

    def test_mean_time_to_absorption_from_mci(self, ad_model):
        # MCI to death: ~8-15 years in literature
        mtta = ad_model.mean_time_to_absorption(2)
        assert 5.0 <= mtta <= 20.0

    def test_mean_time_to_absorption_death_is_zero(self, ad_model):
        assert ad_model.mean_time_to_absorption(6) == 0.0

    def test_simulate_trajectory(self, ad_model):
        rng = np.random.default_rng(42)
        traj = ad_model.simulate_trajectory(0, 50.0, rng)
        assert len(traj) >= 1
        assert traj[0] == (0.0, 0)
        # All states should be valid
        for _, s in traj:
            assert 0 <= s < 7
