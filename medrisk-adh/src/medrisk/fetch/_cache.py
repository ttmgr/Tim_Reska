"""
_cache.py — Filesystem cache with sidecar checksum files.

Merged from cohort_fetch.cache.__init__ and cohort_fetch.cache.store.

Cache layout:
  <base_dir>/<source>/<dataset_id_safe>/<filename>
  <base_dir>/<source>/<dataset_id_safe>/<filename>.sha256
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

_log = logging.getLogger(__name__)

_SAFE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")


def _safe_name(s: str) -> str:
    """Replace characters unsafe for filesystem paths with underscores."""
    return "".join(c if c in _SAFE_CHARS else "_" for c in s)


class CacheStore:
    """
    Filesystem cache keyed by (source, dataset_id, filename).
    Checksums are stored in sidecar .sha256 files adjacent to each cached file.
    """

    def __init__(self, base_dir: Path, algo: str = "sha256") -> None:
        self.base_dir = Path(base_dir)
        self.algo = algo

    def _dir(self, source: str, dataset_id: str) -> Path:
        return self.base_dir / _safe_name(source) / _safe_name(dataset_id)

    def get_path(self, source: str, dataset_id: str, filename: str) -> Path:
        """Return deterministic cache path (does not check existence)."""
        return self._dir(source, dataset_id) / filename

    def is_cached(
        self,
        source: str,
        dataset_id: str,
        filename: str,
        expected_checksum: str | None = None,
    ) -> bool:
        """
        Return True if file exists and checksum matches (or no checksum required).
        """
        path = self.get_path(source, dataset_id, filename)
        if not path.exists():
            return False
        if expected_checksum is None:
            # Accept if sidecar checksum exists and is non-empty
            sidecar = path.with_suffix(path.suffix + f".{self.algo}")
            return sidecar.exists()
        return self.verify(path, expected_checksum)

    def compute_checksum(self, path: Path) -> str:
        """Stream-compute checksum of file at path."""
        h = hashlib.new(self.algo)
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def write_checksum(self, path: Path, checksum: str) -> None:
        """Write checksum to sidecar file <path>.<algo>."""
        sidecar = path.with_suffix(path.suffix + f".{self.algo}")
        sidecar.write_text(checksum)

    def verify(self, path: Path, expected: str) -> bool:
        """Compute and compare checksum; return True if match."""
        actual = self.compute_checksum(path)
        if actual != expected:
            _log.warning("Checksum mismatch for %s: expected %s, got %s", path, expected, actual)
            return False
        return True

    def ensure_dir(self, source: str, dataset_id: str) -> Path:
        """Create cache directory if it does not exist; return its path."""
        d = self._dir(source, dataset_id)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def invalidate(self, source: str, dataset_id: str) -> None:
        """Remove all cached files and sidecar checksums for a dataset."""
        d = self._dir(source, dataset_id)
        if d.exists():
            for f in d.iterdir():
                f.unlink()
            _log.info("Invalidated cache for %s / %s", source, dataset_id)
