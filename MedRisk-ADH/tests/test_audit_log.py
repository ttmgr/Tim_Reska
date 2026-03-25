"""Tests for audit logging."""

import json

from medrisk.governance.audit_log import AuditEntry, AuditLogger


class TestAuditLogger:
    def test_log_single_decision(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)
        entry = AuditEntry(patient_id="P001", reliability_decision="accept", p_wrong=0.05)
        logger.log_decision(entry)
        assert log_path.exists()
        assert logger.count() == 1

    def test_log_batch(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)
        entries = [
            AuditEntry(patient_id=f"P{i:03d}", reliability_decision="accept")
            for i in range(10)
        ]
        logger.log_batch(entries)
        assert logger.count() == 10

    def test_entries_are_valid_json(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)
        logger.log_decision(AuditEntry(patient_id="P001"))
        with log_path.open() as f:
            line = f.readline()
            record = json.loads(line)
            assert record["patient_id"] == "P001"
            assert "timestamp" in record

    def test_query_by_patient_id(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)
        logger.log_decision(AuditEntry(patient_id="P001", reliability_decision="accept"))
        logger.log_decision(AuditEntry(patient_id="P002", reliability_decision="reject"))
        logger.log_decision(AuditEntry(patient_id="P001", reliability_decision="human_review"))
        results = logger.query(patient_id="P001")
        assert len(results) == 2

    def test_query_by_decision(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)
        logger.log_decision(AuditEntry(patient_id="P001", reliability_decision="accept"))
        logger.log_decision(AuditEntry(patient_id="P002", reliability_decision="reject"))
        results = logger.query(decision="reject")
        assert len(results) == 1
        assert results[0].patient_id == "P002"

    def test_query_empty_log(self, tmp_path):
        log_path = tmp_path / "nonexistent.jsonl"
        logger = AuditLogger(log_path)
        results = logger.query()
        assert results == []

    def test_creates_parent_dirs(self, tmp_path):
        log_path = tmp_path / "sub" / "dir" / "audit.jsonl"
        logger = AuditLogger(log_path)
        logger.log_decision(AuditEntry(patient_id="P001"))
        assert log_path.exists()

    def test_batch_shares_run_id(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        logger = AuditLogger(log_path)
        entries = [AuditEntry(patient_id=f"P{i}") for i in range(3)]
        logger.log_batch(entries)
        results = logger.query()
        run_ids = {r.run_id for r in results}
        assert len(run_ids) == 1  # all share same run_id
