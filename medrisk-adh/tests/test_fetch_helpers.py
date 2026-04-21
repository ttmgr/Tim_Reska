"""Tests for _export_helpers.py."""

from __future__ import annotations

import pandas as pd
import pytest

from medrisk.fetch._export_helpers import (
    build_cgm_sequences,
    build_multistate_frame,
    build_survival_frame,
)

pytest_plugins = ["tests.conftest_fetch"]


@pytest.fixture()
def persons_df():
    return pd.DataFrame(
        {
            "person_id": ["P001", "P002", "P003", "P004", "P005"],
            "baseline_date": [
                "2015-01-01",
                "2015-01-01",
                "2015-01-01",
                "2015-01-01",
                "2015-01-01",
            ],
        }
    )


@pytest.fixture()
def events_df():
    return pd.DataFrame(
        {
            "person_id": ["P001", "P003"],
            "event_date": ["2016-06-01", "2018-03-15"],
            "code": ["E11.9", "E11.9"],
            "code_system": ["ICD10", "ICD10"],
            "event_type": ["diagnosis", "diagnosis"],
        }
    )


@pytest.fixture()
def cgm_measurements_df():
    rows = []
    for pid in ["P001", "P002"]:
        for i in range(288):  # 24h x 12 readings/h = 288 for 5-min intervals
            ts = pd.Timestamp("2020-01-01") + pd.Timedelta(minutes=5 * i)
            rows.append(
                {
                    "person_id": pid,
                    "measured_at": ts,
                    "measure_type": "glucose_mg_dl",
                    "value": 100.0 + i % 20,
                    "unit": "mg/dL",
                }
            )
    return pd.DataFrame(rows)


class TestBuildSurvivalFrame:
    def test_basic_survival_frame(self, persons_df, events_df):
        frame = build_survival_frame(persons_df, events_df, event_codes=["E11.9"])
        assert len(frame) == 5
        assert set(frame.columns) >= {"person_id", "time_to_event", "event"}

    def test_event_indicator_correct(self, persons_df, events_df):
        frame = build_survival_frame(persons_df, events_df, event_codes=["E11.9"])
        events = frame[frame["person_id"] == "P001"]["event"].iloc[0]
        assert events == 1
        no_event = frame[frame["person_id"] == "P002"]["event"].iloc[0]
        assert no_event == 0

    def test_time_to_event_positive(self, persons_df, events_df):
        frame = build_survival_frame(persons_df, events_df, event_codes=["E11.9"])
        assert (frame["time_to_event"] >= 0).all()

    def test_empty_events_all_censored(self, persons_df):
        empty_events = pd.DataFrame(columns=["person_id", "event_date", "code", "code_system"])
        frame = build_survival_frame(persons_df, empty_events, event_codes=["E11.9"])
        assert frame.empty or (frame["event"] == 0).all()

    def test_code_system_filter(self, persons_df, events_df):
        frame = build_survival_frame(
            persons_df, events_df, event_codes=["E11.9"], code_system="ICD9"
        )
        # No ICD9 codes in events_df -> all censored
        assert (frame["event"] == 0).all()


class TestBuildMultistateFrame:
    def test_basic_transitions(self, persons_df, events_df):
        transition_codes = {("healthy", "diabetes"): ["E11.9"]}
        frame = build_multistate_frame(
            persons_df,
            events_df,
            states=["healthy", "diabetes"],
            transition_codes=transition_codes,
        )
        assert len(frame) == 2  # P001 and P003
        assert set(frame["from_state"]) == {"healthy"}
        assert set(frame["to_state"]) == {"diabetes"}

    def test_empty_when_no_matching_codes(self, persons_df, events_df):
        transition_codes = {("state_a", "state_b"): ["X99.9"]}
        frame = build_multistate_frame(
            persons_df,
            events_df,
            states=["state_a", "state_b"],
            transition_codes=transition_codes,
        )
        assert frame.empty or len(frame) == 0


class TestBuildCGMSequences:
    def test_produces_windows(self, cgm_measurements_df):
        result = build_cgm_sequences(cgm_measurements_df, window_hours=24)
        assert not result.empty
        # Should have windows for both persons
        assert "P001" in result.index.get_level_values("person_id")
        assert "P002" in result.index.get_level_values("person_id")

    def test_window_columns_present(self, cgm_measurements_df):
        result = build_cgm_sequences(cgm_measurements_df, window_hours=24)
        # 24h at 5min = 288 steps (step_0000 to step_0287)
        assert "step_0000" in result.columns
        assert "step_0287" in result.columns

    def test_filter_by_person_id(self, cgm_measurements_df):
        result = build_cgm_sequences(cgm_measurements_df, person_ids=["P001"], window_hours=24)
        pids = result.index.get_level_values("person_id").unique()
        assert list(pids) == ["P001"]

    def test_empty_for_non_cgm_data(self):
        # DataFrame with no CGM measure_type values
        import pandas as pd

        df = pd.DataFrame(
            {
                "person_id": ["P001"],
                "measured_at": ["2020-01-01"],
                "measure_type": ["bmi_kg_m2"],
                "value": [25.0],
                "unit": ["kg/m2"],
            }
        )
        result = build_cgm_sequences(df)
        assert result.empty
