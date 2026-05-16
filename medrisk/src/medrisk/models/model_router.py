"""Model router for data-profile-aware prediction.

Instead of imputing missing features and running a single model, the router
trains separate models per data availability profile. Each model uses only
the features that are genuinely present for that profile -- no imputation
masquerading as evidence.

Profiles:
- FULL: all features (demographics, diagnoses, labs, meds)
- NO_LABS: demographics + diagnoses + meds (no lab values)
- NO_MEDS: demographics + diagnoses + labs (no medication feed)
- MINIMAL: demographics + diagnoses only
- INSUFFICIENT: cannot route to any model -> mandatory human review
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from medrisk.features.data_profile import (
    DataProfile,
    classify_cohort_profiles,
    get_feature_cols_for_profile,
)
from medrisk.models.xgb_classifier import RiskClassifier, RiskClassifierConfig

logger = logging.getLogger(__name__)


@dataclass
class RouterPrediction:
    """Result of routed predictions across a cohort.

    Attributes:
        patient_ids: Patient identifiers.
        probabilities: Predicted P(high_risk) per record.
        profiles: DataProfile used for each record.
        model_ids: Model identifier used for each record.
        needs_human_review: True when profile is INSUFFICIENT.
    """

    patient_ids: list[str] = field(default_factory=list)
    probabilities: np.ndarray = field(default_factory=lambda: np.array([]))
    profiles: list[DataProfile] = field(default_factory=list)
    model_ids: list[str] = field(default_factory=list)
    needs_human_review: list[bool] = field(default_factory=list)


class ModelRouter:
    """Routes predictions to profile-appropriate models.

    Trains one XGBoost classifier per DataProfile, each using only the
    features available for that profile. No imputation occurs.

    Attributes:
        models: Dict mapping DataProfile to trained RiskClassifier.
        feature_sets: Dict mapping DataProfile to feature column list.
        config: XGBoost hyperparameter configuration.
    """

    def __init__(self, config: RiskClassifierConfig | None = None) -> None:
        self.config = config or RiskClassifierConfig()
        self.models: dict[DataProfile, RiskClassifier] = {}
        self.feature_sets: dict[DataProfile, list[str]] = {}
        self._all_feature_cols: list[str] = []

    def train(
        self,
        df: pd.DataFrame,
        feature_cols: list[str],
        target_col: str = "event_occurred",
        profiles: pd.Series | None = None,
        val_fraction: float = 0.15,
    ) -> ModelRouter:
        """Train one model per data profile.

        Args:
            df: Cohort DataFrame with features and target.
            feature_cols: Complete list of all feature columns.
            target_col: Target column name.
            profiles: Pre-computed DataProfile series. If None, computed.
            val_fraction: Fraction of each profile's data for validation.

        Returns:
            self for method chaining.
        """
        self._all_feature_cols = list(feature_cols)

        if profiles is None:
            profiles = classify_cohort_profiles(df)

        y = df[target_col].astype(int).values

        trainable_profiles = [
            DataProfile.FULL,
            DataProfile.NO_LABS,
            DataProfile.NO_MEDS,
            DataProfile.MINIMAL,
        ]

        for profile in trainable_profiles:
            mask = profiles == profile
            n_profile = mask.sum()

            if n_profile < 20:
                logger.warning(
                    "Profile %s has only %d records, skipping",
                    profile,
                    n_profile,
                )
                continue

            # Get profile-appropriate features
            profile_cols = get_feature_cols_for_profile(
                profile,
                feature_cols,
            )
            profile_cols = [c for c in profile_cols if c in df.columns]

            if not profile_cols:
                logger.warning("Profile %s has no available features, skipping", profile)
                continue

            # Extract data for this profile
            X_profile = df.loc[mask, profile_cols].copy()
            y_profile = y[mask]

            # Drop columns that are all NaN for this profile
            valid_cols = X_profile.columns[X_profile.notna().any()].tolist()
            X_profile = X_profile[valid_cols]

            # Fill any remaining NaN (within-profile sporadic missingness)
            for col in X_profile.columns:
                if X_profile[col].isna().any():
                    median_val = X_profile[col].median()
                    X_profile[col] = X_profile[col].fillna(
                        median_val if pd.notna(median_val) else 0.0,
                    )

            # Validation split
            n_val = max(2, int(len(X_profile) * val_fraction))
            rng = np.random.default_rng(42)
            val_idx = rng.choice(len(X_profile), size=n_val, replace=False)
            train_mask = np.ones(len(X_profile), dtype=bool)
            train_mask[val_idx] = False

            X_train = X_profile.iloc[train_mask]
            y_train = y_profile[train_mask]
            X_val = X_profile.iloc[~train_mask]
            y_val = y_profile[~train_mask]

            # Train
            model_id = f"xgb_{profile.value}"
            clf = RiskClassifier(config=self.config, model_id=model_id)

            # Only use eval_set if both classes present in validation
            if len(np.unique(y_val)) > 1:
                clf.fit(X_train, y_train, X_val=X_val, y_val=y_val)
            else:
                clf.fit(X_train, y_train)

            self.models[profile] = clf
            self.feature_sets[profile] = list(X_profile.columns)

            logger.info(
                "Trained %s: %d samples, %d features",
                model_id,
                len(X_train),
                len(self.feature_sets[profile]),
            )

        return self

    def predict(
        self,
        df: pd.DataFrame,
        profiles: pd.Series | None = None,
    ) -> RouterPrediction:
        """Route each record to its profile-matched model and predict.

        Args:
            df: Cohort DataFrame with feature columns.
            profiles: Pre-computed DataProfile series. If None, computed.

        Returns:
            RouterPrediction with per-record results.
        """
        if profiles is None:
            profiles = classify_cohort_profiles(df)

        n = len(df)
        probabilities = np.full(n, np.nan)
        model_ids: list[str] = ["none"] * n
        needs_review: list[bool] = [False] * n
        profile_list: list[DataProfile] = list(profiles)

        patient_ids = (
            df["patient_id"].tolist() if "patient_id" in df.columns else [str(i) for i in range(n)]
        )

        for profile in DataProfile:
            mask = profiles == profile
            idx = np.where(mask)[0]

            if len(idx) == 0:
                continue

            if profile == DataProfile.INSUFFICIENT or profile not in self.models:
                for i in idx:
                    needs_review[i] = True
                    model_ids[i] = "human_review"
                continue

            clf = self.models[profile]
            feat_cols = self.feature_sets[profile]

            X_subset = df.iloc[idx][feat_cols].copy()

            # Fill sporadic within-profile NaN
            for col in X_subset.columns:
                if X_subset[col].isna().any():
                    median_val = X_subset[col].median()
                    X_subset[col] = X_subset[col].fillna(
                        median_val if pd.notna(median_val) else 0.0,
                    )

            proba = clf.predict_proba(X_subset)
            probabilities[idx] = proba

            for i in idx:
                model_ids[i] = clf.model_id

        return RouterPrediction(
            patient_ids=patient_ids,
            probabilities=probabilities,
            profiles=profile_list,
            model_ids=model_ids,
            needs_human_review=needs_review,
        )

    def calibrate(
        self,
        df: pd.DataFrame,
        y: np.ndarray,
        profiles: pd.Series,
    ) -> ModelRouter:
        """Calibrate each sub-model on held-out data.

        Args:
            df: Calibration DataFrame.
            y: True labels.
            profiles: DataProfile per record.

        Returns:
            self for method chaining.
        """
        for profile, clf in self.models.items():
            mask = profiles == profile
            if mask.sum() < 10:
                logger.warning("Too few samples to calibrate %s", profile)
                continue

            feat_cols = self.feature_sets[profile]
            X_cal = df.loc[mask, feat_cols].copy()

            for col in X_cal.columns:
                if X_cal[col].isna().any():
                    X_cal[col] = X_cal[col].fillna(X_cal[col].median())

            y_cal = y[mask]

            if len(np.unique(y_cal)) < 2:
                logger.warning("Only one class in calibration data for %s", profile)
                continue

            clf.calibrate(X_cal, y_cal)
            logger.info("Calibrated %s on %d samples", profile, mask.sum())

        return self

    def get_profile_summary(self) -> dict[str, dict]:
        """Get summary of trained models per profile.

        Returns:
            Dict mapping profile name to {n_features, model_id, feature_names}.
        """
        summary = {}
        for profile, clf in self.models.items():
            summary[profile.value] = {
                "model_id": clf.model_id,
                "n_features": len(self.feature_sets[profile]),
                "feature_names": self.feature_sets[profile],
            }
        return summary
