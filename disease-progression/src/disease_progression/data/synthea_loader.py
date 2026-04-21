"""
disease_progression.data.synthea_loader - Load and parse Synthea FHIR bundles.

Synthea (https://github.com/synthetichealth/synthea) generates realistic
synthetic patient records as FHIR R4 JSON bundles.  This module provides:

    1. Parsing of FHIR Bundle JSON files, extracting Patient, Condition,
       Observation, MedicationRequest, Encounter, and Procedure resources.
    2. A convenience wrapper to invoke the Synthea CLI for on-the-fly
       generation of synthetic cohorts.
    3. A fallback synthetic data generator that produces FHIR-like records
       without requiring an external Synthea install -- useful for CI/CD,
       unit tests, and quick demonstrations.

CLI entry point::

    python -m disease_progression.data.synthea_loader \\
        --module cvd --n_patients 5000 --output_dir ./data/raw

The ``--module`` flag maps to a Synthea disease module
(e.g. ``cardiovascular``, ``diabetes``).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import subprocess
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FHIR resource type constants
# ---------------------------------------------------------------------------
RESOURCE_TYPES = (
    "Patient",
    "Condition",
    "Observation",
    "MedicationRequest",
    "Encounter",
    "Procedure",
)

# ---------------------------------------------------------------------------
# Synthea module name mapping
# ---------------------------------------------------------------------------
MODULE_MAP: Dict[str, str] = {
    "cvd": "cardiovascular/chf",
    "cardiovascular": "cardiovascular/chf",
    "diabetes": "metabolic/diabetes",
    "copd": "lung_cancer",
    "ckd": "kidney_disease",
}

# ---------------------------------------------------------------------------
# ICD-10 / SNOMED stubs used by the synthetic fallback generator
# ---------------------------------------------------------------------------
_CVD_CONDITIONS = [
    {"code": "I21.9", "system": "http://hl7.org/fhir/sid/icd-10-cm", "display": "Acute myocardial infarction, unspecified"},
    {"code": "I25.10", "system": "http://hl7.org/fhir/sid/icd-10-cm", "display": "Atherosclerotic heart disease of native coronary artery"},
    {"code": "I50.9", "system": "http://hl7.org/fhir/sid/icd-10-cm", "display": "Heart failure, unspecified"},
    {"code": "I63.9", "system": "http://hl7.org/fhir/sid/icd-10-cm", "display": "Cerebral infarction, unspecified"},
    {"code": "I10", "system": "http://hl7.org/fhir/sid/icd-10-cm", "display": "Essential (primary) hypertension"},
    {"code": "I48.91", "system": "http://hl7.org/fhir/sid/icd-10-cm", "display": "Unspecified atrial fibrillation"},
]

_DIABETES_CONDITIONS = [
    {"code": "E11.9", "system": "http://hl7.org/fhir/sid/icd-10-cm", "display": "Type 2 diabetes mellitus without complications"},
    {"code": "E11.65", "system": "http://hl7.org/fhir/sid/icd-10-cm", "display": "Type 2 DM with hyperglycemia"},
    {"code": "E11.21", "system": "http://hl7.org/fhir/sid/icd-10-cm", "display": "Type 2 DM with diabetic nephropathy"},
    {"code": "E11.311", "system": "http://hl7.org/fhir/sid/icd-10-cm", "display": "Type 2 DM with unspecified diabetic retinopathy with macular edema"},
    {"code": "E78.5", "system": "http://hl7.org/fhir/sid/icd-10-cm", "display": "Dyslipidemia, unspecified"},
]

_LOINC_OBSERVATIONS = [
    {"code": "4548-4", "display": "Hemoglobin A1c", "unit": "%", "low": 4.0, "high": 14.0},
    {"code": "2160-0", "display": "Creatinine [Mass/volume] in Serum", "unit": "mg/dL", "low": 0.5, "high": 4.0},
    {"code": "33762-6", "display": "NT-proBNP", "unit": "pg/mL", "low": 20.0, "high": 5000.0},
    {"code": "2093-3", "display": "Total Cholesterol", "unit": "mg/dL", "low": 120.0, "high": 350.0},
    {"code": "2085-9", "display": "HDL Cholesterol", "unit": "mg/dL", "low": 25.0, "high": 100.0},
    {"code": "13457-7", "display": "LDL Cholesterol (calc)", "unit": "mg/dL", "low": 40.0, "high": 250.0},
    {"code": "2571-8", "display": "Triglycerides", "unit": "mg/dL", "low": 50.0, "high": 500.0},
    {"code": "48642-3", "display": "eGFR (CKD-EPI)", "unit": "mL/min/1.73m2", "low": 15.0, "high": 120.0},
    {"code": "8480-6", "display": "Systolic blood pressure", "unit": "mmHg", "low": 90.0, "high": 200.0},
    {"code": "8462-4", "display": "Diastolic blood pressure", "unit": "mmHg", "low": 50.0, "high": 120.0},
]

_MEDICATION_CODES = [
    {"code": "C07AB02", "system": "ATC", "display": "Metoprolol"},
    {"code": "C09AA02", "system": "ATC", "display": "Enalapril"},
    {"code": "C10AA01", "system": "ATC", "display": "Simvastatin"},
    {"code": "B01AC06", "system": "ATC", "display": "Acetylsalicylic acid"},
    {"code": "A10BA02", "system": "ATC", "display": "Metformin"},
    {"code": "C09CA01", "system": "ATC", "display": "Losartan"},
    {"code": "C10AA05", "system": "ATC", "display": "Atorvastatin"},
    {"code": "B01AF01", "system": "ATC", "display": "Rivaroxaban"},
]


# ===================================================================
# Core loader
# ===================================================================

class SyntheaLoader:
    """Load and parse Synthea-generated FHIR R4 JSON bundles.

    Parameters
    ----------
    data_dir : str or Path
        Directory containing ``*.json`` FHIR bundle files.  Each file is
        expected to be a FHIR Bundle with ``entry`` containing heterogeneous
        resource types.
    resource_types : sequence of str, optional
        Which FHIR resource types to extract.  Defaults to
        ``RESOURCE_TYPES``.
    """

    def __init__(
        self,
        data_dir: str | Path,
        resource_types: Sequence[str] = RESOURCE_TYPES,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.resource_types = set(resource_types)
        self._bundles: List[Dict[str, Any]] = []
        self._resources: Dict[str, List[Dict[str, Any]]] = {rt: [] for rt in self.resource_types}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> "SyntheaLoader":
        """Scan ``data_dir`` for FHIR JSON bundles and parse them.

        Returns self for fluent chaining.
        """
        json_files = sorted(self.data_dir.glob("*.json"))
        if not json_files:
            logger.warning("No JSON files found in %s", self.data_dir)
            return self

        logger.info("Loading %d FHIR bundle files from %s", len(json_files), self.data_dir)
        for fpath in json_files:
            try:
                bundle = self._read_bundle(fpath)
                self._bundles.append(bundle)
                self._extract_resources(bundle)
            except (json.JSONDecodeError, KeyError) as exc:
                logger.warning("Skipping %s: %s", fpath.name, exc)
        logger.info(
            "Extracted resources: %s",
            {k: len(v) for k, v in self._resources.items()},
        )
        return self

    def get_resources(self, resource_type: str) -> List[Dict[str, Any]]:
        """Return all parsed resources of the given FHIR type."""
        return self._resources.get(resource_type, [])

    def patients_dataframe(self) -> pd.DataFrame:
        """Return a DataFrame of parsed Patient resources.

        Columns: patient_id, birth_date, death_date, gender,
                 race, ethnicity, city, state, country.
        """
        rows: List[Dict[str, Any]] = []
        for pt in self.get_resources("Patient"):
            row: Dict[str, Any] = {
                "patient_id": pt.get("id", ""),
                "birth_date": pt.get("birthDate"),
                "death_date": pt.get("deceasedDateTime"),
                "gender": pt.get("gender"),
            }
            # Extract race / ethnicity from US-Core extensions
            for ext in pt.get("extension", []):
                url = ext.get("url", "")
                if "us-core-race" in url:
                    row["race"] = _extension_display(ext)
                elif "us-core-ethnicity" in url:
                    row["ethnicity"] = _extension_display(ext)
            # Address
            addresses = pt.get("address", [])
            if addresses:
                addr = addresses[0]
                row["city"] = addr.get("city")
                row["state"] = addr.get("state")
                row["country"] = addr.get("country", "US")
            rows.append(row)
        return pd.DataFrame(rows)

    def conditions_dataframe(self) -> pd.DataFrame:
        """Return a DataFrame of parsed Condition resources.

        Columns: patient_id, condition_code, code_system, display,
                 onset_date, abatement_date, clinical_status.
        """
        rows: List[Dict[str, Any]] = []
        for cond in self.get_resources("Condition"):
            coding = _first_coding(cond.get("code", {}))
            rows.append(
                {
                    "patient_id": _reference_id(cond.get("subject", {})),
                    "condition_code": coding.get("code"),
                    "code_system": coding.get("system"),
                    "display": coding.get("display"),
                    "onset_date": cond.get("onsetDateTime"),
                    "abatement_date": cond.get("abatementDateTime"),
                    "clinical_status": _codeable_code(cond.get("clinicalStatus", {})),
                }
            )
        return pd.DataFrame(rows)

    def observations_dataframe(self) -> pd.DataFrame:
        """Return a DataFrame of parsed Observation resources.

        Columns: patient_id, observation_code, code_system, display,
                 value, unit, effective_date.
        """
        rows: List[Dict[str, Any]] = []
        for obs in self.get_resources("Observation"):
            coding = _first_coding(obs.get("code", {}))
            value, unit = _extract_quantity(obs)
            rows.append(
                {
                    "patient_id": _reference_id(obs.get("subject", {})),
                    "observation_code": coding.get("code"),
                    "code_system": coding.get("system"),
                    "display": coding.get("display"),
                    "value": value,
                    "unit": unit,
                    "effective_date": obs.get("effectiveDateTime"),
                }
            )
        return pd.DataFrame(rows)

    def medications_dataframe(self) -> pd.DataFrame:
        """Return a DataFrame of parsed MedicationRequest resources.

        Columns: patient_id, medication_code, code_system, display,
                 authored_on, status.
        """
        rows: List[Dict[str, Any]] = []
        for med in self.get_resources("MedicationRequest"):
            coding = _first_coding(med.get("medicationCodeableConcept", {}))
            rows.append(
                {
                    "patient_id": _reference_id(med.get("subject", {})),
                    "medication_code": coding.get("code"),
                    "code_system": coding.get("system"),
                    "display": coding.get("display"),
                    "authored_on": med.get("authoredOn"),
                    "status": med.get("status"),
                }
            )
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _read_bundle(path: Path) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if data.get("resourceType") != "Bundle":
            raise ValueError(f"{path.name} is not a FHIR Bundle")
        return data

    def _extract_resources(self, bundle: Dict[str, Any]) -> None:
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            rtype = resource.get("resourceType")
            if rtype in self.resource_types:
                self._resources[rtype].append(resource)


# ===================================================================
# Synthea CLI wrapper
# ===================================================================

def run_synthea(
    module: str = "cardiovascular/chf",
    n_patients: int = 100,
    output_dir: str | Path = "./data/raw",
    synthea_jar: str | Path | None = None,
    seed: int = 42,
) -> Path:
    """Invoke the Synthea CLI to generate synthetic FHIR bundles.

    Parameters
    ----------
    module : str
        Synthea module name (e.g. ``cardiovascular/chf``).
    n_patients : int
        Number of patient records to generate.
    output_dir : str or Path
        Directory for generated FHIR JSON files.
    synthea_jar : str, Path, or None
        Path to ``synthea-with-dependencies.jar``.  If *None*, the
        function looks for ``SYNTHEA_JAR`` in the environment.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    Path
        The directory containing generated FHIR JSON files.

    Raises
    ------
    FileNotFoundError
        If the Synthea JAR cannot be located.
    subprocess.CalledProcessError
        If the Synthea process exits with a non-zero code.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if synthea_jar is None:
        synthea_jar = os.environ.get("SYNTHEA_JAR")
    if synthea_jar is None or not Path(synthea_jar).is_file():
        raise FileNotFoundError(
            "Synthea JAR not found.  Set SYNTHEA_JAR env var or pass "
            "synthea_jar= explicitly.  Alternatively, call "
            "generate_synthetic_fhir() for a lightweight fallback."
        )

    fhir_output = output_dir / "fhir"
    cmd = [
        "java", "-jar", str(synthea_jar),
        "-p", str(n_patients),
        "-m", module,
        "-s", str(seed),
        "--exporter.fhir.export", "true",
        "--exporter.baseDirectory", str(output_dir),
    ]
    logger.info("Running Synthea: %s", " ".join(cmd))
    subprocess.check_call(cmd)
    return fhir_output


# ===================================================================
# Lightweight synthetic FHIR generator (no external dependencies)
# ===================================================================

def generate_synthetic_fhir(
    n_patients: int = 100,
    module: str = "cvd",
    output_dir: str | Path | None = None,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """Generate simple synthetic FHIR-like bundles for demo / testing.

    This does **not** require a Synthea install.  It creates plausible
    but simplified patient bundles with conditions, observations, and
    medications drawn from curated code lists.

    Parameters
    ----------
    n_patients : int
        Number of synthetic patients.
    module : str
        ``"cvd"`` or ``"diabetes"`` -- determines the condition / lab
        distributions used.
    output_dir : str, Path, or None
        If provided, each bundle is written as a JSON file to this
        directory.  Otherwise bundles are returned in-memory only.
    seed : int
        Random seed.

    Returns
    -------
    list of dict
        List of FHIR Bundle dicts, one per patient.
    """
    rng = np.random.default_rng(seed)
    random.seed(seed)

    conditions = _CVD_CONDITIONS if module in ("cvd", "cardiovascular") else _DIABETES_CONDITIONS
    bundles: List[Dict[str, Any]] = []

    if output_dir is not None:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    for i in range(n_patients):
        patient_id = str(uuid.uuid4())
        birth_year = int(rng.integers(1940, 1990))
        birth_date = f"{birth_year}-{int(rng.integers(1, 13)):02d}-{int(rng.integers(1, 29)):02d}"
        gender = rng.choice(["male", "female"])
        is_deceased = rng.random() < 0.08
        death_dt = None
        if is_deceased:
            death_year = int(rng.integers(birth_year + 50, 2026))
            death_dt = f"{death_year}-{int(rng.integers(1, 13)):02d}-{int(rng.integers(1, 29)):02d}T00:00:00Z"

        patient_resource = _make_patient(patient_id, birth_date, gender, death_dt)

        entries: List[Dict[str, Any]] = [{"resource": patient_resource}]

        # Assign 1-4 conditions
        n_cond = int(rng.integers(1, 5))
        chosen_conds = rng.choice(len(conditions), size=min(n_cond, len(conditions)), replace=False)
        for ci in chosen_conds:
            cond = conditions[ci]
            onset_year = int(rng.integers(max(birth_year + 30, 2000), 2025))
            onset_dt = f"{onset_year}-{int(rng.integers(1, 13)):02d}-{int(rng.integers(1, 29)):02d}T00:00:00Z"
            entries.append({"resource": _make_condition(patient_id, cond, onset_dt)})

        # Observations -- 5-20 lab results spread over time
        n_obs = int(rng.integers(5, 21))
        for _ in range(n_obs):
            lab = random.choice(_LOINC_OBSERVATIONS)
            obs_year = int(rng.integers(max(birth_year + 30, 2010), 2025))
            eff_dt = f"{obs_year}-{int(rng.integers(1, 13)):02d}-{int(rng.integers(1, 29)):02d}T00:00:00Z"
            value = float(rng.uniform(lab["low"], lab["high"]))
            entries.append({"resource": _make_observation(patient_id, lab, value, eff_dt)})

        # Medications -- 0-4
        n_med = int(rng.integers(0, 5))
        chosen_meds = rng.choice(len(_MEDICATION_CODES), size=min(n_med, len(_MEDICATION_CODES)), replace=False)
        for mi in chosen_meds:
            med = _MEDICATION_CODES[mi]
            auth_year = int(rng.integers(max(birth_year + 30, 2010), 2025))
            auth_dt = f"{auth_year}-{int(rng.integers(1, 13)):02d}-{int(rng.integers(1, 29)):02d}T00:00:00Z"
            entries.append({"resource": _make_medication_request(patient_id, med, auth_dt)})

        bundle: Dict[str, Any] = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": entries,
        }
        bundles.append(bundle)

        if output_dir is not None:
            out_path = Path(output_dir) / f"patient_{i:06d}.json"
            with open(out_path, "w", encoding="utf-8") as fh:
                json.dump(bundle, fh, indent=2)

    logger.info("Generated %d synthetic FHIR bundles (module=%s)", n_patients, module)
    return bundles


# -------------------------------------------------------------------
# FHIR resource builders (private)
# -------------------------------------------------------------------

def _make_patient(
    patient_id: str,
    birth_date: str,
    gender: str,
    death_datetime: str | None,
) -> Dict[str, Any]:
    resource: Dict[str, Any] = {
        "resourceType": "Patient",
        "id": patient_id,
        "birthDate": birth_date,
        "gender": gender,
        "extension": [
            {
                "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
                "extension": [
                    {"url": "text", "valueString": random.choice(["White", "Black", "Asian", "Other"])},
                ],
            },
            {
                "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity",
                "extension": [
                    {"url": "text", "valueString": random.choice(["Not Hispanic or Latino", "Hispanic or Latino"])},
                ],
            },
        ],
        "address": [
            {"city": "Springfield", "state": random.choice(["MA", "IL", "OH", "CA", "TX"]), "country": "US"},
        ],
    }
    if death_datetime is not None:
        resource["deceasedDateTime"] = death_datetime
    return resource


def _make_condition(
    patient_id: str,
    code_info: Dict[str, str],
    onset_dt: str,
) -> Dict[str, Any]:
    return {
        "resourceType": "Condition",
        "id": str(uuid.uuid4()),
        "subject": {"reference": f"Patient/{patient_id}"},
        "code": {
            "coding": [
                {
                    "system": code_info["system"],
                    "code": code_info["code"],
                    "display": code_info["display"],
                }
            ]
        },
        "onsetDateTime": onset_dt,
        "clinicalStatus": {
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]
        },
    }


def _make_observation(
    patient_id: str,
    lab: Dict[str, Any],
    value: float,
    effective_dt: str,
) -> Dict[str, Any]:
    return {
        "resourceType": "Observation",
        "id": str(uuid.uuid4()),
        "status": "final",
        "subject": {"reference": f"Patient/{patient_id}"},
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": lab["code"],
                    "display": lab["display"],
                }
            ]
        },
        "valueQuantity": {
            "value": round(value, 2),
            "unit": lab["unit"],
            "system": "http://unitsofmeasure.org",
        },
        "effectiveDateTime": effective_dt,
    }


def _make_medication_request(
    patient_id: str,
    med: Dict[str, str],
    authored_on: str,
) -> Dict[str, Any]:
    return {
        "resourceType": "MedicationRequest",
        "id": str(uuid.uuid4()),
        "status": "active",
        "intent": "order",
        "subject": {"reference": f"Patient/{patient_id}"},
        "medicationCodeableConcept": {
            "coding": [
                {
                    "system": f"http://www.whocc.no/atc" if med["system"] == "ATC" else med["system"],
                    "code": med["code"],
                    "display": med["display"],
                }
            ]
        },
        "authoredOn": authored_on,
    }


# -------------------------------------------------------------------
# FHIR parsing helpers
# -------------------------------------------------------------------

def _first_coding(codeable_concept: Dict[str, Any]) -> Dict[str, str]:
    """Return the first coding entry from a CodeableConcept, or empty dict."""
    codings = codeable_concept.get("coding", [])
    return codings[0] if codings else {}


def _codeable_code(codeable_concept: Dict[str, Any]) -> Optional[str]:
    coding = _first_coding(codeable_concept)
    return coding.get("code")


def _reference_id(reference: Dict[str, Any]) -> str:
    """Extract the logical id from a FHIR Reference (e.g. 'Patient/abc' -> 'abc')."""
    ref = reference.get("reference", "")
    return ref.split("/")[-1] if "/" in ref else ref


def _extension_display(ext: Dict[str, Any]) -> Optional[str]:
    """Extract display text from a US-Core extension."""
    for sub in ext.get("extension", []):
        if sub.get("url") == "text":
            return sub.get("valueString")
        if "valueCoding" in sub:
            return sub["valueCoding"].get("display")
    return None


def _extract_quantity(obs: Dict[str, Any]) -> Tuple[Optional[float], Optional[str]]:
    """Extract numeric value and unit from an Observation resource."""
    vq = obs.get("valueQuantity")
    if vq:
        return vq.get("value"), vq.get("unit")
    # Component observations (e.g. blood pressure)
    components = obs.get("component", [])
    if components:
        first = components[0].get("valueQuantity", {})
        return first.get("value"), first.get("unit")
    return None, None


# ===================================================================
# CLI entry point
# ===================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load or generate Synthea FHIR bundles for disease progression modeling.",
    )
    parser.add_argument(
        "--module",
        type=str,
        default="cvd",
        choices=list(MODULE_MAP.keys()),
        help="Disease module (default: cvd)",
    )
    parser.add_argument(
        "--n_patients",
        type=int,
        default=100,
        help="Number of patients to generate (default: 100)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./data/raw",
        help="Output directory for FHIR JSON files",
    )
    parser.add_argument(
        "--synthea_jar",
        type=str,
        default=None,
        help="Path to synthea-with-dependencies.jar (optional, uses fallback if missing)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    module_name = MODULE_MAP.get(args.module, args.module)

    # Try Synthea CLI first, fall back to synthetic generator
    try:
        fhir_dir = run_synthea(
            module=module_name,
            n_patients=args.n_patients,
            output_dir=args.output_dir,
            synthea_jar=args.synthea_jar,
            seed=args.seed,
        )
        logger.info("Synthea output written to %s", fhir_dir)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        logger.warning("Synthea CLI unavailable (%s). Using synthetic fallback.", exc)
        bundles = generate_synthetic_fhir(
            n_patients=args.n_patients,
            module=args.module,
            output_dir=args.output_dir,
            seed=args.seed,
        )
        logger.info("Generated %d synthetic bundles in %s", len(bundles), args.output_dir)

    # Demonstrate loading
    loader = SyntheaLoader(args.output_dir)
    loader.load()
    patients_df = loader.patients_dataframe()
    conditions_df = loader.conditions_dataframe()
    observations_df = loader.observations_dataframe()
    medications_df = loader.medications_dataframe()

    print(f"\nPatients:     {len(patients_df)}")
    print(f"Conditions:   {len(conditions_df)}")
    print(f"Observations: {len(observations_df)}")
    print(f"Medications:  {len(medications_df)}")
    print("\nSample patients:")
    print(patients_df.head())


if __name__ == "__main__":
    main()
