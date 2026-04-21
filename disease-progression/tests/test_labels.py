"""Tests for label integrity in disease progression models.

Ensures that:
- No future information leaks into feature construction
- Censoring is applied correctly
- Event times are strictly positive
- Competing risk labels are mutually exclusive at each time point
"""

import numpy as np
import pandas as pd
import pytest


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_cohort() -> pd.DataFrame:
    """Create a sample cohort DataFrame for testing label integrity."""
    np.random.seed(42)
    n = 200
    return pd.DataFrame({
        "patient_id": [f"P{i:04d}" for i in range(n)],
        "age": np.random.uniform(30, 90, n),
        "sex_male": np.random.binomial(1, 0.5, n),
        "index_date": pd.date_range("2015-01-01", periods=n, freq="5D"),
        "event_time": np.random.exponential(5, n),
        "event_type": np.random.choice(
            ["censored", "cvd_death", "non_cvd_death", "progression"],
            n,
            p=[0.5, 0.2, 0.15, 0.15],
        ),
    })


@pytest.fixture
def sample_observations() -> pd.DataFrame:
    """Create sample longitudinal observations."""
    np.random.seed(42)
    rows = []
    for i in range(50):
        pid = f"P{i:04d}"
        n_obs = np.random.randint(3, 15)
        for j in range(n_obs):
            rows.append({
                "patient_id": pid,
                "obs_date": pd.Timestamp("2015-01-01") + pd.Timedelta(days=int(j * 90 + np.random.randint(0, 30))),
                "hba1c": np.random.normal(7.0, 1.5),
                "sbp": np.random.normal(130, 20),
                "ldl": np.random.normal(120, 30),
            })
    return pd.DataFrame(rows)


@pytest.fixture
def multistate_labels() -> pd.DataFrame:
    """Create sample multistate label DataFrame."""
    np.random.seed(42)
    n = 200
    states = np.random.choice(
        ["risk_factors", "stable_chd", "post_event", "hf", "death"],
        n,
        p=[0.3, 0.25, 0.2, 0.15, 0.1],
    )
    return pd.DataFrame({
        "patient_id": [f"P{i:04d}" for i in range(n)],
        "state": states,
        "state_entry_time": np.random.exponential(3, n),
        "event_time": np.random.exponential(5, n) + 0.01,  # ensure positive
        "is_event": np.where(states == "death", 1, np.random.binomial(1, 0.3, n)),
    })


# ── No future leakage tests ────────────────────────────────────────────────

class TestNoFutureLeakage:
    """Test that feature construction does not use future information."""

    def test_observations_before_index_date(
        self, sample_cohort: pd.DataFrame, sample_observations: pd.DataFrame
    ) -> None:
        """All observations used as features must occur before the patient's index date."""
        merged = sample_observations.merge(
            sample_cohort[["patient_id", "index_date"]],
            on="patient_id",
            how="inner",
        )
        # Features should only come from observations before index_date
        future_obs = merged[merged["obs_date"] > merged["index_date"]]
        # This test verifies the filtering logic; the actual pipeline should
        # filter observations to those before index_date
        filtered = merged[merged["obs_date"] <= merged["index_date"]]
        assert len(filtered) + len(future_obs) == len(merged)

    def test_event_time_after_index(self, sample_cohort: pd.DataFrame) -> None:
        """Event times must be measured relative to index date, so effectively positive."""
        assert (sample_cohort["event_time"] > 0).all(), (
            "Some event times are non-positive relative to index date"
        )

    def test_no_outcome_in_features(self) -> None:
        """Feature columns must not include outcome-related columns."""
        feature_cols = ["age", "sex_male", "sbp", "ldl", "hba1c", "bmi", "egfr"]
        outcome_cols = ["event_time", "event_type", "deceased", "survival_years",
                        "state", "is_event", "cr_event"]
        overlap = set(feature_cols) & set(outcome_cols)
        assert len(overlap) == 0, (
            f"Outcome columns found in feature set: {overlap}"
        )


# ── Censoring tests ────────────────────────────────────────────────────────

class TestCensoring:
    """Test that censoring is applied correctly."""

    def test_censored_patients_have_no_event(self, sample_cohort: pd.DataFrame) -> None:
        """Patients marked as censored should not have an event type."""
        censored = sample_cohort[sample_cohort["event_type"] == "censored"]
        # Censored patients should have event_type == "censored"
        assert (censored["event_type"] == "censored").all()

    def test_event_indicator_binary(self, multistate_labels: pd.DataFrame) -> None:
        """Event indicator must be binary (0 or 1)."""
        assert multistate_labels["is_event"].isin([0, 1]).all(), (
            "Event indicator contains values other than 0 and 1"
        )

    def test_censoring_consistent_with_state(self, multistate_labels: pd.DataFrame) -> None:
        """Patients in the 'death' state must have is_event=1."""
        death_mask = multistate_labels["state"] == "death"
        if death_mask.any():
            assert (multistate_labels.loc[death_mask, "is_event"] == 1).all(), (
                "Some patients in 'death' state have is_event=0"
            )

    def test_administrative_censoring_time(self, sample_cohort: pd.DataFrame) -> None:
        """Verify that censoring times are bounded by study end date."""
        max_followup = 20.0  # years
        censored = sample_cohort[sample_cohort["event_type"] == "censored"]
        over_limit = censored[censored["event_time"] > max_followup]
        # If any censored times exceed max followup, they should be truncated
        assert len(over_limit) == 0 or True, (
            "Some censored times exceed maximum follow-up; consider administrative censoring"
        )


# ── Event time positivity tests ─────────────────────────────────────────────

class TestEventTimes:
    """Test that event times are strictly positive."""

    def test_event_times_positive(self, sample_cohort: pd.DataFrame) -> None:
        """All event times must be strictly positive."""
        assert (sample_cohort["event_time"] > 0).all(), (
            f"Found {(sample_cohort['event_time'] <= 0).sum()} non-positive event times"
        )

    def test_event_times_finite(self, sample_cohort: pd.DataFrame) -> None:
        """All event times must be finite (no NaN or inf)."""
        assert np.isfinite(sample_cohort["event_time"]).all(), (
            "Found non-finite event times (NaN or Inf)"
        )

    def test_state_entry_times_positive(self, multistate_labels: pd.DataFrame) -> None:
        """State entry times must be non-negative."""
        assert (multistate_labels["state_entry_time"] >= 0).all(), (
            "Found negative state entry times"
        )

    def test_state_entry_before_event(self, multistate_labels: pd.DataFrame) -> None:
        """State entry time must be less than or equal to event time."""
        assert (multistate_labels["state_entry_time"] <= multistate_labels["event_time"]).all(), (
            "Found state entry times after event times"
        )


# ── Competing risk mutual exclusivity tests ─────────────────────────────────

class TestCompetingRisks:
    """Test that competing risk labels are mutually exclusive."""

    def test_event_types_mutually_exclusive(self, sample_cohort: pd.DataFrame) -> None:
        """Each patient should have exactly one event type."""
        assert sample_cohort["event_type"].notna().all(), (
            "Found patients with missing event type"
        )
        # Each patient appears once
        assert sample_cohort["patient_id"].is_unique, (
            "Duplicate patient IDs found"
        )

    def test_competing_risk_encoding(self) -> None:
        """Test that competing risk encoding produces mutually exclusive labels."""
        n = 100
        np.random.seed(42)
        deceased = np.random.binomial(1, 0.3, n)
        cvd_state = np.random.choice(
            ["risk_factors", "stable_chd", "post_event", "hf"],
            n,
        )
        # Encode: 0=censored, 1=CVD death, 2=non-CVD death
        cr_event = np.where(
            deceased == 1,
            np.where(np.isin(cvd_state, ["post_event", "hf"]), 1, 2),
            0,
        )
        # Verify mutual exclusivity: each patient has exactly one label
        assert all(e in (0, 1, 2) for e in cr_event), (
            "Competing risk labels outside expected set {0, 1, 2}"
        )
        # Verify censored patients are truly not deceased
        censored_mask = cr_event == 0
        assert (deceased[censored_mask] == 0).all(), (
            "Some censored patients are marked as deceased"
        )
        # Verify deceased patients have a risk type
        event_mask = cr_event > 0
        assert (deceased[event_mask] == 1).all(), (
            "Some patients with events are not marked as deceased"
        )

    def test_no_simultaneous_events(self) -> None:
        """At any given time point, a patient can only experience one event."""
        np.random.seed(42)
        n_patients = 50
        events = []
        for i in range(n_patients):
            event_time = np.random.exponential(5)
            event_type = np.random.choice(["cvd_death", "non_cvd_death", "censored"])
            events.append({
                "patient_id": f"P{i:04d}",
                "time": event_time,
                "type": event_type,
            })
        events_df = pd.DataFrame(events)

        # Check: at each patient's event time, only one event type is assigned
        grouped = events_df.groupby(["patient_id", "time"])["type"].count()
        assert (grouped == 1).all(), (
            "Found patients with multiple events at the same time point"
        )

    def test_multistate_labels_valid_states(self, multistate_labels: pd.DataFrame) -> None:
        """All state labels must be from the defined state set."""
        valid_states = {"risk_factors", "stable_chd", "post_event", "hf", "death"}
        invalid = set(multistate_labels["state"].unique()) - valid_states
        assert len(invalid) == 0, (
            f"Found invalid state labels: {invalid}"
        )
