"""
t1_granada.py — T1DiabetesGranada adapter.

Wraps ZenodoAdapter for download; provides domain-specific parsing of the four
CSV files that constitute the dataset:
  - Patient_info.csv
  - Glucose_measurements.csv
  - Biochemical_parameters.csv
  - Diagnostics.csv

Access requires a Zenodo Data Usage Agreement approval and a personal access token.
Dataset DOI: https://doi.org/10.5281/zenodo.8386456
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from medrisk.fetch._auth import AuthProvider
from medrisk.fetch._cache import CacheStore
from medrisk.fetch._registry import register
from medrisk.fetch._schema import (
    CohortDataset,
    Event,
    Measurement,
    Person,
)
from medrisk.fetch.adapters.base import AbstractAdapter, DatasetInfo, DownloadOptions
from medrisk.fetch.adapters.zenodo import ZenodoAdapter

_log = logging.getLogger(__name__)

_ZENODO_RECORD_ID = "8386456"
_DATASET_ID = f"t1_granada::{_ZENODO_RECORD_ID}"

_EXPECTED_FILES = {
    "Patient_info.csv",
    "Glucose_measurements.csv",
    "Biochemical_parameters.csv",
    "Diagnostics.csv",
}

# ICD-9-CM prefix -> internal event type label (simplified; filters.yml has full lists)
_ICD9_COMPLICATION_MAP = {
    "250.5": "diabetic_retinopathy",
    "250.4": "diabetic_kidney_disease",
    "250.6": "diabetic_neuropathy",
    "362": "diabetic_retinopathy",
    "583": "diabetic_kidney_disease",
    "401": "hypertension",
    "410": "myocardial_infarction",
    "428": "heart_failure",
    "434": "stroke",
    "585": "chronic_kidney_disease",
}


@register
class T1DiabetesGranadaAdapter(AbstractAdapter):
    """
    Adapter for the T1DiabetesGranada longitudinal type 1 diabetes dataset.

    dataset_id: ``t1_granada::8386456``
    """

    source_name = "t1_granada"

    def __init__(self, config: dict, auth: AuthProvider, cache: CacheStore) -> None:
        super().__init__(config, auth, cache)
        # Delegate HTTP/download logic to generic Zenodo adapter
        zenodo_config = {**config, "api_base": "https://zenodo.org/api"}
        self._zenodo = ZenodoAdapter(zenodo_config, auth, cache)

    # ------------------------------------------------------------------
    # AbstractAdapter interface
    # ------------------------------------------------------------------

    def list_datasets(self, filters: dict | None = None) -> list[DatasetInfo]:
        return [self.get_metadata(_DATASET_ID)]

    def get_metadata(self, dataset_id: str) -> DatasetInfo:
        return DatasetInfo(
            dataset_id=_DATASET_ID,
            source=self.source_name,
            title="T1DiabetesGranada -- Longitudinal Multi-Modal Type 1 Diabetes Dataset",
            description=(
                "736 patients, >22.6M glucose measurements, >257K patient-days of CGM. "
                "Includes biochemical parameters, ICD-9-CM diagnoses, and demographics. "
                "Hosted on Zenodo; requires Data Usage Agreement approval."
            ),
            url=f"https://zenodo.org/record/{_ZENODO_RECORD_ID}",
            tags=["diabetes", "CGM", "longitudinal", "type-1-diabetes", "HbA1c"],
            requires_auth=True,
            license="CC BY 4.0",
        )

    def download(
        self,
        dataset_id: str,
        dest: Path,
        options: DownloadOptions | None = None,
    ) -> list[Path]:
        """Delegate download to ZenodoAdapter for the fixed record ID."""
        zenodo_id = f"zenodo::{_ZENODO_RECORD_ID}"
        return self._zenodo.download(zenodo_id, dest, options)

    def parse(self, dataset_id: str, files: list[Path]) -> CohortDataset:
        """
        Parse the four CSV files into the internal schema.
        files: list of local paths; this method finds files by name.
        """
        file_map: dict[str, Path] = {f.name: f for f in files}
        missing = _EXPECTED_FILES - file_map.keys()
        if missing:
            _log.warning("T1DiabetesGranada: missing expected files: %s", missing)

        persons: list[Person] = []
        measurements: list[Measurement] = []
        events: list[Event] = []

        if "Patient_info.csv" in file_map:
            persons = self._parse_patient_info(pd.read_csv(file_map["Patient_info.csv"]))

        if "Glucose_measurements.csv" in file_map:
            measurements += self._parse_glucose(pd.read_csv(file_map["Glucose_measurements.csv"]))

        if "Biochemical_parameters.csv" in file_map:
            measurements += self._parse_biochemical(
                pd.read_csv(file_map["Biochemical_parameters.csv"])
            )

        if "Diagnostics.csv" in file_map:
            events = self._parse_diagnostics(pd.read_csv(file_map["Diagnostics.csv"]))

        return CohortDataset(persons=persons, measurements=measurements, events=events)

    # ------------------------------------------------------------------
    # Domain-specific parsers
    # ------------------------------------------------------------------

    def _parse_patient_info(self, df: pd.DataFrame) -> list[Person]:
        persons = []
        for _, row in df.iterrows():
            pid = str(row.get("Patient_ID", row.get("patient_id", row.name)))
            sex_raw = str(row.get("Sex", row.get("sex", ""))).strip()
            persons.append(
                Person(
                    person_id=pid,
                    source=self.source_name,
                    dataset_id=_DATASET_ID,
                    sex=sex_raw or None,
                    extra={
                        k: v
                        for k, v in row.items()
                        if k not in ("Patient_ID", "patient_id", "Sex", "sex")
                    },
                )
            )
        _log.debug("T1Granada: parsed %d persons", len(persons))
        return persons

    def _parse_glucose(self, df: pd.DataFrame) -> list[Measurement]:
        measurements = []
        date_col = _first_col(df, ("Date", "date", "DateTime", "datetime"))
        time_col = _first_col(df, ("Time", "time"))
        glucose_col = _first_col(df, ("Glucose", "glucose", "GlucoseValue", "glucose_value"))
        pid_col = _first_col(df, ("Patient_ID", "patient_id", "PatientID"))

        for _, row in df.iterrows():
            pid = str(row[pid_col]) if pid_col else "unknown"
            ts = _parse_timestamp(row.get(date_col), row.get(time_col) if time_col else None)
            if ts is None or glucose_col is None:
                continue
            raw_val = row.get(glucose_col)
            if pd.isna(raw_val):
                continue
            measurements.append(
                Measurement(
                    person_id=pid,
                    source=self.source_name,
                    dataset_id=_DATASET_ID,
                    measured_at=ts,
                    measure_type="glucose_mg_dl",
                    value=float(raw_val),
                    unit="mg/dL",
                    method="CGM",
                )
            )
        _log.debug("T1Granada: parsed %d glucose measurements", len(measurements))
        return measurements

    def _parse_biochemical(self, df: pd.DataFrame) -> list[Measurement]:
        measurements = []
        date_col = _first_col(df, ("Date", "date", "DateTime", "datetime"))
        pid_col = _first_col(df, ("Patient_ID", "patient_id", "PatientID"))
        param_col = _first_col(df, ("Parameter", "parameter", "Test", "test", "ParameterName"))
        value_col = _first_col(df, ("Value", "value", "Result", "result"))
        unit_col = _first_col(df, ("Unit", "unit", "Units", "units"))

        _PARAM_MAP = {
            "hba1c": "hba1c_pct",
            "hba1c (%)": "hba1c_pct",
            "glucose": "glucose_mg_dl",
            "creatinine": "creatinine_mg_dl",
            "ldl": "ldl_mg_dl",
            "hdl": "hdl_mg_dl",
            "triglycerides": "triglycerides_mg_dl",
            "bmi": "bmi_kg_m2",
            "weight": "weight_kg",
            "height": "height_cm",
        }

        for _, row in df.iterrows():
            pid = str(row[pid_col]) if pid_col else "unknown"
            ts = _parse_timestamp(row.get(date_col))
            if ts is None or value_col is None:
                continue
            raw_val = row.get(value_col)
            if pd.isna(raw_val):
                continue
            param_raw = str(row.get(param_col, "")).lower().strip() if param_col else ""
            measure_type = _PARAM_MAP.get(param_raw, param_raw.replace(" ", "_").replace("/", "_"))
            unit = str(row.get(unit_col, "")).strip() if unit_col else ""
            measurements.append(
                Measurement(
                    person_id=pid,
                    source=self.source_name,
                    dataset_id=_DATASET_ID,
                    measured_at=ts,
                    measure_type=measure_type,
                    value=float(raw_val),
                    unit=unit or "unknown",
                    method="lab",
                )
            )
        _log.debug("T1Granada: parsed %d biochemical measurements", len(measurements))
        return measurements

    def _parse_diagnostics(self, df: pd.DataFrame) -> list[Event]:
        events = []
        date_col = _first_col(df, ("Date", "date", "DiagnosisDate", "diagnosis_date"))
        pid_col = _first_col(df, ("Patient_ID", "patient_id", "PatientID"))
        code_col = _first_col(df, ("ICD_code", "icd_code", "Code", "code", "ICD9", "icd9"))
        desc_col = _first_col(df, ("Description", "description", "Diagnosis", "diagnosis"))

        for _, row in df.iterrows():
            pid = str(row[pid_col]) if pid_col else "unknown"
            ts = _parse_timestamp(row.get(date_col))
            code = str(row.get(code_col, "")).strip() if code_col else ""
            if not code or ts is None:
                continue
            description = str(row.get(desc_col, "")).strip() if desc_col else None
            events.append(
                Event(
                    person_id=pid,
                    source=self.source_name,
                    dataset_id=_DATASET_ID,
                    event_date=ts.date(),
                    event_type="diagnosis",
                    code_system="ICD9",
                    code=code,
                    description=description or None,
                )
            )
        _log.debug("T1Granada: parsed %d diagnostic events", len(events))
        return events


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------


def _first_col(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    """Return the first column name from candidates that exists in df."""
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _parse_timestamp(date_val, time_val=None) -> datetime | None:
    """Attempt to parse a date (and optional time) value into a datetime."""
    if date_val is None or (isinstance(date_val, float) and pd.isna(date_val)):
        return None
    try:
        if time_val is not None and not (isinstance(time_val, float) and pd.isna(time_val)):
            dt = pd.to_datetime(f"{date_val} {time_val}", format="mixed", dayfirst=True)
        else:
            dt = pd.to_datetime(date_val, format="mixed", dayfirst=True)
        return dt.to_pydatetime().replace(tzinfo=None)
    except Exception:
        return None
