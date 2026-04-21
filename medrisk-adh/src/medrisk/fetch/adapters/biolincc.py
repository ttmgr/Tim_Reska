"""
biolincc.py — NHLBI BioLINCC adapter.

Supports:
  - Public teaching datasets: direct HTTPS download from BioLINCC
  - Controlled datasets: no-op stub (workspace assumption)

Teaching datasets include a simplified Framingham Heart Study dataset with
three examination cycles and 20-year follow-up.

dataset_id format: ``biolincc::<access>::<study_name>``
  e.g. ``biolincc::teaching::framingham``
       ``biolincc::controlled::aric``
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd

from medrisk.fetch._auth import AuthProvider
from medrisk.fetch._cache import CacheStore
from medrisk.fetch._registry import register
from medrisk.fetch._schema import CohortDataset, Event, Measurement, Person
from medrisk.fetch.adapters.base import AbstractAdapter, DatasetInfo, DownloadOptions

_log = logging.getLogger(__name__)

# Known teaching datasets with metadata
_TEACHING_DATASETS: dict[str, dict] = {
    "framingham": {
        "title": "Framingham Heart Study Teaching Dataset",
        "description": (
            "Simplified Framingham dataset with 3 examination cycles, "
            "20-year follow-up for cardiovascular outcomes. "
            "Includes demographics, risk factors (BP, cholesterol, glucose, BMI), "
            "and events (coronary heart disease, death)."
        ),
        "url": "https://biolincc.nhlbi.nih.gov/teaching/",
        "tags": ["Framingham", "cardiovascular", "hypertension", "diabetes", "longitudinal"],
        "license": "BioLINCC Data Use Agreement",
    },
}

_KNOWN_CONTROLLED: set[str] = {"aric", "mesa", "chs", "jhs", "cardia", "accord", "sprint"}


@register
class BioLINCCAdapter(AbstractAdapter):
    """
    NHLBI BioLINCC adapter.

    Teaching datasets: direct HTTPS download.
    Controlled datasets: raises NotImplementedError; assumes workspace environment.
    """

    source_name = "biolincc"

    def __init__(self, config: dict, auth: AuthProvider, cache: CacheStore) -> None:
        super().__init__(config, auth, cache)
        env_var = config.get("data_path_env", "BIOLINCC_DATA_PATH")
        self._local_path = (
            Path(os.environ.get(env_var, config.get("data_path", "")))
            if os.environ.get(env_var)
            else None
        )

    # ------------------------------------------------------------------
    # AbstractAdapter interface
    # ------------------------------------------------------------------

    def list_datasets(self, filters: dict | None = None) -> list[DatasetInfo]:
        datasets = []
        for name, info in _TEACHING_DATASETS.items():
            dataset_id = f"biolincc::teaching::{name}"
            datasets.append(
                DatasetInfo(
                    dataset_id=dataset_id,
                    source=self.source_name,
                    title=info["title"],
                    description=info["description"],
                    url=info["url"],
                    tags=info["tags"],
                    requires_auth=False,
                    license=info.get("license", ""),
                )
            )
        for name in _KNOWN_CONTROLLED:
            datasets.append(
                DatasetInfo(
                    dataset_id=f"biolincc::controlled::{name}",
                    source=self.source_name,
                    title=f"BioLINCC -- {name.upper()} (controlled access)",
                    description=f"Controlled-access NHLBI cohort study {name.upper()}. "
                    "Requires BioLINCC application.",
                    url="https://biolincc.nhlbi.nih.gov/studies/",
                    tags=["cardiovascular", "longitudinal", name],
                    requires_auth=True,
                    license="BioLINCC Data Use Agreement",
                )
            )
        return datasets

    def get_metadata(self, dataset_id: str) -> DatasetInfo:
        parts = self._parse_dataset_id(dataset_id)
        access = parts[1] if len(parts) > 1 else "teaching"
        name = parts[2] if len(parts) > 2 else "unknown"
        if access == "teaching" and name in _TEACHING_DATASETS:
            info = _TEACHING_DATASETS[name]
            return DatasetInfo(
                dataset_id=dataset_id,
                source=self.source_name,
                title=info["title"],
                description=info["description"],
                url=info["url"],
                tags=info["tags"],
                requires_auth=False,
                license=info.get("license", ""),
            )
        return DatasetInfo(
            dataset_id=dataset_id,
            source=self.source_name,
            title=f"BioLINCC {name}",
            description="Controlled-access NHLBI cohort study.",
            requires_auth=(access == "controlled"),
        )

    def download(
        self,
        dataset_id: str,
        dest: Path,
        options: DownloadOptions | None = None,
    ) -> list[Path]:
        parts = self._parse_dataset_id(dataset_id)
        access = parts[1] if len(parts) > 1 else "teaching"
        name = parts[2] if len(parts) > 2 else "unknown"

        if access == "controlled":
            # Check if data has been manually placed in local path
            if self._local_path and self._local_path.exists():
                _log.info("BioLINCC: using local data at %s", self._local_path)
                return list(self._local_path.glob(f"{name}*.*"))
            raise NotImplementedError(
                f"BioLINCC controlled dataset {name!r} cannot be downloaded automatically. "
                "To access this data:\n"
                "1. Submit an application at https://biolincc.nhlbi.nih.gov/studies/\n"
                "2. After approval, download the dataset to a local directory\n"
                "3. Set BIOLINCC_DATA_PATH to that directory\n"
                "Alternatively, use NHLBI BioData Catalyst cloud workspace at "
                "https://biodatacatalyst.nhlbi.nih.gov"
            )

        # Teaching dataset: attempt to use local path first, then note manual download needed
        if self._local_path and self._local_path.exists():
            local_files = list(self._local_path.glob(f"{name}*.*"))
            if local_files:
                _log.info("BioLINCC teaching: using local files at %s", self._local_path)
                return local_files

        info = _TEACHING_DATASETS.get(name, {})
        _log.warning(
            "BioLINCC teaching dataset %r must be downloaded manually from %s. "
            "Set BIOLINCC_DATA_PATH to the download directory.",
            name,
            info.get("url", "https://biolincc.nhlbi.nih.gov/teaching/"),
        )
        return []

    def parse(self, dataset_id: str, files: list[Path]) -> CohortDataset:
        """
        Parse BioLINCC teaching dataset files.
        Expects CSV/SAS files with exam visit data.
        """
        parts = self._parse_dataset_id(dataset_id)
        name = parts[2] if len(parts) > 2 else "unknown"

        persons: list[Person] = []
        measurements: list[Measurement] = []
        events: list[Event] = []

        for fpath in files:
            try:
                if fpath.suffix.lower() in (".sas7bdat", ".xpt"):
                    df = pd.read_sas(fpath, encoding="iso-8859-1")
                elif fpath.suffix.lower() == ".csv":
                    df = pd.read_csv(fpath)
                else:
                    continue
            except Exception as exc:
                _log.warning("BioLINCC: failed to read %s: %s", fpath, exc)
                continue

            ps, ms, es = self._parse_exam_file(df, dataset_id, name)
            persons.extend(ps)
            measurements.extend(ms)
            events.extend(es)

        # De-duplicate persons
        seen_pids = set()
        unique_persons = []
        for p in persons:
            if p.person_id not in seen_pids:
                unique_persons.append(p)
                seen_pids.add(p.person_id)

        _log.debug(
            "BioLINCC %s: parsed %d persons, %d measurements, %d events",
            name,
            len(unique_persons),
            len(measurements),
            len(events),
        )
        return CohortDataset(persons=unique_persons, measurements=measurements, events=events)

    # ------------------------------------------------------------------
    # Internal parsers
    # ------------------------------------------------------------------

    def _parse_exam_file(
        self, df: pd.DataFrame, dataset_id: str, study_name: str
    ) -> tuple[list[Person], list[Measurement], list[Event]]:
        """Generic exam file parser using common variable naming conventions."""
        persons = []
        measurements = []
        events = []

        # Common ID column names across BioLINCC cohorts
        id_col = _first_col(df, ("RANDID", "id", "ID", "SUBJID", "randid"))
        sex_col = _first_col(df, ("SEX", "sex", "GENDER", "gender"))
        _first_col(df, ("AGE", "age", "AGE1", "AGEBL"))  # reserved for future use
        # Exam date -- Framingham uses PERIOD; others use EXAMDATE
        exam_col = _first_col(df, ("PERIOD", "EXAM", "exam", "EXAMDATE", "examdate"))

        _VAR_MAP: dict[str, tuple[str, str]] = {
            "SYSBP": ("sbp_mmhg", "mmHg"),
            "DIABP": ("dbp_mmhg", "mmHg"),
            "BMI": ("bmi_kg_m2", "kg/m2"),
            "GLUCOSE": ("glucose_mg_dl", "mg/dL"),
            "TOTCHOL": ("total_cholesterol_mg_dl", "mg/dL"),
            "HDLC": ("hdl_mg_dl", "mg/dL"),
            "LDLC": ("ldl_mg_dl", "mg/dL"),
        }

        _EVENT_COLS: dict[str, tuple[str, str]] = {
            # col_flag: (event_type_label, code)
            "DIABETES": ("diagnosis", "FRAMINGHAM_DIABETES"),
            "HYPERTEN": ("diagnosis", "FRAMINGHAM_HYPERTENSION"),
            "ANGINA": ("diagnosis", "FRAMINGHAM_ANGINA"),
            "MI": ("hospitalization", "FRAMINGHAM_MI"),
            "STROKE": ("hospitalization", "FRAMINGHAM_STROKE"),
            "CVD": ("hospitalization", "FRAMINGHAM_CVD"),
            "DEATH": ("death", "FRAMINGHAM_DEATH"),
        }

        from datetime import date as date_cls

        for _, row in df.iterrows():
            if id_col is None:
                continue
            pid = str(row[id_col])
            sex_raw = row.get(sex_col)
            sex = None
            if sex_raw is not None and not (isinstance(sex_raw, float) and pd.isna(sex_raw)):
                sex = "M" if int(sex_raw) == 1 else "F"

            persons.append(
                Person(
                    person_id=pid,
                    source=self.source_name,
                    dataset_id=dataset_id,
                    sex=sex,
                    extra={"study": study_name},
                )
            )

            # Exam period/year for timestamp
            exam_period = row.get(exam_col, 1) if exam_col else 1
            try:
                exam_year = 1960 + int(exam_period) * 4  # rough Framingham approximation
            except (ValueError, TypeError):
                exam_year = 2000
            from datetime import datetime

            exam_dt = datetime(exam_year, 1, 1)

            # Measurements
            for var, (measure_type, unit) in _VAR_MAP.items():
                val = row.get(var)
                if val is None or (isinstance(val, float) and pd.isna(val)):
                    continue
                measurements.append(
                    Measurement(
                        person_id=pid,
                        source=self.source_name,
                        dataset_id=dataset_id,
                        measured_at=exam_dt,
                        measure_type=measure_type,
                        value=float(val),
                        unit=unit,
                        method="exam",
                        extra={"exam_period": str(exam_period), "study": study_name},
                    )
                )

            # Events (binary flag columns)
            for event_col, (event_type, code) in _EVENT_COLS.items():
                val = row.get(event_col)
                if val is None or (isinstance(val, float) and pd.isna(val)):
                    continue
                if int(val) == 1:
                    events.append(
                        Event(
                            person_id=pid,
                            source=self.source_name,
                            dataset_id=dataset_id,
                            event_date=date_cls(exam_year, 1, 1),
                            event_type=event_type,
                            code_system="custom",
                            code=code,
                            description=f"{study_name.upper()} {event_col}=1 at exam {exam_period}",
                        )
                    )

        return persons, measurements, events


def _first_col(df: pd.DataFrame, candidates: tuple) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None
