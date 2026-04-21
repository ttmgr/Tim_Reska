"""
disease_progression.data.omop_etl - FHIR to OMOP-lite ETL transform.

Implements a lightweight Extract-Transform-Load pipeline that maps FHIR R4
resources produced by ``synthea_loader`` into a simplified OMOP Common Data
Model (CDM) v5.4 representation stored as pandas DataFrames.

Target tables:
    - **person**: Demographics (person_id, year_of_birth, gender_concept_id, ...)
    - **condition_occurrence**: Diagnoses with start/end dates and ICD-10 codes
    - **drug_exposure**: Medication prescriptions with ATC/RxNorm codes
    - **measurement**: Quantitative lab results (LOINC-coded)
    - **observation_period**: Per-person observation windows

The OMOP-lite schema intentionally omits vocabulary tables, visit_occurrence,
and other ancillary tables to keep the pipeline self-contained for downstream
survival-analysis feature engineering.  Concept IDs are mapped via a small
internal lookup; unmapped codes receive ``concept_id = 0``.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from disease_progression.data.synthea_loader import SyntheaLoader

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Lightweight concept mapping
# -------------------------------------------------------------------

GENDER_CONCEPT: Dict[str, int] = {
    "male": 8507,
    "female": 8532,
    "other": 8521,
    "unknown": 8551,
}

RACE_CONCEPT: Dict[str, int] = {
    "white": 8527,
    "black": 8516,
    "asian": 8515,
    "other": 8522,
}

ETHNICITY_CONCEPT: Dict[str, int] = {
    "hispanic or latino": 38003563,
    "not hispanic or latino": 38003564,
}


def _stable_person_id(uuid_str: str) -> int:
    """Deterministic integer person_id derived from UUID string."""
    return int(hashlib.sha256(uuid_str.encode()).hexdigest()[:15], 16)


def _parse_date(dt_str: Optional[str]) -> Optional[datetime]:
    """Best-effort ISO datetime parser."""
    if dt_str is None:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            return datetime.strptime(dt_str.replace("+00:00", "Z"), fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


# ===================================================================
# OMOP table dataclass containers
# ===================================================================

@dataclass
class OMOPTables:
    """Container holding OMOP-lite tables as DataFrames.

    Attributes
    ----------
    person : pd.DataFrame
    condition_occurrence : pd.DataFrame
    drug_exposure : pd.DataFrame
    measurement : pd.DataFrame
    observation_period : pd.DataFrame
    """
    person: pd.DataFrame = field(default_factory=pd.DataFrame)
    condition_occurrence: pd.DataFrame = field(default_factory=pd.DataFrame)
    drug_exposure: pd.DataFrame = field(default_factory=pd.DataFrame)
    measurement: pd.DataFrame = field(default_factory=pd.DataFrame)
    observation_period: pd.DataFrame = field(default_factory=pd.DataFrame)

    def summary(self) -> Dict[str, int]:
        return {
            "person": len(self.person),
            "condition_occurrence": len(self.condition_occurrence),
            "drug_exposure": len(self.drug_exposure),
            "measurement": len(self.measurement),
            "observation_period": len(self.observation_period),
        }


# ===================================================================
# Transformer
# ===================================================================

class FHIRToOMOPTransformer:
    """Transform FHIR resources into OMOP-lite DataFrames.

    This transformer consumes the DataFrames produced by
    :class:`SyntheaLoader` (patients, conditions, observations,
    medications) and produces an :class:`OMOPTables` instance.

    Parameters
    ----------
    loader : SyntheaLoader
        A loader that has already called ``.load()``.

    Example
    -------
    >>> loader = SyntheaLoader("./data/raw").load()
    >>> omop = FHIRToOMOPTransformer(loader).transform()
    >>> print(omop.summary())
    """

    def __init__(self, loader: SyntheaLoader) -> None:
        self.loader = loader
        self._tables: Optional[OMOPTables] = None

    def transform(self) -> OMOPTables:
        """Run the full ETL and return OMOP tables."""
        patients_df = self.loader.patients_dataframe()
        conditions_df = self.loader.conditions_dataframe()
        observations_df = self.loader.observations_dataframe()
        medications_df = self.loader.medications_dataframe()

        person = self._build_person(patients_df)
        pid_map = dict(zip(person["source_patient_id"], person["person_id"]))

        condition_occurrence = self._build_condition_occurrence(conditions_df, pid_map)
        drug_exposure = self._build_drug_exposure(medications_df, pid_map)
        measurement = self._build_measurement(observations_df, pid_map)
        observation_period = self._build_observation_period(
            person, condition_occurrence, drug_exposure, measurement
        )

        self._tables = OMOPTables(
            person=person,
            condition_occurrence=condition_occurrence,
            drug_exposure=drug_exposure,
            measurement=measurement,
            observation_period=observation_period,
        )
        logger.info("OMOP ETL complete: %s", self._tables.summary())
        return self._tables

    # ------------------------------------------------------------------
    # Table builders
    # ------------------------------------------------------------------

    @staticmethod
    def _build_person(patients_df: pd.DataFrame) -> pd.DataFrame:
        """Map FHIR Patient -> OMOP person table.

        Columns: person_id, source_patient_id, gender_concept_id,
        year_of_birth, month_of_birth, day_of_birth,
        race_concept_id, ethnicity_concept_id, death_datetime.
        """
        rows: List[Dict[str, Any]] = []
        for _, pt in patients_df.iterrows():
            pid = _stable_person_id(str(pt.get("patient_id", "")))
            bd = _parse_date(str(pt.get("birth_date", "")))
            dd = _parse_date(pt.get("death_date"))

            gender_str = str(pt.get("gender", "unknown")).lower()
            race_str = str(pt.get("race", "other")).lower()
            eth_str = str(pt.get("ethnicity", "")).lower()

            rows.append(
                {
                    "person_id": pid,
                    "source_patient_id": pt.get("patient_id"),
                    "gender_concept_id": GENDER_CONCEPT.get(gender_str, 0),
                    "year_of_birth": bd.year if bd else None,
                    "month_of_birth": bd.month if bd else None,
                    "day_of_birth": bd.day if bd else None,
                    "race_concept_id": RACE_CONCEPT.get(race_str, 0),
                    "ethnicity_concept_id": ETHNICITY_CONCEPT.get(eth_str, 0),
                    "death_datetime": dd,
                }
            )
        return pd.DataFrame(rows)

    @staticmethod
    def _build_condition_occurrence(
        conditions_df: pd.DataFrame,
        pid_map: Dict[str, int],
    ) -> pd.DataFrame:
        """Map FHIR Condition -> OMOP condition_occurrence.

        Columns: condition_occurrence_id, person_id, condition_source_value,
        condition_source_system, condition_start_date, condition_end_date,
        condition_status.
        """
        if conditions_df.empty:
            return pd.DataFrame()

        rows: List[Dict[str, Any]] = []
        for idx, cond in conditions_df.iterrows():
            src_pid = str(cond.get("patient_id", ""))
            person_id = pid_map.get(src_pid)
            if person_id is None:
                continue
            rows.append(
                {
                    "condition_occurrence_id": idx,
                    "person_id": person_id,
                    "condition_source_value": cond.get("condition_code"),
                    "condition_source_system": cond.get("code_system"),
                    "condition_concept_name": cond.get("display"),
                    "condition_start_date": _parse_date(cond.get("onset_date")),
                    "condition_end_date": _parse_date(cond.get("abatement_date")),
                    "condition_status": cond.get("clinical_status"),
                }
            )
        return pd.DataFrame(rows)

    @staticmethod
    def _build_drug_exposure(
        medications_df: pd.DataFrame,
        pid_map: Dict[str, int],
    ) -> pd.DataFrame:
        """Map FHIR MedicationRequest -> OMOP drug_exposure.

        Columns: drug_exposure_id, person_id, drug_source_value,
        drug_source_system, drug_concept_name, drug_exposure_start_date,
        drug_exposure_status.
        """
        if medications_df.empty:
            return pd.DataFrame()

        rows: List[Dict[str, Any]] = []
        for idx, med in medications_df.iterrows():
            src_pid = str(med.get("patient_id", ""))
            person_id = pid_map.get(src_pid)
            if person_id is None:
                continue
            rows.append(
                {
                    "drug_exposure_id": idx,
                    "person_id": person_id,
                    "drug_source_value": med.get("medication_code"),
                    "drug_source_system": med.get("code_system"),
                    "drug_concept_name": med.get("display"),
                    "drug_exposure_start_date": _parse_date(med.get("authored_on")),
                    "drug_exposure_status": med.get("status"),
                }
            )
        return pd.DataFrame(rows)

    @staticmethod
    def _build_measurement(
        observations_df: pd.DataFrame,
        pid_map: Dict[str, int],
    ) -> pd.DataFrame:
        """Map FHIR Observation -> OMOP measurement.

        Columns: measurement_id, person_id, measurement_source_value,
        measurement_concept_name, value_as_number, unit_source_value,
        measurement_date.
        """
        if observations_df.empty:
            return pd.DataFrame()

        rows: List[Dict[str, Any]] = []
        for idx, obs in observations_df.iterrows():
            src_pid = str(obs.get("patient_id", ""))
            person_id = pid_map.get(src_pid)
            if person_id is None:
                continue
            rows.append(
                {
                    "measurement_id": idx,
                    "person_id": person_id,
                    "measurement_source_value": obs.get("observation_code"),
                    "measurement_concept_name": obs.get("display"),
                    "value_as_number": obs.get("value"),
                    "unit_source_value": obs.get("unit"),
                    "measurement_date": _parse_date(obs.get("effective_date")),
                }
            )
        return pd.DataFrame(rows)

    @staticmethod
    def _build_observation_period(
        person: pd.DataFrame,
        condition_occurrence: pd.DataFrame,
        drug_exposure: pd.DataFrame,
        measurement: pd.DataFrame,
    ) -> pd.DataFrame:
        """Derive observation_period from earliest/latest events per person.

        For each person, the observation period spans from the earliest
        recorded clinical event to the latest (or death, if applicable).

        Columns: observation_period_id, person_id,
        observation_period_start_date, observation_period_end_date.
        """
        date_records: List[Dict[str, Any]] = []

        for table, date_col in [
            (condition_occurrence, "condition_start_date"),
            (drug_exposure, "drug_exposure_start_date"),
            (measurement, "measurement_date"),
        ]:
            if table.empty or date_col not in table.columns:
                continue
            for _, row in table.iterrows():
                dt = row.get(date_col)
                if dt is not None:
                    date_records.append({"person_id": row["person_id"], "event_date": dt})

        if not date_records:
            return pd.DataFrame(columns=[
                "observation_period_id", "person_id",
                "observation_period_start_date", "observation_period_end_date",
            ])

        events = pd.DataFrame(date_records)
        events["event_date"] = pd.to_datetime(events["event_date"], errors="coerce")
        grouped = events.dropna(subset=["event_date"]).groupby("person_id")["event_date"]

        result = pd.DataFrame(
            {
                "person_id": grouped.min().index,
                "observation_period_start_date": grouped.min().values,
                "observation_period_end_date": grouped.max().values,
            }
        )

        # Extend end date to death_datetime if available
        death_map = person.dropna(subset=["death_datetime"]).set_index("person_id")["death_datetime"]
        for pid, death_dt in death_map.items():
            mask = result["person_id"] == pid
            if mask.any():
                current_end = result.loc[mask, "observation_period_end_date"].iloc[0]
                death_ts = pd.Timestamp(death_dt)
                if pd.isna(current_end) or death_ts > current_end:
                    result.loc[mask, "observation_period_end_date"] = death_ts

        result = result.reset_index(drop=True)
        result["observation_period_id"] = result.index
        return result[
            ["observation_period_id", "person_id",
             "observation_period_start_date", "observation_period_end_date"]
        ]
