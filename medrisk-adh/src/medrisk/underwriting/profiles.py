"""Pydantic models and YAML loaders for underwriting disease profiles.

Loads disease-specific underwriting rules, comorbidity interaction tables,
and case studies from YAML configuration files.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Default config directory relative to this file's package root
_PKG_ROOT = Path(__file__).parent.parent.parent.parent  # repo root
_CONFIG_DIR = _PKG_ROOT / "configs"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_yaml(path: Path) -> dict[str, Any] | list[Any]:
    """Load a YAML file and return its contents."""
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


# ---------------------------------------------------------------------------
# Disease profile models
# ---------------------------------------------------------------------------

class PrognosticFactor(BaseModel):
    """A single prognostic factor that influences underwriting risk."""

    model_config = {"extra": "allow"}

    name: str
    type: str  # categorical, integer, boolean, numeric
    thresholds: dict[str, Any] | None = None
    risk_impact: str | None = None
    weight: str | None = None
    evidence: str | None = None


class AUDuration(BaseModel):
    """Expected Arbeitsunfaehigkeit (sick-leave) duration for a scenario."""

    model_config = {"extra": "allow"}

    description: str | None = None
    median_weeks: list[int | None] | None = None
    recurrence_rate: float | list[float] | None = None
    recurrence_window_years: int | None = None
    evidence: str
    source: str | None = None


class UnderwritingResponse(BaseModel):
    """Underwriting action for a set of conditions."""

    model_config = {"extra": "allow"}

    conditions: list[str]
    evidence: str
    loading_range: list[int] | None = None
    exclusion_type: str | None = None
    duration_months: list[int] | None = None


class FailureModeEntry(BaseModel):
    """A known failure mode for the disease profile."""

    type: str
    description: str


class ICDSubtype(BaseModel):
    """ICD-10 subtype with severity classification."""

    severity: str
    label: str


class DiseaseProfile(BaseModel):
    """Complete disease-specific underwriting profile.

    Attributes:
        cluster: Clinical cluster (psychiatric, musculoskeletal, etc.).
        label: Human-readable disease label.
        icd_codes: Primary ICD-10 codes covered by this profile.
        icd_subtypes: Optional mapping of code to subtype details.
        au_durations: Expected sick-leave durations keyed by scenario.
        prognostic_factors: Factors that modify risk assessment.
        underwriting_responses: Decision tiers keyed by action label.
        failure_modes: Known failure modes for this disease cluster.
        lookback_standard_years: Standard look-back window in years.
        lookback_extended_years: Extended look-back window in years.
        lookback_extended_condition: Condition that triggers extended lookback.
    """

    model_config = {"extra": "allow"}

    cluster: str
    label: str
    icd_codes: list[str]
    icd_subtypes: dict[str, ICDSubtype] | None = None
    au_durations: dict[str, AUDuration] | None = None
    prognostic_factors: list[PrognosticFactor] = Field(default_factory=list)
    underwriting_responses: dict[str, UnderwritingResponse] = Field(
        default_factory=dict,
    )
    failure_modes: list[FailureModeEntry] = Field(default_factory=list)
    lookback_standard_years: int | None = 5  # None = lifetime
    lookback_extended_years: int | None = 10  # None = lifetime
    lookback_extended_condition: str | None = None


# ---------------------------------------------------------------------------
# Comorbidity interaction models
# ---------------------------------------------------------------------------

class ComorbidityInteraction(BaseModel):
    """A known comorbidity interaction that modifies underwriting risk.

    Attributes:
        codes_a: ICD-10 code prefixes for the first condition group.
        codes_b: ICD-10 code prefixes for the second condition group.
        interaction_type: Nature of the interaction (e.g. 'synergistic').
        au_multiplier: Multiplicative factor on AU duration.
        expert_review: Whether this interaction mandates expert review.
        recommendation: Recommended underwriting action.
        evidence: Evidence citation or tier.
        description: Human-readable description of the interaction.
    """

    model_config = {"extra": "allow"}

    codes_a: list[str]
    codes_b: list[str]
    interaction_type: str
    au_multiplier: float | None = None
    expert_review: bool = False
    recommendation: str
    evidence: str
    description: str | None = None


# ---------------------------------------------------------------------------
# Case study models
# ---------------------------------------------------------------------------

class CaseStudyApplicant(BaseModel):
    """Applicant demographics for a case study."""

    model_config = {"extra": "allow"}

    age: int
    occupation: str
    occupation_class: int
    ktg_daily: int


class CaseStudyICD(BaseModel):
    """A single ICD entry in a case study history."""

    model_config = {"extra": "allow"}

    code: str
    date: str | None = None
    au_weeks: int | float | list[int] | None = None
    treatment: str | None = None


class CaseStudyAlgorithmOutput(BaseModel):
    """The algorithm's (potentially flawed) output for a case study."""

    model_config = {"extra": "allow"}

    decision: str
    rule: str
    loading_pct: int | None = None


class CaseStudyCorrectDecision(BaseModel):
    """The correct underwriting decision for a case study."""

    model_config = {"extra": "allow"}

    decision: str
    loading_pct: int | list[int] | None = None
    exclusion: str | None = None
    duration_years: int | None = None


class CaseStudy(BaseModel):
    """A complete underwriting case study illustrating a failure mode.

    Attributes:
        id: Numeric case identifier.
        title: Descriptive title of the case.
        failure_mode: The failure mode this case demonstrates.
        difficulty: Difficulty level (basic, intermediate, expert).
        applicant: Applicant demographics.
        icd_history: Diagnosis history entries.
        additional_info: Free-text supplemental information.
        algorithm_output: The algorithm's output to evaluate.
        correct_decision: The correct underwriting decision.
        explanation: Detailed explanation of the correct reasoning.
        key_learning: Summary learning point.
        evidence_tier: Evidence tier (T1-T4).
    """

    model_config = {"extra": "allow"}

    id: int
    title: str
    failure_mode: str
    difficulty: str
    applicant: CaseStudyApplicant
    icd_history: list[CaseStudyICD]
    additional_info: list[str] = Field(default_factory=list)
    algorithm_output: CaseStudyAlgorithmOutput
    correct_decision: CaseStudyCorrectDecision
    explanation: str
    key_learning: str
    evidence_tier: str


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_underwriting_profiles(
    config_dir: Path | None = None,
) -> dict[str, DiseaseProfile]:
    """Load disease profiles from configs/underwriting_profiles.yml.

    Args:
        config_dir: Override config directory. Defaults to repo ``configs/``.

    Returns:
        Mapping of cluster key to DiseaseProfile.
    """
    base = Path(config_dir) if config_dir else _CONFIG_DIR
    path = base / "underwriting_profiles.yml"
    raw = _load_yaml(path)

    # YAML has a top-level 'profiles:' wrapper
    profile_data = raw.get("profiles", raw)

    profiles: dict[str, DiseaseProfile] = {}
    for key, data in profile_data.items():
        profiles[key] = DiseaseProfile.model_validate(data)

    logger.info("Loaded %d underwriting profiles from %s", len(profiles), path)
    return profiles


def load_comorbidity_interactions(
    config_dir: Path | None = None,
) -> list[ComorbidityInteraction]:
    """Load comorbidity interactions from configs/comorbidity_interactions.yml.

    Args:
        config_dir: Override config directory. Defaults to repo ``configs/``.

    Returns:
        List of ComorbidityInteraction objects.
    """
    base = Path(config_dir) if config_dir else _CONFIG_DIR
    path = base / "comorbidity_interactions.yml"
    raw = _load_yaml(path)

    # YAML may have top-level 'interactions:' wrapper (dict keyed by ID)
    interaction_data = raw.get("interactions", raw)
    if isinstance(interaction_data, dict):
        items = list(interaction_data.values())
    else:
        items = interaction_data
    interactions = [ComorbidityInteraction.model_validate(item) for item in items]
    logger.info(
        "Loaded %d comorbidity interactions from %s", len(interactions), path,
    )
    return interactions


def load_case_studies(
    config_dir: Path | None = None,
) -> list[CaseStudy]:
    """Load case studies from configs/case_studies.yml.

    Args:
        config_dir: Override config directory. Defaults to repo ``configs/``.

    Returns:
        List of CaseStudy objects.
    """
    base = Path(config_dir) if config_dir else _CONFIG_DIR
    path = base / "case_studies.yml"
    raw = _load_yaml(path)

    # YAML has a top-level 'cases:' wrapper
    case_data = raw.get("cases", raw) if isinstance(raw, dict) else raw
    studies = [CaseStudy.model_validate(item) for item in case_data]
    logger.info("Loaded %d case studies from %s", len(studies), path)
    return studies


def get_profile_for_icd(
    icd_code: str,
    profiles: dict[str, DiseaseProfile] | None = None,
) -> DiseaseProfile | None:
    """Find the disease profile matching an ICD-10 code by prefix.

    Attempts exact match first, then progressively shorter prefixes
    (e.g. ``F32.1`` -> ``F32`` -> ``F3``). Returns the first match.

    Args:
        icd_code: ICD-10 code to look up.
        profiles: Pre-loaded profiles dict. If ``None``, loads from default
            config directory.

    Returns:
        Matching DiseaseProfile or ``None`` if no profile covers the code.
    """
    if profiles is None:
        profiles = load_underwriting_profiles()

    # Normalise: strip whitespace, uppercase
    code = icd_code.strip().upper()

    for _key, profile in profiles.items():
        for profile_code in profile.icd_codes:
            if code.startswith(profile_code) or profile_code.startswith(code):
                return profile

    logger.debug("No underwriting profile found for ICD code %s", icd_code)
    return None
