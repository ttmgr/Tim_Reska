"""KTG underwriting decision engine: disease profiles, clinical checks, and decision logic."""

from medrisk.underwriting.clinical_checks import (
    ClinicalCheckResult,
    ClinicalValidationResult,
    run_clinical_checks,
)
from medrisk.underwriting.decision_engine import (
    UnderwritingDecision,
    UnderwritingEngine,
)
from medrisk.underwriting.profiles import (
    CaseStudy,
    ComorbidityInteraction,
    DiseaseProfile,
    get_profile_for_icd,
    load_case_studies,
    load_comorbidity_interactions,
    load_underwriting_profiles,
)

__all__ = [
    "DiseaseProfile",
    "ComorbidityInteraction",
    "CaseStudy",
    "load_underwriting_profiles",
    "load_comorbidity_interactions",
    "load_case_studies",
    "get_profile_for_icd",
    "ClinicalCheckResult",
    "ClinicalValidationResult",
    "run_clinical_checks",
    "UnderwritingDecision",
    "UnderwritingEngine",
]
