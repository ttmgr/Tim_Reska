"""Tests for human override support."""

from medrisk.governance.audit_log import AuditEntry, AuditLogger
from medrisk.governance.human_override import HumanOverride, apply_override


class TestApplyOverride:
    def test_override_logged(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)

        original = AuditEntry(
            patient_id="P001",
            reliability_decision="reject",
            p_wrong=0.85,
        )

        override = HumanOverride(
            override_decision="accept",
            override_reason="Clinical review confirms low risk",
            overrider_id="UW_42",
        )

        result = apply_override(original, override, logger)
        assert result.reliability_decision == "accept"
        assert result.human_override is not None
        assert result.human_override["original_decision"] == "reject"
        assert result.human_override["reason"] == "Clinical review confirms low risk"
        assert logger.count() == 1

    def test_override_preserves_patient_id(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)

        original = AuditEntry(patient_id="P999", reliability_decision="human_review")
        override = HumanOverride(override_decision="accept", override_reason="OK")

        result = apply_override(original, override, logger)
        assert result.patient_id == "P999"
        assert override.patient_id == "P999"

    def test_override_gets_id_and_timestamp(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)

        original = AuditEntry(patient_id="P001", reliability_decision="reject")
        override = HumanOverride(override_decision="accept", override_reason="OK")

        apply_override(original, override, logger)
        assert override.override_id != ""
        assert override.timestamp != ""
