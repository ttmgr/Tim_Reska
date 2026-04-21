"""Tests for Alzheimer-specific synthetic data generation."""

import numpy as np
import pytest

from medrisk.data.icd10 import CODELIST, get_codes_by_category
from medrisk.data.synthetic import (
    BASELINE_PREVALENCE,
    LAB_DEFINITIONS,
    MEDICATION_MAP,
    generate_ad_cohort,
    generate_ad_patient,
)

# ---------------------------------------------------------------------------
# ICD-10 code tests
# ---------------------------------------------------------------------------


class TestAlzheimerICD10:
    def test_alzheimer_codes_registered(self):
        expected = ["G30.0", "G30.1", "G30.8", "G30.9", "F00.0", "F00.1", "F00.2", "F00.9"]
        for code in expected:
            assert code in CODELIST, f"{code} not registered"

    def test_alzheimer_category_lookup(self):
        codes = get_codes_by_category("alzheimer")
        assert len(codes) >= 4

    def test_alzheimer_early_category(self):
        codes = get_codes_by_category("alzheimer_early")
        assert len(codes) >= 2

    def test_alzheimer_late_category(self):
        codes = get_codes_by_category("alzheimer_late")
        assert len(codes) >= 2

    def test_existing_dementia_code_unchanged(self):
        assert "F03.9" in CODELIST
        assert CODELIST["F03.9"].category == "dementia"


# ---------------------------------------------------------------------------
# Prevalence and config tests
# ---------------------------------------------------------------------------


class TestAlzheimerConfig:
    def test_alzheimer_in_baseline_prevalence(self):
        assert "alzheimer" in BASELINE_PREVALENCE
        assert 0.008 <= BASELINE_PREVALENCE["alzheimer"] <= 0.02

    def test_cognitive_labs_defined(self):
        loinc_codes = list(LAB_DEFINITIONS.keys())
        assert "72106-8" in loinc_codes  # MMSE
        assert "72172-0" in loinc_codes  # MoCA

    def test_csf_biomarkers_defined(self):
        assert "33203-1" in LAB_DEFINITIONS  # CSF Abeta42
        assert "72260-3" in LAB_DEFINITIONS  # CSF p-tau181

    def test_alzheimer_medications_defined(self):
        assert "alzheimer" in MEDICATION_MAP
        atc_codes = [atc for atc, _, _ in MEDICATION_MAP["alzheimer"]]
        assert "N06DA02" in atc_codes  # Donepezil
        assert "N06DX01" in atc_codes  # Memantine


# ---------------------------------------------------------------------------
# Patient generation tests
# ---------------------------------------------------------------------------


class TestAlzheimerPatientGeneration:
    @pytest.fixture
    def ad_patient(self):
        rng = np.random.default_rng(42)
        return generate_ad_patient(rng, "DE")

    def test_generates_valid_patient(self, ad_patient):
        assert ad_patient.patient_id is not None
        assert ad_patient.market.value == "DE"

    def test_apoe4_field_present(self, ad_patient):
        assert ad_patient.apoe4_carrier is not None
        assert isinstance(ad_patient.apoe4_carrier, bool)

    def test_education_years_present(self, ad_patient):
        assert ad_patient.education_years is not None
        assert 6 <= ad_patient.education_years <= 22

    def test_family_history_present(self, ad_patient):
        assert ad_patient.family_history_dementia is not None
        assert isinstance(ad_patient.family_history_dementia, bool)

    def test_has_alzheimer_condition(self, ad_patient):
        ad_cats = {"alzheimer", "alzheimer_early", "alzheimer_late"}
        assert any(c in ad_cats for c in ad_patient.gt_true_conditions)

    def test_age_distribution_older(self):
        rng = np.random.default_rng(123)
        ages = [generate_ad_patient(rng, "DE").age for _ in range(100)]
        mean_age = np.mean(ages)
        assert mean_age >= 65, f"Mean age {mean_age} too young for AD cohort"


class TestAlzheimerCohort:
    def test_generate_ad_cohort(self):
        cohort = generate_ad_cohort(n_per_market=10, markets=["DE"], seed=42)
        assert len(cohort) == 10

    def test_ad_cohort_multi_market(self):
        cohort = generate_ad_cohort(n_per_market=5, markets=["DE", "INT"], seed=42)
        assert len(cohort) == 10
        markets = {p.market.value for p in cohort}
        assert markets == {"DE", "INT"}

    def test_event_type_validation(self):
        cohort = generate_ad_cohort(n_per_market=50, markets=["DE"], seed=42)
        valid = {"death", "institutionalization", "cognitive_decline", None}
        for p in cohort:
            assert p.event_type in valid, f"Invalid event_type: {p.event_type}"
