"""Multi-market synthetic patient cohort generator.

Generates GDPR-safe synthetic patient records using epidemiological prevalence
rates and parametric distributions. No individual-level data is used.

The generator operates in two stages:
1. Ground truth: simulate true disease trajectories via CTMC
2. Observation: degrade ground truth with market-specific missingness and noise

This separation enables controlled failure mode experiments.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date, timedelta

import numpy as np
from numpy.random import Generator

from medrisk.data.charlson import compute_charlson_index
from medrisk.data.icd10 import CODELIST, get_codes_by_category
from medrisk.data.schemas import (
    MARKET_CONFIGS,
    Diagnosis,
    LabResult,
    Market,
    MarketConfig,
    Medication,
    PatientRecord,
    Sex,
    SmokingStatus,
)

logger = logging.getLogger(__name__)

# --- Baseline prevalence rates (approximate, age-adjusted) ---
# Sources: GBD 2019, RKI DEGS1, Eurostat

BASELINE_PREVALENCE: dict[str, float] = {
    "hypertension": 0.30,
    "ihd": 0.06,
    "mi": 0.03,
    "afib": 0.04,
    "hf": 0.03,
    "stroke": 0.02,
    "cvd": 0.02,
    "pvd": 0.03,
    "diabetes": 0.10,
    "diabetes_renal": 0.02,
    "diabetes_eye": 0.015,
    "prediabetes": 0.08,
    "dyslipidemia": 0.25,
    "obesity": 0.20,
    "ckd": 0.08,
    "copd": 0.10,
    "asthma": 0.05,
    "cancer": 0.02,
    "liver_mild": 0.03,
    "liver_severe": 0.005,
    "substance": 0.04,
    "depression": 0.08,
    "anxiety": 0.06,
    "msk": 0.15,
    "dementia": 0.01,
    "alzheimer": 0.012,
    "alzheimer_early": 0.002,
    "alzheimer_late": 0.010,
    "hemiplegia": 0.005,
    "rheumatic": 0.01,
    "peptic_ulcer": 0.02,
    "hiv": 0.001,
}

# Age-dependent prevalence multipliers (relative to baseline)
AGE_MULTIPLIERS: dict[str, dict[str, float]] = {
    "young": {  # 18-40
        "hypertension": 0.3,
        "ihd": 0.1,
        "mi": 0.05,
        "afib": 0.1,
        "hf": 0.05,
        "stroke": 0.1,
        "diabetes": 0.2,
        "ckd": 0.1,
        "copd": 0.1,
        "cancer": 0.2,
        "dementia": 0.01,
        "alzheimer": 0.001,
        "pvd": 0.1,
    },
    "middle": {  # 40-65
        "hypertension": 1.0,
        "ihd": 1.0,
        "mi": 1.0,
        "afib": 0.8,
        "hf": 0.8,
        "stroke": 0.8,
        "diabetes": 1.0,
        "ckd": 0.8,
        "copd": 0.8,
        "cancer": 1.0,
        "dementia": 0.1,
        "alzheimer": 0.05,
        "pvd": 1.0,
    },
    "elderly": {  # 65+
        "hypertension": 1.8,
        "ihd": 2.5,
        "mi": 2.5,
        "afib": 3.0,
        "hf": 3.5,
        "stroke": 3.0,
        "diabetes": 1.5,
        "ckd": 2.5,
        "copd": 2.0,
        "cancer": 2.0,
        "dementia": 5.0,
        "alzheimer": 8.0,
        "pvd": 2.5,
    },
}

# Comorbidity co-occurrence: conditions that increase probability of others
COMORBIDITY_LINKS: dict[str, dict[str, float]] = {
    "diabetes": {"ihd": 2.0, "ckd": 2.5, "pvd": 1.8, "stroke": 1.5, "hf": 1.5, "alzheimer": 1.5},
    "hypertension": {"ihd": 1.8, "stroke": 2.0, "ckd": 1.5, "hf": 1.5, "afib": 1.3, "alzheimer": 1.4},
    "obesity": {"diabetes": 2.5, "hypertension": 1.8, "dyslipidemia": 2.0, "msk": 1.5},
    "ihd": {"mi": 3.0, "hf": 2.0, "afib": 1.5},
    "copd": {"hf": 1.5, "cancer": 1.5},
    "alzheimer": {"depression": 2.0, "anxiety": 1.5},
}

# Lab reference ranges and condition-dependent distributions
LAB_DEFINITIONS: dict[str, dict] = {
    "4548-4": {
        "name": "HbA1c",
        "unit": "%",
        "ref_low": 4.0,
        "ref_high": 5.6,
        "normal": (5.0, 0.3),
        "diabetes": (8.0, 1.5),
        "prediabetes": (6.0, 0.3),
    },
    "2160-0": {
        "name": "Creatinine",
        "unit": "mg/dL",
        "ref_low": 0.6,
        "ref_high": 1.2,
        "normal": (0.9, 0.15),
        "ckd": (2.5, 1.0),
    },
    "48642-3": {
        "name": "eGFR",
        "unit": "mL/min/1.73m2",
        "ref_low": 60.0,
        "ref_high": 120.0,
        "normal": (90.0, 15.0),
        "ckd": (35.0, 15.0),
    },
    "2093-3": {
        "name": "Total Cholesterol",
        "unit": "mg/dL",
        "ref_low": 125.0,
        "ref_high": 200.0,
        "normal": (185.0, 25.0),
        "dyslipidemia": (260.0, 35.0),
    },
    "2085-9": {
        "name": "HDL",
        "unit": "mg/dL",
        "ref_low": 40.0,
        "ref_high": 60.0,
        "normal": (55.0, 10.0),
        "dyslipidemia": (35.0, 8.0),
    },
    "13457-7": {
        "name": "LDL",
        "unit": "mg/dL",
        "ref_low": 0.0,
        "ref_high": 100.0,
        "normal": (100.0, 20.0),
        "dyslipidemia": (170.0, 30.0),
    },
    "2571-8": {
        "name": "Triglycerides",
        "unit": "mg/dL",
        "ref_low": 0.0,
        "ref_high": 150.0,
        "normal": (110.0, 30.0),
        "dyslipidemia": (250.0, 60.0),
    },
    "8480-6": {
        "name": "Systolic BP",
        "unit": "mmHg",
        "ref_low": 90.0,
        "ref_high": 120.0,
        "normal": (118.0, 10.0),
        "hypertension": (150.0, 15.0),
    },
    "8462-4": {
        "name": "Diastolic BP",
        "unit": "mmHg",
        "ref_low": 60.0,
        "ref_high": 80.0,
        "normal": (75.0, 8.0),
        "hypertension": (95.0, 10.0),
    },
    "33762-6": {
        "name": "NT-proBNP",
        "unit": "pg/mL",
        "ref_low": 0.0,
        "ref_high": 125.0,
        "normal": (60.0, 30.0),
        "hf": (1500.0, 800.0),
    },
    # Cognitive and Alzheimer biomarkers
    "72106-8": {
        "name": "MMSE",
        "unit": "score",
        "ref_low": 24.0,
        "ref_high": 30.0,
        "normal": (28.0, 1.5),
        "alzheimer": (18.0, 5.0),
        "alzheimer_early": (22.0, 3.0),
        "alzheimer_late": (16.0, 5.0),
    },
    "72172-0": {
        "name": "MoCA",
        "unit": "score",
        "ref_low": 26.0,
        "ref_high": 30.0,
        "normal": (27.0, 2.0),
        "alzheimer": (16.0, 5.0),
        "alzheimer_early": (20.0, 3.0),
        "alzheimer_late": (14.0, 5.0),
    },
    "33203-1": {
        "name": "CSF Amyloid-Beta42",
        "unit": "pg/mL",
        "ref_low": 600.0,
        "ref_high": 1500.0,
        "normal": (900.0, 150.0),
        "alzheimer": (450.0, 120.0),
        "alzheimer_early": (500.0, 100.0),
        "alzheimer_late": (400.0, 120.0),
    },
    "72260-3": {
        "name": "CSF p-tau181",
        "unit": "pg/mL",
        "ref_low": 0.0,
        "ref_high": 22.0,
        "normal": (15.0, 5.0),
        "alzheimer": (65.0, 20.0),
        "alzheimer_early": (55.0, 15.0),
        "alzheimer_late": (70.0, 20.0),
    },
}

# Medication mappings: condition -> [(ATC, name, probability)]
MEDICATION_MAP: dict[str, list[tuple[str, str, float]]] = {
    "hypertension": [
        ("C07AB02", "Metoprolol", 0.40),
        ("C09AA02", "Enalapril", 0.35),
        ("C09CA01", "Losartan", 0.30),
    ],
    "dyslipidemia": [
        ("C10AA01", "Simvastatin", 0.30),
        ("C10AA05", "Atorvastatin", 0.45),
    ],
    "ihd": [
        ("B01AC06", "ASA", 0.70),
    ],
    "mi": [
        ("B01AC06", "ASA", 0.85),
    ],
    "afib": [
        ("B01AF01", "Rivaroxaban", 0.50),
    ],
    "diabetes": [
        ("A10BA02", "Metformin", 0.65),
    ],
    "alzheimer": [
        ("N06DA02", "Donepezil", 0.50),
        ("N06DA03", "Rivastigmine", 0.25),
        ("N06DA04", "Galantamine", 0.15),
        ("N06DX01", "Memantine", 0.35),
    ],
}

# CTMC state definitions for disease progression
# States: 0=Healthy, 1=Risk factors, 2=Diagnosed chronic, 3=Complication, 4=Major event (absorbing)
CTMC_INTENSITIES: dict[tuple[int, int], float] = {
    (0, 1): 0.08,  # healthy -> risk factors
    (1, 2): 0.06,  # risk factors -> chronic condition
    (1, 0): 0.02,  # risk factors -> healthy (lifestyle change)
    (2, 3): 0.04,  # chronic -> complication
    (3, 4): 0.03,  # complication -> major event
    (2, 4): 0.01,  # chronic -> major event (skip complication)
}

EVENT_TYPES = ["death", "mi", "stroke", "hf", "ckd_progression"]

# Alzheimer-specific CTMC (7-state model)
# States: 0=NC, 1=SCD, 2=MCI, 3=Mild AD, 4=Moderate AD, 5=Severe AD, 6=Death
AD_CTMC_INTENSITIES: dict[tuple[int, int], float] = {
    (0, 1): 0.04,   # NC -> SCD
    (1, 2): 0.08,   # SCD -> MCI
    (2, 3): 0.15,   # MCI -> Mild AD
    (3, 4): 0.25,   # Mild -> Moderate AD
    (4, 5): 0.33,   # Moderate -> Severe AD
    (5, 6): 0.50,   # Severe AD -> Death
    (3, 6): 0.02,   # Mild AD direct mortality
    (4, 6): 0.05,   # Moderate AD direct mortality
}
AD_ABSORBING_STATES = {6}
AD_EVENT_TYPES = ["death", "institutionalization", "cognitive_decline"]


def _get_age_bracket(age: int) -> str:
    if age < 40:
        return "young"
    if age < 65:
        return "middle"
    return "elderly"


def _simulate_ctmc_trajectory(
    rng: Generator,
    max_time: float,
    age_bracket: str,
    has_risk_factors: bool,
) -> tuple[float, bool, str | None]:
    """Simulate a continuous-time Markov chain trajectory.

    Returns:
        (time_to_event, event_occurred, event_type)
    """
    # Start state depends on existing risk factors
    state = 1 if has_risk_factors else 0
    elapsed = 0.0

    # Age-based intensity multiplier
    age_mult = {"young": 0.5, "middle": 1.0, "elderly": 1.8}.get(age_bracket, 1.0)

    while elapsed < max_time and state < 4:
        # Compute total outgoing rate from current state
        outgoing = {
            (s, d): rate * age_mult for (s, d), rate in CTMC_INTENSITIES.items() if s == state
        }
        if not outgoing:
            break

        total_rate = sum(outgoing.values())
        if total_rate <= 0:
            break

        # Time to next transition (exponential)
        dt = rng.exponential(1.0 / total_rate)
        elapsed += dt

        if elapsed >= max_time:
            break

        # Choose destination state
        destinations = list(outgoing.keys())
        probs = np.array([outgoing[d] for d in destinations]) / total_rate
        chosen_idx = rng.choice(len(destinations), p=probs)
        state = destinations[chosen_idx][1]

    if state == 4:
        event_type = rng.choice(EVENT_TYPES)
        return elapsed, True, event_type
    return max_time, False, None


def _generate_conditions(
    rng: Generator,
    age: int,
    sex: str,
    bmi: float,
    smoking: str,
    market_config: MarketConfig,
) -> list[str]:
    """Generate a set of true conditions for a patient based on prevalence and risk factors."""
    age_bracket = _get_age_bracket(age)
    age_mults = AGE_MULTIPLIERS.get(age_bracket, {})
    conditions: list[str] = []

    # First pass: independent conditions
    for category, base_prev in BASELINE_PREVALENCE.items():
        adjusted = base_prev * age_mults.get(category, 1.0)

        # Sex adjustments
        if sex == "M" and category in ("ihd", "mi", "pvd"):
            adjusted *= 1.4
        if sex == "F" and category in ("osteoporosis", "depression", "anxiety"):
            adjusted *= 1.3

        # BMI adjustments
        if bmi > 30 and category in ("diabetes", "hypertension", "dyslipidemia", "msk"):
            adjusted *= 1.5
        if bmi > 35:
            adjusted *= 1.2

        # Smoking adjustments
        if smoking == "current" and category in ("copd", "cancer", "ihd", "mi", "pvd", "stroke"):
            adjusted *= 2.0
        elif smoking == "former" and category in ("copd", "cancer"):
            adjusted *= 1.3

        # Market prevalence modifiers
        adjusted *= market_config.prevalence_modifiers.get(category, 1.0)

        # Cap at 0.9
        adjusted = min(adjusted, 0.9)

        if rng.random() < adjusted:
            conditions.append(category)

    # Second pass: comorbidity co-occurrence
    for trigger, targets in COMORBIDITY_LINKS.items():
        if trigger in conditions:
            for target, multiplier in targets.items():
                if target not in conditions:
                    base = BASELINE_PREVALENCE.get(target, 0.01)
                    boosted = min(base * multiplier * age_mults.get(target, 1.0), 0.8)
                    if rng.random() < boosted:
                        conditions.append(target)

    return list(set(conditions))


def _conditions_to_diagnoses(
    rng: Generator,
    conditions: list[str],
    reference_date: date,
    market_config: MarketConfig,
) -> list[Diagnosis]:
    """Convert condition categories to ICD-10 coded diagnoses with market degradation."""
    diagnoses: list[Diagnosis] = []

    for condition in conditions:
        # Skip with probability (1 - coding_completeness)
        if rng.random() > market_config.coding_completeness:
            continue

        codes = get_codes_by_category(condition)
        if not codes:
            continue

        # Pick one representative code
        chosen = rng.choice(codes)

        # Apply diagnosis lag
        lag_days = max(
            0,
            int(
                rng.normal(
                    market_config.diagnosis_lag_mean_days,
                    market_config.diagnosis_lag_std_days,
                )
            ),
        )
        diag_date = reference_date - timedelta(days=int(rng.integers(365, 3650)) + lag_days)

        diagnoses.append(
            Diagnosis(
                icd10_code=chosen.code,
                description=chosen.description,
                date_recorded=diag_date,
                is_primary=(len(diagnoses) == 0),
            )
        )

    return diagnoses


def _generate_labs(
    rng: Generator,
    conditions: list[str],
    reference_date: date,
    market_config: MarketConfig,
) -> list[LabResult]:
    """Generate lab results with condition-dependent values and market degradation."""
    labs: list[LabResult] = []

    for loinc, defn in LAB_DEFINITIONS.items():
        # Skip with probability (1 - lab_completeness)
        if rng.random() > market_config.lab_completeness:
            continue

        # Determine distribution based on conditions
        mean, std = defn["normal"]
        for condition in conditions:
            if condition in defn:
                mean, std = defn[condition]
                break

        value = rng.normal(mean, std)
        # Add market-specific noise
        value += rng.normal(0, market_config.lab_noise_sigma * abs(mean))
        # Ensure non-negative for most labs
        if defn["ref_low"] >= 0:
            value = max(0.0, value)
        # Clamp cognitive scores to valid range (0-30)
        if defn["unit"] == "score":
            value = np.clip(value, 0.0, 30.0)

        # Lab date: within past 2 years with some variability
        days_ago = int(rng.integers(30, 730))
        lab_date = reference_date - timedelta(days=days_ago)

        labs.append(
            LabResult(
                loinc_code=loinc,
                name=defn["name"],
                value=round(float(value), 1),
                unit=defn["unit"],
                date_collected=lab_date,
                reference_low=defn["ref_low"],
                reference_high=defn["ref_high"],
            )
        )

    return labs


def _generate_medications(
    rng: Generator,
    conditions: list[str],
    reference_date: date,
    market_config: MarketConfig,
) -> list[Medication]:
    """Generate medication records based on conditions with market degradation."""
    meds: list[Medication] = []

    for condition in conditions:
        med_options = MEDICATION_MAP.get(condition, [])
        for atc, name, prob in med_options:
            # Recording probability adjusted by market
            effective_prob = prob * market_config.medication_recording
            if rng.random() < effective_prob:
                rx_date = reference_date - timedelta(days=int(rng.integers(30, 1826)))
                meds.append(
                    Medication(
                        atc_code=atc,
                        name=name,
                        date_prescribed=rx_date,
                        active=rng.random() > 0.15,
                    )
                )

    # Deduplicate by ATC code (keep most recent)
    seen: dict[str, Medication] = {}
    for med in meds:
        if med.atc_code not in seen or med.date_prescribed > seen[med.atc_code].date_prescribed:
            seen[med.atc_code] = med

    return list(seen.values())


def generate_patient(
    rng: Generator,
    market: str,
    reference_date: date | None = None,
) -> PatientRecord:
    """Generate a single synthetic patient record.

    Args:
        rng: NumPy random generator for reproducibility.
        market: Market code ("DE", "ES", "FR", "INT").
        reference_date: Reference date for the patient record.

    Returns:
        A complete PatientRecord with ground truth annotations.
    """
    if reference_date is None:
        reference_date = date(2024, 1, 1)

    config = MARKET_CONFIGS[market]

    # Demographics
    age = int(np.clip(rng.normal(config.age_mean, config.age_std), 18, 95))
    sex = rng.choice(["M", "F"])
    bmi = float(np.clip(rng.normal(26.5, 5.0), 15.0, 55.0))
    smoking = rng.choice(
        ["never", "former", "current"],
        p=[0.55, 0.25, 0.20],
    )

    # Ground truth conditions
    gt_conditions = _generate_conditions(rng, age, sex, bmi, smoking, config)

    # CTMC trajectory
    has_risk_factors = any(
        c in gt_conditions for c in ("hypertension", "diabetes", "dyslipidemia", "obesity")
    )
    follow_up = float(rng.uniform(1.0, 10.0))
    time_to_event, event_occurred, event_type = _simulate_ctmc_trajectory(
        rng,
        follow_up,
        _get_age_bracket(age),
        has_risk_factors,
    )

    # Observed data (degraded by market config)
    diagnoses = _conditions_to_diagnoses(rng, gt_conditions, reference_date, config)
    labs = _generate_labs(rng, gt_conditions, reference_date, config)
    medications = _generate_medications(rng, gt_conditions, reference_date, config)

    # Compute ground truth risk score (Charlson-based)
    gt_codes = []
    for cond in gt_conditions:
        codes = get_codes_by_category(cond)
        if codes:
            gt_codes.append(codes[0].code)
    gt_cci = compute_charlson_index(gt_codes)

    # DQS approximation for ground truth annotation
    total_expected_features = 50
    observed_features = (
        5  # demographics (always present)
        + len(diagnoses)
        + len(labs)
        + len(medications)
    )
    gt_dqs = min(1.0, observed_features / total_expected_features)

    return PatientRecord(
        patient_id=str(uuid.uuid4()),
        market=Market(market),
        age=age,
        sex=Sex(sex),
        bmi=round(bmi, 1),
        smoking_status=SmokingStatus(smoking),
        diagnoses=diagnoses,
        lab_results=labs,
        medications=medications,
        follow_up_years=round(follow_up, 2),
        event_occurred=event_occurred,
        event_type=event_type,
        time_to_event=round(float(time_to_event), 2),
        gt_true_conditions=gt_conditions,
        gt_true_risk_score=float(gt_cci),
        gt_data_quality_score=round(gt_dqs, 3),
    )


def generate_cohort(
    n_per_market: int = 5000,
    markets: list[str] | None = None,
    seed: int = 42,
    reference_date: date | None = None,
) -> list[PatientRecord]:
    """Generate a multi-market synthetic cohort.

    Args:
        n_per_market: Number of patients per market.
        markets: List of market codes. Defaults to all four markets.
        seed: Random seed for reproducibility.
        reference_date: Reference date for patient records.

    Returns:
        List of PatientRecord objects across all markets.
    """
    if markets is None:
        markets = ["DE", "ES", "FR", "INT"]

    rng = np.random.default_rng(seed)
    cohort: list[PatientRecord] = []

    for market in markets:
        logger.info("Generating %d patients for market %s", n_per_market, market)
        for _ in range(n_per_market):
            patient = generate_patient(rng, market, reference_date)
            cohort.append(patient)
        logger.info("Market %s complete: %d patients", market, n_per_market)

    logger.info("Total cohort size: %d patients", len(cohort))
    return cohort


def cohort_to_dataframe(cohort: list[PatientRecord]):
    """Convert a list of PatientRecords to a flat pandas DataFrame.

    Flattens diagnoses, labs, and medications into summary columns suitable
    for modelling.
    """
    import pandas as pd

    records = []
    for p in cohort:
        row: dict = {
            "patient_id": p.patient_id,
            "market": p.market.value,
            "age": p.age,
            "sex": p.sex.value,
            "bmi": p.bmi,
            "smoking_status": p.smoking_status.value,
            "n_diagnoses": len(p.diagnoses),
            "n_labs": len(p.lab_results),
            "n_medications": len(p.medications),
            "follow_up_years": p.follow_up_years,
            "event_occurred": p.event_occurred,
            "event_type": p.event_type,
            "time_to_event": p.time_to_event,
            "gt_true_risk_score": p.gt_true_risk_score,
            "gt_data_quality_score": p.gt_data_quality_score,
        }

        # Charlson index from observed diagnoses
        icd_codes = [d.icd10_code for d in p.diagnoses]
        row["charlson_index"] = compute_charlson_index(icd_codes)

        # ICD-10 category binary flags
        observed_categories = set()
        for d in p.diagnoses:
            code_info = CODELIST.get(d.icd10_code)
            if code_info:
                observed_categories.add(code_info.category)

        for cat in sorted(BASELINE_PREVALENCE.keys()):
            row[f"has_{cat}"] = cat in observed_categories

        # Lab values (most recent per LOINC code)
        lab_map: dict[str, float] = {}
        for lr in p.lab_results:
            lab_map[lr.loinc_code] = lr.value
        for loinc, defn in LAB_DEFINITIONS.items():
            col_name = f"lab_{defn['name'].lower().replace(' ', '_').replace('-', '_')}"
            row[col_name] = lab_map.get(loinc)

        # Medication flags
        med_atcs = {m.atc_code for m in p.medications if m.active}
        for _condition, med_list in MEDICATION_MAP.items():
            for atc, name, _ in med_list:
                col_name = f"med_{name.lower()}"
                row[col_name] = atc in med_atcs

        # Ground truth conditions count
        row["gt_n_conditions"] = len(p.gt_true_conditions)

        records.append(row)

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Alzheimer's Disease -- specialised generators
# ---------------------------------------------------------------------------


def _simulate_ad_ctmc_trajectory(
    rng: Generator,
    max_time: float,
    age: int,
    apoe4: bool,
) -> tuple[float, bool, str | None, int]:
    """Simulate an Alzheimer-specific 7-state CTMC trajectory.

    Returns:
        (time_to_event, event_occurred, event_type, final_state)
    """
    state = 0
    elapsed = 0.0

    # Age-based multiplier (AD accelerates sharply with age)
    age_mult = 1.0
    if age >= 80:
        age_mult = 2.0
    elif age >= 70:
        age_mult = 1.5
    elif age < 65:
        age_mult = 0.3

    # ApoE4 effect: strongest on risk/onset (pre-clinical), weaker post-diagnosis
    # Literature: ApoE4 accelerates early transitions but has mixed effect on
    # late-stage progression (Suzuki et al. 2020, Lancet Neurol)
    _apoe4_by_state = {0: 1.5, 1: 1.5, 2: 1.3, 3: 1.1, 4: 1.0, 5: 1.0}

    while elapsed < max_time and state not in AD_ABSORBING_STATES:
        apoe4_mult = _apoe4_by_state.get(state, 1.0) if apoe4 else 1.0
        combined_mult = age_mult * apoe4_mult
        outgoing = {
            (s, d): rate * combined_mult
            for (s, d), rate in AD_CTMC_INTENSITIES.items()
            if s == state
        }
        if not outgoing:
            break

        total_rate = sum(outgoing.values())
        if total_rate <= 0:
            break

        dt = rng.exponential(1.0 / total_rate)
        elapsed += dt

        if elapsed >= max_time:
            break

        destinations = list(outgoing.keys())
        probs = np.array([outgoing[d] for d in destinations]) / total_rate
        chosen_idx = rng.choice(len(destinations), p=probs)
        state = destinations[chosen_idx][1]

    if state in AD_ABSORBING_STATES:
        event_type = rng.choice(AD_EVENT_TYPES)
        return elapsed, True, event_type, state

    return max_time, False, None, state


def generate_ad_patient(
    rng: Generator,
    market: str,
    reference_date: date | None = None,
) -> PatientRecord:
    """Generate a synthetic Alzheimer's disease patient record.

    Produces patients with AD-relevant demographics (older age distribution),
    apoE4 genotype, cognitive biomarkers, and cholinesterase inhibitor medications.
    Uses the 7-state AD CTMC for disease trajectory simulation.

    Args:
        rng: NumPy random generator.
        market: Market code.
        reference_date: Reference date for the record.

    Returns:
        A PatientRecord with Alzheimer-specific fields populated.
    """
    if reference_date is None:
        reference_date = date(2024, 1, 1)

    config = MARKET_CONFIGS[market]

    # Demographics -- skewed older for AD cohort
    age = int(np.clip(rng.normal(72, 8), 50, 95))
    sex = rng.choice(["M", "F"], p=[0.40, 0.60])  # AD more common in women
    bmi = float(np.clip(rng.normal(25.5, 4.5), 16.0, 45.0))
    smoking = rng.choice(
        ["never", "former", "current"],
        p=[0.60, 0.30, 0.10],
    )

    # AD-specific risk factors
    apoe4 = bool(rng.random() < 0.40)  # ~40% of AD patients carry apoE4
    family_history = bool(rng.random() < 0.35)
    education_years = int(np.clip(rng.normal(12, 3), 6, 22))

    # Generate general conditions (may include cardiovascular comorbidities)
    gt_conditions = _generate_conditions(rng, age, sex, bmi, smoking, config)

    # Ensure Alzheimer category is present
    if "alzheimer" not in gt_conditions and "alzheimer_early" not in gt_conditions and "alzheimer_late" not in gt_conditions:
        if age < 65:
            gt_conditions.append("alzheimer_early")
        else:
            gt_conditions.append("alzheimer_late")

    # AD CTMC trajectory
    follow_up = float(rng.uniform(2.0, 15.0))
    time_to_event, event_occurred, event_type, _final_state = _simulate_ad_ctmc_trajectory(
        rng, follow_up, age, apoe4,
    )

    # Observed data
    diagnoses = _conditions_to_diagnoses(rng, gt_conditions, reference_date, config)
    labs = _generate_labs(rng, gt_conditions, reference_date, config)
    medications = _generate_medications(rng, gt_conditions, reference_date, config)

    # Ground truth risk score
    gt_codes = []
    for cond in gt_conditions:
        codes = get_codes_by_category(cond)
        if codes:
            gt_codes.append(codes[0].code)
    gt_cci = compute_charlson_index(gt_codes)

    # DQS approximation
    total_expected_features = 50
    observed_features = 5 + len(diagnoses) + len(labs) + len(medications)
    gt_dqs = min(1.0, observed_features / total_expected_features)

    return PatientRecord(
        patient_id=str(uuid.uuid4()),
        market=Market(market),
        age=age,
        sex=Sex(sex),
        bmi=round(bmi, 1),
        smoking_status=SmokingStatus(smoking),
        diagnoses=diagnoses,
        lab_results=labs,
        medications=medications,
        follow_up_years=round(follow_up, 2),
        event_occurred=event_occurred,
        event_type=event_type,
        time_to_event=round(float(time_to_event), 2),
        gt_true_conditions=gt_conditions,
        gt_true_risk_score=float(gt_cci),
        gt_data_quality_score=round(gt_dqs, 3),
        apoe4_carrier=apoe4,
        family_history_dementia=family_history,
        education_years=education_years,
    )


def generate_ad_cohort(
    n_per_market: int = 500,
    markets: list[str] | None = None,
    seed: int = 42,
    reference_date: date | None = None,
) -> list[PatientRecord]:
    """Generate a multi-market Alzheimer's disease synthetic cohort.

    Args:
        n_per_market: Number of AD patients per market.
        markets: List of market codes. Defaults to all four markets.
        seed: Random seed for reproducibility.
        reference_date: Reference date for patient records.

    Returns:
        List of PatientRecord objects with AD-specific fields.
    """
    if markets is None:
        markets = ["DE", "ES", "FR", "INT"]

    rng = np.random.default_rng(seed)
    cohort: list[PatientRecord] = []

    for market in markets:
        logger.info("Generating %d AD patients for market %s", n_per_market, market)
        for _ in range(n_per_market):
            patient = generate_ad_patient(rng, market, reference_date)
            cohort.append(patient)
        logger.info("Market %s AD cohort complete: %d patients", market, n_per_market)

    logger.info("Total AD cohort size: %d patients", len(cohort))
    return cohort
