"""Feature matrix construction from patient cohort DataFrames.

Assembles the full feature matrix used by the risk models, combining
demographics, ICD-10 encodings, lab values, and medication flags.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Columns expected in the cohort DataFrame (from synthetic.cohort_to_dataframe)
DEMOGRAPHIC_FEATURES = ["age", "bmi"]
DEMOGRAPHIC_CATEGORICAL = ["sex", "smoking_status"]
TARGET_COL = "event_occurred"
TIME_COL = "time_to_event"


def build_feature_matrix(
    df: pd.DataFrame,
    include_labs: bool = True,
    include_medications: bool = True,
    impute_strategy: str = "median",
) -> tuple[pd.DataFrame, list[str]]:
    """Build a model-ready feature matrix from a cohort DataFrame.

    Args:
        df: Cohort DataFrame from cohort_to_dataframe().
        include_labs: Whether to include lab value columns.
        include_medications: Whether to include medication flag columns.
        impute_strategy: How to handle missing lab values ("median" or "zero").

    Returns:
        Tuple of (feature DataFrame, list of feature column names).
    """
    feature_cols: list[str] = []

    # Demographics (numeric)
    feature_cols.extend(DEMOGRAPHIC_FEATURES)

    # Demographics (one-hot encoded)
    if "sex" in df.columns:
        df = df.copy()
        df["sex_male"] = (df["sex"] == "M").astype(int)
        feature_cols.append("sex_male")

    if "smoking_status" in df.columns:
        for status in ["former", "current"]:
            col = f"smoking_{status}"
            df[col] = (df["smoking_status"] == status).astype(int)
            feature_cols.append(col)

    # Charlson index
    if "charlson_index" in df.columns:
        feature_cols.append("charlson_index")

    # Diagnosis flags (has_*)
    diag_cols = [c for c in df.columns if c.startswith("has_")]
    for col in diag_cols:
        df[col] = df[col].astype(int)
    feature_cols.extend(sorted(diag_cols))

    # Lab values
    if include_labs:
        lab_cols = [c for c in df.columns if c.startswith("lab_")]
        if lab_cols:
            if impute_strategy == "median":
                for col in lab_cols:
                    median_val = df[col].median()
                    df[col] = df[col].fillna(median_val if pd.notna(median_val) else 0.0)
            elif impute_strategy == "zero":
                for col in lab_cols:
                    df[col] = df[col].fillna(0.0)
            elif impute_strategy == "none":
                pass  # Leave NaN in place for model routing

            feature_cols.extend(sorted(lab_cols))

    # Medication flags
    if include_medications:
        med_cols = [c for c in df.columns if c.startswith("med_")]
        for col in med_cols:
            df[col] = df[col].astype(int)
        feature_cols.extend(sorted(med_cols))

    # Deduplicate while preserving order
    seen = set()
    unique_cols = []
    for col in feature_cols:
        if col not in seen and col in df.columns:
            seen.add(col)
            unique_cols.append(col)

    feature_df = df[unique_cols].copy()

    # Final NaN check
    nan_counts = feature_df.isna().sum()
    if nan_counts.any():
        logger.warning(
            "Remaining NaN values after imputation: %s", nan_counts[nan_counts > 0].to_dict()
        )
        feature_df = feature_df.fillna(0.0)

    logger.info("Feature matrix: %d samples x %d features", len(feature_df), len(unique_cols))
    return feature_df, unique_cols


def get_targets(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Extract target arrays for classification and survival.

    Args:
        df: Cohort DataFrame.

    Returns:
        Tuple of (event_occurred array, time_to_event array).
    """
    events = df[TARGET_COL].astype(int).values
    times = df[TIME_COL].values
    return events, times
