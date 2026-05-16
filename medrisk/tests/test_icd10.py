"""Tests for ICD-10 codelist and lookups."""

import pytest

from medrisk.data.icd10 import (
    CODELIST,
    get_all_categories,
    get_all_codes,
    get_codes_by_category,
    get_codes_by_chapter,
    lookup,
    validate_icd10,
)


class TestValidateICD10:
    @pytest.mark.parametrize(
        "code",
        ["I10", "E11.9", "N18.3", "C34.9", "I21.0", "R73.03"],
    )
    def test_valid_codes(self, code: str) -> None:
        assert validate_icd10(code)

    @pytest.mark.parametrize(
        "code",
        ["", "123", "I1", "I10.", "ZZ9.9", "i10", "I10.12345"],
    )
    def test_invalid_codes(self, code: str) -> None:
        assert not validate_icd10(code)


class TestLookup:
    def test_known_code(self) -> None:
        result = lookup("I10")
        assert result is not None
        assert result.description == "Essential hypertension"
        assert result.chapter == "IX"

    def test_unknown_code(self) -> None:
        assert lookup("Z99.9") is None

    def test_diabetes_code(self) -> None:
        result = lookup("E11.9")
        assert result is not None
        assert "T2D" in result.description
        assert result.category == "diabetes"


class TestCategoryLookups:
    def test_get_diabetes_codes(self) -> None:
        codes = get_codes_by_category("diabetes")
        assert len(codes) >= 5
        assert all(c.category == "diabetes" for c in codes)

    def test_get_hf_codes(self) -> None:
        codes = get_codes_by_category("hf")
        assert len(codes) >= 3
        code_strings = [c.code for c in codes]
        assert "I50.9" in code_strings

    def test_empty_category(self) -> None:
        assert get_codes_by_category("nonexistent") == []

    def test_get_by_chapter(self) -> None:
        chapter_ix = get_codes_by_chapter("IX")
        assert len(chapter_ix) > 0
        assert all(c.chapter == "IX" for c in chapter_ix)


class TestCodelistIntegrity:
    def test_all_codes_valid_format(self) -> None:
        for code in get_all_codes():
            assert validate_icd10(code), f"Invalid format: {code}"

    def test_categories_not_empty(self) -> None:
        categories = get_all_categories()
        assert len(categories) > 10

    def test_codelist_has_minimum_coverage(self) -> None:
        assert len(CODELIST) >= 50
