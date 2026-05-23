"""
disease_progression.features.static - Extract static (baseline) features.

Static features are time-invariant covariates measured once at cohort entry
(index date).  They include demographics, baseline comorbidity burden, and
summary indicators derived from the OMOP person and condition_occurrence
tables.

Typical output columns:
    age_at_index, sex_male, charlson_index, has_hypertension,
    has_diabetes, has_af, has_ckd, has_prior_mi, has_prior_stroke, ...

These features feed directly into classical survival models (Cox PH) or
serve as the static branch of hybrid static+temporal architectures.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import numpy as np
import pandas as pd

from disease_progression.data.omop_etl import OMOPTables

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# ICD-10 prefix sets for Charlson comorbidities (Quan adaptation)
# -------------------------------------------------------------------
CHARLSON_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "mi": {"prefixes": ["I21", "I22", "I25.2"], "weight": 1},
    "chf": {"prefixes": ["I50", "I11.0", "I13.0", "I13.2"], "weight": 1},
    "pvd": {"prefixes": ["I70", "I71", "I73", "I77.1", "K55.1", "K55.8", "K55.9"], "weight": 1},
    "cvd": {"prefixes": ["I60", "I61", "I62", "I63", "I64", "I65", "I66", "I67", "I68", "I69", "G45", "G46"], "weight": 1},
    "dementia": {"prefixes": ["F00", "F01", "F02", "F03", "G30"], "weight": 1},
    "copd": {"prefixes": ["J40", "J41", "J42", "J43", "J44", "J45", "J46", "J47"], "weight": 1},
    "rheumatic": {"prefixes": ["M05", "M06", "M31.5", "M32", "M33", "M34", "M35.1", "M35.3", "M36.0"], "weight": 1},
    "peptic_ulcer": {"prefixes": ["K25", "K26", "K27", "K28"], "weight": 1},
    "mild_liver": {"prefixes": ["K70.0", "K70.1", "K70.2", "K70.3", "K70.9", "K71", "K73", "K74", "K76.0"], "weight": 1},
    "diabetes_uncomplicated": {"prefixes": ["E10.0", "E10.1", "E10.9", "E11.0", "E11.1", "E11.9", "E13.0", "E13.1", "E13.9"], "weight": 1},
    "diabetes_complicated": {"prefixes": ["E10.2", "E10.3", "E10.4", "E10.5", "E11.2", "E11.3", "E11.4", "E11.5"], "weight": 2},
    "hemiplegia": {"prefixes": ["G04.1", "G11.4", "G80.1", "G80.2", "G81", "G82", "G83"], "weight": 2},
    "renal": {"prefixes": ["N18.3", "N18.4", "N18.5", "N18.6", "N19", "N25.0", "I12.0", "I13.1"], "weight": 2},
    "malignancy": {"prefixes": ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"], "weight": 2},
    "moderate_severe_liver": {"prefixes": ["K70.4", "K71.1", "K72.1", "K72.9", "K76.5", "K76.6", "K76.7"], "weight": 3},
    "metastatic": {"prefixes": ["C77", "C78", "C79", "C80"], "weight": 6},
    "hiv": {"prefixes": ["B20", "B21", "B22", "B24"], "weight": 6},
}

# Additional clinical flags beyond Charlson
CLINICAL_FLAGS: Dict[str, List[str]] = {
    "has_hypertension": ["I10", "I11", "I12", "I13", "I15"],
    "has_atrial_fibrillation": ["I48"],
    "has_diabetes": ["E10", "E11", "E13", "E14"],
    "has_ckd": ["N18"],
    "has_prior_mi": ["I21", "I22", "I25.2"],
    "has_prior_stroke": ["I60", "I61", "I63", "I64"],
    "has_heart_failure": ["I50"],
    "has_dyslipidemia": ["E78"],
    "has_obesity": ["E66"],
    "has_copd": ["J44"],
}


def _code_matches_any(code: Optional[str], prefixes: List[str]) -> bool:
    """Check whether an ICD-10 code starts with any of the given prefixes."""
    if code is None:
        return False
    code = str(code).strip().upper()
    return any(code.startswith(p.upper()) for p in prefixes)


class StaticFeatureExtractor:
    """Extract static baseline features from OMOP tables.

    Parameters
    ----------
    index_date : datetime or str, optional
        The reference date for computing age and baseline comorbidities.
        Defaults to ``2024-01-01``.
    lookback_days : int
        How far before ``index_date`` to search for baseline conditions.
        Default 3650 (approx. 10 years).
    """

    def __init__(
        self,
        index_date: datetime | str = "2024-01-01",
        lookback_days: int = 3650,
    ) -> None:
        if isinstance(index_date, str):
            index_date = datetime.fromisoformat(index_date)
        self.index_date = index_date
        self.lookback_days = lookback_days

    def transform(self, omop: OMOPTables) -> pd.DataFrame:
        """Build a static feature matrix -- one row per person.

        Returns
        -------
        pd.DataFrame
            Index = ``person_id``. Columns include demographics,
            Charlson comorbidity index, and binary clinical flags.
        """
        person = omop.person.copy()
        conditions = omop.condition_occurrence.copy()

        # --- Demographics ---
        features = self._extract_demographics(person)

        # --- Comorbidities ---
        # The three helpers below each handle an empty condition frame, so a
        # single code path covers both "no conditions table" and "conditions
        # exist but none fall in the baseline window". Branching on
        # ``conditions.empty`` here would duplicate the zero-fill defaults and
        # let the two paths drift apart silently.
        baseline_conds = self._filter_baseline_conditions(conditions)
        person_ids = set(features.index)
        charlson = self._compute_charlson(baseline_conds, person_ids)
        flags = self._compute_clinical_flags(baseline_conds, person_ids)
        comorbidity_count = self._compute_comorbidity_count(baseline_conds)
        features = features.join(charlson, how="left")
        features = features.join(flags, how="left")
        features = features.join(comorbidity_count, how="left")

        # Fill numeric NaNs introduced by the left joins; leave the categorical
        # age_group untouched (filling it with 0 raises on a non-category value).
        fill_cols = [c for c in features.columns if c != "age_group"]
        features[fill_cols] = features[fill_cols].fillna(0)
        logger.info("Static features: %d patients, %d columns", *features.shape)
        return features

    # ------------------------------------------------------------------
    # Demographics
    # ------------------------------------------------------------------

    def _extract_demographics(self, person: pd.DataFrame) -> pd.DataFrame:
        """Compute age, sex indicator, race, ethnicity from OMOP person."""
        rows: List[Dict[str, Any]] = []
        for _, p in person.iterrows():
            yob = p.get("year_of_birth")
            age = (self.index_date.year - int(yob)) if yob is not None else np.nan
            rows.append(
                {
                    "person_id": p["person_id"],
                    "age_at_index": age,
                    "sex_male": 1 if p.get("gender_concept_id") == 8507 else 0,
                    "race_concept_id": p.get("race_concept_id", 0),
                    "ethnicity_concept_id": p.get("ethnicity_concept_id", 0),
                    "is_deceased": 1 if pd.notna(p.get("death_datetime")) else 0,
                }
            )
        df = pd.DataFrame(rows).set_index("person_id")
        # Age bins for stratification
        df["age_group"] = pd.cut(
            df["age_at_index"],
            bins=[0, 40, 50, 60, 70, 80, 120],
            labels=["<40", "40-49", "50-59", "60-69", "70-79", "80+"],
            right=False,
        )
        return df

    # ------------------------------------------------------------------
    # Baseline condition filtering
    # ------------------------------------------------------------------

    def _filter_baseline_conditions(self, conditions: pd.DataFrame) -> pd.DataFrame:
        """Keep conditions that occurred in the lookback window before index_date."""
        df = conditions.copy()
        if "condition_start_date" not in df.columns:
            return df
        df["condition_start_date"] = pd.to_datetime(df["condition_start_date"], errors="coerce")
        cutoff = self.index_date - pd.Timedelta(days=self.lookback_days)
        mask = (
            (df["condition_start_date"] >= cutoff)
            & (df["condition_start_date"] <= self.index_date)
        )
        return df.loc[mask]

    # ------------------------------------------------------------------
    # Charlson comorbidity index
    # ------------------------------------------------------------------

    def _compute_charlson(
        self,
        conditions: pd.DataFrame,
        person_ids: Set[int],
    ) -> pd.DataFrame:
        """Compute Quan-adapted Charlson comorbidity index per person."""
        scores: Dict[int, int] = {pid: 0 for pid in person_ids}

        if conditions.empty:
            return pd.DataFrame({"charlson_index": scores}).rename_axis("person_id")

        for pid, group in conditions.groupby("person_id"):
            codes = group["condition_source_value"].dropna().tolist()
            pid_score = 0
            counted_categories: Set[str] = set()
            for cat_name, cat_info in CHARLSON_CATEGORIES.items():
                for code in codes:
                    if cat_name not in counted_categories and _code_matches_any(code, cat_info["prefixes"]):
                        pid_score += cat_info["weight"]
                        counted_categories.add(cat_name)
                        break
            scores[pid] = pid_score

        return pd.DataFrame.from_dict(scores, orient="index", columns=["charlson_index"]).rename_axis("person_id")

    # ------------------------------------------------------------------
    # Binary clinical flags
    # ------------------------------------------------------------------

    def _compute_clinical_flags(
        self,
        conditions: pd.DataFrame,
        person_ids: Set[int],
    ) -> pd.DataFrame:
        """Compute binary flags for clinically important conditions."""
        flag_data: Dict[str, Dict[int, int]] = {
            flag_name: {pid: 0 for pid in person_ids} for flag_name in CLINICAL_FLAGS
        }

        if conditions.empty:
            return pd.DataFrame(flag_data).rename_axis("person_id")

        for pid, group in conditions.groupby("person_id"):
            codes = group["condition_source_value"].dropna().tolist()
            for flag_name, prefixes in CLINICAL_FLAGS.items():
                for code in codes:
                    if _code_matches_any(code, prefixes):
                        flag_data[flag_name][pid] = 1
                        break

        return pd.DataFrame(flag_data).rename_axis("person_id")

    # ------------------------------------------------------------------
    # Comorbidity count
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_comorbidity_count(conditions: pd.DataFrame) -> pd.DataFrame:
        """Count distinct ICD-10 codes (3-char level) per person."""
        if conditions.empty:
            return pd.DataFrame(columns=["n_distinct_conditions"]).rename_axis("person_id")

        df = conditions.copy()
        df["icd3"] = df["condition_source_value"].str[:3]
        counts = df.groupby("person_id")["icd3"].nunique().rename("n_distinct_conditions")
        return counts.to_frame()
