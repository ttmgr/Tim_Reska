"""Tests for medrisk.underwriting.profiles."""

import pytest

from medrisk.underwriting.profiles import (
    DiseaseProfile,
    get_profile_for_icd,
    load_case_studies,
    load_comorbidity_interactions,
    load_underwriting_profiles,
)


@pytest.fixture(scope="module")
def profiles():
    return load_underwriting_profiles()


@pytest.fixture(scope="module")
def interactions():
    return load_comorbidity_interactions()


@pytest.fixture(scope="module")
def cases():
    return load_case_studies()


class TestLoadProfiles:
    def test_load_all_profiles(self, profiles):
        assert len(profiles) == 15

    def test_profile_has_required_fields(self, profiles):
        for key, profile in profiles.items():
            assert isinstance(profile, DiseaseProfile), f"{key} is not a DiseaseProfile"
            assert profile.cluster, f"{key}: cluster is empty"
            assert profile.label, f"{key}: label is empty"
            assert profile.icd_codes, f"{key}: icd_codes is empty"
            assert profile.underwriting_responses, f"{key}: underwriting_responses is empty"


class TestICDMatching:
    def test_icd_matching_mood(self, profiles):
        result = get_profile_for_icd("F32.1", profiles)
        assert result is not None
        assert result.cluster == "psychiatric"

    def test_icd_matching_hypertension(self, profiles):
        result = get_profile_for_icd("I10", profiles)
        assert result is not None
        assert "I10" in result.icd_codes

    def test_icd_matching_diabetes(self, profiles):
        result = get_profile_for_icd("E11.9", profiles)
        assert result is not None
        assert "E11" in result.icd_codes

    def test_icd_matching_ms(self, profiles):
        result = get_profile_for_icd("G35", profiles)
        assert result is not None
        assert "G35" in result.icd_codes

    def test_icd_matching_unknown(self, profiles):
        result = get_profile_for_icd("X99", profiles)
        assert result is None


class TestLoadComorbidityInteractions:
    def test_load_comorbidity_interactions(self, interactions):
        assert len(interactions) == 8

    def test_interaction_has_codes(self, interactions):
        for interaction in interactions:
            assert interaction.codes_a, "codes_a is empty"
            assert isinstance(interaction.codes_a, list)
            assert isinstance(interaction.codes_b, list)


class TestLoadCaseStudies:
    def test_load_case_studies(self, cases):
        assert len(cases) == 10

    def test_case_study_has_required_fields(self, cases):
        for case in cases:
            assert case.applicant is not None, f"case {case.id}: applicant missing"
            assert case.icd_history, f"case {case.id}: icd_history is empty"
            assert case.algorithm_output is not None, f"case {case.id}: algorithm_output missing"
            assert case.correct_decision is not None, f"case {case.id}: correct_decision missing"
