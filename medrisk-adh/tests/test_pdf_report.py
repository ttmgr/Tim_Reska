"""Tests for PDF report generation."""

import os
from pathlib import Path

from medrisk.reporting.pdf_report import ReportData, generate_report


class TestGenerateReport:
    def test_generates_valid_pdf(self, tmp_path: Path) -> None:
        data = ReportData(
            patient_id="test-001",
            market="DE",
            age=55,
            sex="M",
            bmi=27.5,
            smoking_status="former",
            charlson_index=3,
            n_diagnoses=5,
            n_labs=8,
            risk_probability=0.72,
            risk_class="Substandard",
            concordance_index=0.68,
            median_survival=12.5,
            dqs=0.85,
            dqs_tier="adequate",
            dqs_completeness=0.90,
            dqs_consistency=0.80,
            dqs_recency=0.75,
            validation_recommendation="accept",
            validation_explanation="All checks passed.",
            flags_triggered=[],
            top_features=[("age", 0.15), ("charlson_index", 0.12), ("bmi", 0.08)],
        )

        output = tmp_path / "test_report.pdf"
        result = generate_report(data, output)

        assert result.exists()
        assert result.suffix == ".pdf"
        assert os.path.getsize(result) > 0
        assert os.path.getsize(result) < 2_000_000  # <2MB

    def test_flagged_report(self, tmp_path: Path) -> None:
        data = ReportData(
            patient_id="test-flagged",
            market="INT",
            age=62,
            sex="F",
            bmi=32.0,
            smoking_status="current",
            charlson_index=5,
            n_diagnoses=2,
            n_labs=3,
            risk_probability=0.91,
            risk_class="Decline",
            concordance_index=0.65,
            median_survival=6.2,
            dqs=0.35,
            dqs_tier="insufficient",
            dqs_completeness=0.40,
            dqs_consistency=0.50,
            dqs_recency=0.15,
            validation_recommendation="reject_prediction",
            validation_explanation="PBW: Model confidence not supported by data quality.",
            flags_triggered=["pbw", "ccm_high"],
            top_features=[("age", 0.20)],
        )

        output = tmp_path / "flagged_report.pdf"
        result = generate_report(data, output)
        assert result.exists()
        assert os.path.getsize(result) > 0

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        data = ReportData(patient_id="test-dirs", market="DE")
        output = tmp_path / "nested" / "dir" / "report.pdf"
        result = generate_report(data, output)
        assert result.exists()
