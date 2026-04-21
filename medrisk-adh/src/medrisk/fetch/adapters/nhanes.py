"""
nhanes.py — NHANES (National Health and Nutrition Examination Survey) adapter.

Supports listing and downloading SAS XPT files for any cycle/domain combination.
Tables are merged on participant ID (SEQN) during parsing.

dataset_id format: ``nhanes::<cycle>::<domain>``
  e.g.  ``nhanes::2017-2018::demographics``
        ``nhanes::2017-2018::labs``
        ``nhanes::2017-2018::examination``
        ``nhanes::2017-2018::questionnaire``
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from medrisk.fetch._auth import AuthProvider
from medrisk.fetch._cache import CacheStore
from medrisk.fetch._registry import register
from medrisk.fetch._schema import CohortDataset, Event, Measurement, Person
from medrisk.fetch.adapters.base import AbstractAdapter, DatasetInfo, DownloadOptions

_log = logging.getLogger(__name__)

BASE_URL = "https://wwwn.cdc.gov/nchs/nhanes"

# Survey cycles with their letter suffix used in file URLs
CYCLE_SUFFIX: dict[str, str] = {
    "1999-2000": "A",
    "2001-2002": "B",
    "2003-2004": "C",
    "2005-2006": "D",
    "2007-2008": "E",
    "2009-2010": "F",
    "2011-2012": "G",
    "2013-2014": "H",
    "2015-2016": "I",
    "2017-2018": "J",
    "2019-2020": "K",  # 2019-March 2020 pre-pandemic
    "2021-2023": "L",
}

DOMAINS = ("demographics", "labs", "examination", "questionnaire")

# Domain -> list of (component_code, filename_stem) tuples for key files
DOMAIN_COMPONENTS: dict[str, list[tuple[str, str]]] = {
    "demographics": [("DEMO", "DEMO")],
    "labs": [
        ("GHB", "GHB"),  # HbA1c
        ("GLU", "GLU"),  # Fasting glucose
        ("BIOPRO", "BIOPRO"),  # Standard biochemistry panel
        ("TCHOL", "TCHOL"),  # Total cholesterol
        ("HDL", "HDL"),  # HDL cholesterol
        ("TRIGLY", "TRIGLY"),  # Triglycerides
        ("BPXO", "BPXO"),  # Blood pressure oscillometric (2019+)
    ],
    "examination": [
        ("BMX", "BMX"),  # Body measures
        ("BPX", "BPX"),  # Blood pressure
    ],
    "questionnaire": [
        ("DIQ", "DIQ"),  # Diabetes
        ("BPQ", "BPQ"),  # Blood pressure
        ("MCQ", "MCQ"),  # Medical conditions
        ("RXQ_RX", "RXQ_RX"),  # Prescription medications
    ],
}

# NHANES variable -> internal schema mapping
_DEMO_MAP = {
    "SEQN": "person_id",
    "RIAGENDR": "sex",  # 1=Male, 2=Female
    "RIDAGEYR": "age_years",
    "RIDRETH3": "race_ethnicity",
    "RIDEXAGM": "age_months",
}

_LABS_MEASURE_MAP: dict[str, tuple[str, str]] = {
    # nhanes_var: (measure_type, unit)
    "LBXGH": ("hba1c_pct", "%"),
    "LBXGLU": ("glucose_mg_dl", "mg/dL"),
    "LBXSCR": ("creatinine_mg_dl", "mg/dL"),
    "LBXTC": ("total_cholesterol_mg_dl", "mg/dL"),
    "LBDHDL": ("hdl_mg_dl", "mg/dL"),
    "LBXTR": ("triglycerides_mg_dl", "mg/dL"),
}

_EXAM_MEASURE_MAP: dict[str, tuple[str, str]] = {
    "BMXBMI": ("bmi_kg_m2", "kg/m2"),
    "BMXWT": ("weight_kg", "kg"),
    "BMXHT": ("height_cm", "cm"),
    "BPXSY1": ("sbp_mmhg", "mmHg"),
    "BPXDI1": ("dbp_mmhg", "mmHg"),
    "BPXSY2": ("sbp_mmhg_r2", "mmHg"),
    "BPXDI2": ("dbp_mmhg_r2", "mmHg"),
    "BPXOSY1": ("sbp_mmhg", "mmHg"),  # oscillometric
    "BPXODI1": ("dbp_mmhg", "mmHg"),
}

_DIABETES_DIAGNOSIS_VAR = "DIQ010"  # 1 = Yes (told by doctor)
_HYPERTENSION_VAR = "BPQ020"  # 1 = Yes (told high BP)


@register
class NHANESAdapter(AbstractAdapter):
    """NHANES adapter -- SAS XPT files, all public cycles and domains."""

    source_name = "nhanes"

    def __init__(self, config: dict, auth: AuthProvider, cache: CacheStore) -> None:
        super().__init__(config, auth, cache)
        self._base_url = config.get("base_url", BASE_URL)

    # ------------------------------------------------------------------
    # AbstractAdapter interface
    # ------------------------------------------------------------------

    def list_datasets(self, filters: dict | None = None) -> list[DatasetInfo]:
        datasets = []
        cycles = list(CYCLE_SUFFIX)
        if filters and "cycle" in filters:
            cycles = [filters["cycle"]]
        domains = list(DOMAINS)
        if filters and "domain" in filters:
            domains = [filters["domain"]]

        for cycle in cycles:
            for domain in domains:
                dataset_id = f"nhanes::{cycle}::{domain}"
                datasets.append(
                    DatasetInfo(
                        dataset_id=dataset_id,
                        source=self.source_name,
                        title=f"NHANES {cycle} -- {domain.capitalize()}",
                        description=f"NHANES {cycle} survey cycle, {domain} domain. "
                        f"SAS XPT format. Components: {DOMAIN_COMPONENTS.get(domain, [])}",
                        url=f"{self._base_url}/{cycle}",
                        tags=["NHANES", "chronic-disease", "diabetes", "hypertension", domain],
                        requires_auth=False,
                        license="Public domain (CDC/NCHS)",
                    )
                )
        return datasets

    def get_metadata(self, dataset_id: str) -> DatasetInfo:
        parts = self._parse_dataset_id(dataset_id)
        if len(parts) < 3:
            raise ValueError(f"Invalid NHANES dataset_id: {dataset_id!r}")
        _, cycle, domain = parts[0], parts[1], parts[2]
        return DatasetInfo(
            dataset_id=dataset_id,
            source=self.source_name,
            title=f"NHANES {cycle} -- {domain.capitalize()}",
            description=f"Cycle {cycle}, {domain} domain.",
            url=f"{self._base_url}/{cycle}",
            tags=["NHANES", domain, cycle],
        )

    def download(
        self,
        dataset_id: str,
        dest: Path,
        options: DownloadOptions | None = None,
    ) -> list[Path]:
        opts = options or DownloadOptions()
        parts = self._parse_dataset_id(dataset_id)
        if len(parts) < 3:
            raise ValueError(f"Invalid NHANES dataset_id: {dataset_id!r}")
        cycle, domain = parts[1], parts[2]
        suffix = CYCLE_SUFFIX.get(cycle, "")
        components = DOMAIN_COMPONENTS.get(domain, [])

        cache_dir = self.cache.ensure_dir(self.source_name, dataset_id)
        local_paths: list[Path] = []

        for _code, stem in components:
            filename = f"{stem}_{suffix}.XPT" if suffix else f"{stem}.XPT"
            url = f"{self._base_url}/{cycle}/DataFiles/{filename}"
            local_path = cache_dir / filename
            try:
                result = self._download_file(url, local_path, opts)
                local_paths.append(result)
            except Exception as exc:
                _log.warning("NHANES: could not download %s (%s): %s", filename, url, exc)

        return local_paths

    def parse(self, dataset_id: str, files: list[Path]) -> CohortDataset:
        parts = self._parse_dataset_id(dataset_id)
        domain = parts[2] if len(parts) >= 3 else "unknown"
        cycle = parts[1] if len(parts) >= 2 else "unknown"

        dfs: dict[str, pd.DataFrame] = {}
        for f in files:
            try:
                dfs[f.stem.split("_")[0]] = pd.read_sas(f, format="xport", encoding="iso-8859-1")
            except Exception as exc:
                _log.warning("NHANES: failed to read %s: %s", f, exc)

        if domain == "demographics":
            return self._parse_demographics(dataset_id, dfs, cycle)
        if domain == "labs":
            return self._parse_labs(dataset_id, dfs, cycle)
        if domain == "examination":
            return self._parse_examination(dataset_id, dfs, cycle)
        if domain == "questionnaire":
            return self._parse_questionnaire(dataset_id, dfs, cycle)
        return CohortDataset()

    # ------------------------------------------------------------------
    # Domain parsers
    # ------------------------------------------------------------------

    def _parse_demographics(self, dataset_id: str, dfs: dict, cycle: str) -> CohortDataset:
        df = next(iter(dfs.values()), None)
        if df is None:
            return CohortDataset()
        persons = []
        for _, row in df.iterrows():
            pid = str(int(row["SEQN"])) if "SEQN" in row and not pd.isna(row["SEQN"]) else None
            if pid is None:
                continue
            sex_code = row.get("RIAGENDR")
            sex = None
            if not pd.isna(sex_code) if isinstance(sex_code, float) else sex_code is not None:
                sex = "M" if int(sex_code) == 1 else "F"
            race_code = row.get("RIDRETH3")
            race_map = {
                1: "Mexican American",
                2: "Other Hispanic",
                3: "Non-Hispanic White",
                4: "Non-Hispanic Black",
                6: "Non-Hispanic Asian",
                7: "Other/Multi",
            }
            race = race_map.get(int(race_code)) if race_code and not pd.isna(race_code) else None
            persons.append(
                Person(
                    person_id=pid,
                    source=self.source_name,
                    dataset_id=dataset_id,
                    sex=sex,
                    race_ethnicity=race,
                    extra={"nhanes_cycle": cycle},
                )
            )
        _log.debug("NHANES demographics: parsed %d persons from cycle %s", len(persons), cycle)
        return CohortDataset(persons=persons)

    def _parse_labs(self, dataset_id: str, dfs: dict, cycle: str) -> CohortDataset:
        measurements = []
        # Use a synthetic "exam date" based on cycle start year
        year = int(cycle.split("-")[0])
        exam_dt = datetime(year, 7, 1)  # mid-cycle approximation

        for _stem, df in dfs.items():
            if "SEQN" not in df.columns:
                continue
            for nhanes_var, (measure_type, unit) in _LABS_MEASURE_MAP.items():
                if nhanes_var not in df.columns:
                    continue
                for _, row in df.iterrows():
                    pid = str(int(row["SEQN"])) if not pd.isna(row["SEQN"]) else None
                    val = row.get(nhanes_var)
                    if pid is None or val is None or (isinstance(val, float) and pd.isna(val)):
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
                            method="lab",
                            extra={"nhanes_variable": nhanes_var, "nhanes_cycle": cycle},
                        )
                    )
        _log.debug("NHANES labs: parsed %d measurements from cycle %s", len(measurements), cycle)
        return CohortDataset(measurements=measurements)

    def _parse_examination(self, dataset_id: str, dfs: dict, cycle: str) -> CohortDataset:
        measurements = []
        year = int(cycle.split("-")[0])
        exam_dt = datetime(year, 7, 1)

        for _stem, df in dfs.items():
            if "SEQN" not in df.columns:
                continue
            for nhanes_var, (measure_type, unit) in _EXAM_MEASURE_MAP.items():
                if nhanes_var not in df.columns:
                    continue
                for _, row in df.iterrows():
                    pid = str(int(row["SEQN"])) if not pd.isna(row["SEQN"]) else None
                    val = row.get(nhanes_var)
                    if pid is None or val is None or (isinstance(val, float) and pd.isna(val)):
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
                            extra={"nhanes_variable": nhanes_var, "nhanes_cycle": cycle},
                        )
                    )
        _log.debug("NHANES exam: parsed %d measurements from cycle %s", len(measurements), cycle)
        return CohortDataset(measurements=measurements)

    def _parse_questionnaire(self, dataset_id: str, dfs: dict, cycle: str) -> CohortDataset:
        events = []
        year = int(cycle.split("-")[0])
        from datetime import date

        exam_date = date(year, 7, 1)

        for _stem, df in dfs.items():
            if "SEQN" not in df.columns:
                continue
            # Diabetes self-report
            if _DIABETES_DIAGNOSIS_VAR in df.columns:
                diab_df = df[df[_DIABETES_DIAGNOSIS_VAR] == 1]
                for _, row in diab_df.iterrows():
                    pid = str(int(row["SEQN"])) if not pd.isna(row["SEQN"]) else None
                    if pid:
                        events.append(
                            Event(
                                person_id=pid,
                                source=self.source_name,
                                dataset_id=dataset_id,
                                event_date=exam_date,
                                event_type="diagnosis",
                                code_system="custom",
                                code="NHANES_DIABETES_SELFREPORT",
                                description="Doctor-told diabetes (NHANES DIQ010=1)",
                                extra={
                                    "nhanes_variable": _DIABETES_DIAGNOSIS_VAR,
                                    "nhanes_cycle": cycle,
                                },
                            )
                        )
            # Hypertension self-report
            if _HYPERTENSION_VAR in df.columns:
                htn_df = df[df[_HYPERTENSION_VAR] == 1]
                for _, row in htn_df.iterrows():
                    pid = str(int(row["SEQN"])) if not pd.isna(row["SEQN"]) else None
                    if pid:
                        events.append(
                            Event(
                                person_id=pid,
                                source=self.source_name,
                                dataset_id=dataset_id,
                                event_date=exam_date,
                                event_type="diagnosis",
                                code_system="custom",
                                code="NHANES_HYPERTENSION_SELFREPORT",
                                description="Doctor-told hypertension (NHANES BPQ020=1)",
                                extra={
                                    "nhanes_variable": _HYPERTENSION_VAR,
                                    "nhanes_cycle": cycle,
                                },
                            )
                        )
        _log.debug("NHANES questionnaire: parsed %d events from cycle %s", len(events), cycle)
        return CohortDataset(events=events)
