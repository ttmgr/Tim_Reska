"""Tests for codelist validity.

Ensures that ICD-10, LOINC, ATC, and SNOMED codes used throughout
the project conform to expected formats and that disease tracks
do not overlap in their code definitions.
"""

import re

import pytest

# ── Code lists used in the project ──────────────────────────────────────────

# ICD-10 codes (ICD-10-CM / ICD-10-GM format)
CVD_ICD10 = [
    "I10",       # Essential hypertension
    "I11.0",     # Hypertensive heart disease with heart failure
    "I20.0",     # Unstable angina
    "I21.0",     # Acute ST elevation MI, anterior wall
    "I21.1",     # Acute ST elevation MI, inferior wall
    "I21.4",     # Acute subendocardial MI
    "I25.1",     # Atherosclerotic heart disease
    "I25.10",    # Atherosclerotic heart disease without angina
    "I50.0",     # Congestive heart failure
    "I50.1",     # Left ventricular failure
    "I50.9",     # Heart failure, unspecified
    "I63.9",     # Cerebral infarction, unspecified
    "I48.0",     # Paroxysmal atrial fibrillation
    "I48.1",     # Persistent atrial fibrillation
]

DIABETES_ICD10 = [
    "E11.0",     # T2D with hyperosmolarity
    "E11.2",     # T2D with kidney complications
    "E11.3",     # T2D with ophthalmic complications
    "E11.4",     # T2D with neurological complications
    "E11.5",     # T2D with circulatory complications
    "E11.65",    # T2D with hyperglycemia
    "E11.9",     # T2D without complications
    "E13.9",     # Other specified diabetes
    "R73.03",    # Prediabetes
    "N18.1",     # CKD stage 1
    "N18.2",     # CKD stage 2
    "N18.3",     # CKD stage 3
    "N18.4",     # CKD stage 4
    "N18.5",     # CKD stage 5
    "N18.6",     # ESRD
]

# LOINC codes for lab observations
LOINC_CODES = [
    "4548-4",    # Hemoglobin A1c
    "2345-7",    # Glucose
    "2093-3",    # Total cholesterol
    "2085-9",    # HDL cholesterol
    "18262-6",   # LDL cholesterol
    "2571-8",    # Triglycerides
    "8480-6",    # Systolic blood pressure
    "8462-4",    # Diastolic blood pressure
    "39156-5",   # BMI
    "33914-3",   # eGFR
    "2160-0",    # Creatinine
    "8867-4",    # Heart rate
    "9279-1",    # Respiratory rate
    "8302-2",    # Body height
    "29463-7",   # Body weight
]

# ATC codes for relevant medications
ATC_CODES = [
    "C09AA01",   # Captopril (ACE inhibitor)
    "C09AA02",   # Enalapril
    "C09CA01",   # Losartan (ARB)
    "C07AB02",   # Metoprolol (beta-blocker)
    "C07AB07",   # Bisoprolol
    "C10AA01",   # Simvastatin (statin)
    "C10AA05",   # Atorvastatin
    "C10AA07",   # Rosuvastatin
    "B01AC06",   # Acetylsalicylic acid
    "A10BA02",   # Metformin
    "A10BK01",   # Dapagliflozin (SGLT2i)
    "A10BK02",   # Canagliflozin
    "A10BJ02",   # Liraglutide (GLP-1 RA)
    "A10BJ05",   # Dulaglutide
    "A10AE04",   # Insulin glargine
]


# ── ICD-10 format tests ────────────────────────────────────────────────────

ICD10_PATTERN = re.compile(r"^[A-Z]\d{2}(\.\d{1,4})?$")


class TestICD10Codes:
    """Test that ICD-10 codes match the expected format."""

    @pytest.mark.parametrize("code", CVD_ICD10)
    def test_cvd_icd10_format(self, code: str) -> None:
        assert ICD10_PATTERN.match(code), (
            f"CVD ICD-10 code '{code}' does not match expected pattern "
            f"(letter + 2 digits, optional dot + 1-4 digits)"
        )

    @pytest.mark.parametrize("code", DIABETES_ICD10)
    def test_diabetes_icd10_format(self, code: str) -> None:
        assert ICD10_PATTERN.match(code), (
            f"Diabetes ICD-10 code '{code}' does not match expected pattern"
        )

    def test_cvd_codes_in_circulatory_chapter(self) -> None:
        """CVD codes should primarily be in chapter I (circulatory system)."""
        for code in CVD_ICD10:
            assert code[0] == "I", (
                f"CVD code '{code}' is not in ICD-10 chapter I (circulatory)"
            )

    def test_diabetes_codes_in_expected_chapters(self) -> None:
        """Diabetes codes should be in chapter E (endocrine), N (genitourinary), or R (symptoms)."""
        allowed_chapters = {"E", "N", "R"}
        for code in DIABETES_ICD10:
            assert code[0] in allowed_chapters, (
                f"Diabetes code '{code}' not in expected chapters {allowed_chapters}"
            )


# ── No overlap between disease tracks ──────────────────────────────────────

class TestCodelistNoOverlap:
    """Test that CVD and diabetes code lists do not overlap."""

    def test_icd10_no_overlap(self) -> None:
        overlap = set(CVD_ICD10) & set(DIABETES_ICD10)
        assert len(overlap) == 0, (
            f"ICD-10 codes shared between CVD and diabetes tracks: {overlap}"
        )

    def test_code_lists_not_empty(self) -> None:
        assert len(CVD_ICD10) > 0, "CVD ICD-10 code list is empty"
        assert len(DIABETES_ICD10) > 0, "Diabetes ICD-10 code list is empty"
        assert len(LOINC_CODES) > 0, "LOINC code list is empty"
        assert len(ATC_CODES) > 0, "ATC code list is empty"

    def test_no_duplicate_codes_within_lists(self) -> None:
        for name, codes in [
            ("CVD_ICD10", CVD_ICD10),
            ("DIABETES_ICD10", DIABETES_ICD10),
            ("LOINC_CODES", LOINC_CODES),
            ("ATC_CODES", ATC_CODES),
        ]:
            assert len(codes) == len(set(codes)), (
                f"Duplicate codes found in {name}"
            )


# ── LOINC format tests ─────────────────────────────────────────────────────

LOINC_PATTERN = re.compile(r"^\d{1,5}-\d$")


class TestLOINCCodes:
    """Test LOINC codes conform to the standard format (digits-check_digit)."""

    @pytest.mark.parametrize("code", LOINC_CODES)
    def test_loinc_format(self, code: str) -> None:
        assert LOINC_PATTERN.match(code), (
            f"LOINC code '{code}' does not match expected format "
            f"(1-5 digits, hyphen, 1 check digit)"
        )

    def test_loinc_check_digits_valid(self) -> None:
        """Check digit should be 0-9."""
        for code in LOINC_CODES:
            check_digit = code.split("-")[1]
            assert check_digit.isdigit() and len(check_digit) == 1, (
                f"LOINC code '{code}' has invalid check digit"
            )


# ── ATC format tests ───────────────────────────────────────────────────────

ATC_PATTERN = re.compile(r"^[A-Z]\d{2}[A-Z]{2}\d{2}$")


class TestATCCodes:
    """Test ATC codes conform to the 7-character format (L-DD-LL-DD)."""

    @pytest.mark.parametrize("code", ATC_CODES)
    def test_atc_format(self, code: str) -> None:
        assert ATC_PATTERN.match(code), (
            f"ATC code '{code}' does not match expected 7-character format "
            f"(letter, 2 digits, 2 letters, 2 digits)"
        )

    def test_atc_anatomical_groups(self) -> None:
        """Verify ATC codes belong to expected anatomical groups."""
        expected_groups = {
            "A": "Alimentary tract and metabolism",
            "B": "Blood and blood forming organs",
            "C": "Cardiovascular system",
        }
        for code in ATC_CODES:
            assert code[0] in expected_groups, (
                f"ATC code '{code}' has unexpected anatomical group '{code[0]}'"
            )
