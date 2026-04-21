"""Tests for _schema.py — Pydantic models."""

from __future__ import annotations

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from medrisk.fetch._schema import (
    CohortDataset,
    Measurement,
    Person,
    Treatment,
)

pytest_plugins = ["tests.conftest_fetch"]


class TestPerson:
    def test_valid_person(self, sample_person):
        assert sample_person.person_id == "P001"
        assert sample_person.sex == "M"
        assert sample_person.birth_year == 1960

    def test_sex_normalisation(self):
        p = Person(person_id="x", source="s", dataset_id="d", sex="female")
        assert p.sex == "F"
        p2 = Person(person_id="x", source="s", dataset_id="d", sex="1")
        assert p2.sex == "M"

    def test_invalid_birth_year(self):
        with pytest.raises(ValidationError):
            Person(person_id="x", source="s", dataset_id="d", birth_year=1700)

    def test_missing_optional_fields(self):
        p = Person(person_id="x", source="s", dataset_id="d")
        assert p.sex is None
        assert p.birth_year is None
        assert p.extra == {}


class TestMeasurement:
    def test_valid_measurement(self, sample_measurement):
        assert sample_measurement.measure_type == "hba1c_pct"
        assert sample_measurement.value == 7.2
        assert sample_measurement.unit == "%"

    def test_infinite_value_rejected(self):
        with pytest.raises(ValidationError):
            Measurement(
                person_id="x",
                source="s",
                dataset_id="d",
                measured_at=datetime(2020, 1, 1),
                measure_type="glucose_mg_dl",
                value=float("inf"),
                unit="mg/dL",
            )

    def test_nan_value_rejected(self):
        with pytest.raises(ValidationError):
            Measurement(
                person_id="x",
                source="s",
                dataset_id="d",
                measured_at=datetime(2020, 1, 1),
                measure_type="glucose_mg_dl",
                value=float("nan"),
                unit="mg/dL",
            )


class TestEvent:
    def test_valid_event(self, sample_event):
        assert sample_event.code == "E11.9"
        assert sample_event.code_system == "ICD10"
        assert sample_event.event_type == "diagnosis"


class TestTreatment:
    def test_valid_treatment(self, sample_treatment):
        assert sample_treatment.drug_name == "Metformin"
        assert sample_treatment.atc_code == "A10BA02"

    def test_end_before_start_rejected(self):
        with pytest.raises(ValidationError):
            Treatment(
                person_id="x",
                source="s",
                dataset_id="d",
                start_date=date(2020, 6, 1),
                end_date=date(2020, 1, 1),
            )


class TestCohortDataset:
    def test_summary(self, sample_cohort_dataset):
        s = sample_cohort_dataset.summary()
        assert s["persons"] == 1
        assert s["measurements"] == 1
        assert s["events"] == 1
        assert s["treatments"] == 1

    def test_is_empty(self):
        ds = CohortDataset()
        assert ds.is_empty()

    def test_not_empty(self, sample_cohort_dataset):
        assert not sample_cohort_dataset.is_empty()
