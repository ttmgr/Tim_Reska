"""Tests for Charlson Comorbidity Index computation."""

from medrisk.data.charlson import (
    CHARLSON_CATEGORIES,
    compute_charlson_categories,
    compute_charlson_index,
)


class TestCharlsonCategories:
    def test_empty_codes(self) -> None:
        result = compute_charlson_categories([])
        assert all(not v for v in result.values())

    def test_mi_detected(self) -> None:
        result = compute_charlson_categories(["I21.0"])
        assert result["mi"]

    def test_diabetes_uncomplicated(self) -> None:
        result = compute_charlson_categories(["E11.9"])
        assert result["diabetes_uncomplicated"]
        assert not result["diabetes_complicated"]

    def test_diabetes_complicated(self) -> None:
        result = compute_charlson_categories(["E11.2"])
        assert result["diabetes_complicated"]

    def test_ckd_maps_to_renal(self) -> None:
        result = compute_charlson_categories(["N18.3"])
        assert result["renal"]

    def test_hiv_detected(self) -> None:
        result = compute_charlson_categories(["B20"])
        assert result["hiv"]


class TestCharlsonIndex:
    def test_zero_for_empty(self) -> None:
        assert compute_charlson_index([]) == 0

    def test_single_weight_1(self) -> None:
        # MI alone = weight 1
        assert compute_charlson_index(["I21.0"]) == 1

    def test_multiple_weight_1(self) -> None:
        # MI (1) + CHF (1) + COPD (1) = 3
        assert compute_charlson_index(["I21.0", "I50.9", "J44.9"]) == 3

    def test_weight_2_category(self) -> None:
        # Renal disease alone = weight 2
        assert compute_charlson_index(["N18.5"]) == 2

    def test_diabetes_hierarchy(self) -> None:
        # Both uncomplicated and complicated present: only complicated counts (weight 2)
        codes = ["E11.9", "E11.2"]
        assert compute_charlson_index(codes) == 2

    def test_liver_hierarchy(self) -> None:
        # Both mild and severe liver: only severe counts (weight 3)
        codes = ["K70.3", "K70.4"]
        assert compute_charlson_index(codes) == 3

    def test_cancer_hierarchy(self) -> None:
        # Both primary and metastatic: only metastatic counts (weight 6)
        codes = ["C34.9", "C78"]
        assert compute_charlson_index(codes) == 6

    def test_complex_patient(self) -> None:
        # MI(1) + CHF(1) + T2D complicated(2) + CKD(2) + COPD(1) = 7
        codes = ["I21.0", "I50.9", "E11.3", "N18.4", "J44.9"]
        assert compute_charlson_index(codes) == 7

    def test_hiv_weight_6(self) -> None:
        assert compute_charlson_index(["B20"]) == 6

    def test_result_always_non_negative(self) -> None:
        assert compute_charlson_index([]) >= 0
        assert compute_charlson_index(["Z99.9"]) >= 0  # unrecognised code


class TestCategoryDefinitions:
    def test_all_categories_have_prefixes(self) -> None:
        for key, cat in CHARLSON_CATEGORIES.items():
            assert len(cat.icd10_prefixes) > 0, f"{key} has no prefixes"

    def test_all_weights_positive(self) -> None:
        for key, cat in CHARLSON_CATEGORIES.items():
            assert cat.weight > 0, f"{key} has non-positive weight"

    def test_seventeen_categories(self) -> None:
        assert len(CHARLSON_CATEGORIES) == 17
