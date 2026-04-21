"""
disease_progression.data - Data ingestion, ETL, and codelist management.

This subpackage handles the full data pipeline from raw clinical data sources
to analysis-ready tables:

    - ``synthea_loader``: Parse Synthea-generated FHIR JSON bundles or generate
      synthetic FHIR-like data for demonstration and testing.
    - ``omop_etl``: Transform FHIR resources into simplified OMOP CDM tables
      (person, condition_occurrence, drug_exposure, measurement, observation_period).
    - ``codelists/``: Curated YAML codelist definitions for disease tracks
      (cardiovascular disease, diabetes) mapping ICD-10, ATC, and LOINC codes.
"""

from disease_progression.data.synthea_loader import SyntheaLoader
from disease_progression.data.omop_etl import FHIRToOMOPTransformer

__all__ = [
    "SyntheaLoader",
    "FHIRToOMOPTransformer",
]
