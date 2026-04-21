"""Tests for adapters/nhanes.py — metadata and parse logic."""

from __future__ import annotations

import contextlib

import pandas as pd
import pytest

from medrisk.fetch._schema import CohortDataset
from medrisk.fetch.adapters.nhanes import CYCLE_SUFFIX, DOMAINS, NHANESAdapter

pytest_plugins = ["tests.conftest_fetch"]


@pytest.fixture()
def adapter(no_auth, cache_store):
    config = {"base_url": "https://wwwn.cdc.gov/nchs/nhanes", "auth": "none"}
    return NHANESAdapter(config, no_auth, cache_store)


class TestNHANESListDatasets:
    def test_returns_all_cycles_and_domains(self, adapter):
        datasets = adapter.list_datasets()
        # Should return len(CYCLE_SUFFIX) x len(DOMAINS) datasets
        expected = len(CYCLE_SUFFIX) * len(DOMAINS)
        assert len(datasets) == expected

    def test_filter_by_cycle(self, adapter):
        datasets = adapter.list_datasets({"cycle": "2017-2018"})
        assert len(datasets) == len(DOMAINS)
        for d in datasets:
            assert "2017-2018" in d.dataset_id

    def test_filter_by_domain(self, adapter):
        datasets = adapter.list_datasets({"domain": "labs"})
        assert len(datasets) == len(CYCLE_SUFFIX)
        for d in datasets:
            assert "labs" in d.dataset_id


class TestNHANESGetMetadata:
    def test_valid_dataset_id(self, adapter):
        info = adapter.get_metadata("nhanes::2017-2018::labs")
        assert "NHANES" in info.title
        assert info.source == "nhanes"

    def test_invalid_dataset_id(self, adapter):
        with pytest.raises(ValueError, match="Invalid NHANES dataset_id"):
            adapter.get_metadata("nhanes::badid")


class TestNHANESParseDemographics:
    def test_parse_demographics_from_csv(self, adapter, tmp_path):
        """Test demographics parse using a CSV file (fallback for test env)."""
        df = pd.DataFrame(
            {
                "SEQN": [1.0, 2.0, 3.0],
                "RIAGENDR": [1.0, 2.0, 1.0],
                "RIDAGEYR": [45.0, 62.0, 38.0],
                "RIDRETH3": [3.0, 4.0, 1.0],
            }
        )
        xpt_path = tmp_path / "DEMO_J.XPT"
        df.to_csv(xpt_path, index=False)

        # Monkeypatch _read_xpt to use pd.read_csv for this test
        def mock_parse(dataset_id, files):
            dfs = {}
            for f in files:
                with contextlib.suppress(Exception):
                    dfs[f.stem.split("_")[0]] = pd.read_csv(f)
            return adapter._parse_demographics(dataset_id, dfs, "2017-2018")

        dataset = mock_parse("nhanes::2017-2018::demographics", [xpt_path])
        assert isinstance(dataset, CohortDataset)
        assert len(dataset.persons) == 3
        pids = {p.person_id for p in dataset.persons}
        assert "1" in pids

    def test_sex_mapping(self, adapter, tmp_path):
        df = pd.DataFrame({"SEQN": [1.0, 2.0], "RIAGENDR": [1.0, 2.0]})
        xpt_path = tmp_path / "DEMO_J.XPT"
        df.to_csv(xpt_path, index=False)
        dfs = {"DEMO": pd.read_csv(xpt_path)}
        dataset = adapter._parse_demographics("nhanes::2017-2018::demographics", dfs, "2017-2018")
        persons = {p.person_id: p for p in dataset.persons}
        assert persons["1"].sex == "M"
        assert persons["2"].sex == "F"
