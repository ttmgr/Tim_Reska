"""No-future-leakage tests for static feature construction.

The package docstrings assert that "no future information leaks into feature
construction," but the existing label tests only check the consistency of an
inline sample DataFrame -- they never run a feature extractor. These tests
exercise ``StaticFeatureExtractor`` directly and prove the load-bearing
invariant: a condition recorded *after* the index date must not change any
extracted feature.
"""

import pandas as pd
import pytest

from disease_progression.data.omop_etl import OMOPTables
from disease_progression.features.static import StaticFeatureExtractor

INDEX_DATE = "2024-01-01"
PERSON_ID = 1


def _person() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "person_id": PERSON_ID,
                "year_of_birth": 1970,
                "gender_concept_id": 8507,  # male
                "race_concept_id": 0,
                "ethnicity_concept_id": 0,
                "death_datetime": pd.NaT,
            }
        ]
    )


def _conditions(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(
        rows, columns=["person_id", "condition_start_date", "condition_source_value"]
    )


# A diabetes code recorded comfortably inside the lookback window, before index.
BASELINE_CONDITION = {
    "person_id": PERSON_ID,
    "condition_start_date": "2022-06-01",
    "condition_source_value": "E119",
}
# A heart-failure code recorded *after* the index date -- must be ignored.
FUTURE_CONDITION = {
    "person_id": PERSON_ID,
    "condition_start_date": "2026-03-01",
    "condition_source_value": "I509",
}


@pytest.fixture
def extractor() -> StaticFeatureExtractor:
    # Lookback long enough that the baseline condition is in-window.
    return StaticFeatureExtractor(index_date=INDEX_DATE, lookback_days=3650)


def test_future_condition_does_not_leak_into_static_features(extractor) -> None:
    """Adding a post-index condition must not change any extracted feature."""
    baseline_only = OMOPTables(
        person=_person(), condition_occurrence=_conditions([BASELINE_CONDITION])
    )
    with_future = OMOPTables(
        person=_person(),
        condition_occurrence=_conditions([BASELINE_CONDITION, FUTURE_CONDITION]),
    )

    features_baseline = extractor.transform(baseline_only)
    features_with_future = extractor.transform(with_future)

    # If the future condition leaked, n_distinct_conditions / charlson / flags
    # would differ. The whole feature row must be identical.
    pd.testing.assert_frame_equal(features_baseline, features_with_future)


def test_baseline_condition_is_actually_counted(extractor) -> None:
    """Guard against a vacuous pass: an in-window condition must register."""
    none = OMOPTables(person=_person(), condition_occurrence=_conditions([]))
    one = OMOPTables(
        person=_person(), condition_occurrence=_conditions([BASELINE_CONDITION])
    )

    f_none = extractor.transform(none)
    f_one = extractor.transform(one)

    assert f_none.loc[PERSON_ID, "n_distinct_conditions"] == 0
    assert f_one.loc[PERSON_ID, "n_distinct_conditions"] == 1


def test_only_future_conditions_yield_empty_baseline(extractor) -> None:
    """A patient whose only condition is after index looks condition-free."""
    only_future = OMOPTables(
        person=_person(), condition_occurrence=_conditions([FUTURE_CONDITION])
    )
    features = extractor.transform(only_future)
    assert features.loc[PERSON_ID, "n_distinct_conditions"] == 0


def test_empty_and_filtered_conditions_produce_identical_features(extractor) -> None:
    """Empty condition_occurrence and filtered-to-empty conditions converge.

    The old transform() branched on ``conditions.empty``: one path filled
    defaults explicitly, the other relied on left-join + fillna via the
    helpers. Both paths could drift apart -- a helper changing its empty-frame
    contract would only affect one branch. This test pins the unified path:
    no matter how the baseline window ends up empty, the feature row must be
    identical and fully zero-filled across the comorbidity columns.
    """
    fully_empty = OMOPTables(
        person=_person(), condition_occurrence=pd.DataFrame()
    )
    filtered_empty = OMOPTables(
        person=_person(), condition_occurrence=_conditions([FUTURE_CONDITION])
    )

    f_fully = extractor.transform(fully_empty)
    f_filtered = extractor.transform(filtered_empty)

    pd.testing.assert_frame_equal(f_fully, f_filtered)

    # And the load-bearing comorbidity columns must all be zero.
    expected_zero_cols = [
        "charlson_index",
        "n_distinct_conditions",
        "has_hypertension",
        "has_atrial_fibrillation",
        "has_diabetes",
        "has_ckd",
        "has_prior_mi",
        "has_prior_stroke",
        "has_heart_failure",
        "has_dyslipidemia",
        "has_obesity",
        "has_copd",
    ]
    for col in expected_zero_cols:
        assert f_fully.loc[PERSON_ID, col] == 0, f"{col} should be 0 on empty conditions"
