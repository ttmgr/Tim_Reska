"""Tests for plausible-but-wrong failure mode detection."""

import numpy as np

from medrisk.validation.confidence import compute_ccm, compute_epu, probability_to_risk_decile
from medrisk.validation.failure_detection import batch_detect, detect_failure_modes


class TestCCM:
    def test_identical_probas_zero_ccm(self) -> None:
        raw = np.array([0.5, 0.8, 0.2])
        cal = np.array([0.5, 0.8, 0.2])
        ccm = compute_ccm(raw, cal)
        np.testing.assert_allclose(ccm, 0.0)

    def test_divergent_probas(self) -> None:
        raw = np.array([0.9, 0.1])
        cal = np.array([0.5, 0.5])
        ccm = compute_ccm(raw, cal)
        assert ccm[0] == 0.4
        assert ccm[1] == 0.4


class TestRiskDeciles:
    def test_deciles_range(self) -> None:
        proba = np.linspace(0, 1, 100)
        deciles = probability_to_risk_decile(proba)
        assert deciles.min() >= 1
        assert deciles.max() <= 10

    def test_constant_predictions(self) -> None:
        proba = np.full(50, 0.5)
        deciles = probability_to_risk_decile(proba)
        assert np.all(deciles == 5)


class TestEPU:
    def test_agreeing_models_zero_epu(self) -> None:
        d1 = np.array([5, 5, 5])
        d2 = np.array([5, 5, 5])
        epu = compute_epu([d1, d2])
        np.testing.assert_array_equal(epu, [0, 0, 0])

    def test_disagreeing_models(self) -> None:
        d1 = np.array([2, 8, 5])
        d2 = np.array([8, 2, 5])
        d3 = np.array([5, 5, 5])
        epu = compute_epu([d1, d2, d3])
        assert epu[0] == 6  # 8 - 2
        assert epu[1] == 6  # 8 - 2
        assert epu[2] == 0  # all 5


class TestDetectFailureModes:
    def test_clean_case_no_flags(self) -> None:
        result = detect_failure_modes(
            patient_id="clean-001",
            dqs=0.90,
            dqs_tier="adequate",
            raw_proba=0.85,
            calibrated_proba=0.82,
            model_risk_deciles=[8, 9, 8],
        )
        assert result.recommendation == "accept"
        assert not result.pbw_flag
        assert result.flags_triggered == []

    def test_pbw_fires_on_adversarial(self) -> None:
        """High confidence + low DQS = PBW flag."""
        result = detect_failure_modes(
            patient_id="adversarial-001",
            dqs=0.30,
            dqs_tier="insufficient",
            raw_proba=0.95,
        )
        assert result.pbw_flag
        assert "pbw" in result.flags_triggered
        assert result.recommendation == "reject_prediction"

    def test_pbw_does_not_fire_on_supported(self) -> None:
        """High confidence + high DQS = no PBW."""
        result = detect_failure_modes(
            patient_id="supported-001",
            dqs=0.90,
            dqs_tier="adequate",
            raw_proba=0.95,
        )
        assert not result.pbw_flag

    def test_ccm_flag(self) -> None:
        result = detect_failure_modes(
            patient_id="ccm-001",
            dqs=0.85,
            dqs_tier="adequate",
            raw_proba=0.90,
            calibrated_proba=0.50,
        )
        assert "ccm_high" in result.flags_triggered
        assert result.recommendation == "review"

    def test_epu_flag(self) -> None:
        result = detect_failure_modes(
            patient_id="epu-001",
            dqs=0.85,
            dqs_tier="adequate",
            raw_proba=0.60,
            model_risk_deciles=[2, 8, 5],
        )
        assert "epu_high" in result.flags_triggered
        assert result.recommendation == "review"

    def test_low_confidence_no_pbw(self) -> None:
        """Low confidence + low DQS = no PBW (model is appropriately uncertain)."""
        result = detect_failure_modes(
            patient_id="uncertain-001",
            dqs=0.30,
            dqs_tier="insufficient",
            raw_proba=0.55,
        )
        assert not result.pbw_flag

    def test_pbw_on_low_proba_high_confidence(self) -> None:
        """P=0.05 is also high confidence (95% sure it's low risk)."""
        result = detect_failure_modes(
            patient_id="low-proba-001",
            dqs=0.30,
            dqs_tier="insufficient",
            raw_proba=0.05,
        )
        assert result.pbw_flag


class TestBatchDetect:
    def test_batch_returns_correct_count(self) -> None:
        results = batch_detect(
            patient_ids=["p1", "p2", "p3"],
            dqs_scores=np.array([0.90, 0.30, 0.70]),
            dqs_tiers=["adequate", "insufficient", "caution"],
            raw_probas=np.array([0.60, 0.95, 0.55]),
        )
        assert len(results) == 3

    def test_batch_catches_pbw(self) -> None:
        results = batch_detect(
            patient_ids=["p1", "p2"],
            dqs_scores=np.array([0.90, 0.20]),
            dqs_tiers=["adequate", "insufficient"],
            raw_probas=np.array([0.60, 0.95]),
        )
        assert not results[0].pbw_flag
        assert results[1].pbw_flag
