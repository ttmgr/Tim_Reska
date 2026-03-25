"""Plausible-but-wrong failure mode detection.

The core intellectual contribution of MedRisk-ADH. Detects when an
underwriting model produces a confident prediction on insufficient data —
the most dangerous failure mode in automated underwriting.

Three detection signals:
1. CCM — calibration-confidence mismatch
2. EPU — epistemic prediction uncertainty (model disagreement)
3. PBW — DQS-conditioned confidence (the hard flag)

When PBW fires, the model literally cannot have enough information to
justify its confidence. The confidence must come from the training
distribution's prior, not the patient's data.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of failure mode detection for a single patient.

    Attributes:
        patient_id: Patient identifier.
        dqs: Composite data quality score.
        dqs_tier: Quality tier ("adequate", "caution", "insufficient").
        raw_confidence: Model's raw predicted probability.
        calibrated_confidence: Calibrated probability (if available).
        ccm: Calibration-confidence mismatch.
        epu: Epistemic prediction uncertainty (decile disagreement).
        pbw_flag: Whether the plausible-but-wrong flag is triggered.
        flags_triggered: List of triggered flag names.
        recommendation: Underwriting recommendation.
        explanation: Human-readable explanation.
    """

    patient_id: str
    dqs: float
    dqs_tier: str
    raw_confidence: float
    calibrated_confidence: float | None
    ccm: float
    epu: int
    pbw_flag: bool
    flags_triggered: list[str] = field(default_factory=list)
    recommendation: str = "accept"
    explanation: str = ""


def detect_failure_modes(
    patient_id: str,
    dqs: float,
    dqs_tier: str,
    raw_proba: float,
    calibrated_proba: float | None = None,
    model_risk_deciles: list[int] | None = None,
    ccm_threshold: float = 0.20,
    epu_threshold: int = 3,
    confidence_threshold: float = 0.80,
    dqs_threshold: float = 0.60,
) -> ValidationResult:
    """Run all three failure mode detectors on a single patient.

    Args:
        patient_id: Patient identifier.
        dqs: Data quality score.
        dqs_tier: DQS tier classification.
        raw_proba: Raw model probability of high risk.
        calibrated_proba: Calibrated probability (None if not available).
        model_risk_deciles: List of risk deciles from different models.
        ccm_threshold: Threshold for CCM flag (default 0.20).
        epu_threshold: Threshold for EPU flag (default 3 deciles).
        confidence_threshold: Confidence level above which PBW applies.
        dqs_threshold: DQS level below which PBW applies.

    Returns:
        ValidationResult with all flags and recommendation.
    """
    flags: list[str] = []

    # --- Signal 1: Calibration-Confidence Mismatch ---
    ccm = 0.0
    if calibrated_proba is not None:
        ccm = abs(raw_proba - calibrated_proba)
        if ccm > ccm_threshold:
            flags.append("ccm_high")

    # --- Signal 2: Epistemic Prediction Uncertainty ---
    epu = 0
    if model_risk_deciles is not None and len(model_risk_deciles) >= 2:
        epu = max(model_risk_deciles) - min(model_risk_deciles)
        if epu > epu_threshold:
            flags.append("epu_high")

    # --- Signal 3: DQS-Conditioned Confidence (PBW) ---
    effective_confidence = max(raw_proba, 1.0 - raw_proba)
    pbw_flag = (effective_confidence > confidence_threshold) and (dqs < dqs_threshold)
    if pbw_flag:
        flags.append("pbw")

    # --- Decision logic ---
    if not flags:
        recommendation = "accept"
        explanation = "All validation checks passed. Prediction is supported by data quality."
    elif "pbw" in flags:
        recommendation = "reject_prediction"
        explanation = (
            f"PLAUSIBLE-BUT-WRONG: Model confidence ({effective_confidence:.0%}) "
            f"is not supported by data quality (DQS={dqs:.2f}, tier={dqs_tier}). "
            f"The model cannot have enough information to justify this prediction. "
            f"Escalate to human underwriter."
        )
    else:
        recommendation = "review"
        parts = []
        if "ccm_high" in flags:
            parts.append(
                f"Calibration mismatch ({ccm:.2f}): raw and calibrated probabilities diverge"
            )
        if "epu_high" in flags:
            parts.append(
                f"Model disagreement (EPU={epu}): risk models produce inconsistent assessments"
            )
        explanation = "REVIEW NEEDED: " + "; ".join(parts) + "."

    return ValidationResult(
        patient_id=patient_id,
        dqs=dqs,
        dqs_tier=dqs_tier,
        raw_confidence=raw_proba,
        calibrated_confidence=calibrated_proba,
        ccm=round(ccm, 4),
        epu=epu,
        pbw_flag=pbw_flag,
        flags_triggered=flags,
        recommendation=recommendation,
        explanation=explanation,
    )


def batch_detect(
    patient_ids: list[str],
    dqs_scores: np.ndarray,
    dqs_tiers: list[str],
    raw_probas: np.ndarray,
    calibrated_probas: np.ndarray | None = None,
    model_risk_decile_arrays: list[np.ndarray] | None = None,
    **kwargs,
) -> list[ValidationResult]:
    """Run failure mode detection on an entire cohort.

    Args:
        patient_ids: List of patient identifiers.
        dqs_scores: Array of DQS values.
        dqs_tiers: List of DQS tier strings.
        raw_probas: Array of raw model probabilities.
        calibrated_probas: Array of calibrated probabilities (optional).
        model_risk_decile_arrays: List of decile arrays per model (optional).
        **kwargs: Additional threshold arguments passed to detect_failure_modes.

    Returns:
        List of ValidationResult objects.
    """
    n = len(patient_ids)
    results: list[ValidationResult] = []

    for i in range(n):
        cal_p = float(calibrated_probas[i]) if calibrated_probas is not None else None
        deciles = (
            [int(arr[i]) for arr in model_risk_decile_arrays]
            if model_risk_decile_arrays is not None
            else None
        )

        result = detect_failure_modes(
            patient_id=patient_ids[i],
            dqs=float(dqs_scores[i]),
            dqs_tier=dqs_tiers[i],
            raw_proba=float(raw_probas[i]),
            calibrated_proba=cal_p,
            model_risk_deciles=deciles,
            **kwargs,
        )
        results.append(result)

    n_flagged = sum(1 for r in results if r.flags_triggered)
    n_pbw = sum(1 for r in results if r.pbw_flag)
    logger.info(
        "Batch validation: %d patients, %d flagged, %d PBW",
        n,
        n_flagged,
        n_pbw,
    )
    return results
