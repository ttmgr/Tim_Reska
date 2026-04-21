"""Charlson Comorbidity Index computation from ICD-10 codes.

Implements the Quan-adapted Charlson Comorbidity Index (Quan et al., 2005)
using ICD-10 code prefix mappings. Each of the 17 comorbidity categories is
mapped to a set of ICD-10 prefixes and assigned a weight.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CharlsonCategory:
    """A single Charlson comorbidity category with its ICD-10 prefixes and weight."""

    name: str
    weight: int
    icd10_prefixes: tuple[str, ...]


# Quan-adapted Charlson categories with ICD-10 prefix mappings
CHARLSON_CATEGORIES: dict[str, CharlsonCategory] = {
    "mi": CharlsonCategory(
        name="Myocardial infarction",
        weight=1,
        icd10_prefixes=("I21", "I22", "I25.2"),
    ),
    "chf": CharlsonCategory(
        name="Congestive heart failure",
        weight=1,
        icd10_prefixes=("I09.9", "I11.0", "I13.0", "I13.2", "I25.5", "I42", "I43", "I50"),
    ),
    "pvd": CharlsonCategory(
        name="Peripheral vascular disease",
        weight=1,
        icd10_prefixes=(
            "I70",
            "I71",
            "I73.1",
            "I73.8",
            "I73.9",
            "I77.1",
            "I79.0",
            "I79.2",
            "K55.1",
            "K55.8",
            "K55.9",
            "Z95.8",
            "Z95.9",
        ),
    ),
    "cvd": CharlsonCategory(
        name="Cerebrovascular disease",
        weight=1,
        icd10_prefixes=(
            "G45",
            "G46",
            "H34.0",
            "I60",
            "I61",
            "I62",
            "I63",
            "I64",
            "I65",
            "I66",
            "I67",
            "I68",
        ),
    ),
    "dementia": CharlsonCategory(
        name="Dementia",
        weight=1,
        icd10_prefixes=("F00", "F01", "F02", "F03", "F05.1", "G30", "G31.1"),
    ),
    "copd": CharlsonCategory(
        name="Chronic pulmonary disease",
        weight=1,
        icd10_prefixes=(
            "I27.8",
            "I27.9",
            "J40",
            "J41",
            "J42",
            "J43",
            "J44",
            "J45",
            "J46",
            "J47",
            "J60",
            "J61",
            "J62",
            "J63",
            "J64",
            "J65",
            "J66",
            "J67",
        ),
    ),
    "rheumatic": CharlsonCategory(
        name="Rheumatic disease",
        weight=1,
        icd10_prefixes=("M05", "M06", "M31.5", "M32", "M33", "M34", "M35.1", "M35.3", "M36.0"),
    ),
    "peptic_ulcer": CharlsonCategory(
        name="Peptic ulcer disease",
        weight=1,
        icd10_prefixes=("K25", "K26", "K27", "K28"),
    ),
    "liver_mild": CharlsonCategory(
        name="Mild liver disease",
        weight=1,
        icd10_prefixes=(
            "B18",
            "K70.0",
            "K70.1",
            "K70.2",
            "K70.3",
            "K70.9",
            "K71.3",
            "K71.4",
            "K71.5",
            "K73",
            "K74",
            "K76.0",
            "K76.2",
            "K76.3",
            "K76.4",
            "K76.8",
            "K76.9",
            "Z94.4",
        ),
    ),
    "diabetes_uncomplicated": CharlsonCategory(
        name="Diabetes without chronic complications",
        weight=1,
        icd10_prefixes=(
            "E10.0",
            "E10.1",
            "E10.6",
            "E10.8",
            "E10.9",
            "E11.0",
            "E11.1",
            "E11.6",
            "E11.8",
            "E11.9",
            "E12.0",
            "E12.1",
            "E12.6",
            "E12.8",
            "E12.9",
            "E13.0",
            "E13.1",
            "E13.6",
            "E13.8",
            "E13.9",
            "E14.0",
            "E14.1",
            "E14.6",
            "E14.8",
            "E14.9",
        ),
    ),
    "diabetes_complicated": CharlsonCategory(
        name="Diabetes with chronic complications",
        weight=2,
        icd10_prefixes=(
            "E10.2",
            "E10.3",
            "E10.4",
            "E10.5",
            "E10.7",
            "E11.2",
            "E11.3",
            "E11.4",
            "E11.5",
            "E11.7",
            "E12.2",
            "E12.3",
            "E12.4",
            "E12.5",
            "E12.7",
            "E13.2",
            "E13.3",
            "E13.4",
            "E13.5",
            "E13.7",
            "E14.2",
            "E14.3",
            "E14.4",
            "E14.5",
            "E14.7",
        ),
    ),
    "hemiplegia": CharlsonCategory(
        name="Hemiplegia or paraplegia",
        weight=2,
        icd10_prefixes=(
            "G04.1",
            "G11.4",
            "G80.1",
            "G80.2",
            "G81",
            "G82",
            "G83.0",
            "G83.1",
            "G83.2",
            "G83.3",
            "G83.4",
            "G83.9",
        ),
    ),
    "renal": CharlsonCategory(
        name="Renal disease",
        weight=2,
        icd10_prefixes=(
            "I12.0",
            "I13.1",
            "N03.2",
            "N03.3",
            "N03.4",
            "N03.5",
            "N03.6",
            "N03.7",
            "N05.2",
            "N05.3",
            "N05.4",
            "N05.5",
            "N05.6",
            "N05.7",
            "N18",
            "N19",
            "N25.0",
            "Z49.0",
            "Z49.1",
            "Z49.2",
            "Z94.0",
            "Z99.2",
        ),
    ),
    "cancer": CharlsonCategory(
        name="Any malignancy",
        weight=2,
        icd10_prefixes=(
            "C00",
            "C01",
            "C02",
            "C03",
            "C04",
            "C05",
            "C06",
            "C07",
            "C08",
            "C09",
            "C10",
            "C11",
            "C12",
            "C13",
            "C14",
            "C15",
            "C16",
            "C17",
            "C18",
            "C19",
            "C20",
            "C21",
            "C22",
            "C23",
            "C24",
            "C25",
            "C26",
            "C30",
            "C31",
            "C32",
            "C33",
            "C34",
            "C37",
            "C38",
            "C39",
            "C40",
            "C41",
            "C43",
            "C45",
            "C46",
            "C47",
            "C48",
            "C49",
            "C50",
            "C51",
            "C52",
            "C53",
            "C54",
            "C55",
            "C56",
            "C57",
            "C58",
            "C60",
            "C61",
            "C62",
            "C63",
            "C64",
            "C65",
            "C66",
            "C67",
            "C68",
            "C69",
            "C70",
            "C71",
            "C72",
            "C73",
            "C74",
            "C75",
            "C76",
            "C81",
            "C82",
            "C83",
            "C84",
            "C85",
            "C88",
            "C90",
            "C91",
            "C92",
            "C93",
            "C94",
            "C95",
            "C96",
            "C97",
        ),
    ),
    "liver_severe": CharlsonCategory(
        name="Moderate or severe liver disease",
        weight=3,
        icd10_prefixes=(
            "I85.0",
            "I85.9",
            "I86.4",
            "I98.2",
            "K70.4",
            "K71.1",
            "K72.1",
            "K72.9",
            "K76.5",
            "K76.6",
            "K76.7",
        ),
    ),
    "metastatic_cancer": CharlsonCategory(
        name="Metastatic solid tumour",
        weight=6,
        icd10_prefixes=("C77", "C78", "C79", "C80"),
    ),
    "hiv": CharlsonCategory(
        name="AIDS/HIV",
        weight=6,
        icd10_prefixes=("B20", "B21", "B22", "B24"),
    ),
}


def _code_matches_any_prefix(code: str, prefixes: tuple[str, ...]) -> bool:
    """Check if an ICD-10 code matches any of the given prefixes."""
    return any(code.startswith(p) for p in prefixes)


def compute_charlson_categories(icd10_codes: list[str]) -> dict[str, bool]:
    """Determine which Charlson categories are present for a set of ICD-10 codes.

    Args:
        icd10_codes: List of ICD-10 codes (e.g., ["I21.0", "E11.9", "N18.3"]).

    Returns:
        Dictionary mapping category name to boolean presence.
    """
    result: dict[str, bool] = {}
    for cat_key, cat in CHARLSON_CATEGORIES.items():
        result[cat_key] = any(
            _code_matches_any_prefix(code, cat.icd10_prefixes) for code in icd10_codes
        )
    return result


def compute_charlson_index(icd10_codes: list[str]) -> int:
    """Compute the Charlson Comorbidity Index from a list of ICD-10 codes.

    Uses the Quan-adapted weighting scheme (Quan et al., 2005). Higher-weight
    categories supersede lower-weight categories for the same organ system:
    - Complicated diabetes (weight=2) supersedes uncomplicated (weight=1)
    - Severe liver disease (weight=3) supersedes mild (weight=1)
    - Metastatic cancer (weight=6) supersedes any malignancy (weight=2)

    Args:
        icd10_codes: List of ICD-10 codes.

    Returns:
        Charlson Comorbidity Index (non-negative integer).
    """
    categories = compute_charlson_categories(icd10_codes)
    score = 0

    for cat_key, present in categories.items():
        if not present:
            continue

        # Apply hierarchy rules: higher-severity supersedes lower
        cat = CHARLSON_CATEGORIES[cat_key]

        if cat_key == "diabetes_uncomplicated" and categories.get("diabetes_complicated"):
            continue
        if cat_key == "liver_mild" and categories.get("liver_severe"):
            continue
        if cat_key == "cancer" and categories.get("metastatic_cancer"):
            continue

        score += cat.weight

    return score


def get_category_names() -> list[str]:
    """Return sorted list of all Charlson category keys."""
    return sorted(CHARLSON_CATEGORIES.keys())
