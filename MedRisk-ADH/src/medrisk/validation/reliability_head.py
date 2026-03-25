"""Learned reliability scoring for failure mode detection.

Replaces v1's fixed PBW thresholds (confidence > 0.80 AND DQS < 0.60) with
a learned model that estimates P(wrong | prediction, quality features) and
makes cost-optimal decisions.

The ReliabilityHead is trained on validation data where the target is
whether the main model's prediction disagrees with ground truth. It uses
DQS components, missingness patterns, and the predicted score as features.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from medrisk.features.data_profile import DataProfile
from medrisk.validation.data_quality import DQSv2Result

logger = logging.getLogger(__name__)


@dataclass
class ReliabilityConfig:
    """Cost parameters for decision optimization.

    Attributes:
        cost_fp: Cost of false positive (deny a valid applicant).
        cost_fn: Cost of false negative (accept a truly high-risk applicant).
        cost_review: Cost of escalating to human underwriter.
    """

    cost_fp: float = 1.0
    cost_fn: float = 5.0
    cost_review: float = 0.5


@dataclass
class ReliabilityDecision:
    """Per-record reliability assessment and cost-optimal decision.

    Attributes:
        patient_id: Patient identifier.
        p_wrong: Estimated P(model prediction is wrong).
        expected_cost_accept: Expected cost if we accept the model's output.
        expected_cost_reject: Expected cost if we reject the model's output.
        expected_cost_review: Cost of human review.
        decision: Cost-optimal action: "accept", "reject", or "human_review".
        v1_pbw_flag: What the v1 fixed-threshold PBW would have flagged.
        explanation: Human-readable explanation.
    """

    patient_id: str
    p_wrong: float
    expected_cost_accept: float
    expected_cost_reject: float
    expected_cost_review: float
    decision: str
    v1_pbw_flag: bool
    explanation: str


class ReliabilityHead:
    """Learned failure mode detector with cost-optimal decisions.

    Instead of fixed thresholds, learns P(wrong | features) from validation
    data and chooses the action that minimizes expected cost.

    Uses logistic regression for interpretability -- regulators need to
    understand why a decision was flagged. Coefficients directly show the
    relationship between quality features and error probability.

    Attributes:
        config: Cost parameters.
        model: Trained logistic regression.
        scaler: Feature standardizer.
        feature_names: Names of reliability features.
        is_fitted: Whether fit() has been called.
        coefficients: Dict of feature -> coefficient (after fitting).
    """

    def __init__(self, config: ReliabilityConfig | None = None) -> None:
        self.config = config or ReliabilityConfig()
        self.model: LogisticRegression | None = None
        self.scaler: StandardScaler | None = None
        self.feature_names: list[str] = []
        self.is_fitted: bool = False
        self.coefficients: dict[str, float] = {}

    def _build_features(
        self,
        predicted_scores: np.ndarray,
        dqs_results: list[DQSv2Result],
        data_profiles: list[DataProfile],
    ) -> pd.DataFrame:
        """Build the reliability feature matrix.

        Features:
        - predicted_score: raw model probability
        - effective_confidence: max(p, 1-p) -- how certain the model is
        - completeness, consistency, recency, range_score: DQS components
        - n_structural_missing, n_workflow_missing, n_random_missing
        - profile_* one-hot encoding of data profile
        - conf_x_completeness: interaction (high confidence on low completeness = risky)
        - conf_x_range: interaction
        """
        rows = []
        for score, dqs, profile in zip(
            predicted_scores, dqs_results, data_profiles, strict=False,
        ):
            eff_conf = max(score, 1.0 - score)
            row = {
                "predicted_score": score,
                "effective_confidence": eff_conf,
                "completeness": dqs.completeness,
                "consistency": dqs.consistency,
                "recency": dqs.recency,
                "range_score": dqs.range_score,
                "n_structural_missing": dqs.n_structural_missing,
                "n_workflow_missing": dqs.n_workflow_missing,
                "n_random_missing": dqs.n_random_missing,
                "conf_x_completeness": eff_conf * dqs.completeness,
                "conf_x_range": eff_conf * dqs.range_score,
            }
            # One-hot for data profile
            for p in [
                DataProfile.FULL,
                DataProfile.NO_LABS,
                DataProfile.NO_MEDS,
                DataProfile.MINIMAL,
            ]:
                row[f"profile_{p.value}"] = 1.0 if profile == p else 0.0
            rows.append(row)

        return pd.DataFrame(rows)

    def fit(
        self,
        predicted_scores: np.ndarray,
        true_labels: np.ndarray,
        dqs_results: list[DQSv2Result],
        data_profiles: list[DataProfile],
        predicted_classes: np.ndarray | None = None,
        threshold: float = 0.5,
    ) -> ReliabilityHead:
        """Train the reliability model on validation data.

        Target: whether the main model's prediction disagrees with truth.

        Args:
            predicted_scores: Model's predicted probabilities.
            true_labels: Ground truth labels.
            dqs_results: DQS v2 results per record.
            data_profiles: DataProfile per record.
            predicted_classes: Binary predictions. If None, derived from threshold.
            threshold: Classification threshold for deriving predicted_classes.

        Returns:
            self for method chaining.
        """
        X = self._build_features(predicted_scores, dqs_results, data_profiles)
        self.feature_names = list(X.columns)

        if predicted_classes is None:
            predicted_classes = (predicted_scores >= threshold).astype(int)

        # Target: model was wrong
        y_error = (predicted_classes != true_labels).astype(int)

        logger.info(
            "ReliabilityHead training: %d samples, %d errors (%.1f%%)",
            len(y_error),
            y_error.sum(),
            100 * y_error.mean(),
        )

        # Standardize features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Logistic regression with balanced class weights (errors are rare)
        self.model = LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=42,
            C=1.0,
        )
        self.model.fit(X_scaled, y_error)

        # Store coefficients for interpretability
        self.coefficients = dict(
            zip(self.feature_names, self.model.coef_[0], strict=True),
        )
        self.is_fitted = True

        logger.info(
            "ReliabilityHead fitted. Top risk factors: %s",
            sorted(self.coefficients.items(), key=lambda x: -abs(x[1]))[:5],
        )
        return self

    def predict(
        self,
        predicted_scores: np.ndarray,
        dqs_results: list[DQSv2Result],
        data_profiles: list[DataProfile],
        patient_ids: list[str] | None = None,
    ) -> list[ReliabilityDecision]:
        """Compute P(wrong) and make cost-optimal decisions.

        Decision logic:
        - expected_cost_accept = P(wrong) * cost_fn
        - expected_cost_reject = (1 - P(wrong)) * cost_fp
        - expected_cost_review = cost_review
        - Choose action = argmin(accept, reject, review)

        Args:
            predicted_scores: Model's predicted probabilities.
            dqs_results: DQS v2 results per record.
            data_profiles: DataProfile per record.
            patient_ids: Optional patient identifiers.

        Returns:
            List of ReliabilityDecision, one per record.
        """
        if not self.is_fitted:
            msg = "ReliabilityHead not fitted. Call fit() first."
            raise RuntimeError(msg)

        X = self._build_features(predicted_scores, dqs_results, data_profiles)
        X_scaled = self.scaler.transform(X)

        p_wrong = self.model.predict_proba(X_scaled)[:, 1]

        if patient_ids is None:
            patient_ids = [str(i) for i in range(len(predicted_scores))]

        decisions = []
        for pid, pw, score, dqs in zip(
            patient_ids, p_wrong, predicted_scores, dqs_results, strict=False,
        ):
            cost_accept = pw * self.config.cost_fn
            cost_reject = (1.0 - pw) * self.config.cost_fp
            cost_review = self.config.cost_review

            costs = {"accept": cost_accept, "reject": cost_reject, "human_review": cost_review}
            decision = min(costs, key=costs.get)

            # v1 backward compat: what would fixed thresholds say?
            eff_conf = max(score, 1.0 - score)
            v1_flag = bool(eff_conf > 0.80 and dqs.dqs < 0.60)

            # Human-readable explanation
            if decision == "accept":
                explanation = f"P(wrong)={pw:.3f} is low; expected cost of accepting ({cost_accept:.3f}) < review ({cost_review:.3f})"
            elif decision == "human_review":
                explanation = f"P(wrong)={pw:.3f}; review cost ({cost_review:.3f}) < accept ({cost_accept:.3f}) and reject ({cost_reject:.3f})"
            else:
                explanation = f"P(wrong)={pw:.3f} is high; expected cost of rejecting ({cost_reject:.3f}) < accept ({cost_accept:.3f})"

            decisions.append(
                ReliabilityDecision(
                    patient_id=pid,
                    p_wrong=round(float(pw), 4),
                    expected_cost_accept=round(float(cost_accept), 4),
                    expected_cost_reject=round(float(cost_reject), 4),
                    expected_cost_review=round(float(cost_review), 4),
                    decision=decision,
                    v1_pbw_flag=v1_flag,
                    explanation=explanation,
                )
            )

        return decisions

    def predict_proba_from_quality(
        self,
        completeness: float,
        consistency: float,
        recency: float,
        range_score: float = 1.0,
        n_structural_missing: int = 0,
        n_workflow_missing: int = 0,
        n_random_missing: int = 0,
        predicted_score: float = 0.5,
        data_profile: DataProfile = DataProfile.FULL,
    ) -> float:
        """Estimate P(model_error) from quality features alone.

        Convenience method for DQS v2 integration. Can be called before
        the main model runs by using predicted_score=0.5 (uninformative).

        Returns:
            P(model error) in [0, 1].
        """
        if not self.is_fitted:
            return None

        eff_conf = max(predicted_score, 1.0 - predicted_score)
        row = {
            "predicted_score": predicted_score,
            "effective_confidence": eff_conf,
            "completeness": completeness,
            "consistency": consistency,
            "recency": recency,
            "range_score": range_score,
            "n_structural_missing": n_structural_missing,
            "n_workflow_missing": n_workflow_missing,
            "n_random_missing": n_random_missing,
            "conf_x_completeness": eff_conf * completeness,
            "conf_x_range": eff_conf * range_score,
        }
        for p in [DataProfile.FULL, DataProfile.NO_LABS, DataProfile.NO_MEDS, DataProfile.MINIMAL]:
            row[f"profile_{p.value}"] = 1.0 if data_profile == p else 0.0

        X = pd.DataFrame([row])[self.feature_names]
        X_scaled = self.scaler.transform(X)
        return float(self.model.predict_proba(X_scaled)[0, 1])

    def get_coefficient_table(self) -> pd.DataFrame:
        """Get interpretable coefficient table for regulators.

        Returns:
            DataFrame with feature names, coefficients, and abs values,
            sorted by absolute coefficient descending.
        """
        if not self.coefficients:
            return pd.DataFrame()

        df = pd.DataFrame(
            [
                {"feature": k, "coefficient": v, "abs_coefficient": abs(v)}
                for k, v in self.coefficients.items()
            ]
        ).sort_values("abs_coefficient", ascending=False)

        return df.reset_index(drop=True)
