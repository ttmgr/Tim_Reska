"""ICD-10 feature encoding strategies.

Three encoding approaches for transforming ICD-10 codes into numerical
feature vectors:
1. Binary presence flags per clinical category
2. Charlson category indicators (17 binary features)
3. Hierarchical chapter-level grouping
"""

from __future__ import annotations

import logging

from medrisk.data.charlson import CHARLSON_CATEGORIES, compute_charlson_categories
from medrisk.data.icd10 import CODELIST, get_all_categories

logger = logging.getLogger(__name__)


def encode_binary_categories(icd10_codes: list[str]) -> dict[str, bool]:
    """Encode ICD-10 codes as binary presence flags per clinical category.

    Args:
        icd10_codes: List of ICD-10 codes for a patient.

    Returns:
        Dictionary mapping category names to boolean presence.
    """
    observed = set()
    for code in icd10_codes:
        info = CODELIST.get(code)
        if info:
            observed.add(info.category)

    return {cat: cat in observed for cat in get_all_categories()}


def encode_charlson_categories(icd10_codes: list[str]) -> dict[str, bool]:
    """Encode ICD-10 codes as Charlson comorbidity category indicators.

    Args:
        icd10_codes: List of ICD-10 codes for a patient.

    Returns:
        Dictionary mapping 17 Charlson category keys to boolean presence.
    """
    return compute_charlson_categories(icd10_codes)


def encode_chapter_groups(icd10_codes: list[str]) -> dict[str, int]:
    """Encode ICD-10 codes by chapter, counting codes per chapter.

    Args:
        icd10_codes: List of ICD-10 codes for a patient.

    Returns:
        Dictionary mapping chapter IDs to count of codes in that chapter.
    """
    chapters: dict[str, int] = {}
    for code in icd10_codes:
        info = CODELIST.get(code)
        if info:
            chapters[info.chapter] = chapters.get(info.chapter, 0) + 1
    return chapters


def get_binary_feature_names() -> list[str]:
    """Return sorted list of binary category feature names."""
    return [f"has_{cat}" for cat in get_all_categories()]


def get_charlson_feature_names() -> list[str]:
    """Return sorted list of Charlson category feature names."""
    return [f"charlson_{cat}" for cat in sorted(CHARLSON_CATEGORIES.keys())]
