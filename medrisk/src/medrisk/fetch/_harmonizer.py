"""
_harmonizer.py — Post-parse normalisation: unit conversion, code mapping, stub-person creation.

Applied by PipelineRunner after adapter.parse() to ensure cross-source comparability.
"""

from __future__ import annotations

import logging

from medrisk.fetch._schema import CohortDataset, Event, Measurement, Person

_log = logging.getLogger(__name__)

# (source_unit, target_unit) -> multiplicative factor
_UNIT_CONVERSIONS: dict[tuple[str, str], float] = {
    ("mmol/l", "mg/dl"): 18.0182,
    ("mmol_l", "mg_dl"): 18.0182,
    ("mg/dl", "mmol/l"): 1 / 18.0182,
    ("mg_dl", "mmol_l"): 1 / 18.0182,
    ("kg/m2", "kg_m2"): 1.0,
    ("mmhg", "mmhg"): 1.0,  # identity -- normalise spelling
}

# ICD-9 prefix -> ICD-10 prefix (simplified; full mapping lives in filters.yml)
_ICD9_TO_ICD10_PREFIX: dict[str, str] = {
    "250": "E11",  # diabetes (simplified to T2DM; adapters set correct type)
    "401": "I10",  # essential hypertension
    "410": "I21",  # MI
    "428": "I50",  # heart failure
    "434": "I63",  # stroke
    "585": "N18",  # CKD
}

# Canonical measure_type names and their canonical unit
_CANONICAL_UNITS: dict[str, str] = {
    "glucose_mg_dl": "mg/dL",
    "glucose_mmol_l": "mmol/L",
    "hba1c_pct": "%",
    "sbp_mmhg": "mmHg",
    "dbp_mmhg": "mmHg",
    "bmi_kg_m2": "kg/m2",
    "weight_kg": "kg",
    "height_cm": "cm",
    "ldl_mg_dl": "mg/dL",
    "hdl_mg_dl": "mg/dL",
    "triglycerides_mg_dl": "mg/dL",
    "creatinine_mg_dl": "mg/dL",
    "egfr_ml_min_1_73m2": "mL/min/1.73m2",
}


class Harmonizer:
    """
    Applies normalisation rules to a CohortDataset.
    Returns a new CohortDataset; does not mutate in place.
    """

    def normalize_all(self, dataset: CohortDataset) -> CohortDataset:
        persons = self.fill_missing_persons(dataset.measurements, list(dataset.persons))
        measurements = self.normalize_units(list(dataset.measurements))
        events = dataset.events  # code mapping is opt-in (see map_codes)
        treatments = dataset.treatments
        return CohortDataset(
            persons=persons,
            measurements=measurements,
            events=list(events),
            treatments=list(treatments),
        )

    def normalize_units(self, measurements: list[Measurement]) -> list[Measurement]:
        """Normalise unit spellings to canonical form (e.g. 'mg/dl' -> 'mg/dL')."""
        result = []
        for m in measurements:
            canonical = _CANONICAL_UNITS.get(m.measure_type)
            if canonical and m.unit.lower().replace(" ", "") != canonical.lower().replace(" ", ""):
                key = (m.unit.lower().replace(" ", ""), canonical.lower().replace(" ", ""))
                factor = _UNIT_CONVERSIONS.get(key, 1.0)
                m = m.model_copy(update={"value": m.value * factor, "unit": canonical})
            result.append(m)
        return result

    def map_codes(
        self,
        events: list[Event],
        code_map: dict[str, str] | None = None,
    ) -> list[Event]:
        """
        Translate event codes using a provided mapping dict or the built-in ICD9->ICD10 prefix map.
        code_map: {old_code: new_code}
        """
        if code_map is None:
            code_map = {}

        result = []
        for e in events:
            new_code = code_map.get(e.code)
            if new_code:
                e = e.model_copy(update={"code": new_code, "code_system": "ICD10"})
            elif e.code_system in ("ICD9", "icd9"):
                prefix = e.code.split(".")[0]
                mapped_prefix = _ICD9_TO_ICD10_PREFIX.get(prefix)
                if mapped_prefix:
                    _log.debug("ICD9->ICD10 prefix mapping: %s -> %s", e.code, mapped_prefix)
                    e = e.model_copy(update={"code": mapped_prefix, "code_system": "ICD10"})
            result.append(e)
        return result

    def fill_missing_persons(
        self,
        measurements: list[Measurement],
        persons: list[Person],
    ) -> list[Person]:
        """Create stub Person records for person_ids that appear in measurements but not in persons."""
        known_ids = {p.person_id for p in persons}
        stub_map: dict[str, Person] = {}
        for m in measurements:
            if m.person_id not in known_ids and m.person_id not in stub_map:
                stub_map[m.person_id] = Person(
                    person_id=m.person_id,
                    source=m.source,
                    dataset_id=m.dataset_id,
                )
        if stub_map:
            _log.debug("Created %d stub Person records from measurements", len(stub_map))
        return persons + list(stub_map.values())
