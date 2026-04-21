"""
glucose_ml.py — Glucose-ML meta-adapter.

Glucose-ML is a curated catalog of 10 longitudinal CGM datasets.
This adapter reads the catalog YAML and delegates per-dataset downloads
to appropriate sub-adapters (mostly ZenodoAdapter or direct HTTP).

dataset_id format: ``glucose_ml::<entry_id>``
  e.g. ``glucose_ml::glucose_ml::ohio_t1dm``
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import yaml

from medrisk.fetch._auth import AuthProvider
from medrisk.fetch._cache import CacheStore
from medrisk.fetch._registry import register
from medrisk.fetch._schema import CohortDataset, Measurement
from medrisk.fetch.adapters.base import AbstractAdapter, DatasetInfo, DownloadOptions
from medrisk.fetch.adapters.zenodo import ZenodoAdapter

_log = logging.getLogger(__name__)

_DEFAULT_CATALOG = "configs/glucose_ml_catalog.yml"


@register
class GlucoseMLAdapter(AbstractAdapter):
    """
    Glucose-ML meta-adapter.

    Reads a catalog YAML describing 10 CGM datasets and delegates
    download+parse to per-dataset sub-adapters.
    """

    source_name = "glucose_ml"

    def __init__(self, config: dict, auth: AuthProvider, cache: CacheStore) -> None:
        super().__init__(config, auth, cache)
        catalog_path = config.get("catalog_file", _DEFAULT_CATALOG)
        self._catalog: list[dict] = self._load_catalog(catalog_path)
        self._zenodo = ZenodoAdapter({"api_base": "https://zenodo.org/api"}, auth, cache)

    # ------------------------------------------------------------------
    # AbstractAdapter interface
    # ------------------------------------------------------------------

    def list_datasets(self, filters: dict | None = None) -> list[DatasetInfo]:
        results = []
        for entry in self._catalog:
            info = self._entry_to_datasetinfo(entry)
            if filters and "access" in filters and entry.get("access") != filters["access"]:
                continue
            results.append(info)
        return results

    def get_metadata(self, dataset_id: str) -> DatasetInfo:
        entry = self._find_entry(dataset_id)
        if entry is None:
            raise KeyError(f"Dataset {dataset_id!r} not found in Glucose-ML catalog")
        return self._entry_to_datasetinfo(entry)

    def download(
        self,
        dataset_id: str,
        dest: Path,
        options: DownloadOptions | None = None,
    ) -> list[Path]:
        opts = options or DownloadOptions()
        entry = self._find_entry(dataset_id)
        if entry is None:
            raise KeyError(f"Dataset {dataset_id!r} not found in Glucose-ML catalog")

        backend = entry.get("backend", "http")
        access = entry.get("access", "open")

        if access == "controlled":
            raise PermissionError(
                f"Dataset {dataset_id!r} requires controlled access registration. "
                f"Notes: {entry.get('notes', 'See dataset documentation.')}"
            )

        if backend == "zenodo":
            record_id = entry.get("zenodo_record_id")
            if not record_id:
                _log.warning("No zenodo_record_id for %s; skipping download", dataset_id)
                return []
            zenodo_id = f"zenodo::{record_id}"
            return self._zenodo.download(zenodo_id, dest, opts)

        if backend == "http":
            url = entry.get("url")
            if not url:
                _log.warning("No URL for %s; skipping download", dataset_id)
                return []
            cache_dir = self.cache.ensure_dir(self.source_name, dataset_id)
            filename = url.split("/")[-1] or "data.csv"
            local_path = cache_dir / filename
            return [self._download_file(url, local_path, opts)]

        raise ValueError(f"Unknown backend {backend!r} for {dataset_id!r}")

    def parse(self, dataset_id: str, files: list[Path]) -> CohortDataset:
        """
        Generic CGM parse: reads CSV files and maps columns to Measurement objects.
        Returns best-effort parse; domain-specific adapters can override per dataset.
        """
        measurements = []
        self._find_entry(dataset_id)  # validate dataset_id exists

        for fpath in files:
            if fpath.suffix.lower() not in (".csv", ".txt", ".tsv"):
                _log.debug("Skipping non-CSV file %s", fpath)
                continue
            try:
                import pandas as pd

                sep = "\t" if fpath.suffix.lower() in (".txt", ".tsv") else ","
                df = pd.read_csv(fpath, sep=sep)
            except Exception as exc:
                _log.warning("Could not read %s: %s", fpath, exc)
                continue

            pid_col = _first_col(df, ("patient_id", "PatientID", "id", "subject_id", "subjectid"))
            ts_col = _first_col(df, ("datetime", "DateTime", "timestamp", "date", "Date"))
            glucose_col = _first_col(df, ("glucose", "Glucose", "GlucoseValue", "value", "cgm"))

            if glucose_col is None:
                _log.debug("No glucose column found in %s", fpath)
                continue

            for _, row in df.iterrows():
                pid = str(row[pid_col]) if pid_col else "unknown"
                ts = _parse_ts(row.get(ts_col)) if ts_col else datetime.now()
                val = row.get(glucose_col)
                if (
                    ts is None
                    or val is None
                    or (isinstance(val, float) and __import__("math").isnan(val))
                ):
                    continue
                measurements.append(
                    Measurement(
                        person_id=pid,
                        source=self.source_name,
                        dataset_id=dataset_id,
                        measured_at=ts,
                        measure_type="glucose_mg_dl",
                        value=float(val),
                        unit="mg/dL",
                        method="CGM",
                    )
                )

        _log.debug("Glucose-ML %s: parsed %d CGM measurements", dataset_id, len(measurements))
        return CohortDataset(measurements=measurements)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load_catalog(self, catalog_path: str) -> list[dict]:
        p = Path(catalog_path)
        if not p.exists():
            _log.warning("Glucose-ML catalog not found at %s; using empty catalog", catalog_path)
            return []
        with open(p) as fh:
            data = yaml.safe_load(fh) or {}
        return data.get("datasets", [])

    def _find_entry(self, dataset_id: str) -> dict | None:
        for entry in self._catalog:
            if entry.get("id") == dataset_id:
                return entry
        return None

    def _entry_to_datasetinfo(self, entry: dict) -> DatasetInfo:
        return DatasetInfo(
            dataset_id=entry.get("id", "unknown"),
            source=self.source_name,
            title=entry.get("title", ""),
            description=entry.get("description", ""),
            url=entry.get("url", ""),
            tags=["CGM", "diabetes", "glucose-ml"],
            requires_auth=entry.get("access") == "controlled",
            extra={
                "backend": entry.get("backend"),
                "access": entry.get("access"),
                "n_persons": entry.get("n_persons"),
            },
        )


def _first_col(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _parse_ts(val) -> datetime | None:
    if val is None:
        return None
    try:
        import pandas as pd

        return pd.to_datetime(val).to_pydatetime().replace(tzinfo=None)
    except Exception:
        return None
