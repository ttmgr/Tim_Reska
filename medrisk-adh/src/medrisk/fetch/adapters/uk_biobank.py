"""
uk_biobank.py — UK Biobank adapter.

Controlled-access adapter: assumes application data has already been downloaded
to a local directory pointed to by env var UKB_DATA_PATH (or config['data_path']).

The adapter's value is in parse(): mapping UKB field IDs to internal schema
and translating ICD-10 / Read / SNOMED codes from hospital episode and
primary care tables.

This adapter does NOT attempt to automate or bypass the UKB access approval process.
download() is a no-op that verifies the expected files are present locally.

dataset_id format: ``ukb::<application_id_or_label>``
  e.g. ``ukb::application``
"""

from __future__ import annotations

import contextlib
import logging
import os
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from medrisk.fetch._auth import AuthProvider
from medrisk.fetch._cache import CacheStore
from medrisk.fetch._registry import register
from medrisk.fetch._schema import CohortDataset, Event, Measurement, Person
from medrisk.fetch.adapters.base import AbstractAdapter, DatasetInfo, DownloadOptions

_log = logging.getLogger(__name__)

# UKB field IDs of interest for diabetes/hypertension progression modeling
_FIELD_MAP: dict[int, str] = {
    31: "sex",  # 0=Female, 1=Male
    34: "birth_year",
    21003: "age_at_recruitment",
    21001: "bmi_kg_m2",
    4079: "dbp_mmhg",
    4080: "sbp_mmhg",
    30750: "hba1c_mmol_mol",
    2443: "diabetes_diagnosed",
    2453: "cancer_diagnosed",
    40000: "death_date",
}

# Hospital episode tables expected under UKB_DATA_PATH
_HES_DIAG_FILE = "hesin_diag.txt"
_HES_FILE = "hesin.txt"
_GP_CLINICAL_FILE = "gp_clinical.txt"
_GP_SCRIPTS_FILE = "gp_scripts.txt"


@register
class UKBiobankAdapter(AbstractAdapter):
    """
    UK Biobank adapter -- local-file only.

    Requires UKB_DATA_PATH environment variable pointing to the directory
    containing the application phenotype files.
    """

    source_name = "uk_biobank"

    def __init__(self, config: dict, auth: AuthProvider, cache: CacheStore) -> None:
        super().__init__(config, auth, cache)
        env_var = config.get("data_path_env", "UKB_DATA_PATH")
        raw = os.environ.get(env_var, config.get("data_path", ""))
        self._data_path: Path | None = Path(raw) if raw else None

    # ------------------------------------------------------------------
    # AbstractAdapter interface
    # ------------------------------------------------------------------

    def list_datasets(self, filters: dict | None = None) -> list[DatasetInfo]:
        if not self._data_path or not self._data_path.exists():
            _log.warning(
                "UKB_DATA_PATH not set or does not exist. "
                "Set UKB_DATA_PATH to the directory with your approved application data."
            )
            return []
        files = list(self._data_path.glob("*.tab")) + list(self._data_path.glob("*.enc_ukb"))
        return [
            DatasetInfo(
                dataset_id=f"ukb::{f.stem}",
                source=self.source_name,
                title=f"UK Biobank -- {f.name}",
                description=f"Application data file: {f}",
                url=None,
                requires_auth=True,
                license="UK Biobank Data Access Agreement",
            )
            for f in files
        ]

    def get_metadata(self, dataset_id: str) -> DatasetInfo:
        return DatasetInfo(
            dataset_id=dataset_id,
            source=self.source_name,
            title="UK Biobank application data",
            description=(
                "Controlled-access prospective cohort (~500K participants). "
                "Requires approved application. Access via UKB_DATA_PATH."
            ),
            url="https://www.ukbiobank.ac.uk",
            requires_auth=True,
            license="UK Biobank Data Access Agreement",
        )

    def download(
        self,
        dataset_id: str,
        dest: Path,
        options: DownloadOptions | None = None,
    ) -> list[Path]:
        """
        No-op download: UK Biobank data must already be present locally.
        Verifies that UKB_DATA_PATH is set and contains expected files.
        """
        if not self._data_path or not self._data_path.exists():
            raise FileNotFoundError(
                "UK Biobank data path not found. "
                "Please set the UKB_DATA_PATH environment variable to the directory "
                "containing your approved application data files."
                "\n\nUKB data must be obtained via an approved application at "
                "https://www.ukbiobank.ac.uk/enable-your-research/apply-for-access"
            )
        _log.info("UKB: using local data at %s", self._data_path)
        return list(self._data_path.glob("*.tab")) + list(self._data_path.glob("*.txt"))

    def parse(self, dataset_id: str, files: list[Path]) -> CohortDataset:
        """
        Parse UKB application files into internal schema.

        Expects:
          - A main phenotype .tab file with field IDs as column headers (f.<field>.<instance>.<array>)
          - hesin_diag.txt for hospital diagnoses (ICD-10)
          - gp_clinical.txt for primary care (Read codes)
          - gp_scripts.txt for prescriptions
        """
        persons: list[Person] = []
        measurements: list[Measurement] = []
        events: list[Event] = []
        from medrisk.fetch._schema import Treatment

        treatments: list[Treatment] = []

        for fpath in files:
            if fpath.name == _HES_DIAG_FILE:
                events += self._parse_hes_diag(fpath, dataset_id)
            elif fpath.name == _GP_CLINICAL_FILE:
                events += self._parse_gp_clinical(fpath, dataset_id)
            elif fpath.name == _GP_SCRIPTS_FILE:
                treatments += self._parse_gp_scripts(fpath, dataset_id)
            elif fpath.suffix == ".tab":
                ps, ms = self._parse_phenotype_tab(fpath, dataset_id)
                persons += ps
                measurements += ms

        _log.debug(
            "UKB: parsed %d persons, %d measurements, %d events, %d treatments",
            len(persons),
            len(measurements),
            len(events),
            len(treatments),
        )
        return CohortDataset(
            persons=persons,
            measurements=measurements,
            events=events,
            treatments=treatments,
        )

    # ------------------------------------------------------------------
    # Domain parsers
    # ------------------------------------------------------------------

    def _parse_phenotype_tab(
        self, fpath: Path, dataset_id: str
    ) -> tuple[list[Person], list[Measurement]]:
        """Parse the main phenotype .tab file; maps field IDs to schema."""
        try:
            df = pd.read_csv(fpath, sep="\t", nrows=None, low_memory=False)
        except Exception as exc:
            _log.warning("UKB: failed to read phenotype file %s: %s", fpath, exc)
            return [], []

        persons: list[Person] = []
        measurements: list[Measurement] = []
        # UKB columns follow f.<field_id>.<instance>.<array_index> convention
        col_field: dict[str, int] = {}
        for col in df.columns:
            parts = col.split(".")
            if len(parts) >= 2 and parts[0] == "f":
                with contextlib.suppress(ValueError):
                    col_field[col] = int(parts[1])

        eid_col = "eid" if "eid" in df.columns else df.columns[0]

        for _, row in df.iterrows():
            pid = str(row[eid_col])
            sex_val = None
            birth_year = None

            # Pick up key fields
            for col, field_id in col_field.items():
                val = row.get(col)
                if val is None or (isinstance(val, float) and pd.isna(val)):
                    continue
                if field_id == 31:
                    sex_val = "M" if int(val) == 1 else "F"
                elif field_id == 34:
                    with contextlib.suppress(ValueError, TypeError):
                        birth_year = int(val)
                elif field_id in (21001, 4079, 4080, 30750):
                    measure_type, unit = {
                        21001: ("bmi_kg_m2", "kg/m2"),
                        4079: ("dbp_mmhg", "mmHg"),
                        4080: ("sbp_mmhg", "mmHg"),
                        30750: ("hba1c_mmol_mol", "mmol/mol"),
                    }[field_id]
                    measurements.append(
                        Measurement(
                            person_id=pid,
                            source=self.source_name,
                            dataset_id=dataset_id,
                            measured_at=datetime(birth_year or 2006, 1, 1),
                            measure_type=measure_type,
                            value=float(val),
                            unit=unit,
                            method="exam" if field_id in (4079, 4080, 21001) else "lab",
                        )
                    )

            persons.append(
                Person(
                    person_id=pid,
                    source=self.source_name,
                    dataset_id=dataset_id,
                    sex=sex_val,
                    birth_year=birth_year,
                )
            )

        return persons, measurements

    def _parse_hes_diag(self, fpath: Path, dataset_id: str) -> list[Event]:
        """Parse hospital episode diagnoses (ICD-10)."""
        try:
            df = pd.read_csv(fpath, sep="\t", low_memory=False)
        except Exception as exc:
            _log.warning("UKB: failed to read HES diag %s: %s", fpath, exc)
            return []
        events = []
        for _, row in df.iterrows():
            pid = str(row.get("eid", ""))
            code = str(row.get("diag_icd10", row.get("diag_icd9", ""))).strip()
            date_raw = row.get("epistart") or row.get("admidate")
            if not pid or not code:
                continue
            event_date = _parse_date(date_raw)
            if event_date is None:
                continue
            code_system = "ICD10" if "diag_icd10" in df.columns else "ICD9"
            events.append(
                Event(
                    person_id=pid,
                    source=self.source_name,
                    dataset_id=dataset_id,
                    event_date=event_date,
                    event_type="hospitalization",
                    code_system=code_system,
                    code=code,
                )
            )
        return events

    def _parse_gp_clinical(self, fpath: Path, dataset_id: str) -> list[Event]:
        """Parse GP (primary care) clinical events (Read codes)."""
        try:
            df = pd.read_csv(fpath, sep="\t", low_memory=False)
        except Exception as exc:
            _log.warning("UKB: failed to read GP clinical %s: %s", fpath, exc)
            return []
        events = []
        for _, row in df.iterrows():
            pid = str(row.get("eid", ""))
            code = str(row.get("read_2", row.get("read_3", ""))).strip()
            date_raw = row.get("event_dt")
            if not pid or not code:
                continue
            event_date = _parse_date(date_raw)
            if event_date is None:
                continue
            events.append(
                Event(
                    person_id=pid,
                    source=self.source_name,
                    dataset_id=dataset_id,
                    event_date=event_date,
                    event_type="diagnosis",
                    code_system="Read",
                    code=code,
                )
            )
        return events

    def _parse_gp_scripts(self, fpath: Path, dataset_id: str):
        """Parse GP prescriptions into Treatment records."""
        from medrisk.fetch._schema import Treatment

        try:
            df = pd.read_csv(fpath, sep="\t", low_memory=False)
        except Exception as exc:
            _log.warning("UKB: failed to read GP scripts %s: %s", fpath, exc)
            return []
        treatments = []
        for _, row in df.iterrows():
            pid = str(row.get("eid", ""))
            date_raw = row.get("issue_date")
            drug = str(row.get("drug_name", "")).strip()
            if not pid or not drug:
                continue
            start_date = _parse_date(date_raw)
            if start_date is None:
                continue
            treatments.append(
                Treatment(
                    person_id=pid,
                    source=self.source_name,
                    dataset_id=dataset_id,
                    start_date=start_date,
                    drug_name=drug,
                )
            )
        return treatments


def _parse_date(val) -> date | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return pd.to_datetime(val, dayfirst=True).date()
    except Exception:
        return None
