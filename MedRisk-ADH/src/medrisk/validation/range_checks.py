"""Physiological range and unit validation for lab values.

Checks that lab results fall within physiologically plausible ranges
and detects likely unit conversion errors (e.g., HbA1c in % vs mmol/mol).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RangeCheckResult:
    """Result of physiological range validation.

    Attributes:
        violations: List of (feature_name, value, reason) tuples.
        suspected_unit_errors: List of (feature_name, value, suspected_unit).
        range_score: Fraction of checked values within plausible range [0, 1].
        n_checked: Number of values checked.
    """

    violations: list[tuple[str, float, str]] = field(default_factory=list)
    suspected_unit_errors: list[tuple[str, float, str]] = field(default_factory=list)
    range_score: float = 1.0
    n_checked: int = 0


# Physiological limits: (min, max) for each lab feature
PHYSIOLOGICAL_LIMITS: dict[str, tuple[float, float]] = {
    "lab_hba1c": (2.0, 20.0),
    "lab_creatinine": (0.1, 30.0),
    "lab_egfr": (2.0, 200.0),
    "lab_total_cholesterol": (50.0, 600.0),
    "lab_hdl": (5.0, 150.0),
    "lab_ldl": (5.0, 400.0),
    "lab_triglycerides": (10.0, 2000.0),
    "lab_systolic_bp": (50.0, 300.0),
    "lab_diastolic_bp": (20.0, 200.0),
    "lab_nt_probnp": (0.0, 50000.0),
}

# Unit conversion detection rules
UNIT_CONVERSIONS: dict[str, dict] = {
    "lab_hba1c": {
        "expected_unit": "%",
        "alt_unit": "mmol/mol",
        "detection_threshold": 20.0,
        "description": "Value > 20 suggests mmol/mol instead of %",
    },
    "lab_egfr": {
        "expected_unit": "mL/min/1.73m2",
        "alt_unit": "L/min/1.73m2",
        "detection_threshold": 0.5,
        "description": "Value < 0.5 suggests L/min instead of mL/min",
    },
}


def check_ranges(
    values: dict[str, float | None],
) -> RangeCheckResult:
    """Check lab values against physiological limits.

    Args:
        values: Dict mapping feature names to values. None values are skipped.

    Returns:
        RangeCheckResult with violations, suspected unit errors, and score.
    """
    violations: list[tuple[str, float, str]] = []
    unit_errors: list[tuple[str, float, str]] = []
    n_checked = 0

    for feature, value in values.items():
        if value is None:
            continue

        limits = PHYSIOLOGICAL_LIMITS.get(feature)
        if limits is None:
            continue

        n_checked += 1
        lo, hi = limits

        if value < lo or value > hi:
            violations.append(
                (
                    feature,
                    value,
                    f"Outside range [{lo}, {hi}]",
                )
            )

        # Check for unit conversion errors
        conv = UNIT_CONVERSIONS.get(feature)
        if conv is not None:
            threshold = conv["detection_threshold"]
            if feature == "lab_hba1c" and value > threshold or feature == "lab_egfr" and value < threshold:
                unit_errors.append((feature, value, conv["alt_unit"]))

    range_score = 1.0
    if n_checked > 0:
        n_valid = n_checked - len(violations)
        range_score = n_valid / n_checked

    return RangeCheckResult(
        violations=violations,
        suspected_unit_errors=unit_errors,
        range_score=round(range_score, 4),
        n_checked=n_checked,
    )


def check_patient_ranges(patient_row: dict) -> RangeCheckResult:
    """Check a patient record's lab values against physiological limits.

    Args:
        patient_row: Dict-like with lab_* keys.

    Returns:
        RangeCheckResult.
    """
    lab_values = {k: v for k, v in patient_row.items() if k.startswith("lab_") and v is not None}
    return check_ranges(lab_values)
