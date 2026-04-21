"""Tests for adapters/uk_biobank.py."""

from __future__ import annotations

import os

import pytest

from medrisk.fetch.adapters.uk_biobank import UKBiobankAdapter

pytest_plugins = ["tests.conftest_fetch"]


@pytest.fixture()
def adapter(no_auth, cache_store):
    config = {"auth": "local_path", "data_path_env": "UKB_DATA_PATH"}
    return UKBiobankAdapter(config, no_auth, cache_store)


class TestUKBiobankDownload:
    def test_download_raises_when_path_not_set(self, no_auth, cache_store, tmp_path):
        """download() raises FileNotFoundError with setup instructions when UKB_DATA_PATH unset."""
        os.environ.pop("UKB_DATA_PATH", None)
        # Create adapter AFTER clearing env var so path is empty at construction
        adapter = UKBiobankAdapter(
            {"auth": "local_path", "data_path_env": "UKB_DATA_PATH"},
            no_auth,
            cache_store,
        )
        with pytest.raises(FileNotFoundError, match="UKB_DATA_PATH"):
            adapter.download("ukb::application", tmp_path)

    def test_list_datasets_empty_when_no_path(self, no_auth, cache_store):
        os.environ.pop("UKB_DATA_PATH", None)
        adapter = UKBiobankAdapter(
            {"auth": "local_path", "data_path_env": "UKB_DATA_PATH"},
            no_auth,
            cache_store,
        )
        datasets = adapter.list_datasets()
        assert datasets == []

    def test_download_returns_files_when_path_set(self, adapter, tmp_path, monkeypatch):
        """When UKB_DATA_PATH points to a directory with .tab files, download returns them."""
        # Create a fake .tab file
        (tmp_path / "phenotype.tab").write_text("eid\tf.31.0.0\n1\t1\n")
        monkeypatch.setenv("UKB_DATA_PATH", str(tmp_path))
        # Recreate adapter with new env
        from medrisk.fetch.adapters.uk_biobank import UKBiobankAdapter

        adapter2 = UKBiobankAdapter(
            {"auth": "local_path", "data_path_env": "UKB_DATA_PATH"},
            adapter.auth,
            adapter.cache,
        )
        files = adapter2.download("ukb::application", tmp_path)
        assert len(files) > 0


class TestUKBiobankMetadata:
    def test_get_metadata(self, adapter):
        info = adapter.get_metadata("ukb::application")
        assert "UK Biobank" in info.title
        assert info.requires_auth is True
