"""
conftest_fetch.py — Shared pytest fixtures for fetch module tests.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pytest

# ------------------------------------------------------------------
# Directory fixtures
# ------------------------------------------------------------------


@pytest.fixture()
def tmp_cache(tmp_path: Path) -> Path:
    d = tmp_path / "cache"
    d.mkdir()
    return d


@pytest.fixture()
def tmp_output(tmp_path: Path) -> Path:
    d = tmp_path / "output"
    d.mkdir()
    return d


# ------------------------------------------------------------------
# AppSettings fixture
# ------------------------------------------------------------------


@pytest.fixture()
def settings(tmp_path: Path, tmp_cache: Path):
    """Return an AppSettings instance pointing to the real configs/ dir."""
    from medrisk.fetch._settings import AppSettings

    config_dir = Path(__file__).parent.parent / "configs"
    return AppSettings(config_dir=config_dir, cache_dir=tmp_cache, log_level="WARNING")


# ------------------------------------------------------------------
# Cache fixture
# ------------------------------------------------------------------


@pytest.fixture()
def cache_store(tmp_cache: Path):
    from medrisk.fetch._cache import CacheStore

    return CacheStore(tmp_cache)


# ------------------------------------------------------------------
# Auth fixtures
# ------------------------------------------------------------------


@pytest.fixture()
def no_auth():
    from medrisk.fetch._auth import NoAuth

    return NoAuth()


# ------------------------------------------------------------------
# Schema fixtures
# ------------------------------------------------------------------


@pytest.fixture()
def sample_person():
    from medrisk.fetch._schema import Person

    return Person(
        person_id="P001",
        source="test",
        dataset_id="test::001",
        sex="M",
        birth_year=1960,
    )


@pytest.fixture()
def sample_measurement():
    from medrisk.fetch._schema import Measurement

    return Measurement(
        person_id="P001",
        source="test",
        dataset_id="test::001",
        measured_at=datetime(2020, 6, 15, 9, 0),
        measure_type="hba1c_pct",
        value=7.2,
        unit="%",
        method="lab",
    )


@pytest.fixture()
def sample_event():
    from medrisk.fetch._schema import Event

    return Event(
        person_id="P001",
        source="test",
        dataset_id="test::001",
        event_date=date(2020, 1, 1),
        event_type="diagnosis",
        code_system="ICD10",
        code="E11.9",
        description="Type 2 diabetes mellitus without complications",
    )


@pytest.fixture()
def sample_treatment():
    from medrisk.fetch._schema import Treatment

    return Treatment(
        person_id="P001",
        source="test",
        dataset_id="test::001",
        start_date=date(2020, 2, 1),
        drug_name="Metformin",
        atc_code="A10BA02",
        dose_value=500.0,
        dose_unit="mg",
        route="oral",
    )


@pytest.fixture()
def sample_cohort_dataset(sample_person, sample_measurement, sample_event, sample_treatment):
    from medrisk.fetch._schema import CohortDataset

    return CohortDataset(
        persons=[sample_person],
        measurements=[sample_measurement],
        events=[sample_event],
        treatments=[sample_treatment],
    )


# ------------------------------------------------------------------
# Zenodo mock response fixture
# ------------------------------------------------------------------


@pytest.fixture()
def zenodo_record_response():
    return {
        "id": 8386456,
        "doi": "10.5281/zenodo.8386456",
        "metadata": {
            "title": "T1DiabetesGranada Mock Record",
            "description": "Mock Zenodo record for testing",
            "keywords": ["diabetes", "CGM"],
            "license": {"id": "cc-by-4.0"},
        },
        "files": [
            {
                "key": "Patient_info.csv",
                "links": {"self": "https://zenodo.org/record/8386456/files/Patient_info.csv"},
                "checksum": "abc123",
            },
        ],
        "links": {},
    }


# ------------------------------------------------------------------
# T1Granada CSV fixtures
# ------------------------------------------------------------------


@pytest.fixture()
def t1g_patient_csv(tmp_path: Path) -> Path:
    content = "Patient_ID,Sex,Age\nP001,Male,35\nP002,Female,42\n"
    p = tmp_path / "Patient_info.csv"
    p.write_text(content)
    return p


@pytest.fixture()
def t1g_glucose_csv(tmp_path: Path) -> Path:
    content = (
        "Patient_ID,Date,Time,Glucose\n"
        "P001,2020-01-01,08:00,120.0\n"
        "P001,2020-01-01,08:05,118.5\n"
        "P002,2020-01-02,10:00,95.0\n"
    )
    p = tmp_path / "Glucose_measurements.csv"
    p.write_text(content)
    return p


@pytest.fixture()
def t1g_biochem_csv(tmp_path: Path) -> Path:
    content = (
        "Patient_ID,Date,Parameter,Value,Unit\n"
        "P001,2020-03-15,HbA1c,7.5,%\n"
        "P001,2020-03-15,Creatinine,0.9,mg/dl\n"
        "P002,2020-04-01,HbA1c,8.1,%\n"
    )
    p = tmp_path / "Biochemical_parameters.csv"
    p.write_text(content)
    return p


@pytest.fixture()
def t1g_diagnostics_csv(tmp_path: Path) -> Path:
    content = (
        "Patient_ID,Date,ICD_code,Description\n"
        "P001,2018-05-10,250.51,Diabetic retinopathy\n"
        "P002,2019-11-20,401,Essential hypertension\n"
    )
    p = tmp_path / "Diagnostics.csv"
    p.write_text(content)
    return p


# ------------------------------------------------------------------
# NHANES mock SAS XPT fixture
# ------------------------------------------------------------------


@pytest.fixture()
def nhanes_demo_xpt(tmp_path: Path) -> Path:
    """Create a minimal SAS XPT-like file as a CSV for testing parse logic."""
    import pandas as pd

    df = pd.DataFrame(
        {
            "SEQN": [1.0, 2.0, 3.0],
            "RIAGENDR": [1.0, 2.0, 1.0],
            "RIDAGEYR": [45.0, 62.0, 38.0],
            "RIDRETH3": [3.0, 4.0, 1.0],
        }
    )
    p = tmp_path / "DEMO_J.XPT"
    # Write as SAS XPT using pandas
    try:
        df.to_sas(p, format="xport", index=False)
    except Exception:
        # Fallback: save as CSV with .XPT extension for test environments
        # where SAS export isn't available
        df.to_csv(p, index=False)
    return p


# ------------------------------------------------------------------
# CDC PLACES JSONL fixture
# ------------------------------------------------------------------


@pytest.fixture()
def places_jsonl(tmp_path: Path) -> Path:
    rows = [
        {
            "locationid": "06001",
            "measureid": "DIABETES",
            "data_value": "8.5",
            "geographiclevel": "County",
            "locationname": "Alameda County, CA",
            "measure": "Diagnosed diabetes among adults",
            "low_confidence_limit": "7.9",
            "high_confidence_limit": "9.1",
        },
        {
            "locationid": "06001",
            "measureid": "BPHIGH",
            "data_value": "30.1",
            "geographiclevel": "County",
            "locationname": "Alameda County, CA",
            "measure": "High blood pressure among adults",
            "low_confidence_limit": "29.0",
            "high_confidence_limit": "31.2",
        },
    ]
    p = tmp_path / "places_2023_county.jsonl"
    with open(p, "w") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    return p
