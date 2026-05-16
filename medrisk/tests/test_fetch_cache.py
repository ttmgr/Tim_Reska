"""Tests for _cache.py."""

from __future__ import annotations

from medrisk.fetch._cache import CacheStore, _safe_name

pytest_plugins = ["tests.conftest_fetch"]


class TestSafeName:
    def test_safe_chars_unchanged(self):
        assert _safe_name("abc-123_XYZ.ext") == "abc-123_XYZ.ext"

    def test_unsafe_chars_replaced(self):
        assert _safe_name("nhanes::2017-2018::labs") == "nhanes__2017-2018__labs"
        assert _safe_name("my/file:name") == "my_file_name"


class TestCacheStore:
    def test_get_path_deterministic(self, tmp_cache):
        store = CacheStore(tmp_cache)
        p1 = store.get_path("nhanes", "nhanes::2017-2018::labs", "DEMO_J.XPT")
        p2 = store.get_path("nhanes", "nhanes::2017-2018::labs", "DEMO_J.XPT")
        assert p1 == p2

    def test_is_cached_false_when_absent(self, tmp_cache):
        store = CacheStore(tmp_cache)
        assert not store.is_cached("nhanes", "nhanes::2017-2018::labs", "DEMO_J.XPT")

    def test_is_cached_true_after_write(self, tmp_cache):
        store = CacheStore(tmp_cache)
        path = store.ensure_dir("test", "test::001") / "data.csv"
        path.write_text("hello")
        checksum = store.compute_checksum(path)
        store.write_checksum(path, checksum)
        assert store.is_cached("test", "test::001", "data.csv")

    def test_checksum_mismatch_returns_false(self, tmp_cache):
        store = CacheStore(tmp_cache)
        path = store.ensure_dir("test", "test::001") / "data.csv"
        path.write_text("hello")
        store.write_checksum(path, "wrongchecksum")
        assert not store.verify(path, "wrongchecksum2")

    def test_verify_correct_checksum(self, tmp_cache):
        store = CacheStore(tmp_cache)
        path = store.ensure_dir("test", "test::002") / "file.txt"
        path.write_text("test content")
        checksum = store.compute_checksum(path)
        assert store.verify(path, checksum)

    def test_invalidate_removes_files(self, tmp_cache):
        store = CacheStore(tmp_cache)
        path = store.ensure_dir("test", "test::003") / "data.csv"
        path.write_text("data")
        checksum = store.compute_checksum(path)
        store.write_checksum(path, checksum)
        assert path.exists()
        store.invalidate("test", "test::003")
        assert not path.exists()

    def test_ensure_dir_creates_directory(self, tmp_cache):
        store = CacheStore(tmp_cache)
        d = store.ensure_dir("new_source", "new_dataset::001")
        assert d.exists()
        assert d.is_dir()
