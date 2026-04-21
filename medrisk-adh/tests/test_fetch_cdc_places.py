"""Tests for adapters/cdc_places.py."""

from __future__ import annotations

import pytest

from medrisk.fetch._schema import CohortDataset
from medrisk.fetch.adapters.cdc_places import CDCPLACESAdapter

pytest_plugins = ["tests.conftest_fetch"]


@pytest.fixture()
def adapter(no_auth, cache_store):
    config = {
        "base_url": "https://chronicdata.cdc.gov/resource",
        "auth": "app_token",
        "app_token_env": "SOCRATA_APP_TOKEN",
    }
    return CDCPLACESAdapter(config, no_auth, cache_store)


class TestCDCPLACESMetadata:
    def test_list_datasets_returns_expected(self, adapter):
        datasets = adapter.list_datasets()
        assert len(datasets) > 0
        ids = [d.dataset_id for d in datasets]
        assert "cdc_places::2023::county" in ids

    def test_get_metadata(self, adapter):
        info = adapter.get_metadata("cdc_places::2023::county")
        assert "PLACES" in info.title
        assert info.requires_auth is False


class TestCDCPLACESParse:
    def test_parse_jsonl(self, adapter, places_jsonl):
        dataset = adapter.parse("cdc_places::2023::county", [places_jsonl])
        assert isinstance(dataset, CohortDataset)
        assert len(dataset.measurements) == 2

    def test_measurement_fields(self, adapter, places_jsonl):
        dataset = adapter.parse("cdc_places::2023::county", [places_jsonl])
        diabetes_m = next(m for m in dataset.measurements if "diabetes" in m.measure_type)
        assert diabetes_m.value == pytest.approx(8.5)
        assert diabetes_m.unit == "%"
        assert diabetes_m.person_id == "06001"

    def test_source_field(self, adapter, places_jsonl):
        dataset = adapter.parse("cdc_places::2023::county", [places_jsonl])
        assert all(m.source == "cdc_places" for m in dataset.measurements)
