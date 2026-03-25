"""Data profile classification for model routing.

Classifies each patient record into a data availability profile that
determines which model should be used for prediction. This replaces
blind median imputation with intentional model selection based on
what data is actually present.
"""

from __future__ import annotations

import logging
from enum import StrEnum

import pandas as pd

logger = logging.getLogger(__name__)


class DataProfile(StrEnum):
    """Data availability profile for model routing."""

    FULL = "full"
    NO_LABS = "no_labs"
    NO_MEDS = "no_meds"
    MINIMAL = "minimal"
    INSUFFICIENT = "insufficient"


# Default column groups
DEFAULT_LAB_COLS = [
    "lab_hba1c",
    "lab_creatinine",
    "lab_egfr",
    "lab_total_cholesterol",
    "lab_hdl",
    "lab_ldl",
    "lab_triglycerides",
    "lab_systolic_bp",
    "lab_diastolic_bp",
    "lab_nt_probnp",
]

DEFAULT_MED_COLS = [
    "med_metoprolol",
    "med_enalapril",
    "med_losartan",
    "med_simvastatin",
    "med_atorvastatin",
    "med_asa",
    "med_rivaroxaban",
    "med_metformin",
]

DEFAULT_CORE_COLS = [
    "age",
    "bmi",
    "sex",
    "smoking_status",
    "charlson_index",
]


def classify_data_profile(
    row: pd.Series,
    lab_cols: list[str] | None = None,
    med_cols: list[str] | None = None,
    core_cols: list[str] | None = None,
    lab_threshold: float = 0.3,
    med_threshold: float = 0.3,
) -> DataProfile:
    """Classify a single record's data availability profile.

    Args:
        row: A single row from a cohort DataFrame.
        lab_cols: Lab value column names.
        med_cols: Medication flag column names.
        core_cols: Core demographic/diagnosis columns.
        lab_threshold: Fraction of labs that must be non-null to count as present.
        med_threshold: Fraction of meds that must be non-null to count as present.

    Returns:
        DataProfile indicating which model should be used.
    """
    lab_cols = lab_cols or [c for c in DEFAULT_LAB_COLS if c in row.index]
    med_cols = med_cols or [c for c in DEFAULT_MED_COLS if c in row.index]
    core_cols = core_cols or [c for c in DEFAULT_CORE_COLS if c in row.index]

    # Check core features
    if core_cols:
        core_present = sum(1 for c in core_cols if pd.notna(row.get(c)))
        if core_present < len(core_cols) * 0.5:
            return DataProfile.INSUFFICIENT

    # Check lab and med availability
    has_labs = False
    has_meds = False

    if lab_cols:
        lab_present = sum(1 for c in lab_cols if pd.notna(row.get(c)))
        has_labs = (lab_present / len(lab_cols)) >= lab_threshold

    if med_cols:
        med_present = sum(1 for c in med_cols if pd.notna(row.get(c)))
        has_meds = (med_present / len(med_cols)) >= med_threshold

    if has_labs and has_meds:
        return DataProfile.FULL
    if not has_labs and has_meds:
        return DataProfile.NO_LABS
    if has_labs and not has_meds:
        return DataProfile.NO_MEDS
    # Neither labs nor meds, but core is OK
    return DataProfile.MINIMAL


def classify_cohort_profiles(
    df: pd.DataFrame,
    lab_cols: list[str] | None = None,
    med_cols: list[str] | None = None,
    core_cols: list[str] | None = None,
    lab_threshold: float = 0.3,
    med_threshold: float = 0.3,
) -> pd.Series:
    """Classify data profiles for an entire cohort.

    Args:
        df: Cohort DataFrame.
        lab_cols: Lab value column names.
        med_cols: Medication flag column names.
        core_cols: Core demographic/diagnosis columns.
        lab_threshold: Fraction of labs that must be non-null.
        med_threshold: Fraction of meds that must be non-null.

    Returns:
        Series of DataProfile values indexed like df.
    """
    lab_cols = lab_cols or [c for c in DEFAULT_LAB_COLS if c in df.columns]
    med_cols = med_cols or [c for c in DEFAULT_MED_COLS if c in df.columns]
    core_cols = core_cols or [c for c in DEFAULT_CORE_COLS if c in df.columns]

    profiles = df.apply(
        classify_data_profile,
        axis=1,
        lab_cols=lab_cols,
        med_cols=med_cols,
        core_cols=core_cols,
        lab_threshold=lab_threshold,
        med_threshold=med_threshold,
    )

    # Log distribution
    counts = profiles.value_counts()
    for profile, count in counts.items():
        logger.info("Profile %s: %d records (%.1f%%)", profile, count, 100 * count / len(df))

    return profiles


def get_feature_cols_for_profile(
    profile: DataProfile,
    all_feature_cols: list[str],
    lab_cols: list[str] | None = None,
    med_cols: list[str] | None = None,
) -> list[str]:
    """Get the feature columns appropriate for a given data profile.

    Args:
        profile: The data availability profile.
        all_feature_cols: Complete list of feature column names.
        lab_cols: Lab column names to exclude for NO_LABS.
        med_cols: Med column names to exclude for NO_MEDS.

    Returns:
        Filtered list of feature column names.
    """
    lab_cols_set = set(lab_cols or DEFAULT_LAB_COLS)
    med_cols_set = set(med_cols or DEFAULT_MED_COLS)

    if profile == DataProfile.FULL:
        return list(all_feature_cols)
    elif profile == DataProfile.NO_LABS:
        return [c for c in all_feature_cols if c not in lab_cols_set]
    elif profile == DataProfile.NO_MEDS:
        return [c for c in all_feature_cols if c not in med_cols_set]
    elif profile == DataProfile.MINIMAL:
        return [c for c in all_feature_cols if c not in lab_cols_set and c not in med_cols_set]
    else:
        return []
