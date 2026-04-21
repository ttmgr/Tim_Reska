"""
cdc_places.py — CDC PLACES adapter.

CDC PLACES provides model-based small-area estimates of chronic disease
measures (diabetes, hypertension, obesity, etc.) for US counties, census
tracts, ZCTAs, and places.

Data are served via Socrata Open Data APIs.
An optional Socrata App Token (SOCRATA_APP_TOKEN env var) raises rate limits.

dataset_id format: ``cdc_places::<year>::<geography>``
  e.g. ``cdc_places::2023::county``
       ``cdc_places::2023::censustract``
       ``cdc_places::2023::zcta``
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

# Socrata dataset IDs for PLACES releases
# See: https://chronicdata.cdc.gov/browse?category=500+Cities+%26+Places
_SOCRATA_IDS: dict[str, dict[str, str]] = {
    "2023": {
        "county": "swc5-untb",
        "censustract": "cwsq-ngmh",
        "zcta": "qnzd-25i4",
    },
    "2022": {
        "county": "duw2-7jbt",
        "censustract": "shc3-fzig",
        "zcta": "hfr9-rurv",
    },
    "2021": {
        "county": "pqpp-u99h",
        "censustract": "373s-ayzu",
    },
}

_DEFAULT_SOCRATA_BASE = "https://chronicdata.cdc.gov/resource"
_PAGE_SIZE = 5000

# Measures of interest for disease progression modeling
_MEASURES_OF_INTEREST = {
    "DIABETES",  # Diagnosed diabetes among adults aged >=18 years
    "BPHIGH",  # High blood pressure among adults aged >=18 years
    "OBESITY",  # Obesity among adults aged >=18 years
    "BPMED",  # Taking medicine for high blood pressure
    "CHD",  # Coronary heart disease among adults
    "STROKE",  # Stroke among adults
    "KIDNEY",  # Chronic kidney disease among adults
}


@register
class CDCPLACESAdapter(AbstractAdapter):
    """CDC PLACES adapter -- area-level chronic disease prevalence estimates."""

    source_name = "cdc_places"

    def __init__(self, config: dict, auth: AuthProvider, cache: CacheStore) -> None:
        super().__init__(config, auth, cache)
        self._base = config.get("base_url", _DEFAULT_SOCRATA_BASE)

    # ------------------------------------------------------------------
    # AbstractAdapter interface
    # ------------------------------------------------------------------

    def list_datasets(self, filters: dict | None = None) -> list[DatasetInfo]:
        datasets = []
        for year, geos in _SOCRATA_IDS.items():
            for geo, socrata_id in geos.items():
                dataset_id = f"cdc_places::{year}::{geo}"
                datasets.append(
                    DatasetInfo(
                        dataset_id=dataset_id,
                        source=self.source_name,
                        title=f"CDC PLACES {year} -- {geo.replace('censustract', 'Census Tract').title()}",
                        description=(
                            f"Model-based chronic disease estimates for US {geo}s. "
                            f"Release year {year}. "
                            f"Measures include: {', '.join(sorted(_MEASURES_OF_INTEREST))}."
                        ),
                        url=f"https://chronicdata.cdc.gov/resource/{socrata_id}.csv",
                        tags=["CDC", "PLACES", "chronic-disease", "diabetes", "hypertension", geo],
                        requires_auth=False,
                        license="Public domain (CDC)",
                        extra={"socrata_id": socrata_id, "year": year, "geography": geo},
                    )
                )
        return datasets

    def get_metadata(self, dataset_id: str) -> DatasetInfo:
        parts = self._parse_dataset_id(dataset_id)
        year = parts[1] if len(parts) > 1 else "unknown"
        geo = parts[2] if len(parts) > 2 else "unknown"
        socrata_id = _SOCRATA_IDS.get(year, {}).get(geo, "unknown")
        return DatasetInfo(
            dataset_id=dataset_id,
            source=self.source_name,
            title=f"CDC PLACES {year} -- {geo}",
            description=f"Socrata ID: {socrata_id}",
            url=f"https://chronicdata.cdc.gov/resource/{socrata_id}.csv",
            tags=["CDC", "PLACES"],
            extra={"socrata_id": socrata_id},
        )

    def download(
        self,
        dataset_id: str,
        dest: Path,
        options: DownloadOptions | None = None,
    ) -> list[Path]:
        opts = options or DownloadOptions()
        parts = self._parse_dataset_id(dataset_id)
        year = parts[1] if len(parts) > 1 else "2023"
        geo = parts[2] if len(parts) > 2 else "county"
        socrata_id = _SOCRATA_IDS.get(year, {}).get(geo)
        if not socrata_id:
            raise ValueError(f"No Socrata dataset ID for {dataset_id!r}")

        cache_dir = self.cache.ensure_dir(self.source_name, dataset_id)
        out_path = cache_dir / f"places_{year}_{geo}.jsonl"

        if not opts.force_refresh and out_path.exists():
            _log.debug("Cache hit: %s", out_path)
            return [out_path]

        url = f"{self._base}/{socrata_id}.json"
        all_rows = []
        offset = 0
        while True:
            params = {
                "$limit": _PAGE_SIZE,
                "$offset": offset,
                "$where": f"measureid in ({','.join(repr(m) for m in _MEASURES_OF_INTEREST)})",
            }
            resp = self._get_with_retry(url, params=params, timeout=opts.timeout_seconds)
            rows = resp.json()
            if not rows:
                break
            all_rows.extend(rows)
            offset += len(rows)
            if len(rows) < _PAGE_SIZE:
                break
            _log.debug("PLACES %s %s: fetched %d rows so far", year, geo, offset)

        with open(out_path, "w") as fh:
            for row in all_rows:
                fh.write(json.dumps(row) + "\n")

        _log.info("PLACES %s %s: saved %d rows to %s", year, geo, len(all_rows), out_path)
        return [out_path]

    def parse(self, dataset_id: str, files: list[Path]) -> CohortDataset:
        """
        PLACES is area-level, not person-level.
        Maps each row to a Measurement with person_id = geo_id.
        measure_type = PLACES measure code (e.g. "DIABETES").
        value = prevalence estimate (data_value).
        """
        parts = self._parse_dataset_id(dataset_id)
        year = parts[1] if len(parts) > 1 else "unknown"
        measurements = []

        for fpath in files:
            with open(fpath) as fh:
                for line in fh:
                    row = json.loads(line)
                    geo_id = (
                        row.get("locationid")
                        or row.get("tractfips")
                        or row.get("locationname", "unknown")
                    )
                    measure_id = row.get("measureid", row.get("measure_id", ""))
                    raw_val = row.get("data_value")
                    if raw_val is None or raw_val == "":
                        continue
                    try:
                        val = float(raw_val)
                    except (ValueError, TypeError):
                        continue
                    # Use Jan 1 of the release year as the timestamp
                    ts = datetime(int(year), 1, 1) if year.isdigit() else datetime(2023, 1, 1)
                    measurements.append(
                        Measurement(
                            person_id=str(geo_id),
                            source=self.source_name,
                            dataset_id=dataset_id,
                            measured_at=ts,
                            measure_type=f"places_{measure_id.lower()}",
                            value=val,
                            unit="%",  # prevalence estimate
                            method="model-based",
                            extra={
                                "geography_level": row.get("geographiclevel", ""),
                                "location_name": row.get("locationname", ""),
                                "measure": row.get("measure", ""),
                                "confidence_low": row.get("low_confidence_limit"),
                                "confidence_high": row.get("high_confidence_limit"),
                            },
                        )
                    )
        _log.debug("PLACES: parsed %d area-level measurements", len(measurements))
        return CohortDataset(measurements=measurements)
