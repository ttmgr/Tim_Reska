"""
disease_progression - Clinical disease progression modeling framework.

A comprehensive survival analysis and disease trajectory modeling toolkit
designed for longitudinal electronic health record (EHR) data. Supports
classical survival models (Cox PH), deep survival models (DeepSurv, DeepHit),
continuous-time multistate models, and transformer-based architectures
(SurvTRACE) for predicting clinical outcomes and competing risks.

Key capabilities:
    - Synthea FHIR bundle ingestion and OMOP-lite ETL
    - Curated codelists for cardiovascular disease and diabetes tracks
    - Static and temporal feature engineering with EHR tokenization
    - Model registry supporting Cox, DeepSurv, DeepHit, multistate, SurvTRACE
    - Evaluation via C-index, time-dependent AUC, Brier score, fairness audits
    - Automated model card generation
"""

__version__ = "0.1.0"
__author__ = "Disease Progression Team"

from disease_progression.models.registry import ModelRegistry

__all__ = [
    "__version__",
    "ModelRegistry",
]
