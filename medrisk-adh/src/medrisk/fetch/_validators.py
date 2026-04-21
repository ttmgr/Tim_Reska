"""
_validators.py — Cross-table integrity checks on a CohortDataset.

Run after harmonization to catch data-quality issues before export.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from medrisk.fetch._schema import CohortDataset

_log = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def __str__(self) -> str:
        lines = []
        for e in self.errors:
            lines.append(f"ERROR: {e}")
        for w in self.warnings:
            lines.append(f"WARNING: {w}")
        return "\n".join(lines) if lines else "OK"


def validate(dataset: CohortDataset) -> ValidationResult:
    """Run all integrity checks and return a ValidationResult."""
    result = ValidationResult()
    person_ids = {p.person_id for p in dataset.persons}

    # Measurements must reference known persons (if persons table is non-empty)
    if person_ids:
        orphan_meas = [m.person_id for m in dataset.measurements if m.person_id not in person_ids]
        if orphan_meas:
            unique = set(orphan_meas)
            result.warnings.append(
                f"{len(unique)} person_id(s) appear in measurements but not in persons table"
                f" (e.g. {next(iter(unique))})"
            )

    # Events must reference known persons
    if person_ids:
        orphan_evts = [e.person_id for e in dataset.events if e.person_id not in person_ids]
        if orphan_evts:
            unique = set(orphan_evts)
            result.warnings.append(
                f"{len(unique)} person_id(s) appear in events but not in persons table"
            )

    # Treatment dates: end >= start
    for t in dataset.treatments:
        if t.end_date is not None and t.end_date < t.start_date:
            result.errors.append(
                f"Treatment for person {t.person_id}: end_date {t.end_date} < start_date {t.start_date}"
            )

    # No negative measurement values for non-signed measures
    _negative_disallowed = {"glucose_mg_dl", "hba1c_pct", "bmi_kg_m2", "sbp_mmhg", "dbp_mmhg"}
    for m in dataset.measurements:
        if m.measure_type in _negative_disallowed and m.value < 0:
            result.errors.append(
                f"Negative value {m.value} for measure_type '{m.measure_type}' (person {m.person_id})"
            )

    if result.errors or result.warnings:
        _log.warning("Validation result:\n%s", result)
    else:
        _log.debug("Validation passed for dataset with %s", dataset.summary())

    return result
