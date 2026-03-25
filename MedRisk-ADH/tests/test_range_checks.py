"""Tests for physiological range validation."""

from medrisk.validation.range_checks import (
    PHYSIOLOGICAL_LIMITS,
    check_patient_ranges,
    check_ranges,
)


class TestCheckRanges:
    def test_all_valid_values(self):
        values = {"lab_hba1c": 6.5, "lab_egfr": 90.0, "lab_systolic_bp": 130.0}
        result = check_ranges(values)
        assert result.range_score == 1.0
        assert len(result.violations) == 0
        assert result.n_checked == 3

    def test_out_of_range_detected(self):
        values = {"lab_systolic_bp": 999.0}
        result = check_ranges(values)
        assert result.range_score == 0.0
        assert len(result.violations) == 1
        assert result.violations[0][0] == "lab_systolic_bp"

    def test_none_values_skipped(self):
        values = {"lab_hba1c": None, "lab_egfr": 90.0}
        result = check_ranges(values)
        assert result.n_checked == 1
        assert result.range_score == 1.0

    def test_empty_values(self):
        result = check_ranges({})
        assert result.range_score == 1.0
        assert result.n_checked == 0

    def test_mixed_valid_invalid(self):
        values = {"lab_hba1c": 7.0, "lab_egfr": 0.5, "lab_systolic_bp": 120.0}
        result = check_ranges(values)
        assert result.n_checked == 3
        assert len(result.violations) == 1
        assert abs(result.range_score - 2 / 3) < 0.01

    def test_unit_conversion_hba1c(self):
        values = {"lab_hba1c": 48.0}  # mmol/mol, not %
        result = check_ranges(values)
        assert len(result.suspected_unit_errors) == 1
        assert result.suspected_unit_errors[0][2] == "mmol/mol"

    def test_unit_conversion_egfr(self):
        values = {"lab_egfr": 0.09}  # L/min, not mL/min
        result = check_ranges(values)
        assert len(result.suspected_unit_errors) == 1

    def test_unknown_feature_ignored(self):
        values = {"unknown_lab": 42.0, "lab_hba1c": 6.0}
        result = check_ranges(values)
        assert result.n_checked == 1

    def test_all_limits_defined(self):
        assert len(PHYSIOLOGICAL_LIMITS) == 10


class TestCheckPatientRanges:
    def test_extracts_lab_cols(self):
        row = {"lab_hba1c": 7.0, "age": 55, "lab_egfr": 80.0}
        result = check_patient_ranges(row)
        assert result.n_checked == 2
