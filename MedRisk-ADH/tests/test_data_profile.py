"""Tests for data profile classification."""

import pandas as pd
import pytest

from medrisk.features.data_profile import (
    DataProfile,
    classify_cohort_profiles,
    classify_data_profile,
    get_feature_cols_for_profile,
)


@pytest.fixture
def full_row():
    data = {"age": 55, "bmi": 27.0, "sex": "M", "smoking_status": "never", "charlson_index": 2}
    for i in range(10):
        data[f"lab_{i}"] = float(i)
    for i in range(8):
        data[f"med_{i}"] = True
    return pd.Series(data)


@pytest.fixture
def no_labs_row():
    data = {"age": 55, "bmi": 27.0, "sex": "M", "smoking_status": "never", "charlson_index": 2}
    for i in range(8):
        data[f"med_{i}"] = True
    return pd.Series(data)


class TestClassifyDataProfile:
    def test_full_profile(self, full_row):
        lab_cols = [f"lab_{i}" for i in range(10)]
        med_cols = [f"med_{i}" for i in range(8)]
        profile = classify_data_profile(full_row, lab_cols=lab_cols, med_cols=med_cols)
        assert profile == DataProfile.FULL

    def test_no_labs_profile(self, no_labs_row):
        lab_cols = [f"lab_{i}" for i in range(10)]
        med_cols = [f"med_{i}" for i in range(8)]
        profile = classify_data_profile(no_labs_row, lab_cols=lab_cols, med_cols=med_cols)
        assert profile == DataProfile.NO_LABS

    def test_minimal_profile(self):
        data = {"age": 55, "bmi": 27.0, "sex": "M", "smoking_status": "never", "charlson_index": 2}
        row = pd.Series(data)
        lab_cols = [f"lab_{i}" for i in range(10)]
        med_cols = [f"med_{i}" for i in range(8)]
        profile = classify_data_profile(row, lab_cols=lab_cols, med_cols=med_cols)
        assert profile == DataProfile.MINIMAL

    def test_insufficient_profile(self):
        row = pd.Series({"age": None, "bmi": None, "sex": None})
        core = ["age", "bmi", "sex", "smoking_status", "charlson_index"]
        profile = classify_data_profile(row, core_cols=core, lab_cols=[], med_cols=[])
        assert profile == DataProfile.INSUFFICIENT


class TestClassifyCohortProfiles:
    def test_batch_classification(self, full_row):
        df = pd.DataFrame([full_row] * 5)
        lab_cols = [f"lab_{i}" for i in range(10)]
        med_cols = [f"med_{i}" for i in range(8)]
        profiles = classify_cohort_profiles(df, lab_cols=lab_cols, med_cols=med_cols)
        assert len(profiles) == 5
        assert all(p == DataProfile.FULL for p in profiles)


class TestGetFeatureColsForProfile:
    def test_full_keeps_all(self):
        all_cols = ["age", "lab_hba1c", "med_metformin"]
        result = get_feature_cols_for_profile(DataProfile.FULL, all_cols)
        assert result == all_cols

    def test_no_labs_removes_labs(self):
        all_cols = ["age", "lab_hba1c", "med_metformin"]
        result = get_feature_cols_for_profile(DataProfile.NO_LABS, all_cols, lab_cols=["lab_hba1c"])
        assert "lab_hba1c" not in result
        assert "age" in result

    def test_minimal_removes_both(self):
        all_cols = ["age", "lab_hba1c", "med_metformin"]
        result = get_feature_cols_for_profile(
            DataProfile.MINIMAL, all_cols,
            lab_cols=["lab_hba1c"], med_cols=["med_metformin"],
        )
        assert result == ["age"]

    def test_insufficient_returns_empty(self):
        result = get_feature_cols_for_profile(DataProfile.INSUFFICIENT, ["age", "bmi"])
        assert result == []
