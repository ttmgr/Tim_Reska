"""Tests for _harmonizer.py."""

from __future__ import annotations

from datetime import datetime

from medrisk.fetch._harmonizer import Harmonizer
from medrisk.fetch._schema import CohortDataset, Event, Measurement

pytest_plugins = ["tests.conftest_fetch"]


class TestNormalizeUnits:
    def test_identity_when_already_canonical(self):
        h = Harmonizer()
        m = Measurement(
            person_id="P1",
            source="s",
            dataset_id="d",
            measured_at=datetime(2020, 1, 1),
            measure_type="hba1c_pct",
            value=7.5,
            unit="%",
        )
        result = h.normalize_units([m])
        assert len(result) == 1
        assert result[0].value == 7.5
        assert result[0].unit == "%"

    def test_passthrough_unmapped_type(self):
        h = Harmonizer()
        m = Measurement(
            person_id="P1",
            source="s",
            dataset_id="d",
            measured_at=datetime(2020, 1, 1),
            measure_type="some_custom_type",
            value=42.0,
            unit="arbitrary",
        )
        result = h.normalize_units([m])
        assert result[0].value == 42.0


class TestMapCodes:
    def test_icd9_prefix_mapped_to_icd10(self):
        h = Harmonizer()
        e = Event(
            person_id="P1",
            source="s",
            dataset_id="d",
            event_date=__import__("datetime").date(2020, 1, 1),
            event_type="diagnosis",
            code_system="ICD9",
            code="401.9",
        )
        result = h.map_codes([e])
        assert len(result) == 1
        assert result[0].code == "I10"
        assert result[0].code_system == "ICD10"

    def test_custom_code_map_applied(self):
        h = Harmonizer()
        e = Event(
            person_id="P1",
            source="s",
            dataset_id="d",
            event_date=__import__("datetime").date(2020, 1, 1),
            event_type="diagnosis",
            code_system="ICD9",
            code="250.00",
        )
        result = h.map_codes([e], code_map={"250.00": "E11.9"})
        assert result[0].code == "E11.9"

    def test_icd10_unchanged(self):
        h = Harmonizer()
        e = Event(
            person_id="P1",
            source="s",
            dataset_id="d",
            event_date=__import__("datetime").date(2020, 1, 1),
            event_type="diagnosis",
            code_system="ICD10",
            code="E11.9",
        )
        result = h.map_codes([e])
        assert result[0].code == "E11.9"


class TestFillMissingPersons:
    def test_creates_stub_for_orphan(self):
        h = Harmonizer()
        m = Measurement(
            person_id="P_ORPHAN",
            source="s",
            dataset_id="d",
            measured_at=datetime(2020, 1, 1),
            measure_type="glucose_mg_dl",
            value=95.0,
            unit="mg/dL",
        )
        persons = h.fill_missing_persons([m], [])
        assert len(persons) == 1
        assert persons[0].person_id == "P_ORPHAN"

    def test_no_stub_when_person_exists(self, sample_person, sample_measurement):
        h = Harmonizer()
        persons = h.fill_missing_persons([sample_measurement], [sample_person])
        assert len(persons) == 1  # no stub added


class TestNormalizeAll:
    def test_full_pipeline(self, sample_cohort_dataset):
        h = Harmonizer()
        result = h.normalize_all(sample_cohort_dataset)
        assert isinstance(result, CohortDataset)
        assert len(result.persons) >= 1
