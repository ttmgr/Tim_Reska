"""Underwriting decision engine with most-restrictive-profile-wins logic.

Ties together disease profiles, temporal risk assessment, and clinical
consistency checks to produce a fully traced underwriting decision.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from pydantic import BaseModel as _PydanticBase

from medrisk.underwriting.clinical_checks import (
    ClinicalValidationResult,
    run_clinical_checks,
)
from medrisk.underwriting.profiles import (
    DiseaseProfile,
    get_profile_for_icd,
    load_comorbidity_interactions,
    load_underwriting_profiles,
)
from medrisk.underwriting.temporal import (
    is_within_lookback,
    time_decay_factor,
)

logger = logging.getLogger(__name__)


def _to_dict(obj: Any) -> dict:
    """Convert a Pydantic model or dict to a plain dict."""
    if isinstance(obj, _PydanticBase):
        return obj.model_dump()
    if isinstance(obj, dict):
        return obj
    return vars(obj)


# ---------------------------------------------------------------------------
# Decision hierarchy (most restrictive first)
# ---------------------------------------------------------------------------

_DECISION_RANK: dict[str, int] = {
    "decline": 0,
    "postpone": 1,
    "accept_exclusion": 2,
    "accept_loading": 3,
    "accept": 4,
}


def _more_restrictive(a: str, b: str) -> str:
    """Return the more restrictive of two decisions."""
    return a if _DECISION_RANK.get(a, 99) <= _DECISION_RANK.get(b, 99) else b


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class UnderwritingDecision:
    """Complete underwriting decision with reasoning trace.

    Attributes:
        patient_id: Patient identifier.
        decision: Final decision (accept, accept_loading, accept_exclusion,
            postpone, decline).
        loading_pct: Loading percentage, if applicable.
        exclusion_type: Exclusion description, if applicable.
        reasoning_trace: Step-by-step reasoning log.
        rules_fired: List of rule identifiers that contributed.
        evidence_tier: Lowest (most conservative) evidence tier used.
        expert_review_required: Whether the case requires expert review.
        clinical_findings: Full clinical validation result.
    """

    patient_id: str
    decision: str = "accept"
    loading_pct: float | None = None
    exclusion_type: str | None = None
    reasoning_trace: list[str] = field(default_factory=list)
    rules_fired: list[str] = field(default_factory=list)
    evidence_tier: str = "T3"
    expert_review_required: bool = False
    clinical_findings: ClinicalValidationResult | None = None


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class UnderwritingEngine:
    """Rule-based underwriting engine driven by YAML disease profiles.

    Uses most-restrictive-profile-wins: if any matched profile yields a
    ``decline``, the overall decision is ``decline``.

    Args:
        config_dir: Override config directory for YAML files.
    """

    def __init__(self, config_dir: Any = None) -> None:
        self._profiles = load_underwriting_profiles(config_dir)
        self._interactions = load_comorbidity_interactions(config_dir)

    @property
    def profiles(self) -> dict[str, DiseaseProfile]:
        """Return loaded disease profiles."""
        return self._profiles

    @property
    def interactions(self):
        """Return loaded comorbidity interactions."""
        return self._interactions

    def assess(
        self,
        patient_id: str,
        diagnoses: list[dict],
        medications: list[dict] | None = None,
        labs: list[dict] | None = None,
        occupation_class: int = 1,
        age: int | None = None,
        au_episodes: list[dict] | None = None,
    ) -> UnderwritingDecision:
        """Produce an underwriting decision for a patient.

        Processing pipeline:
        1. Match ICD codes to disease profiles.
        2. For each matched profile, evaluate underwriting response tier.
        3. Apply temporal decay (unless overridden for chronic/recurrent).
        4. Check comorbidity interactions and escalate if synergistic.
        5. Run clinical consistency checks.
        6. Return most-restrictive decision with full reasoning trace.

        Args:
            patient_id: Patient identifier.
            diagnoses: List of diagnosis dicts (requires ``'icd10_code'``,
                ``'date_recorded'``).
            medications: Optional medication dicts (``'atc_code'``, ``'active'``).
            labs: Optional lab result dicts.
            occupation_class: Occupation class (1 = sedentary ... 4 = heavy).
            age: Patient age (used for age-adjusted rules).
            au_episodes: Optional AU episode history dicts (``'icd10_code'``,
                ``'start_date'``, ``'duration_weeks'``).

        Returns:
            Fully traced UnderwritingDecision.
        """
        # Normalise Pydantic objects to dicts for uniform .get() access
        diagnoses = [_to_dict(d) for d in diagnoses]
        medications = [_to_dict(m) for m in (medications or [])]
        labs = [_to_dict(lb) for lb in (labs or [])]
        au_episodes_safe: list[dict] = [_to_dict(e) for e in (au_episodes or [])]

        decision = UnderwritingDecision(patient_id=patient_id)
        overall = "accept"
        max_loading = 0.0

        decision.reasoning_trace.append(
            f"Assessment started: {len(diagnoses)} diagnoses, "
            f"{len(medications)} medications, "
            f"occupation class {occupation_class}",
        )

        # ----- Step 1 & 2: Match profiles and evaluate responses -----
        matched_profiles: dict[str, DiseaseProfile] = {}
        for diag in diagnoses:
            icd = diag.get("icd10_code", "")
            if not icd:
                continue

            profile = get_profile_for_icd(icd, self._profiles)
            if profile is None:
                decision.reasoning_trace.append(
                    f"  ICD {icd}: no matching profile (standard terms)",
                )
                continue

            # Avoid duplicate processing for same cluster
            if profile.cluster in matched_profiles:
                decision.reasoning_trace.append(
                    f"  ICD {icd}: already matched to profile '{profile.cluster}'",
                )
                continue

            matched_profiles[profile.cluster] = profile
            decision.reasoning_trace.append(
                f"  ICD {icd}: matched profile '{profile.cluster}' ({profile.label})",
            )

            # Check lookback window
            diag_date = diag.get("date_recorded")
            if diag_date is not None and isinstance(diag_date, str):
                try:
                    diag_date = date.fromisoformat(diag_date)
                except ValueError:
                    diag_date = None

            if diag_date is not None and not is_within_lookback(diag_date, profile):
                decision.reasoning_trace.append(
                    f"    Diagnosis outside standard lookback "
                    f"({profile.lookback_standard_years}y) - reduced weight",
                )

            # Evaluate underwriting responses from most to least restrictive
            profile_decision = "accept"
            profile_loading = 0.0

            for tier_name, response in sorted(
                profile.underwriting_responses.items(),
                key=lambda x: _DECISION_RANK.get(
                    _extract_decision_type(x[1].conditions), 99,
                ),
            ):
                # Check if conditions match patient data
                tier_decision = _evaluate_response_tier(
                    tier_name,
                    response,
                    diagnoses,
                    medications,
                    au_episodes_safe,
                    decision.reasoning_trace,
                )
                if tier_decision is not None:
                    d_type, d_loading = tier_decision
                    if _DECISION_RANK.get(d_type, 99) < _DECISION_RANK.get(
                        profile_decision, 99,
                    ):
                        profile_decision = d_type
                        profile_loading = d_loading

            # Apply temporal decay to loading
            if diag_date is not None and profile_loading > 0:
                months_since = max(
                    0, (date.today() - diag_date).days // 30,
                )
                decay = time_decay_factor(
                    months_since, profile.cluster, icd,
                )
                adjusted_loading = profile_loading * decay
                if decay < 1.0:
                    decision.reasoning_trace.append(
                        f"    Time decay applied: {profile_loading:.0f}% x "
                        f"{decay:.2f} = {adjusted_loading:.0f}% "
                        f"({months_since} months since episode)",
                    )
                profile_loading = adjusted_loading

            decision.rules_fired.append(
                f"{profile.cluster}:{profile_decision}",
            )

            overall = _more_restrictive(overall, profile_decision)
            max_loading = max(max_loading, profile_loading)

        # ----- Step 3: Comorbidity interactions -----
        if len(matched_profiles) >= 2:
            decision.reasoning_trace.append("Checking comorbidity interactions...")
            diag_codes = [
                d.get("icd10_code", "").strip().upper() for d in diagnoses
            ]
            for interaction in self._interactions:
                has_a = any(
                    any(dc.startswith(p) for p in interaction.codes_a)
                    for dc in diag_codes
                )
                has_b = any(
                    any(dc.startswith(p) for p in interaction.codes_b)
                    for dc in diag_codes
                )
                if has_a and has_b:
                    decision.reasoning_trace.append(
                        f"  Comorbidity interaction: "
                        f"{interaction.description or interaction.interaction_type} "
                        f"(AU x{interaction.au_multiplier})",
                    )
                    decision.rules_fired.append(
                        f"comorbidity:{interaction.codes_a[0]}+{interaction.codes_b[0]}",
                    )
                    if interaction.expert_review:
                        decision.expert_review_required = True
                    # Escalate loading by multiplier
                    if max_loading > 0:
                        max_loading = min(
                            max_loading * interaction.au_multiplier, 200.0,
                        )
                    else:
                        # Even without base loading, interaction triggers loading
                        max_loading = max(max_loading, 25.0)
                        overall = _more_restrictive(overall, "accept_loading")

        # ----- Step 4: Clinical consistency checks -----
        decision.reasoning_trace.append("Running clinical consistency checks...")
        clinical_result = run_clinical_checks(
            patient_id=patient_id,
            diagnoses=diagnoses,
            medications=medications,
            labs=labs,
            occupation_class=occupation_class,
            au_episodes=au_episodes_safe if au_episodes_safe else None,
            profiles=self._profiles,
            interactions=self._interactions,
        )
        decision.clinical_findings = clinical_result

        if clinical_result.has_critical:
            decision.reasoning_trace.append(
                f"  CRITICAL findings: {sum(1 for f in clinical_result.findings if f.severity == 'critical')} — "
                f"expert review required",
            )
            decision.expert_review_required = True

        if clinical_result.expert_review_required:
            decision.reasoning_trace.append(
                f"  Expert review triggered ({len(clinical_result.findings)} total findings)",
            )
            decision.expert_review_required = True

        # ----- Step 5: Assemble final decision -----
        if not matched_profiles:
            decision.reasoning_trace.append(
                "No disease profiles matched. Standard terms apply.",
            )
            overall = "accept"

        decision.decision = overall
        if max_loading > 0 and overall in (
            "accept_loading", "accept_exclusion", "postpone", "decline",
        ):
            decision.loading_pct = round(max_loading, 1)

        decision.reasoning_trace.append(
            f"Final decision: {overall}"
            + (f" (loading {decision.loading_pct}%)" if decision.loading_pct else "")
            + (" [EXPERT REVIEW REQUIRED]" if decision.expert_review_required else ""),
        )

        logger.info(
            "Underwriting %s: %s (loading=%s, expert=%s, rules=%d)",
            patient_id,
            decision.decision,
            decision.loading_pct,
            decision.expert_review_required,
            len(decision.rules_fired),
        )

        return decision


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _extract_decision_type(conditions: list[str]) -> str:
    """Infer the decision type from response condition strings.

    Heuristic: looks for keywords in conditions to determine tier.
    """
    text = " ".join(c.lower() for c in conditions)
    if "decline" in text:
        return "decline"
    if "postpone" in text:
        return "postpone"
    if "exclusion" in text:
        return "accept_exclusion"
    if "loading" in text or "zuschlag" in text:
        return "accept_loading"
    return "accept"


def _evaluate_response_tier(
    tier_name: str,
    response: Any,
    diagnoses: list[dict],
    medications: list[dict],
    au_episodes: list[dict],
    trace: list[str],
) -> tuple[str, float] | None:
    """Evaluate whether a response tier's conditions are met.

    Returns ``(decision_type, loading_pct)`` if the tier applies, else ``None``.

    This is a heuristic matcher that checks condition strings against
    patient data patterns. A production system would use a formal rule engine.
    """
    conditions_text = " ".join(c.lower() for c in response.conditions)

    # Determine decision type from tier name and conditions
    tier_lower = tier_name.lower()
    if "decline" in tier_lower or "decline" in conditions_text:
        decision_type = "decline"
    elif "postpone" in tier_lower or "postpone" in conditions_text:
        decision_type = "postpone"
    elif "exclusion" in tier_lower or "exclusion" in conditions_text:
        decision_type = "accept_exclusion"
    elif "loading" in tier_lower or "zuschlag" in conditions_text:
        decision_type = "accept_loading"
    elif "accept" in tier_lower or "normal" in tier_lower or "standard" in tier_lower:
        decision_type = "accept"
    else:
        decision_type = "accept_loading"

    # Extract loading from response
    loading = 0.0
    if response.loading_range:
        # Use midpoint of loading range as default
        loading = sum(response.loading_range) / len(response.loading_range)

    # Check simple condition heuristics
    matched = False

    # Episode count conditions
    if "episode" in conditions_text or "recurrent" in conditions_text:
        episode_count = len(au_episodes)
        if "single" in conditions_text and episode_count <= 1 or "multiple" in conditions_text and episode_count >= 2 or "recurrent" in conditions_text and episode_count >= 2 or episode_count >= 1:
            matched = True

    # Medication conditions
    if "medication" in conditions_text or "treatment" in conditions_text:
        active_meds = [m for m in medications if m.get("active", False)]
        if "ongoing" in conditions_text and active_meds or "no" in conditions_text and not active_meds:
            matched = True

    # Severity conditions
    if "severe" in conditions_text or "schwer" in conditions_text:
        # Check for severe-grade ICD codes (.2, .3 suffixes for F32)
        severe_codes = [
            d.get("icd10_code", "")
            for d in diagnoses
            if d.get("icd10_code", "").endswith((".2", ".3"))
        ]
        if severe_codes:
            matched = True

    # Duration conditions
    if ("week" in conditions_text or "month" in conditions_text) and au_episodes:
            max_weeks = max(
                (ep.get("duration_weeks") or 0) for ep in au_episodes
            )
            if max_weeks > 0:
                matched = True

    # Default: if no specific conditions parsed, apply the tier as a baseline
    if not matched and decision_type == "accept":
        matched = True

    if matched:
        trace.append(
            f"    Tier '{tier_name}' matched -> {decision_type}"
            + (f" (loading ~{loading:.0f}%)" if loading > 0 else ""),
        )
        return decision_type, loading

    return None
