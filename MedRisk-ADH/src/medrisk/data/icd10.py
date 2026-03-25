"""ICD-10 codelist and lookup utilities for underwriting-relevant conditions.

Curated for cardiovascular disease, type 2 diabetes, and Charlson comorbidity
categories. Codes follow ICD-10-CM with notes where ICD-10-GM (German
modification) differs.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

ICD10_PATTERN = re.compile(r"^[A-Z]\d{2}(\.\d{1,4})?$")


@dataclass(frozen=True)
class ICD10Code:
    """A single ICD-10 code with metadata."""

    code: str
    description: str
    chapter: str
    block: str
    category: str


# --- Curated codelist ---

CODELIST: dict[str, ICD10Code] = {}


def _register(code: str, description: str, chapter: str, block: str, category: str) -> None:
    CODELIST[code] = ICD10Code(code, description, chapter, block, category)


# Cardiovascular (Chapter IX: I00-I99)
_register("I10", "Essential hypertension", "IX", "I10-I16", "hypertension")
_register(
    "I11.9", "Hypertensive heart disease without heart failure", "IX", "I10-I16", "hypertension"
)
_register("I20.0", "Unstable angina", "IX", "I20-I25", "ihd")
_register("I21.0", "Acute ST-elevation MI, anterior wall", "IX", "I20-I25", "mi")
_register("I21.1", "Acute ST-elevation MI, inferior wall", "IX", "I20-I25", "mi")
_register("I21.4", "Acute subendocardial MI (NSTEMI)", "IX", "I20-I25", "mi")
_register("I21.9", "Acute MI, unspecified", "IX", "I20-I25", "mi")
_register("I25.1", "Atherosclerotic heart disease", "IX", "I20-I25", "ihd")
_register("I25.10", "ASHD of native coronary artery", "IX", "I20-I25", "ihd")
_register("I48.0", "Paroxysmal atrial fibrillation", "IX", "I44-I49", "afib")
_register("I48.1", "Persistent atrial fibrillation", "IX", "I44-I49", "afib")
_register("I48.91", "Unspecified atrial fibrillation", "IX", "I44-I49", "afib")
_register("I50.0", "Congestive heart failure", "IX", "I50-I52", "hf")
_register("I50.1", "Left ventricular failure", "IX", "I50-I52", "hf")
_register("I50.9", "Heart failure, unspecified", "IX", "I50-I52", "hf")
_register("I63.9", "Cerebral infarction, unspecified", "IX", "I60-I69", "stroke")
_register("I65.2", "Carotid artery occlusion/stenosis", "IX", "I60-I69", "cvd")
_register("I70.0", "Atherosclerosis of aorta", "IX", "I70-I79", "pvd")
_register("I73.9", "Peripheral vascular disease, unspecified", "IX", "I70-I79", "pvd")

# Diabetes and metabolic (Chapter IV: E00-E90)
_register("E11.0", "T2D with hyperosmolarity", "IV", "E10-E14", "diabetes")
_register("E11.2", "T2D with kidney complications", "IV", "E10-E14", "diabetes")
_register("E11.21", "T2D with diabetic nephropathy", "IV", "E10-E14", "diabetes_renal")
_register("E11.3", "T2D with ophthalmic complications", "IV", "E10-E14", "diabetes")
_register("E11.311", "T2D with diabetic retinopathy", "IV", "E10-E14", "diabetes_eye")
_register("E11.4", "T2D with neurological complications", "IV", "E10-E14", "diabetes")
_register("E11.5", "T2D with circulatory complications", "IV", "E10-E14", "diabetes")
_register("E11.65", "T2D with hyperglycemia", "IV", "E10-E14", "diabetes")
_register("E11.9", "T2D without complications", "IV", "E10-E14", "diabetes")
_register("E78.0", "Pure hypercholesterolemia", "IV", "E70-E90", "dyslipidemia")
_register("E78.1", "Pure hypertriglyceridemia", "IV", "E70-E90", "dyslipidemia")
_register("E78.2", "Mixed hyperlipidemia", "IV", "E70-E90", "dyslipidemia")
_register("E78.5", "Dyslipidemia, unspecified", "IV", "E70-E90", "dyslipidemia")
_register("E66.0", "Obesity due to excess calories", "IV", "E65-E68", "obesity")
_register("E66.9", "Obesity, unspecified", "IV", "E65-E68", "obesity")
_register("R73.03", "Prediabetes", "XVIII", "R70-R79", "prediabetes")

# Renal (Chapter XIV: N00-N99)
_register("N18.1", "CKD stage 1", "XIV", "N17-N19", "ckd")
_register("N18.2", "CKD stage 2", "XIV", "N17-N19", "ckd")
_register("N18.3", "CKD stage 3", "XIV", "N17-N19", "ckd")
_register("N18.4", "CKD stage 4", "XIV", "N17-N19", "ckd")
_register("N18.5", "CKD stage 5", "XIV", "N17-N19", "ckd")
_register("N18.6", "ESRD", "XIV", "N17-N19", "ckd")

# Respiratory (Chapter X: J00-J99)
_register("J44.0", "COPD with acute lower resp infection", "X", "J40-J47", "copd")
_register("J44.1", "COPD with acute exacerbation", "X", "J40-J47", "copd")
_register("J44.9", "COPD, unspecified", "X", "J40-J47", "copd")
_register("J45.9", "Asthma, unspecified", "X", "J40-J47", "asthma")

# Neoplasms (Chapter II: C00-D49)
_register("C34.9", "Lung cancer, unspecified", "II", "C30-C39", "cancer")
_register("C50.9", "Breast cancer, unspecified", "II", "C50", "cancer")
_register("C61", "Prostate cancer", "II", "C60-C63", "cancer")
_register("C18.9", "Colon cancer, unspecified", "II", "C15-C26", "cancer")

# Liver (Chapter XI: K00-K93)
_register("K70.3", "Alcoholic cirrhosis", "XI", "K70-K77", "liver_mild")
_register("K74.6", "Other cirrhosis of liver", "XI", "K70-K77", "liver_severe")
_register("K76.0", "Fatty liver, not elsewhere classified", "XI", "K70-K77", "liver_mild")

# Mental and behavioural (Chapter V: F00-F99)
_register("F10.2", "Alcohol dependence", "V", "F10-F19", "substance")
_register("F17.21", "Nicotine dependence, cigarettes", "V", "F10-F19", "substance")
_register("F32.9", "Major depressive disorder, unspecified", "V", "F30-F39", "depression")
_register("F41.1", "Generalized anxiety disorder", "V", "F40-F48", "anxiety")

# Musculoskeletal (Chapter XIII: M00-M99)
_register("M17.9", "Osteoarthritis of knee, unspecified", "XIII", "M15-M19", "msk")
_register("M54.5", "Low back pain", "XIII", "M50-M54", "msk")

# HIV/AIDS
_register("B20", "HIV disease", "I", "B20-B24", "hiv")

# Dementia (non-Alzheimer)
_register("F03.9", "Dementia, unspecified", "V", "F00-F09", "dementia")

# Alzheimer's disease
_register("G30.0", "Alzheimer disease with early onset", "VI", "G30-G32", "alzheimer_early")
_register("G30.1", "Alzheimer disease with late onset", "VI", "G30-G32", "alzheimer_late")
_register("G30.8", "Other Alzheimer disease", "VI", "G30-G32", "alzheimer")
_register("G30.9", "Alzheimer disease, unspecified", "VI", "G30-G32", "alzheimer")
# ICD-10-GM codes (German modification) for dementia in Alzheimer's
_register("F00.0", "Dementia in Alzheimer, early onset", "V", "F00-F09", "alzheimer_early")
_register("F00.1", "Dementia in Alzheimer, late onset", "V", "F00-F09", "alzheimer_late")
_register("F00.2", "Dementia in Alzheimer, atypical or mixed", "V", "F00-F09", "alzheimer")
_register("F00.9", "Dementia in Alzheimer, unspecified", "V", "F00-F09", "alzheimer")

# Hemiplegia
_register("G81.9", "Hemiplegia, unspecified", "VI", "G80-G83", "hemiplegia")

# Rheumatic
_register("M05.79", "RA with rheumatoid factor, unspecified", "XIII", "M05-M14", "rheumatic")
_register("M32.9", "SLE, unspecified", "XIII", "M30-M36", "rheumatic")

# Peptic ulcer
_register("K25.9", "Gastric ulcer, unspecified", "XI", "K20-K31", "peptic_ulcer")
_register("K27.9", "Peptic ulcer, unspecified", "XI", "K20-K31", "peptic_ulcer")


# --- Lookup functions ---


def validate_icd10(code: str) -> bool:
    """Check if a string is a valid ICD-10 format."""
    return bool(ICD10_PATTERN.match(code))


def lookup(code: str) -> ICD10Code | None:
    """Look up a code in the curated codelist."""
    return CODELIST.get(code)


def get_codes_by_category(category: str) -> list[ICD10Code]:
    """Return all codes belonging to a clinical category."""
    return [c for c in CODELIST.values() if c.category == category]


def get_codes_by_chapter(chapter: str) -> list[ICD10Code]:
    """Return all codes belonging to an ICD-10 chapter."""
    return [c for c in CODELIST.values() if c.chapter == chapter]


def get_codes_by_block(block: str) -> list[ICD10Code]:
    """Return all codes belonging to an ICD-10 block."""
    return [c for c in CODELIST.values() if c.block == block]


def code_matches_prefix(code: str, prefix: str) -> bool:
    """Check if an ICD-10 code starts with a given prefix.

    Useful for mapping codes to Charlson categories, which are defined
    by 3-character prefixes.
    """
    return code.startswith(prefix)


def get_all_categories() -> list[str]:
    """Return sorted list of unique clinical categories."""
    return sorted({c.category for c in CODELIST.values()})


def get_all_codes() -> list[str]:
    """Return all registered ICD-10 codes."""
    return list(CODELIST.keys())
