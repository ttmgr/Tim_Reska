"""Temporal risk assessment for underwriting look-back windows.

Handles time-decay of risk, remission assessment, and red-flag detection
for conditions where time since last episode modifies underwriting risk.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from medrisk.underwriting.profiles import DiseaseProfile

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Red flag definitions (Part 3.3 of the KTG underwriting manual)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RedFlag:
    """A clinical red flag that may override time-decay assumptions.

    Attributes:
        category: Red-flag category identifier.
        description: Human-readable explanation.
        override_time_decay: If ``True``, time decay must not be applied.
    """

    category: str
    description: str
    override_time_decay: bool = True


RED_FLAG_CATEGORIES: list[str] = [
    "multiple_episodes",
    "inpatient_psychiatric",
    "repeated_au_gt_8_weeks",
    "ongoing_specialist_followup",
    "ongoing_disease_medication",
    "residual_symptoms",
    "surgery_history",
    "chronic_pain_opioids",
    "prior_disability_application",
]

# Profiles where time-decay never applies (chronic / lifetime lookback)
NO_TIME_DECAY_PROFILES: list[str] = [
    "personality_disorders",
    "ms",
]

# Recurrent conditions where episode count matters more than time since last
RECURRENT_NO_DECAY_CODES: list[str] = [
    "F33",  # Recurrent depressive disorder
    "F31",  # Bipolar affective disorder
]


# ---------------------------------------------------------------------------
# Look-back window check
# ---------------------------------------------------------------------------

def is_within_lookback(
    diagnosis_date: date,
    profile: DiseaseProfile,
    reference_date: date | None = None,
    use_extended: bool = False,
) -> bool:
    """Check if a diagnosis falls within the profile's look-back window.

    Args:
        diagnosis_date: Date of the diagnosis.
        profile: Disease profile containing lookback definitions.
        reference_date: Date to measure from. Defaults to today.
        use_extended: If ``True``, use the extended lookback window.

    Returns:
        ``True`` if the diagnosis is within the applicable lookback window.
    """
    ref = reference_date or date.today()
    years = (
        profile.lookback_extended_years
        if use_extended
        else profile.lookback_standard_years
    )
    delta_days = (ref - diagnosis_date).days
    lookback_days = years * 365
    return delta_days <= lookback_days


# ---------------------------------------------------------------------------
# Time-decay factor
# ---------------------------------------------------------------------------

def time_decay_factor(
    months_since_episode: int,
    profile_key: str,
    icd_code: str | None = None,
) -> float:
    """Return risk decay multiplier based on time since last episode.

    For chronic and recurrent conditions, returns ``1.0`` (no decay) because
    the risk does not diminish with time alone.

    For other conditions, applies a linear decay from ``1.0`` at month 0 to
    ``0.2`` at 60 months (5 years), floored at ``0.2``.

    Args:
        months_since_episode: Months elapsed since last AU episode.
        profile_key: Profile cluster key (e.g. ``'depression'``).
        icd_code: Optional ICD-10 code for recurrent-condition check.

    Returns:
        Decay multiplier in ``[0.2, 1.0]``.
    """
    # No decay for chronic / lifetime conditions
    if profile_key in NO_TIME_DECAY_PROFILES:
        logger.debug(
            "No time decay for chronic profile %s", profile_key,
        )
        return 1.0

    # No decay for recurrent conditions (episode count matters, not time)
    if icd_code is not None:
        code_upper = icd_code.strip().upper()
        for recurrent_prefix in RECURRENT_NO_DECAY_CODES:
            if code_upper.startswith(recurrent_prefix):
                logger.debug(
                    "No time decay for recurrent code %s", icd_code,
                )
                return 1.0

    # Linear decay: 1.0 at month 0 -> 0.2 at month 60, floor at 0.2
    if months_since_episode <= 0:
        return 1.0

    max_months = 60
    min_factor = 0.2
    if months_since_episode >= max_months:
        return min_factor

    factor = 1.0 - (1.0 - min_factor) * (months_since_episode / max_months)
    return round(factor, 4)


# ---------------------------------------------------------------------------
# Remission assessment
# ---------------------------------------------------------------------------

def assess_remission(
    diagnoses: list[dict],
    medications: list[dict],
    months_since_last_au: int | None,
) -> str:
    """Assess remission status based on clinical evidence.

    Uses a conservative hierarchy:
    - ``'full'``: No active diagnoses, no active medications,
      >= 12 months since last AU episode.
    - ``'partial'``: No active AU but still on maintenance medication
      or < 12 months since last episode.
    - ``'none'``: Active diagnoses or recent AU episode.
    - ``'unverifiable'``: Insufficient data to determine status.

    Args:
        diagnoses: List of diagnosis dicts with at minimum ``'is_primary'``
            and ``'date_recorded'`` keys.
        medications: List of medication dicts with at minimum ``'active'`` key.
        months_since_last_au: Months since last AU episode, or ``None``
            if unknown.

    Returns:
        Remission status string.
    """
    if not diagnoses and not medications:
        return "unverifiable"

    if months_since_last_au is None:
        return "unverifiable"

    # Check for active psychotropic / disease-specific medications
    active_meds = [m for m in medications if m.get("active", False)]

    # Recent AU episode -> not in remission
    if months_since_last_au < 6:
        return "none"

    # Between 6-12 months or still on active medication -> partial
    if months_since_last_au < 12 or active_meds:
        return "partial"

    # >= 12 months and no active meds
    return "full"
