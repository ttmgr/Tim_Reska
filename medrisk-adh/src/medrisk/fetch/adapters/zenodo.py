"""
zenodo.py — Generic Zenodo REST API adapter.

Supports listing files for any public Zenodo record and downloading them.
Controlled records require a personal access token in ZENODO_TOKEN.
"""

from __future__ import annotations

import logging
from pathlib import Path

from medrisk.fetch._auth import AuthProvider
from medrisk.fetch._cache import CacheStore
from medrisk.fetch._registry import register
from medrisk.fetch._schema import CohortDataset
from medrisk.fetch.adapters.base import AbstractAdapter, DatasetInfo, DownloadOptions

_log = logging.getLogger(__name__)

API_BASE = "https://zenodo.org/api"


@register
class ZenodoAdapter(AbstractAdapter):
    """
    Generic Zenodo adapter.

    dataset_id format: ``zenodo::<record_id>``
    e.g. ``zenodo::8386456``
    """

    source_name = "zenodo"

    def __init__(self, config: dict, auth: AuthProvider, cache: CacheStore) -> None:
        super().__init__(config, auth, cache)
        self._api_base = config.get("api_base", API_BASE)

    # ------------------------------------------------------------------
    # AbstractAdapter interface
    # ------------------------------------------------------------------

    def list_datasets(self, filters: dict | None = None) -> list[DatasetInfo]:
        """
        Search Zenodo records matching filters.

        Accepted filter keys (mapped to Zenodo API query params):
          q         - free-text query
          communities - Zenodo community ID
          type      - record type (e.g. "dataset")
        """
        params: dict = {"type": "dataset", "size": 20}
        if filters:
            if "q" in filters:
                params["q"] = filters["q"]
            if "communities" in filters:
                params["communities"] = filters["communities"]
            params.update({k: v for k, v in filters.items() if k not in ("q", "communities")})

        resp = self._get_with_retry(f"{self._api_base}/records", params=params)
        hits = resp.json().get("hits", {}).get("hits", [])
        return [self._hit_to_datasetinfo(h) for h in hits]

    def get_metadata(self, dataset_id: str) -> DatasetInfo:
        record_id = self._record_id(dataset_id)
        resp = self._get_with_retry(f"{self._api_base}/records/{record_id}")
        return self._hit_to_datasetinfo(resp.json())

    def download(
        self,
        dataset_id: str,
        dest: Path,
        options: DownloadOptions | None = None,
    ) -> list[Path]:
        opts = options or DownloadOptions()
        record_id = self._record_id(dataset_id)
        resp = self._get_with_retry(f"{self._api_base}/records/{record_id}")
        record = resp.json()

        files = record.get("files", [])
        if not files:
            # Zenodo v3 API uses 'links.files' endpoint for restricted records
            files_url = record.get("links", {}).get("files", "")
            if files_url:
                files_resp = self._get_with_retry(files_url)
                files = files_resp.json().get("entries", [])

        cache_dir = self.cache.ensure_dir(self.source_name, dataset_id)
        local_paths = []
        for f in files:
            filename = f.get("key") or f.get("filename") or f.get("id", "unknown")
            file_url = (
                f.get("links", {}).get("self")
                or f.get("links", {}).get("download")
                or f.get("download_url", "")
            )
            checksum = f.get("checksum", "").replace("md5:", "").replace("sha256:", "")
            local_path = cache_dir / filename
            # Override expected_checksum from record metadata
            file_opts = DownloadOptions(
                force_refresh=opts.force_refresh,
                expected_checksum=checksum or opts.expected_checksum,
                timeout_seconds=opts.timeout_seconds,
                chunk_size=opts.chunk_size,
            )
            result = self._download_file(file_url, local_path, file_opts)
            local_paths.append(result)

        return local_paths

    def parse(self, dataset_id: str, files: list[Path]) -> CohortDataset:
        """
        Generic Zenodo adapter returns an empty CohortDataset.
        Domain-specific subclasses (e.g. T1DiabetesGranadaAdapter) override this.
        """
        _log.warning(
            "ZenodoAdapter.parse() returns empty CohortDataset for %s. "
            "Use a domain-specific adapter for structured parsing.",
            dataset_id,
        )
        return CohortDataset()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _record_id(self, dataset_id: str) -> str:
        parts = self._parse_dataset_id(dataset_id)
        # Accepts both "zenodo::12345" and bare "12345"
        return parts[-1] if len(parts) >= 1 else dataset_id

    def _hit_to_datasetinfo(self, hit: dict) -> DatasetInfo:
        meta = hit.get("metadata", hit)
        record_id = str(hit.get("id", hit.get("record_id", "")))
        doi = hit.get("doi", meta.get("doi", ""))
        return DatasetInfo(
            dataset_id=f"zenodo::{record_id}",
            source=self.source_name,
            title=meta.get("title", ""),
            description=meta.get("description", ""),
            url=f"https://zenodo.org/record/{record_id}",
            tags=meta.get("keywords", []),
            license=meta.get("license", {}).get("id")
            if isinstance(meta.get("license"), dict)
            else meta.get("license"),
            extra={"doi": doi, "record_id": record_id},
        )
