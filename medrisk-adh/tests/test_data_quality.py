"""Tests for Data Quality Score computation."""

from datetime import date

from medrisk.data.schemas import (
    Diagnosis,
    LabResult,
    Market,
    Medication,
    PatientRecord,
    Sex,
    SmokingStatus,
)
from medrisk.validation.data_quality import (
    compute_completeness,
    compute_consistency,
    compute_dqs,
    compute_recency,
)


def _make_patient(**overrides) -> PatientRecord:
    """Helper to create a minimal patient record with overrides."""
    defaults = {
        "patient_id": "test-001",
        "market": Market.DE,
        "age": 55,
        "sex": Sex.MALE,
        "bmi": 27.0,
        "smoking_status": SmokingStatus.NEVER,
        "diagnoses": [],
        "lab_results": [],
        "medications": [],
        "follow_up_years": 5.0,
        "event_occurred": False,
        "event_type": None,
        "time_to_event": 5.0,
    }
    defaults.update(overrides)
    return PatientRecord(**defaults)


class TestCompleteness:
    def test_minimal_patient(self) -> None:
        """Patient with only demographics should have low completeness."""
        p = _make_patient()
        score = compute_completeness(p)
        assert 0.0 < score < 0.5

    def test_rich_patient(self) -> None:
        """Patient with many observations should have high completeness."""
        p = _make_patient(
            diagnoses=[
                Diagnosis(icd10_code="I10", description="HTN", date_recorded=date(2023, 1, 1)),
                Diagnosis(icd10_code="E11.9", description="T2D", date_recorded=date(2023, 1, 1)),
            ]
            * 5,
            lab_results=[
                LabResult(
                    loinc_code="4548-4",
                    name="HbA1c",
                    value=7.0,
                    unit="%",
                    date_collected=date(2023, 6, 1),
                ),
            ]
            * 10,
            medications=[
                Medication(atc_code="A10BA02", name="Metformin", date_prescribed=date(2023, 1, 1)),
            ]
            * 5,
        )
        score = compute_completeness(p)
        assert score > 0.5

    def test_bounded_zero_one(self) -> None:
        p = _make_patient()
        score = compute_completeness(p)
        assert 0.0 <= score <= 1.0


class TestConsistency:
    def test_empty_patient_full_consistency(self) -> None:
        """No applicable rules = perfect consistency."""
        p = _make_patient()
        score, violations = compute_consistency(p)
        assert score == 1.0
        assert violations == []

    def test_diabetes_hba1c_consistent(self) -> None:
        """Diabetes + high HbA1c = consistent."""
        p = _make_patient(
            diagnoses=[
                Diagnosis(icd10_code="E11.9", description="T2D", date_recorded=date(2023, 1, 1))
            ],
            lab_results=[
                LabResult(
                    loinc_code="4548-4",
                    name="HbA1c",
                    value=8.0,
                    unit="%",
                    date_collected=date(2023, 6, 1),
                )
            ],
        )
        score, violations = compute_consistency(p)
        assert "diabetes_hba1c" not in violations

    def test_no_diabetes_high_hba1c_inconsistent(self) -> None:
        """No diabetes code but HbA1c = 9.0% is inconsistent."""
        p = _make_patient(
            lab_results=[
                LabResult(
                    loinc_code="4548-4",
                    name="HbA1c",
                    value=9.0,
                    unit="%",
                    date_collected=date(2023, 6, 1),
                )
            ],
        )
        score, violations = compute_consistency(p)
        assert "no_diabetes_hba1c" in violations
        assert score < 1.0


class TestRecency:
    def test_no_labs_zero_recency(self) -> None:
        p = _make_patient()
        assert compute_recency(p) == 0.0

    def test_recent_labs_high_recency(self) -> None:
        ref = date(2024, 1, 1)
        p = _make_patient(
            lab_results=[
                LabResult(
                    loinc_code="4548-4",
                    name="HbA1c",
                    value=5.0,
                    unit="%",
                    date_collected=date(2023, 10, 1),
                ),
            ],
        )
        score = compute_recency(p, reference_date=ref)
        assert score > 0.8

    def test_old_labs_low_recency(self) -> None:
        ref = date(2024, 1, 1)
        p = _make_patient(
            lab_results=[
                LabResult(
                    loinc_code="4548-4",
                    name="HbA1c",
                    value=5.0,
                    unit="%",
                    date_collected=date(2019, 1, 1),
                ),
            ],
        )
        score = compute_recency(p, reference_date=ref)
        assert score < 0.3

    def test_bounded_zero_one(self) -> None:
        ref = date(2024, 1, 1)
        p = _make_patient(
            lab_results=[
                LabResult(
                    loinc_code="4548-4",
                    name="HbA1c",
                    value=5.0,
                    unit="%",
                    date_collected=date(2023, 6, 1),
                ),
            ],
        )
        score = compute_recency(p, reference_date=ref)
        assert 0.0 <= score <= 1.0


class TestCompositeDQS:
    def test_complete_consistent_recent_is_adequate(self) -> None:
        """A well-documented patient should score as adequate."""
        ref = date(2024, 1, 1)
        p = _make_patient(
            diagnoses=[
                Diagnosis(icd10_code="I10", description="HTN", date_recorded=date(2023, 1, 1)),
            ]
            * 8,
            lab_results=[
                LabResult(
                    loinc_code="4548-4",
                    name="HbA1c",
                    value=5.5,
                    unit="%",
                    date_collected=date(2023, 11, 1),
                ),
                LabResult(
                    loinc_code="8480-6",
                    name="SBP",
                    value=140.0,
                    unit="mmHg",
                    date_collected=date(2023, 11, 1),
                ),
            ]
            * 5,
            medications=[
                Medication(atc_code="C09AA02", name="Enalapril", date_prescribed=date(2023, 6, 1)),
            ]
            * 5,
        )
        result = compute_dqs(p, reference_date=ref)
        assert result.tier == "adequate"
        assert result.dqs >= 0.80

    def test_empty_patient_is_insufficient(self) -> None:
        """A patient with only demographics should be insufficient."""
        result = compute_dqs(_make_patient())
        assert result.dqs < 0.60 or result.tier in ("caution", "insufficient")

    def test_dqs_bounded(self) -> None:
        result = compute_dqs(_make_patient())
        assert 0.0 <= result.dqs <= 1.0
