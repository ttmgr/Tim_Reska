"""
_pipeline.py — PipelineRunner: orchestrates the full fetch pipeline.

Workflow:
  1. Resolve study name -> (source, dataset_ids) if --study is used
  2. Instantiate the adapter from the registry
  3. For each dataset_id: download -> parse
  4. Harmonize (unit conversion, code mapping)
  5. Validate (cross-table integrity)
  6. Export to parquet (if output_dir is given)
  7. Return list of CohortDataset objects
"""

from __future__ import annotations

import logging
from pathlib import Path

import medrisk.fetch.adapters.biolincc  # noqa: F401
import medrisk.fetch.adapters.cdc_places  # noqa: F401
import medrisk.fetch.adapters.datagov  # noqa: F401
import medrisk.fetch.adapters.glucose_ml  # noqa: F401

# Import all adapters so their @register decorators fire
import medrisk.fetch.adapters.nhanes  # noqa: F401
import medrisk.fetch.adapters.t1_granada  # noqa: F401
import medrisk.fetch.adapters.uk_biobank  # noqa: F401
import medrisk.fetch.adapters.zenodo  # noqa: F401
from medrisk.fetch._auth import build_auth_provider
from medrisk.fetch._cache import CacheStore
from medrisk.fetch._harmonizer import Harmonizer
from medrisk.fetch._registry import get_adapter_class, list_sources
from medrisk.fetch._schema import CohortDataset
from medrisk.fetch._settings import AppSettings
from medrisk.fetch._validators import validate
from medrisk.fetch.adapters.base import AbstractAdapter, DownloadOptions

_log = logging.getLogger(__name__)


class PipelineRunner:
    """Orchestrates source discovery, download, parsing, harmonization, and export."""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.cache = CacheStore(settings.cache_dir)
        self._harmonizer = Harmonizer()

    def run(
        self,
        source: str,
        dataset_ids: list[str] | None = None,
        study: str | None = None,
        output_dir: Path | None = None,
        force_refresh: bool = False,
    ) -> list[CohortDataset]:
        """
        Full pipeline for one source.

        Returns a list of CohortDataset objects, one per dataset_id processed.
        """
        if study:
            source, dataset_ids = self._resolve_study(study)

        if not dataset_ids:
            _log.info("No dataset_ids specified; listing all datasets for source %r", source)
            adapter = self._build_adapter(source)
            dataset_ids = [ds.dataset_id for ds in adapter.list_datasets()]
            if not dataset_ids:
                _log.warning("No datasets found for source %r", source)
                return []

        adapter = self._build_adapter(source)
        opts = DownloadOptions(force_refresh=force_refresh)
        results: list[CohortDataset] = []

        for did in dataset_ids:
            _log.info("Pipeline: processing %s", did)
            try:
                # Determine cache/dest dir
                dest = self.cache.ensure_dir(source, did)
                # Download
                files = adapter.download(did, dest, opts)
                # Parse
                dataset = adapter.parse(did, files)
                # Harmonize
                dataset = self._harmonizer.normalize_all(dataset)
                # Validate (warnings logged; errors logged but non-fatal)
                vresult = validate(dataset)
                if not vresult.is_valid:
                    _log.warning("Validation errors for %s:\n%s", did, vresult)
                # Export
                if output_dir:
                    self._export(dataset, did, Path(output_dir))
                results.append(dataset)
                _log.info(
                    "Pipeline: done %s -- %s",
                    did,
                    dataset.summary(),
                )
            except NotImplementedError as exc:
                _log.warning("Pipeline skipping %s (not implemented): %s", did, exc)
            except PermissionError as exc:
                _log.warning("Pipeline skipping %s (controlled access): %s", did, exc)
            except FileNotFoundError as exc:
                _log.error("Pipeline error %s (file not found): %s", did, exc)
            except Exception as exc:
                _log.error("Pipeline error processing %s: %s", did, exc, exc_info=True)

        return results

    def list_datasets(self, source: str, filters: dict | None = None):
        """Delegate to adapter.list_datasets() and return DatasetInfo list."""
        adapter = self._build_adapter(source)
        return adapter.list_datasets(filters)

    def inspect(self, source: str, dataset_id: str):
        """Return DatasetInfo for a specific dataset."""
        adapter = self._build_adapter(source)
        return adapter.get_metadata(dataset_id)

    def available_sources(self) -> list[str]:
        return list_sources()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_study(self, study: str) -> tuple[str, list[str]]:
        """Resolve a named study to (source, dataset_ids) from studies.yml."""
        studies = self.settings.studies()
        if study not in studies:
            raise KeyError(
                f"Study {study!r} not found in studies.yml. Available: {sorted(studies)}"
            )
        entry = studies[study]
        source = entry.get("source", "")
        dataset_ids = entry.get("dataset_ids", [])
        _log.info("Study %r -> source=%r, %d dataset_ids", study, source, len(dataset_ids))
        return source, dataset_ids

    def _build_adapter(self, source: str) -> AbstractAdapter:
        """Construct an adapter instance using settings from sources.yml."""
        sources = self.settings.sources()
        source_config = sources.get(source, {})
        auth = build_auth_provider(source_config)
        if not auth.is_configured and source_config.get("auth") not in ("none", "local_path"):
            _log.warning(
                "Auth for source %r is not configured (missing env var). "
                "Downloads may fail for restricted resources.",
                source,
            )
        adapter_cls = get_adapter_class(source)
        return adapter_cls(source_config, auth, self.cache)

    def _export(self, dataset: CohortDataset, dataset_id: str, output_dir: Path) -> None:
        """Write CohortDataset tables to parquet files under output_dir/<safe_dataset_id>/."""
        from medrisk.fetch._writers import write_cohort_dataset

        safe_id = dataset_id.replace("::", "__").replace("/", "_")
        dest = output_dir / safe_id
        dest.mkdir(parents=True, exist_ok=True)
        write_cohort_dataset(dataset, dest)
        _log.info("Exported %s to %s", dataset_id, dest)
