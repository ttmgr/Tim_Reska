"""Tests for _pipeline.py."""

from __future__ import annotations

import pytest

pytest_plugins = ["tests.conftest_fetch"]


class TestPipelineRunnerSources:
    def test_available_sources(self, settings):
        from medrisk.fetch._pipeline import PipelineRunner

        runner = PipelineRunner(settings)
        sources = runner.available_sources()
        expected = {
            "nhanes",
            "cdc_places",
            "data_gov",
            "zenodo",
            "t1_granada",
            "glucose_ml",
            "uk_biobank",
            "biolincc",
        }
        assert expected.issubset(set(sources))


class TestPipelineRunnerResolveStudy:
    def test_resolve_valid_study(self, settings):
        from medrisk.fetch._pipeline import PipelineRunner

        runner = PipelineRunner(settings)
        source, dataset_ids = runner._resolve_study("nhanes_diabetes")
        assert source == "nhanes"
        assert len(dataset_ids) > 0

    def test_resolve_invalid_study_raises(self, settings):
        from medrisk.fetch._pipeline import PipelineRunner

        runner = PipelineRunner(settings)
        with pytest.raises(KeyError, match="no_such_study"):
            runner._resolve_study("no_such_study")


class TestPipelineRunnerBuildAdapter:
    def test_build_nhanes_adapter(self, settings):
        from medrisk.fetch._pipeline import PipelineRunner
        from medrisk.fetch.adapters.nhanes import NHANESAdapter

        runner = PipelineRunner(settings)
        adapter = runner._build_adapter("nhanes")
        assert isinstance(adapter, NHANESAdapter)

    def test_build_unknown_source_raises(self, settings):
        from medrisk.fetch._pipeline import PipelineRunner

        runner = PipelineRunner(settings)
        with pytest.raises(KeyError):
            runner._build_adapter("nonexistent_source")


class TestPipelineRunnerListDatasets:
    def test_list_nhanes(self, settings):
        from medrisk.fetch._pipeline import PipelineRunner

        runner = PipelineRunner(settings)
        datasets = runner.list_datasets("nhanes", {"cycle": "2017-2018"})
        assert len(datasets) > 0
        for d in datasets:
            assert "2017-2018" in d.dataset_id

    def test_list_t1_granada(self, settings):
        from medrisk.fetch._pipeline import PipelineRunner

        runner = PipelineRunner(settings)
        datasets = runner.list_datasets("t1_granada")
        assert len(datasets) == 1


class TestPipelineRunnerInspect:
    def test_inspect_nhanes(self, settings):
        from medrisk.fetch._pipeline import PipelineRunner

        runner = PipelineRunner(settings)
        info = runner.inspect("nhanes", "nhanes::2017-2018::labs")
        assert "NHANES" in info.title

    def test_inspect_t1_granada(self, settings):
        from medrisk.fetch._pipeline import PipelineRunner

        runner = PipelineRunner(settings)
        info = runner.inspect("t1_granada", "t1_granada::8386456")
        assert "Granada" in info.title
