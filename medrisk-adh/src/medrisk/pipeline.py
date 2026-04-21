"""End-to-end v2 pipeline orchestrator.

Connects all MedRisk-ADH v2 components into a single pipeline:
1. Generate/load cohort
2. Compute data profiles
3. Compute DQS v2
4. Route to profile-matched models
5. Run reliability head
6. Log all decisions

Usage:
    pipeline = MedRiskPipeline()
    result = pipeline.run()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

from medrisk.data.schemas import MARKET_CONFIGS
from medrisk.data.synthetic import cohort_to_dataframe, generate_cohort
from medrisk.features.data_profile import DataProfile, classify_cohort_profiles
from medrisk.features.engineering import build_feature_matrix, get_targets
from medrisk.governance.audit_log import AuditEntry, AuditLogger
from medrisk.models.model_router import ModelRouter
from medrisk.validation.data_quality import DQSv2Result, compute_dqs_v2
from medrisk.validation.reliability_head import (
    ReliabilityConfig,
    ReliabilityDecision,
    ReliabilityHead,
)

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of a full pipeline run.

    Attributes:
        n_patients: Total patients processed.
        n_per_market: Dict of market -> count.
        profile_distribution: Dict of DataProfile -> count.
        predictions: Array of predicted probabilities.
        decisions: List of ReliabilityDecision.
        decision_summary: Dict of decision -> count.
        dqs_results: List of DQSv2Result.
        model_ids: List of model IDs used per patient.
        audit_path: Path to audit log file.
        reliability_coefficients: Dict of feature -> coefficient.
    """

    n_patients: int = 0
    n_per_market: dict[str, int] = field(default_factory=dict)
    profile_distribution: dict[str, int] = field(default_factory=dict)
    predictions: np.ndarray = field(default_factory=lambda: np.array([]))
    decisions: list[ReliabilityDecision] = field(default_factory=list)
    decision_summary: dict[str, int] = field(default_factory=dict)
    dqs_results: list[DQSv2Result] = field(default_factory=list)
    model_ids: list[str] = field(default_factory=list)
    audit_path: str = ""
    reliability_coefficients: dict[str, float] = field(default_factory=dict)


class MedRiskPipeline:
    """End-to-end v2 pipeline.

    Orchestrates: cohort -> profiles -> DQS v2 -> model router ->
    reliability head -> audit log.

    Args:
        config_path: Path to YAML configuration file.
        audit_dir: Directory for audit log output.
    """

    def __init__(
        self,
        config_path: str | Path | None = None,
        audit_dir: str | Path = "data/audit",
    ) -> None:
        self.config: dict = {}
        if config_path and Path(config_path).exists():
            with Path(config_path).open() as f:
                self.config = yaml.safe_load(f)

        self.audit_dir = Path(audit_dir)
        self.router: ModelRouter | None = None
        self.reliability_head: ReliabilityHead | None = None

    def run(
        self,
        cohort=None,
        n_per_market: int = 1000,
        markets: list[str] | None = None,
        seed: int = 42,
    ) -> PipelineResult:
        """Execute the full v2 pipeline.

        Args:
            cohort: Pre-generated cohort. If None, generates synthetic.
            n_per_market: Patients per market (if generating).
            markets: Market codes (if generating).
            seed: Random seed.

        Returns:
            PipelineResult with all outputs.
        """
        # Step 1: Generate or use provided cohort
        if cohort is None:
            logger.info("Step 1: Generating synthetic cohort (%d/market)", n_per_market)
            cohort = generate_cohort(
                n_per_market=n_per_market,
                markets=markets,
                seed=seed,
            )
        else:
            logger.info("Step 1: Using provided cohort (%d patients)", len(cohort))

        # Step 2: Convert to DataFrame
        logger.info("Step 2: Converting to DataFrame")
        df = cohort_to_dataframe(cohort)

        # Step 3: Build feature matrix (no imputation for router)
        logger.info("Step 3: Building feature matrix (no imputation)")
        X, feature_names = build_feature_matrix(df, impute_strategy="none")
        events, times = get_targets(df)

        # Merge into router-ready DataFrame
        router_df = X.copy()
        router_df["event_occurred"] = events
        router_df["patient_id"] = df["patient_id"].values
        router_df["market"] = df["market"].values

        # Step 4: Classify data profiles
        logger.info("Step 4: Classifying data profiles")
        profiles = classify_cohort_profiles(router_df)

        # Step 5: Compute DQS v2
        logger.info("Step 5: Computing DQS v2")
        dqs_results = []
        for p in cohort:
            mc = MARKET_CONFIGS.get(p.market.value)
            dqs_results.append(compute_dqs_v2(p, market_config=mc))

        # Step 6: Train model router
        logger.info("Step 6: Training model router")
        self.router = ModelRouter()
        self.router.train(router_df, feature_names, profiles=profiles)

        # Step 7: Get predictions
        logger.info("Step 7: Getting predictions")
        router_result = self.router.predict(router_df, profiles=profiles)

        # Step 8: Train and run reliability head
        logger.info("Step 8: Training reliability head")
        rel_config = ReliabilityConfig(
            cost_fp=self.config.get("reliability_head", {}).get("cost_fp", 1.0),
            cost_fn=self.config.get("reliability_head", {}).get("cost_fn", 5.0),
            cost_review=self.config.get("reliability_head", {}).get("cost_review", 0.5),
        )
        self.reliability_head = ReliabilityHead(config=rel_config)
        self.reliability_head.fit(
            predicted_scores=router_result.probabilities,
            true_labels=events,
            dqs_results=dqs_results,
            data_profiles=list(profiles),
        )

        logger.info("Step 8b: Running reliability head")
        decisions = self.reliability_head.predict(
            predicted_scores=router_result.probabilities,
            dqs_results=dqs_results,
            data_profiles=list(profiles),
            patient_ids=router_result.patient_ids,
        )

        # Step 9: Audit logging
        logger.info("Step 9: Writing audit log")
        audit_path = self.audit_dir / "pipeline_audit.jsonl"
        audit_logger = AuditLogger(audit_path)

        entries = []
        for i, (decision, dqs) in enumerate(zip(decisions, dqs_results, strict=True)):
            entries.append(
                AuditEntry(
                    patient_id=decision.patient_id,
                    data_profile=str(router_result.profiles[i]),
                    model_id=router_result.model_ids[i],
                    features_used=self.router.feature_sets.get(
                        DataProfile(router_result.profiles[i]),
                        [],
                    ),
                    dqs_score=dqs.dqs,
                    dqs_tier=dqs.tier,
                    dqs_components={
                        "completeness": dqs.completeness,
                        "consistency": dqs.consistency,
                        "recency": dqs.recency,
                        "range_score": dqs.range_score,
                    },
                    predicted_probability=float(router_result.probabilities[i]),
                    reliability_decision=decision.decision,
                    p_wrong=decision.p_wrong,
                    explanation=decision.explanation,
                )
            )
        audit_logger.log_batch(entries)

        # Compile results
        from collections import Counter

        market_counts = Counter(p.market.value for p in cohort)
        profile_counts = Counter(str(p) for p in profiles)
        decision_counts = Counter(d.decision for d in decisions)

        logger.info(
            "Pipeline complete: %d patients, decisions=%s", len(cohort), dict(decision_counts)
        )

        return PipelineResult(
            n_patients=len(cohort),
            n_per_market=dict(market_counts),
            profile_distribution=dict(profile_counts),
            predictions=router_result.probabilities,
            decisions=decisions,
            decision_summary=dict(decision_counts),
            dqs_results=dqs_results,
            model_ids=router_result.model_ids,
            audit_path=str(audit_path),
            reliability_coefficients=self.reliability_head.coefficients,
        )
