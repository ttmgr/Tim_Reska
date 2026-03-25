"""Tests for synthetic patient cohort generator."""

import numpy as np
import pytest

from medrisk.data.schemas import Market, PatientRecord
from medrisk.data.synthetic import (
    cohort_to_dataframe,
    generate_cohort,
    generate_patient,
)


@pytest.fixture
def rng():
    return np.random.default_rng(42)


class TestGeneratePatient:
    def test_returns_valid_record(self, rng: np.random.Generator) -> None:
        patient = generate_patient(rng, "DE")
        assert isinstance(patient, PatientRecord)
        assert patient.market == Market.DE
        assert 18 <= patient.age <= 100
        assert 12.0 <= patient.bmi <= 60.0

    def test_de_market(self, rng: np.random.Generator) -> None:
        patient = generate_patient(rng, "DE")
        assert patient.market == Market.DE

    def test_int_market(self, rng: np.random.Generator) -> None:
        patient = generate_patient(rng, "INT")
        assert patient.market == Market.INT

    def test_has_ground_truth(self, rng: np.random.Generator) -> None:
        patient = generate_patient(rng, "DE")
        assert isinstance(patient.gt_true_conditions, list)
        assert patient.gt_true_risk_score is not None
        assert patient.gt_data_quality_score is not None

    def test_time_to_event_positive(self, rng: np.random.Generator) -> None:
        patient = generate_patient(rng, "DE")
        assert patient.time_to_event > 0

    def test_reproducible(self) -> None:
        p1 = generate_patient(np.random.default_rng(99), "DE")
        p2 = generate_patient(np.random.default_rng(99), "DE")
        assert p1.age == p2.age
        assert p1.bmi == p2.bmi
        assert p1.sex == p2.sex


class TestGenerateCohort:
    def test_correct_total_size(self) -> None:
        cohort = generate_cohort(n_per_market=50, markets=["DE", "INT"], seed=42)
        assert len(cohort) == 100

    def test_all_markets_present(self) -> None:
        cohort = generate_cohort(n_per_market=30, seed=42)
        markets = {p.market.value for p in cohort}
        assert markets == {"DE", "ES", "FR", "INT"}

    def test_schema_validation(self) -> None:
        """Every patient should pass Pydantic validation (it does by construction)."""
        cohort = generate_cohort(n_per_market=50, markets=["DE"], seed=42)
        for p in cohort:
            assert isinstance(p, PatientRecord)
            assert p.age >= 18

    def test_dqs_differs_between_markets(self) -> None:
        """DE should have systematically higher DQS than INT."""
        cohort = generate_cohort(n_per_market=200, markets=["DE", "INT"], seed=42)
        de_dqs = [p.gt_data_quality_score for p in cohort if p.market == Market.DE]
        int_dqs = [p.gt_data_quality_score for p in cohort if p.market == Market.INT]
        assert np.mean(de_dqs) > np.mean(int_dqs)


class TestCohortToDataframe:
    def test_correct_shape(self) -> None:
        cohort = generate_cohort(n_per_market=20, markets=["DE"], seed=42)
        df = cohort_to_dataframe(cohort)
        assert len(df) == 20
        assert "patient_id" in df.columns
        assert "charlson_index" in df.columns
        assert "age" in df.columns

    def test_has_lab_columns(self) -> None:
        cohort = generate_cohort(n_per_market=20, markets=["DE"], seed=42)
        df = cohort_to_dataframe(cohort)
        lab_cols = [c for c in df.columns if c.startswith("lab_")]
        assert len(lab_cols) > 0

    def test_has_diagnosis_flags(self) -> None:
        cohort = generate_cohort(n_per_market=20, markets=["DE"], seed=42)
        df = cohort_to_dataframe(cohort)
        flag_cols = [c for c in df.columns if c.startswith("has_")]
        assert len(flag_cols) > 10

    def test_has_medication_flags(self) -> None:
        cohort = generate_cohort(n_per_market=20, markets=["DE"], seed=42)
        df = cohort_to_dataframe(cohort)
        med_cols = [c for c in df.columns if c.startswith("med_")]
        assert len(med_cols) > 0
