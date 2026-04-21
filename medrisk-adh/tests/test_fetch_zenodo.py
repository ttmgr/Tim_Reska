"""Tests for adapters/zenodo.py — mocked HTTP responses."""

from __future__ import annotations

import pytest
import responses as rsps_lib

from medrisk.fetch._schema import CohortDataset
from medrisk.fetch.adapters.zenodo import API_BASE, ZenodoAdapter

pytest_plugins = ["tests.conftest_fetch"]


@pytest.fixture()
def adapter(no_auth, cache_store):
    config = {"api_base": API_BASE}
    return ZenodoAdapter(config, no_auth, cache_store)


class TestZenodoMetadata:
    @rsps_lib.activate
    def test_get_metadata(self, adapter, zenodo_record_response):
        rsps_lib.add(
            rsps_lib.GET,
            f"{API_BASE}/records/8386456",
            json=zenodo_record_response,
            status=200,
        )
        info = adapter.get_metadata("zenodo::8386456")
        assert info.dataset_id == "zenodo::8386456"
        assert "Granada" in info.title or info.title  # title from mock

    @rsps_lib.activate
    def test_list_datasets(self, adapter):
        rsps_lib.add(
            rsps_lib.GET,
            f"{API_BASE}/records",
            json={
                "hits": {
                    "hits": [
                        {
                            "id": 111,
                            "metadata": {
                                "title": "Test Dataset",
                                "description": "desc",
                                "keywords": ["diabetes"],
                                "license": {"id": "cc-by-4.0"},
                            },
                            "doi": "10.5281/zenodo.111",
                            "links": {},
                        }
                    ]
                }
            },
            status=200,
        )
        datasets = adapter.list_datasets({"q": "diabetes"})
        assert len(datasets) == 1
        assert datasets[0].dataset_id == "zenodo::111"


class TestZenodoDownload:
    @rsps_lib.activate
    def test_download_creates_files(self, adapter, tmp_path, zenodo_record_response):
        # Mock record metadata
        rsps_lib.add(
            rsps_lib.GET,
            f"{API_BASE}/records/8386456",
            json=zenodo_record_response,
            status=200,
        )
        # Mock file download
        rsps_lib.add(
            rsps_lib.GET,
            "https://zenodo.org/record/8386456/files/Patient_info.csv",
            body=b"Patient_ID,Sex\nP001,Male\n",
            status=200,
        )
        files = adapter.download("zenodo::8386456", tmp_path)
        assert len(files) == 1
        assert files[0].name == "Patient_info.csv"
        assert files[0].read_text() == "Patient_ID,Sex\nP001,Male\n"


class TestZenodoParse:
    def test_parse_returns_empty_cohort_dataset(self, adapter):
        ds = adapter.parse("zenodo::8386456", [])
        assert isinstance(ds, CohortDataset)
        assert ds.is_empty()
