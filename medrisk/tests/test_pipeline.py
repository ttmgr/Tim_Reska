"""Tests for end-to-end v2 pipeline."""

from pathlib import Path

from medrisk.pipeline import MedRiskPipeline, PipelineResult


class TestMedRiskPipeline:
    def test_pipeline_runs(self, tmp_path):
        pipeline = MedRiskPipeline(audit_dir=tmp_path / "audit")
        result = pipeline.run(n_per_market=50)
        assert isinstance(result, PipelineResult)
        assert result.n_patients == 200  # 4 markets x 50

    def test_result_fields_populated(self, tmp_path):
        pipeline = MedRiskPipeline(audit_dir=tmp_path / "audit")
        result = pipeline.run(n_per_market=50)
        assert len(result.predictions) == 200
        assert len(result.decisions) == 200
        assert len(result.dqs_results) == 200
        assert sum(result.decision_summary.values()) == 200

    def test_audit_log_created(self, tmp_path):
        audit_dir = tmp_path / "audit"
        pipeline = MedRiskPipeline(audit_dir=audit_dir)
        result = pipeline.run(n_per_market=50)
        audit_path = Path(result.audit_path)
        assert audit_path.exists()
        with audit_path.open() as f:
            lines = f.readlines()
        assert len(lines) == 200

    def test_reliability_coefficients(self, tmp_path):
        pipeline = MedRiskPipeline(audit_dir=tmp_path / "audit")
        result = pipeline.run(n_per_market=100)
        assert len(result.reliability_coefficients) > 0

    def test_all_decisions_valid(self, tmp_path):
        pipeline = MedRiskPipeline(audit_dir=tmp_path / "audit")
        result = pipeline.run(n_per_market=50)
        for d in result.decisions:
            assert d.decision in ("accept", "reject", "human_review")
