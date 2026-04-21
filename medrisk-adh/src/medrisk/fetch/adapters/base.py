"""
base.py — Abstract adapter interface and shared HTTP helper.

Every data-source adapter must subclass AbstractAdapter and set source_name.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from medrisk.fetch._auth import AuthProvider
from medrisk.fetch._cache import CacheStore
from medrisk.fetch._schema import CohortDataset

_log = logging.getLogger(__name__)

_RETRYABLE = (
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    requests.exceptions.ChunkedEncodingError,
)


@dataclass
class DatasetInfo:
    """Metadata describing a single downloadable dataset."""

    dataset_id: str
    source: str
    title: str
    description: str
    url: str | None = None
    tags: list[str] = field(default_factory=list)
    requires_auth: bool = False
    license: str | None = None
    extra: dict = field(default_factory=dict)


@dataclass
class DownloadOptions:
    force_refresh: bool = False  # ignore cache and re-download
    checksum_algo: str = "sha256"  # "md5" | "sha256"
    expected_checksum: str | None = None
    timeout_seconds: int = 120
    chunk_size: int = 65536


class AbstractAdapter(ABC):
    """
    Base class for all data-source adapters.

    Subclasses must set the class-level ``source_name`` constant and implement
    list_datasets, get_metadata, download, and parse.
    """

    source_name: str  # set by each subclass, e.g. "nhanes"

    def __init__(
        self,
        config: dict,
        auth: AuthProvider,
        cache: CacheStore,
    ) -> None:
        self.config = config
        self.auth = auth
        self.cache = cache
        self._session: requests.Session | None = None

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def list_datasets(self, filters: dict | None = None) -> list[DatasetInfo]:
        """Return available datasets, optionally filtered by disease area / year / domain."""
        ...

    @abstractmethod
    def get_metadata(self, dataset_id: str) -> DatasetInfo:
        """Return metadata for a single dataset."""
        ...

    @abstractmethod
    def download(
        self,
        dataset_id: str,
        dest: Path,
        options: DownloadOptions | None = None,
    ) -> list[Path]:
        """
        Download files for dataset_id to dest directory.
        Returns list of local file paths.
        """
        ...

    @abstractmethod
    def parse(self, dataset_id: str, files: list[Path]) -> CohortDataset:
        """Read downloaded files and return a CohortDataset in internal schema."""
        ...

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def fetch(
        self,
        dataset_id: str,
        dest: Path,
        options: DownloadOptions | None = None,
    ) -> CohortDataset:
        """Convenience: download + parse in one call."""
        files = self.download(dataset_id, dest, options)
        return self.parse(dataset_id, files)

    # ------------------------------------------------------------------
    # Shared HTTP helpers
    # ------------------------------------------------------------------

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update(self.auth.get_headers())
        return self._session

    def _get_with_retry(
        self,
        url: str,
        params: dict | None = None,
        timeout: int = 60,
        stream: bool = False,
    ) -> requests.Response:
        """
        HTTP GET with exponential-backoff retry on transient errors.
        Auth headers are injected from self.auth.
        """
        session = self._get_session()
        merged_params = {**self.auth.get_params(), **(params or {})}

        @retry(
            retry=retry_if_exception_type(_RETRYABLE),
            wait=wait_exponential(multiplier=1, min=2, max=30),
            stop=stop_after_attempt(5),
            before_sleep=before_sleep_log(_log, logging.WARNING),
            reraise=True,
        )
        def _do_get() -> requests.Response:
            resp = session.get(url, params=merged_params, timeout=timeout, stream=stream)
            resp.raise_for_status()
            return resp

        _log.debug("GET %s (params=%s)", url, merged_params)
        return _do_get()

    def _download_file(
        self,
        url: str,
        dest_path: Path,
        options: DownloadOptions | None = None,
        params: dict | None = None,
    ) -> Path:
        """
        Download a single file to dest_path, using the cache if already present.
        Writes a sidecar checksum file on completion.
        """
        opts = options or DownloadOptions()
        source = self.source_name
        dataset_id = dest_path.parent.name  # approximate; callers can override
        filename = dest_path.name

        if not opts.force_refresh and self.cache.is_cached(
            source, dataset_id, filename, opts.expected_checksum
        ):
            _log.debug("Cache hit: %s", dest_path)
            return dest_path

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        _log.info("Downloading %s -> %s", url, dest_path)
        resp = self._get_with_retry(url, params=params, timeout=opts.timeout_seconds, stream=True)
        with open(dest_path, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=opts.chunk_size):
                fh.write(chunk)

        checksum = self.cache.compute_checksum(dest_path)
        self.cache.write_checksum(dest_path, checksum)
        if opts.expected_checksum and checksum != opts.expected_checksum:
            _log.error("Checksum mismatch for %s", dest_path)
        return dest_path

    @staticmethod
    def _parse_dataset_id(dataset_id: str) -> list[str]:
        """Split namespaced dataset_id on '::' and return parts."""
        return dataset_id.split("::")
