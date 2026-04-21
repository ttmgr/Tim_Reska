"""Tests for medrisk.underwriting.clinical_checks."""

import pytest

from medrisk.underwriting.clinical_checks import (
    ClinicalValidationResult,
    check_coding_specificity,
    check_comorbidity_interactions,
    check_drug_diagnosis_consistency,
    check_occupation_diagnosis_interaction,
    run_clinical_checks,
)
from medrisk.underwriting.profiles import load_comorbidity_interactions


@pytest.fixture(scope="module")
def interactions():
    return load_comorbidity_interactions()


class TestDrugDiagnosisConsistency:
    def test_drug_without_diagnosis(self):
        # Sertraline (N06AB02) present but no F32/F33/F41 diagnosis → warning
        diagnoses = [{"icd10_code": "E11.9", "date_recorded": "2022-01-01"}]
        medications = [{"atc_code": "N06AB02", "active": True}]
        findings = check_drug_diagnosis_consistency(diagnoses, medications)
        assert len(findings) == 1
        assert findings[0].severity == "warning"
        assert findings[0].check_id == "drug_diag_N06AB02"

    def test_drug_with_matching_diagnosis(self):
        # Metformin (A10BA02) with E11 diagnosis → no findings
        diagnoses = [{"icd10_code": "E11.9", "date_recorded": "2022-01-01"}]
        medications = [{"atc_code": "A10BA02", "active": True}]
        findings = check_drug_diagnosis_consistency(diagnoses, medications)
        assert findings == []


class TestOccupationDiagnosisInteraction:
    def test_occupation_diagnosis_critical(self):
        # M51.1 + occupation_class=4 → critical finding
        diagnoses = [{"icd10_code": "M51.1", "date_recorded": "2022-01-01"}]
        findings = check_occupation_diagnosis_interaction(4, diagnoses)
        assert len(findings) >= 1
        assert any(f.severity == "critical" for f in findings)

    def test_occupation_diagnosis_safe(self):
        # M51.1 + occupation_class=1 → no finding
        diagnoses = [{"icd10_code": "M51.1", "date_recorded": "2022-01-01"}]
        findings = check_occupation_diagnosis_interaction(1, diagnoses)
        assert findings == []


class TestCodingSpecificity:
    def test_coding_specificity_unspecified(self):
        # I48.9 is flagged as too unspecific
        diagnoses = [{"icd10_code": "I48.9", "date_recorded": "2022-01-01"}]
        findings = check_coding_specificity(diagnoses)
        assert len(findings) == 1
        assert findings[0].severity == "warning"
        assert findings[0].failure_mode == "coding_ambiguity"

    def test_coding_specificity_specific(self):
        # I48.0 is specific and must NOT trigger
        diagnoses = [{"icd10_code": "I48.0", "date_recorded": "2022-01-01"}]
        findings = check_coding_specificity(diagnoses)
        assert findings == []


class TestComorbidityInteractionDetected:
    def test_comorbidity_interaction_detected(self, interactions):
        # F33 + M79.7 matches the depression/fibromyalgia interaction
        diagnoses = [
            {"icd10_code": "F33.1", "date_recorded": "2022-01-01"},
            {"icd10_code": "M79.7", "date_recorded": "2022-01-01"},
        ]
        findings = check_comorbidity_interactions(diagnoses, interactions)
        assert len(findings) >= 1
        involved_codes = set()
        for f in findings:
            involved_codes.update(f.icd_codes_involved)
        assert "F33.1" in involved_codes or "M79.7" in involved_codes


class TestRunClinicalChecksOrchestrator:
    def test_run_clinical_checks_orchestrator(self):
        result = run_clinical_checks(
            patient_id="p001",
            diagnoses=[{"icd10_code": "I10", "date_recorded": "2022-01-01"}],
            medications=[],
            labs=[],
            occupation_class=1,
        )
        assert isinstance(result, ClinicalValidationResult)
        assert result.patient_id == "p001"
        assert result.checks_run == 6
