"""Tests for adapters/t1_granada.py using local fixture CSV files."""

from __future__ import annotations

from pathlib import Path

import pytest

from medrisk.fetch._schema import CohortDataset
from medrisk.fetch.adapters.t1_granada import (
    T1DiabetesGranadaAdapter,
    _parse_timestamp,
)

pytest_plugins = ["tests.conftest_fetch"]


@pytest.fixture()
def adapter(no_auth, cache_store):
    config = {
        "api_base": "https://zenodo.org/api",
        "auth": "env_var_token",
        "token_env": "ZENODO_TOKEN",
    }
    return T1DiabetesGranadaAdapter(config, no_auth, cache_store)


class TestT1GranadaMetadata:
    def test_list_datasets_returns_one(self, adapter):
        datasets = adapter.list_datasets()
        assert len(datasets) == 1
        assert "t1_granada" in datasets[0].dataset_id

    def test_get_metadata(self, adapter):
        info = adapter.get_metadata("t1_granada::8386456")
        assert "Granada" in info.title
        assert info.requires_auth is True
        assert info.license == "CC BY 4.0"


class TestT1GranadaParse:
    def test_parse_patient_info(
        self, adapter, t1g_patient_csv, t1g_glucose_csv, t1g_biochem_csv, t1g_diagnostics_csv
    ):
        files = [t1g_patient_csv, t1g_glucose_csv, t1g_biochem_csv, t1g_diagnostics_csv]
        dataset = adapter.parse("t1_granada::8386456", files)
        assert isinstance(dataset, CohortDataset)

    def test_persons_parsed(
        self, adapter, t1g_patient_csv, t1g_glucose_csv, t1g_biochem_csv, t1g_diagnostics_csv
    ):
        files = [t1g_patient_csv, t1g_glucose_csv, t1g_biochem_csv, t1g_diagnostics_csv]
        dataset = adapter.parse("t1_granada::8386456", files)
        assert len(dataset.persons) == 2
        pids = {p.person_id for p in dataset.persons}
        assert "P001" in pids
        assert "P002" in pids

    def test_glucose_measurements_parsed(
        self, adapter, t1g_patient_csv, t1g_glucose_csv, t1g_biochem_csv, t1g_diagnostics_csv
    ):
        files = [t1g_patient_csv, t1g_glucose_csv, t1g_biochem_csv, t1g_diagnostics_csv]
        dataset = adapter.parse("t1_granada::8386456", files)
        glucose = [m for m in dataset.measurements if m.measure_type == "glucose_mg_dl"]
        assert len(glucose) >= 3
        assert all(m.method == "CGM" for m in glucose)
        assert all(m.unit == "mg/dL" for m in glucose)

    def test_biochemical_parsed(
        self, adapter, t1g_patient_csv, t1g_glucose_csv, t1g_biochem_csv, t1g_diagnostics_csv
    ):
        files = [t1g_patient_csv, t1g_glucose_csv, t1g_biochem_csv, t1g_diagnostics_csv]
        dataset = adapter.parse("t1_granada::8386456", files)
        biochem = [m for m in dataset.measurements if m.method == "lab"]
        assert len(biochem) >= 3

    def test_diagnostics_parsed(
        self, adapter, t1g_patient_csv, t1g_glucose_csv, t1g_biochem_csv, t1g_diagnostics_csv
    ):
        files = [t1g_patient_csv, t1g_glucose_csv, t1g_biochem_csv, t1g_diagnostics_csv]
        dataset = adapter.parse("t1_granada::8386456", files)
        assert len(dataset.events) == 2
        assert all(e.code_system == "ICD9" for e in dataset.events)
        codes = {e.code for e in dataset.events}
        assert "250.51" in codes

    def test_source_field_set(
        self, adapter, t1g_patient_csv, t1g_glucose_csv, t1g_biochem_csv, t1g_diagnostics_csv
    ):
        files = [t1g_patient_csv, t1g_glucose_csv, t1g_biochem_csv, t1g_diagnostics_csv]
        dataset = adapter.parse("t1_granada::8386456", files)
        assert all(p.source == "t1_granada" for p in dataset.persons)
        assert all(m.source == "t1_granada" for m in dataset.measurements)

    def test_missing_files_graceful(self, adapter):
        # Only patient info present; no crash
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "Patient_info.csv"
            p.write_text("Patient_ID,Sex\nP001,Male\n")
            dataset = adapter.parse("t1_granada::8386456", [p])
        assert len(dataset.persons) == 1
        assert len(dataset.measurements) == 0


class TestParseTimestamp:
    def test_date_only(self):
        ts = _parse_timestamp("2020-01-15")
        assert ts is not None
        assert ts.year == 2020

    def test_date_and_time(self):
        ts = _parse_timestamp("2020-01-15", "08:30")
        assert ts is not None
        assert ts.hour == 8

    def test_none_returns_none(self):
        assert _parse_timestamp(None) is None

    def test_nan_returns_none(self):

        assert _parse_timestamp(float("nan")) is None
