"""
datagov.py — data.gov catalog adapter.

Searches the US open data catalog (data.gov) for chronic disease datasets
and downloads from Socrata-style endpoints where available.

To avoid brittleness from the wide quality variation in catalog entries,
this adapter maintains a small whitelist of well-structured chronic disease
datasets known to be stable and documented.

dataset_id format: ``data_gov::<catalog_name>``
  e.g. ``data_gov::diabetes-hypertension-comorbidity``
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from medrisk.fetch._auth import AuthProvider
from medrisk.fetch._cache import CacheStore
from medrisk.fetch._registry import register
from medrisk.fetch._schema import CohortDataset, Measurement
from medrisk.fetch.adapters.base import AbstractAdapter, DatasetInfo, DownloadOptions

_log = logging.getLogger(__name__)

_CATALOG_SEARCH_URL = "https://catalog.data.gov/api/3/action/package_search"

# Whitelisted datasets: name -> known Socrata resource URL
_WHITELIST: dict[str, dict] = {
    "diabetes-hypertension-comorbidity": {
        "title": "Diabetes + Hypertension Comorbidity",
        "description": (
            "De-identified population data for diabetes and hypertension comorbidity "
            "prevalence by US county. From data.gov catalog."
        ),
        "socrata_url": "https://data.cdc.gov/resource/g4ie-h725.json",
        "tags": ["diabetes", "hypertension", "comorbidity", "county"],
        "license": "Public domain (CDC)",
    },
}

_PAGE_SIZE = 5000


@register
class DataGovAdapter(AbstractAdapter):
    """data.gov adapter -- chronic disease datasets via Socrata API."""

    source_name = "data_gov"

    def __init__(self, config: dict, auth: AuthProvider, cache: CacheStore) -> None:
        super().__init__(config, auth, cache)
        self._catalog_url = config.get("catalog_url", _CATALOG_SEARCH_URL)
        # Merge config whitelist with built-in whitelist
        extra = {
            name: {"title": name, "description": "", "socrata_url": "", "tags": []}
            for name in config.get("whitelist", [])
        }
        self._whitelist = {**_WHITELIST, **extra}

    # ------------------------------------------------------------------
    # AbstractAdapter interface
    # ------------------------------------------------------------------

    def list_datasets(self, filters: dict | None = None) -> list[DatasetInfo]:
        datasets = []
        for name, info in self._whitelist.items():
            dataset_id = f"data_gov::{name}"
            datasets.append(
                DatasetInfo(
                    dataset_id=dataset_id,
                    source=self.source_name,
                    title=info.get("title", name),
                    description=info.get("description", ""),
                    url=info.get("socrata_url", ""),
                    tags=info.get("tags", []),
                    license=info.get("license", ""),
                )
            )

        # Optionally search the catalog for additional datasets
        if filters and "q" in filters:
            try:
                catalog_results = self._search_catalog(filters["q"])
                datasets.extend(catalog_results)
            except Exception as exc:
                _log.warning("data.gov catalog search failed: %s", exc)

        return datasets

    def get_metadata(self, dataset_id: str) -> DatasetInfo:
        parts = self._parse_dataset_id(dataset_id)
        name = parts[1] if len(parts) > 1 else dataset_id
        info = self._whitelist.get(name, {})
        return DatasetInfo(
            dataset_id=dataset_id,
            source=self.source_name,
            title=info.get("title", name),
            description=info.get("description", ""),
            url=info.get("socrata_url", ""),
            tags=info.get("tags", []),
            license=info.get("license", ""),
        )

    def download(
        self,
        dataset_id: str,
        dest: Path,
        options: DownloadOptions | None = None,
    ) -> list[Path]:
        opts = options or DownloadOptions()
        parts = self._parse_dataset_id(dataset_id)
        name = parts[1] if len(parts) > 1 else dataset_id
        info = self._whitelist.get(name)
        if not info or not info.get("socrata_url"):
            raise ValueError(
                f"No known Socrata URL for {dataset_id!r}. "
                "Add it to the whitelist in sources.yml or pass filters with q=<search term>."
            )

        cache_dir = self.cache.ensure_dir(self.source_name, dataset_id)
        out_path = cache_dir / f"{name}.jsonl"

        if not opts.force_refresh and out_path.exists():
            _log.debug("Cache hit: %s", out_path)
            return [out_path]

        url = info["socrata_url"]
        all_rows = []
        offset = 0
        while True:
            params = {"$limit": _PAGE_SIZE, "$offset": offset}
            try:
                resp = self._get_with_retry(url, params=params, timeout=opts.timeout_seconds)
                rows = resp.json()
            except Exception as exc:
                _log.error("data.gov download error at offset %d: %s", offset, exc)
                break
            if not rows:
                break
            all_rows.extend(rows)
            offset += len(rows)
            if len(rows) < _PAGE_SIZE:
                break

        with open(out_path, "w") as fh:
            for row in all_rows:
                fh.write(json.dumps(row) + "\n")

        _log.info("data.gov %s: saved %d rows to %s", name, len(all_rows), out_path)
        return [out_path]

    def parse(self, dataset_id: str, files: list[Path]) -> CohortDataset:
        """
        Parse a data.gov/Socrata JSONL file into area-level Measurements.
        person_id = geographic unit identifier (county FIPS, etc.)
        """
        measurements = []
        for fpath in files:
            with open(fpath) as fh:
                for line in fh:
                    row = json.loads(line)
                    geo_id = (
                        row.get("countyFIPS")
                        or row.get("county_fips")
                        or row.get("locationid")
                        or row.get("geoid")
                        or "unknown"
                    )
                    for field, val in row.items():
                        if field.lower() in (
                            "countyfips",
                            "county_fips",
                            "locationid",
                            "geoid",
                            "state",
                            "county",
                            "year",
                            "location_name",
                        ):
                            continue
                        try:
                            fval = float(val)
                        except (ValueError, TypeError):
                            continue
                        year_raw = row.get("year", row.get("Year", "2020"))
                        try:
                            ts = datetime(int(str(year_raw)[:4]), 1, 1)
                        except (ValueError, TypeError):
                            ts = datetime(2020, 1, 1)
                        measurements.append(
                            Measurement(
                                person_id=str(geo_id),
                                source=self.source_name,
                                dataset_id=dataset_id,
                                measured_at=ts,
                                measure_type=field.lower().replace(" ", "_"),
                                value=fval,
                                unit="unknown",
                                method="survey-estimate",
                            )
                        )
        _log.debug("data.gov: parsed %d measurements", len(measurements))
        return CohortDataset(measurements=measurements)

    # ------------------------------------------------------------------
    # Catalog search
    # ------------------------------------------------------------------

    def _search_catalog(self, query: str) -> list[DatasetInfo]:
        params = {"q": query, "fq": "organization_type:Federal+Government", "rows": 20}
        resp = self._get_with_retry(self._catalog_url, params=params)
        results = resp.json().get("result", {}).get("results", [])
        datasets = []
        for pkg in results:
            name = pkg.get("name", "")
            dataset_id = f"data_gov::{name}"
            # Extract first downloadable CSV/JSON resource URL
            url = ""
            for resource in pkg.get("resources", []):
                if resource.get("format", "").upper() in ("CSV", "JSON"):
                    url = resource.get("url", "")
                    break
            datasets.append(
                DatasetInfo(
                    dataset_id=dataset_id,
                    source=self.source_name,
                    title=pkg.get("title", name),
                    description=pkg.get("notes", ""),
                    url=url,
                    tags=[t.get("name", "") for t in pkg.get("tags", [])],
                )
            )
        return datasets
