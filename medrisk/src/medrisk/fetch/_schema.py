"""
_schema.py — Internal disease-progression schema.

All adapters parse source-specific formats into these four tables:
  Person, Measurement, Event, Treatment
collected in CohortDataset.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


class Person(BaseModel):
    """One row per study participant."""

    person_id: str
    source: str  # adapter source_name, e.g. "nhanes"
    dataset_id: str  # namespaced dataset ID, e.g. "nhanes::2017-2018::demographics"
    sex: str | None = None  # "M" | "F" | "O" | None
    birth_year: int | None = None
    race_ethnicity: str | None = None
    education_years: float | None = None
    baseline_date: date | None = None
    extra: dict = Field(default_factory=dict)

    @field_validator("sex")
    @classmethod
    def normalise_sex(cls, v: str | None) -> str | None:
        if v is None:
            return None
        mapping = {"male": "M", "female": "F", "m": "M", "f": "F", "1": "M", "2": "F"}
        return mapping.get(v.lower().strip(), v.upper()[:1])

    @field_validator("birth_year")
    @classmethod
    def plausible_birth_year(cls, v: int | None) -> int | None:
        if v is not None and not (1880 <= v <= 2025):
            raise ValueError(f"birth_year {v} is outside plausible range 1880-2025")
        return v


class Measurement(BaseModel):
    """One row per timestamped observation (repeated measures)."""

    person_id: str
    source: str
    dataset_id: str
    measured_at: datetime
    measure_type: str  # e.g. "glucose_mg_dl", "hba1c_pct", "sbp_mmhg", "bmi_kg_m2"
    value: float
    unit: str
    method: str | None = None  # "CGM" | "lab" | "self-report" | "exam"
    extra: dict = Field(default_factory=dict)

    @field_validator("value")
    @classmethod
    def finite_value(cls, v: float) -> float:
        import math

        if not math.isfinite(v):
            raise ValueError(f"Measurement value must be finite, got {v}")
        return v


class Event(BaseModel):
    """One row per timestamped incident event (diagnosis, hospitalisation, death, procedure)."""

    person_id: str
    source: str
    dataset_id: str
    event_date: date
    event_type: str  # "diagnosis" | "hospitalization" | "death" | "procedure"
    code_system: str  # "ICD10" | "ICD9" | "SNOMED" | "Read" | "OPCS" | "custom"
    code: str
    description: str | None = None
    extra: dict = Field(default_factory=dict)


class Treatment(BaseModel):
    """One row per medication/treatment episode."""

    person_id: str
    source: str
    dataset_id: str
    start_date: date
    end_date: date | None = None
    drug_name: str | None = None
    atc_code: str | None = None
    dose_value: float | None = None
    dose_unit: str | None = None
    route: str | None = None  # "oral" | "injection" | "topical" | etc.
    extra: dict = Field(default_factory=dict)

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v: date | None, info) -> date | None:
        if v is not None and "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must not be before start_date")
        return v


class CohortDataset(BaseModel):
    """Top-level container returned by adapter.parse()."""

    persons: list[Person] = Field(default_factory=list)
    measurements: list[Measurement] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    treatments: list[Treatment] = Field(default_factory=list)

    def is_empty(self) -> bool:
        return (
            len(self.persons) == 0
            and len(self.measurements) == 0
            and len(self.events) == 0
            and len(self.treatments) == 0
        )

    def summary(self) -> dict:
        return {
            "persons": len(self.persons),
            "measurements": len(self.measurements),
            "events": len(self.events),
            "treatments": len(self.treatments),
        }
