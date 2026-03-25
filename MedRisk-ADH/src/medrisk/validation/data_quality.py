"""Data Quality Score (DQS) computation.

Per-patient data quality assessment computed before any model inference.

v1 components:
1. Completeness — fraction of expected features observed
2. Consistency — fraction of domain rules that pass
3. Recency — exponential decay on lab result ages

v2 additions:
4. Range checks — physiological plausibility of lab values
5. Missingness classification — structural vs. workflow vs. random
6. Learned P(model_error) — optional trained reliability model

The DQS determines how much a downstream model should trust its own input.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

from medrisk.data.schemas import MarketConfig, PatientRecord
from medrisk.validation.range_checks import RangeCheckResult, check_ranges

logger = logging.getLogger(__name__)

# Expected feature counts
N_DEMOGRAPHIC_FEATURES = 5
N_DIAGNOSIS_CATEGORIES = 17  # Charlson categories
N_LAB_VALUES = 10
N_MEDICATION_FLAGS = 8
TOTAL_EXPECTED_FEATURES = (
    N_DEMOGRAPHIC_FEATURES + N_DIAGNOSIS_CATEGORIES + N_LAB_VALUES + N_MEDICATION_FLAGS
)


@dataclass(frozen=True)
class DQSResult:
    """Result of data quality assessment for a single patient.

    Attributes:
        patient_id: Patient identifier.
        completeness: Fraction of non-missing features [0, 1].
        consistency: Fraction of domain rules that pass [0, 1].
        recency: Weighted recency of lab results [0, 1].
        dqs: Composite data quality score [0, 1].
        tier: Quality tier ("adequate", "caution", "insufficient").
        rule_violations: List of violated consistency rules.
    """

    patient_id: str
    completeness: float
    consistency: float
    recency: float
    dqs: float
    tier: str
    rule_violations: list[str]


# --- Consistency rules ---


def _check_diabetes_hba1c(patient: PatientRecord) -> tuple[bool, bool]:
    """If diabetes diagnosed, HbA1c should be elevated (>=6.5%).
    Returns (applicable, passed).
    """
    has_diabetes = any(d.icd10_code.startswith("E11") for d in patient.diagnoses)
    hba1c_labs = [lr for lr in patient.lab_results if lr.loinc_code == "4548-4"]

    if not has_diabetes or not hba1c_labs:
        return False, True  # not applicable

    latest_hba1c = max(hba1c_labs, key=lambda x: x.date_collected)
    return True, latest_hba1c.value >= 5.7


def _check_ckd_egfr(patient: PatientRecord) -> tuple[bool, bool]:
    """If CKD stage 4-5, eGFR should be < 30."""
    has_severe_ckd = any(d.icd10_code in ("N18.4", "N18.5", "N18.6") for d in patient.diagnoses)
    egfr_labs = [lr for lr in patient.lab_results if lr.loinc_code == "48642-3"]

    if not has_severe_ckd or not egfr_labs:
        return False, True

    latest_egfr = max(egfr_labs, key=lambda x: x.date_collected)
    return True, latest_egfr.value < 30


def _check_hf_bnp(patient: PatientRecord) -> tuple[bool, bool]:
    """If heart failure diagnosed, NT-proBNP should be elevated (>125)."""
    has_hf = any(d.icd10_code.startswith("I50") for d in patient.diagnoses)
    bnp_labs = [lr for lr in patient.lab_results if lr.loinc_code == "33762-6"]

    if not has_hf or not bnp_labs:
        return False, True

    latest_bnp = max(bnp_labs, key=lambda x: x.date_collected)
    return True, latest_bnp.value > 125


def _check_hypertension_bp(patient: PatientRecord) -> tuple[bool, bool]:
    """If hypertension diagnosed, SBP should be > 120 or on medication."""
    has_htn = any(d.icd10_code.startswith("I10") for d in patient.diagnoses)
    sbp_labs = [lr for lr in patient.lab_results if lr.loinc_code == "8480-6"]
    on_antihypertensive = any(
        m.atc_code in ("C07AB02", "C09AA02", "C09CA01") for m in patient.medications
    )

    if not has_htn or (not sbp_labs and not on_antihypertensive):
        return False, True

    if on_antihypertensive:
        return True, True  # controlled hypertension is consistent

    latest_sbp = max(sbp_labs, key=lambda x: x.date_collected)
    return True, latest_sbp.value > 120


def _check_diabetes_no_code(patient: PatientRecord) -> tuple[bool, bool]:
    """If no diabetes code, HbA1c should be < 6.5%."""
    has_diabetes = any(d.icd10_code.startswith("E11") for d in patient.diagnoses)
    hba1c_labs = [lr for lr in patient.lab_results if lr.loinc_code == "4548-4"]

    if has_diabetes or not hba1c_labs:
        return False, True

    latest_hba1c = max(hba1c_labs, key=lambda x: x.date_collected)
    return True, latest_hba1c.value < 6.5


CONSISTENCY_RULES = [
    ("diabetes_hba1c", _check_diabetes_hba1c),
    ("ckd_egfr", _check_ckd_egfr),
    ("hf_bnp", _check_hf_bnp),
    ("hypertension_bp", _check_hypertension_bp),
    ("no_diabetes_hba1c", _check_diabetes_no_code),
]


def compute_completeness(patient: PatientRecord) -> float:
    """Compute feature completeness score for a patient.

    Args:
        patient: PatientRecord to assess.

    Returns:
        Completeness score in [0, 1].
    """
    observed = (
        N_DEMOGRAPHIC_FEATURES  # always present in record
        + len(patient.diagnoses)
        + len(patient.lab_results)
        + len(patient.medications)
    )
    return min(1.0, observed / TOTAL_EXPECTED_FEATURES)


def compute_consistency(patient: PatientRecord) -> tuple[float, list[str]]:
    """Compute consistency score and identify violations.

    Args:
        patient: PatientRecord to assess.

    Returns:
        Tuple of (consistency score in [0, 1], list of violated rule names).
    """
    applicable_count = 0
    passed_count = 0
    violations: list[str] = []

    for rule_name, rule_fn in CONSISTENCY_RULES:
        applicable, passed = rule_fn(patient)
        if applicable:
            applicable_count += 1
            if passed:
                passed_count += 1
            else:
                violations.append(rule_name)

    if applicable_count == 0:
        return 1.0, []

    return passed_count / applicable_count, violations


def compute_recency(
    patient: PatientRecord,
    reference_date: date | None = None,
    half_life_years: float = 1.4,
) -> float:
    """Compute lab recency score with exponential decay.

    Args:
        patient: PatientRecord to assess.
        reference_date: Date to compute age of labs against.
        half_life_years: Half-life for lab value relevance decay.

    Returns:
        Recency score in [0, 1]. Returns 0.0 if no labs present.
    """
    if not patient.lab_results:
        return 0.0

    if reference_date is None:
        reference_date = date(2024, 1, 1)

    decay_rate = math.log(2) / half_life_years
    weights = []

    for lab in patient.lab_results:
        age_years = (reference_date - lab.date_collected).days / 365.25
        if age_years < 0:
            age_years = 0
        weight = math.exp(-decay_rate * age_years)
        weights.append(weight)

    return sum(weights) / len(weights) if weights else 0.0


def compute_dqs(
    patient: PatientRecord,
    reference_date: date | None = None,
    alpha: float = 0.40,
    beta: float = 0.35,
    gamma: float = 0.25,
    half_life_years: float = 1.4,
) -> DQSResult:
    """Compute the composite Data Quality Score for a patient.

    Args:
        patient: PatientRecord to assess.
        reference_date: Date for recency computation.
        alpha: Weight for completeness component.
        beta: Weight for consistency component.
        gamma: Weight for recency component.
        half_life_years: Half-life for lab recency decay.

    Returns:
        DQSResult with all component scores and tier classification.
    """
    completeness = compute_completeness(patient)
    consistency, violations = compute_consistency(patient)
    recency = compute_recency(patient, reference_date, half_life_years)

    dqs = alpha * completeness + beta * consistency + gamma * recency

    if dqs >= 0.80:
        tier = "adequate"
    elif dqs >= 0.60:
        tier = "caution"
    else:
        tier = "insufficient"

    return DQSResult(
        patient_id=patient.patient_id,
        completeness=round(completeness, 4),
        consistency=round(consistency, 4),
        recency=round(recency, 4),
        dqs=round(dqs, 4),
        tier=tier,
        rule_violations=violations,
    )


# ============================================================================
# v2: Missingness classification + extended DQS
# ============================================================================


class MissingnessType(StrEnum):
    """Classification of why a feature is missing."""

    STRUCTURAL = "structural"
    WORKFLOW = "workflow"
    RANDOM = "random"


def classify_missingness(
    patient: PatientRecord,
    market_config: MarketConfig | None = None,
) -> dict[str, MissingnessType]:
    """Classify the missingness type for absent features.

    Args:
        patient: PatientRecord to assess.
        market_config: Market configuration for structural missingness detection.
            If None, all missing features are classified as RANDOM.

    Returns:
        Dict mapping feature category to MissingnessType.
    """
    result: dict[str, MissingnessType] = {}

    has_labs = len(patient.lab_results) > 0
    has_meds = len(patient.medications) > 0

    if not has_labs:
        if market_config and market_config.lab_completeness < 0.4:
            result["labs"] = MissingnessType.STRUCTURAL
        elif market_config and market_config.lab_completeness < 0.75:
            result["labs"] = MissingnessType.WORKFLOW
        else:
            result["labs"] = MissingnessType.RANDOM

    if not has_meds:
        if market_config and market_config.medication_recording < 0.4:
            result["medications"] = MissingnessType.STRUCTURAL
        elif market_config and market_config.medication_recording < 0.75:
            result["medications"] = MissingnessType.WORKFLOW
        else:
            result["medications"] = MissingnessType.RANDOM

    if len(patient.diagnoses) == 0:
        if market_config and market_config.coding_completeness < 0.5:
            result["diagnoses"] = MissingnessType.STRUCTURAL
        elif market_config and market_config.coding_completeness < 0.75:
            result["diagnoses"] = MissingnessType.WORKFLOW
        else:
            result["diagnoses"] = MissingnessType.RANDOM

    return result


@dataclass(frozen=True)
class DQSv2Result:
    """Extended data quality assessment (v2).

    Inherits v1 semantics and adds missingness classification,
    range checks, and optional learned error probability.

    Attributes:
        patient_id: Patient identifier.
        completeness: Fraction of non-missing features [0, 1].
        consistency: Fraction of domain rules that pass [0, 1].
        recency: Weighted recency of lab results [0, 1].
        dqs: Composite data quality score [0, 1] (v1 formula or learned).
        tier: Quality tier.
        rule_violations: Violated consistency rules.
        missingness_types: Per-category missingness classification.
        range_check: Range check results for lab values.
        range_score: Fraction of lab values within physiological range [0, 1].
        n_structural_missing: Count of structurally missing feature categories.
        n_workflow_missing: Count of workflow-missing feature categories.
        n_random_missing: Count of randomly missing feature categories.
        shift_score: Distribution shift indicator [0, 1] (0 = no shift).
        p_model_error: Learned P(model error | quality features), or None.
    """

    patient_id: str
    completeness: float
    consistency: float
    recency: float
    dqs: float
    tier: str
    rule_violations: list[str]
    missingness_types: dict[str, str] = field(default_factory=dict)
    range_check: RangeCheckResult = field(default_factory=RangeCheckResult)
    range_score: float = 1.0
    n_structural_missing: int = 0
    n_workflow_missing: int = 0
    n_random_missing: int = 0
    shift_score: float = 0.0
    p_model_error: float | None = None


def compute_dqs_v2(
    patient: PatientRecord,
    market_config: MarketConfig | None = None,
    reference_date: date | None = None,
    alpha: float = 0.40,
    beta: float = 0.35,
    gamma: float = 0.25,
    half_life_years: float = 1.4,
    error_model: object | None = None,
) -> DQSv2Result:
    """Compute extended Data Quality Score (v2).

    Computes all v1 components plus missingness classification, range checks,
    and optionally a learned P(model_error).

    Args:
        patient: PatientRecord to assess.
        market_config: Market configuration for missingness classification.
        reference_date: Date for recency computation.
        alpha: Weight for completeness (v1 fallback).
        beta: Weight for consistency (v1 fallback).
        gamma: Weight for recency (v1 fallback).
        half_life_years: Half-life for lab recency decay.
        error_model: Optional trained model with predict_proba(features) -> P(error).
            If None, DQS uses v1 weighted average.

    Returns:
        DQSv2Result with all quality features.
    """
    # v1 components
    completeness = compute_completeness(patient)
    consistency, violations = compute_consistency(patient)
    recency = compute_recency(patient, reference_date, half_life_years)

    # v2: missingness classification
    miss_types = classify_missingness(patient, market_config)
    n_structural = sum(1 for v in miss_types.values() if v == MissingnessType.STRUCTURAL)
    n_workflow = sum(1 for v in miss_types.values() if v == MissingnessType.WORKFLOW)
    n_random = sum(1 for v in miss_types.values() if v == MissingnessType.RANDOM)

    # v2: range checks on lab values
    lab_values: dict[str, float | None] = {}
    lab_name_map = {
        "4548-4": "lab_hba1c",
        "2160-0": "lab_creatinine",
        "48642-3": "lab_egfr",
        "2093-3": "lab_total_cholesterol",
        "2085-9": "lab_hdl",
        "13457-7": "lab_ldl",
        "2571-8": "lab_triglycerides",
        "8480-6": "lab_systolic_bp",
        "8462-4": "lab_diastolic_bp",
        "33762-6": "lab_nt_probnp",
    }
    for lr in patient.lab_results:
        col_name = lab_name_map.get(lr.loinc_code)
        if col_name:
            lab_values[col_name] = lr.value

    range_result = check_ranges(lab_values)

    # Composite DQS (v1 formula as default)
    dqs = alpha * completeness + beta * consistency + gamma * recency

    # v2: learned error probability (if model provided)
    p_error = None
    if error_model is not None and hasattr(error_model, "predict_proba_from_quality"):
        p_error = error_model.predict_proba_from_quality(
            completeness=completeness,
            consistency=consistency,
            recency=recency,
            range_score=range_result.range_score,
            n_structural_missing=n_structural,
            n_workflow_missing=n_workflow,
            n_random_missing=n_random,
        )

    if dqs >= 0.80:
        tier = "adequate"
    elif dqs >= 0.60:
        tier = "caution"
    else:
        tier = "insufficient"

    return DQSv2Result(
        patient_id=patient.patient_id,
        completeness=round(completeness, 4),
        consistency=round(consistency, 4),
        recency=round(recency, 4),
        dqs=round(dqs, 4),
        tier=tier,
        rule_violations=violations,
        missingness_types={k: v.value for k, v in miss_types.items()},
        range_check=range_result,
        range_score=range_result.range_score,
        n_structural_missing=n_structural,
        n_workflow_missing=n_workflow,
        n_random_missing=n_random,
        shift_score=0.0,
        p_model_error=p_error,
    )
