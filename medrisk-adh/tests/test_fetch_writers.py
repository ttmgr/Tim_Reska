"""Tests for _writers.py."""

from __future__ import annotations

import pandas as pd
import pytest

from medrisk.fetch._schema import CohortDataset
from medrisk.fetch._writers import read_cohort_dataset, write_cohort_dataset

pytest_plugins = ["tests.conftest_fetch"]


class TestWriteCohortDataset:
    def test_write_creates_parquet_files(self, sample_cohort_dataset, tmp_path):
        written = write_cohort_dataset(sample_cohort_dataset, tmp_path)
        assert "persons" in written
        assert "measurements" in written
        assert "events" in written
        assert "treatments" in written
        for table, path in written.items():
            assert path.exists(), f"{table} parquet file missing"

    def test_written_parquet_readable(self, sample_cohort_dataset, tmp_path):
        write_cohort_dataset(sample_cohort_dataset, tmp_path)
        persons_df = pd.read_parquet(tmp_path / "persons.parquet")
        assert len(persons_df) == 1
        assert "person_id" in persons_df.columns

    def test_empty_tables_skipped(self, tmp_path):

        ds = CohortDataset()
        written = write_cohort_dataset(ds, tmp_path)
        assert written == {}

    def test_schema_fields_preserved(self, sample_cohort_dataset, tmp_path):
        write_cohort_dataset(sample_cohort_dataset, tmp_path)
        df = pd.read_parquet(tmp_path / "measurements.parquet")
        expected_cols = {
            "person_id",
            "source",
            "dataset_id",
            "measured_at",
            "measure_type",
            "value",
            "unit",
        }
        assert expected_cols.issubset(set(df.columns))


class TestReadCohortDataset:
    def test_roundtrip(self, sample_cohort_dataset, tmp_path):
        write_cohort_dataset(sample_cohort_dataset, tmp_path)
        restored = read_cohort_dataset(tmp_path)
        assert len(restored.persons) == 1
        assert len(restored.measurements) == 1
        assert len(restored.events) == 1
        assert len(restored.treatments) == 1

    def test_person_fields_preserved(self, sample_cohort_dataset, tmp_path):
        write_cohort_dataset(sample_cohort_dataset, tmp_path)
        restored = read_cohort_dataset(tmp_path)
        p = restored.persons[0]
        assert p.person_id == "P001"
        assert p.sex == "M"
        assert p.birth_year == 1960

    def test_measurement_fields_preserved(self, sample_cohort_dataset, tmp_path):
        write_cohort_dataset(sample_cohort_dataset, tmp_path)
        restored = read_cohort_dataset(tmp_path)
        m = restored.measurements[0]
        assert m.measure_type == "hba1c_pct"
        assert m.value == pytest.approx(7.2)

    def test_missing_tables_return_empty(self, tmp_path):
        # No files written; should return empty CohortDataset
        restored = read_cohort_dataset(tmp_path)
        assert restored.is_empty()
