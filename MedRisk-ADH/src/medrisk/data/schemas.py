"""Patient record data models for MedRisk-ADH.

All data contracts are enforced via Pydantic strict models. The schemas define
the structure of synthetic patient records flowing through the pipeline.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class Sex(StrEnum):
    MALE = "M"
    FEMALE = "F"


class SmokingStatus(StrEnum):
    NEVER = "never"
    FORMER = "former"
    CURRENT = "current"


class Market(StrEnum):
    DE = "DE"
    ES = "ES"
    FR = "FR"
    INT = "INT"


class Diagnosis(BaseModel):
    """A single ICD-10 coded diagnosis."""

    icd10_code: str = Field(..., pattern=r"^[A-Z]\d{2}(\.\d{1,4})?$")
    description: str
    date_recorded: date
    is_primary: bool = False


class LabResult(BaseModel):
    """A single laboratory observation (LOINC coded)."""

    loinc_code: str
    name: str
    value: float
    unit: str
    date_collected: date
    reference_low: float | None = None
    reference_high: float | None = None


class Medication(BaseModel):
    """A single medication record (ATC coded)."""

    atc_code: str = Field(..., pattern=r"^[A-Z]\d{2}[A-Z]{2}\d{2}$")
    name: str
    date_prescribed: date
    active: bool = True


class PatientRecord(BaseModel):
    """Complete patient record for underwriting assessment.

    Ground truth fields (prefixed gt_) are available only in synthetic data
    and are never visible to the models during training or inference.
    """

    patient_id: str
    market: Market
    age: int = Field(..., ge=18, le=100)
    sex: Sex
    bmi: float = Field(..., ge=12.0, le=60.0)
    smoking_status: SmokingStatus
    diagnoses: list[Diagnosis] = Field(default_factory=list)
    lab_results: list[LabResult] = Field(default_factory=list)
    medications: list[Medication] = Field(default_factory=list)
    follow_up_years: float = Field(..., ge=0.0)
    event_occurred: bool = False
    event_type: str | None = None
    time_to_event: float = Field(..., ge=0.0)

    # Ground truth — synthetic only
    gt_true_conditions: list[str] = Field(default_factory=list)
    gt_true_risk_score: float | None = None
    gt_data_quality_score: float | None = None

    # Alzheimer-specific fields (optional)
    apoe4_carrier: bool | None = None
    family_history_dementia: bool | None = None
    education_years: int | None = None

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str | None, info) -> str | None:
        valid_events = {
            "death", "mi", "stroke", "hf", "ckd_progression",
            "institutionalization", "cognitive_decline", None,
        }
        if v not in valid_events:
            msg = f"event_type must be one of {valid_events}, got {v!r}"
            raise ValueError(msg)
        return v


class MarketConfig(BaseModel):
    """Configuration for market-specific data quality degradation.

    Controls how ground truth patient data is degraded to simulate
    real-world data quality variance across healthcare systems.
    """

    market_code: Market
    coding_completeness: float = Field(..., ge=0.0, le=1.0)
    lab_completeness: float = Field(..., ge=0.0, le=1.0)
    lab_noise_sigma: float = Field(..., ge=0.0)
    diagnosis_lag_mean_days: float = Field(default=0.0, ge=0.0)
    diagnosis_lag_std_days: float = Field(default=0.0, ge=0.0)
    medication_recording: float = Field(default=1.0, ge=0.0, le=1.0)
    age_mean: float = Field(default=55.0)
    age_std: float = Field(default=15.0)
    prevalence_modifiers: dict[str, float] = Field(default_factory=dict)


# Pre-configured market profiles
MARKET_CONFIGS: dict[str, MarketConfig] = {
    "DE": MarketConfig(
        market_code=Market.DE,
        coding_completeness=0.95,
        lab_completeness=0.92,
        lab_noise_sigma=0.02,
        diagnosis_lag_mean_days=14,
        diagnosis_lag_std_days=7,
        medication_recording=0.95,
        age_mean=52,
        age_std=14,
    ),
    "ES": MarketConfig(
        market_code=Market.ES,
        coding_completeness=0.80,
        lab_completeness=0.75,
        lab_noise_sigma=0.05,
        diagnosis_lag_mean_days=30,
        diagnosis_lag_std_days=20,
        medication_recording=0.80,
        age_mean=56,
        age_std=16,
    ),
    "FR": MarketConfig(
        market_code=Market.FR,
        coding_completeness=0.90,
        lab_completeness=0.88,
        lab_noise_sigma=0.03,
        diagnosis_lag_mean_days=60,
        diagnosis_lag_std_days=30,
        medication_recording=0.88,
        age_mean=54,
        age_std=15,
    ),
    "INT": MarketConfig(
        market_code=Market.INT,
        coding_completeness=0.60,
        lab_completeness=0.50,
        lab_noise_sigma=0.10,
        diagnosis_lag_mean_days=90,
        diagnosis_lag_std_days=60,
        medication_recording=0.60,
        age_mean=50,
        age_std=18,
    ),
}
