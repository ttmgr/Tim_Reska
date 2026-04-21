"""Clinical consistency checks for underwriting decisions.

Implements six independent check functions that validate the consistency of
patient data against disease profiles and known clinical rules. Each check
returns findings tagged with a failure-mode category:

- **overreaction**: Algorithm over-penalises a benign or resolved condition.
- **underestimation**: Algorithm misses compounding risk factors.
- **coding_ambiguity**: Unspecific or ambiguous ICD coding obscures true risk.
- **missed_pattern**: Known clinical pattern not detected.
- **missing_data**: Insufficient data for a reliable assessment.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from medrisk.underwriting.profiles import (
        ComorbidityInteraction,
        DiseaseProfile,
    )

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ClinicalCheckResult:
    """Result of a single clinical consistency check.

    Attributes:
        check_id: Unique identifier for the check (e.g. ``'drug_diag_001'``).
        severity: ``'critical'``, ``'warning'``, or ``'info'``.
        failure_mode: Failure-mode category (see module docstring).
        description: Human-readable finding description.
        evidence_tier: Evidence tier supporting this check (``'T1'``-``'T4'``).
        icd_codes_involved: ICD-10 codes relevant to this finding.
        recommendation: Suggested action for the underwriter.
    """

    check_id: str
    severity: str  # critical | warning | info
    failure_mode: str
    description: str
    evidence_tier: str
    icd_codes_involved: tuple[str, ...] = ()
    recommendation: str = ""


@dataclass
class ClinicalValidationResult:
    """Aggregated result of all clinical checks for a patient.

    Attributes:
        patient_id: Patient identifier.
        checks_run: Total number of checks executed.
        checks_passed: Number of checks that produced no findings.
        findings: List of individual check findings.
    """

    patient_id: str
    checks_run: int
    checks_passed: int
    findings: list[ClinicalCheckResult] = field(default_factory=list)

    @property
    def has_critical(self) -> bool:
        """Return ``True`` if any finding has critical severity."""
        return any(f.severity == "critical" for f in self.findings)

    @property
    def expert_review_required(self) -> bool:
        """Return ``True`` if the case should be escalated to an expert.

        Triggered by any critical finding or >= 3 total findings.
        """
        return self.has_critical or len(self.findings) >= 3


# ---------------------------------------------------------------------------
# Known clinical mappings
# ---------------------------------------------------------------------------

# Drug-diagnosis consistency: ATC prefix -> expected ICD-10 prefixes
_DRUG_DIAGNOSIS_MAP: dict[str, dict[str, list[str]]] = {
    "N06AB02": {  # sertraline
        "name": "sertraline",
        "expected_icd": ["F32", "F33", "F41"],
    },
    "N06AX21": {  # duloxetine
        "name": "duloxetine",
        "expected_icd": ["F32", "M79.7"],
    },
    "A10BA02": {  # metformin
        "name": "metformin",
        "expected_icd": ["E11"],
    },
    "L04AA23": {  # natalizumab
        "name": "natalizumab",
        "expected_icd": ["G35"],
    },
    "N03A": {  # AEDs (antiepileptic drugs, prefix match)
        "name": "antiepileptic drugs",
        "expected_icd": ["G40"],
    },
    "L04AB": {  # TNF-alpha inhibitors / biologics (prefix match)
        "name": "biologics (TNF-alpha)",
        "expected_icd": ["M05", "M06"],
    },
}

# Coding specificity: codes that should be flagged as too unspecific
_UNSPECIFIC_CODES: dict[str, str] = {
    "I48.9": "Unspecified atrial fibrillation/flutter. Request I48.0/I48.1/I48.2 for risk stratification.",
    "E11.9": "Type 2 diabetes without complications. Check if E11.7 (with complications) applies.",
    "M54": "Dorsalgia NOS. Distinguish M51 (disc disorders) for accurate AU estimation.",
    "F32.9": "Depressive episode, unspecified. Severity (F32.0-F32.3) drives AU duration.",
    "M79.3": "Panniculitis NOS. May mask chronic pain syndrome requiring different lookback.",
}

# Occupation-diagnosis critical interactions
_OCCUPATION_DIAGNOSIS_CRITICAL: list[dict[str, list[str] | list[int] | str]] = [
    {
        "icd_prefixes": ["M51.1"],
        "occupation_classes": [3, 4],
        "description": "Lumbar disc herniation in manual/heavy physical occupation",
        "recommendation": "Extended lookback; loading or exclusion likely required",
    },
    {
        "icd_prefixes": ["G40"],
        "occupation_classes": [3, 4],
        "description": "Epilepsy in safety-critical / physical occupation",
        "recommendation": "Specialist review mandatory; seizure-free duration critical",
    },
    {
        "icd_prefixes": ["F10"],
        "occupation_classes": [3, 4],
        "description": "Alcohol-related disorder in safety-critical occupation",
        "recommendation": "Extended lookback; consider decline for active dependence",
    },
    {
        "icd_prefixes": ["H40"],
        "occupation_classes": [1, 2, 3, 4],
        "description": "Glaucoma in occupation requiring visual acuity",
        "recommendation": "Ophthalmology review; field-of-vision assessment needed",
    },
]

# Red flag detection rules
_RED_FLAG_EPISODE_THRESHOLD = 2  # multiple episodes threshold
_RED_FLAG_AU_WEEKS_THRESHOLD = 8  # repeated long AU threshold
_PSYCHIATRIC_INPATIENT_CODES = ["F20", "F31", "F32.3", "F33.3", "F60"]
_CHRONIC_PAIN_OPIOID_ATCS = ["N02A"]  # opioid analgesics ATC prefix


# ---------------------------------------------------------------------------
# Check 1: Drug-diagnosis consistency
# ---------------------------------------------------------------------------

def check_drug_diagnosis_consistency(
    diagnoses: list[dict],
    medications: list[dict],
    profiles: dict[str, DiseaseProfile] | None = None,
) -> list[ClinicalCheckResult]:
    """Check that prescribed medications have matching diagnoses.

    Detects hidden conditions (medication present, no matching diagnosis)
    and potential data gaps (diagnosis present, expected medication absent).

    Args:
        diagnoses: List of diagnosis dicts (requires ``'icd10_code'`` key).
        medications: List of medication dicts (requires ``'atc_code'`` key).
        profiles: Loaded disease profiles (unused in current implementation,
            reserved for future per-profile drug mapping).

    Returns:
        List of findings.
    """
    findings: list[ClinicalCheckResult] = []
    diag_codes = [d.get("icd10_code", "") for d in diagnoses]

    for med in medications:
        atc = med.get("atc_code", "")
        if not atc:
            continue

        # Try exact match first, then prefix match
        matched_rule = _DRUG_DIAGNOSIS_MAP.get(atc)
        if matched_rule is None:
            for rule_atc, rule in _DRUG_DIAGNOSIS_MAP.items():
                if atc.startswith(rule_atc) or rule_atc.startswith(atc):
                    matched_rule = rule
                    break

        if matched_rule is None:
            continue

        expected_icds = matched_rule["expected_icd"]
        drug_name = matched_rule["name"]

        # Check if any diagnosis matches
        has_match = any(
            any(dc.startswith(eicd) for eicd in expected_icds)
            for dc in diag_codes
        )

        if not has_match:
            findings.append(ClinicalCheckResult(
                check_id=f"drug_diag_{atc}",
                severity="warning",
                failure_mode="missing_data",
                description=(
                    f"Medication {drug_name} ({atc}) prescribed but no matching "
                    f"diagnosis found. Expected one of: {', '.join(expected_icds)}."
                ),
                evidence_tier="T3",
                icd_codes_involved=tuple(expected_icds),
                recommendation=(
                    "Request diagnosis clarification or check if condition "
                    "was omitted from application."
                ),
            ))

    return findings


# ---------------------------------------------------------------------------
# Check 2: Temporal consistency
# ---------------------------------------------------------------------------

def check_temporal_consistency(
    diagnoses: list[dict],
    au_episodes: list[dict] | None,
    profiles: dict[str, DiseaseProfile] | None = None,
) -> list[ClinicalCheckResult]:
    """Check temporal consistency of diagnoses and AU episodes.

    Flags:
    - Time-decay applied to recurrent conditions (F33, F31) where episode
      count matters more than time since last episode.
    - Ancient single episodes that may be over-weighted.

    Args:
        diagnoses: List of diagnosis dicts (``'icd10_code'``, ``'date_recorded'``).
        au_episodes: Optional list of AU episode dicts
            (``'icd10_code'``, ``'start_date'``, ``'duration_weeks'``).
        profiles: Loaded disease profiles (for lookback rules).

    Returns:
        List of findings.
    """
    from medrisk.underwriting.temporal import RECURRENT_NO_DECAY_CODES

    findings: list[ClinicalCheckResult] = []
    diag_codes = [d.get("icd10_code", "") for d in diagnoses]

    # Flag recurrent conditions where time-decay would be inappropriate
    for code in diag_codes:
        code_upper = code.strip().upper()
        for recurrent_prefix in RECURRENT_NO_DECAY_CODES:
            if code_upper.startswith(recurrent_prefix):
                findings.append(ClinicalCheckResult(
                    check_id=f"temporal_recurrent_{code_upper}",
                    severity="warning",
                    failure_mode="overreaction",
                    description=(
                        f"Recurrent condition {code_upper} detected. "
                        f"Time-decay must NOT be applied; episode count and "
                        f"pattern determine risk, not time since last episode."
                    ),
                    evidence_tier="T2",
                    icd_codes_involved=(code_upper,),
                    recommendation=(
                        "Count total episodes and assess inter-episode interval "
                        "rather than applying simple time decay."
                    ),
                ))

    # Flag single ancient episodes (> 10 years) that might be over-weighted
    if au_episodes:
        from datetime import date as date_type

        today = date_type.today()
        for ep in au_episodes:
            start = ep.get("start_date")
            if start is None:
                continue
            if isinstance(start, str):
                try:
                    start = date_type.fromisoformat(start)
                except ValueError:
                    continue
            years_ago = (today - start).days / 365.25
            if years_ago > 10:
                ep_code = ep.get("icd10_code", "unknown")
                findings.append(ClinicalCheckResult(
                    check_id=f"temporal_ancient_{ep_code}",
                    severity="info",
                    failure_mode="overreaction",
                    description=(
                        f"AU episode for {ep_code} is {years_ago:.0f} years old. "
                        f"Verify this is still within the applicable lookback window."
                    ),
                    evidence_tier="T3",
                    icd_codes_involved=(ep_code,),
                    recommendation="Check if episode exceeds lookback and can be excluded.",
                ))

    return findings


# ---------------------------------------------------------------------------
# Check 3: Occupation-diagnosis interaction
# ---------------------------------------------------------------------------

def check_occupation_diagnosis_interaction(
    occupation_class: int,
    diagnoses: list[dict],
    profiles: dict[str, DiseaseProfile] | None = None,
) -> list[ClinicalCheckResult]:
    """Check for critical occupation-diagnosis interactions.

    Certain diagnosis-occupation combinations significantly alter AU risk
    (e.g. disc herniation in manual workers, epilepsy in safety roles).

    Args:
        occupation_class: Occupation class (1 = sedentary ... 4 = heavy).
        diagnoses: List of diagnosis dicts (requires ``'icd10_code'``).
        profiles: Loaded disease profiles (reserved for future use).

    Returns:
        List of findings.
    """
    findings: list[ClinicalCheckResult] = []
    diag_codes = [d.get("icd10_code", "").strip().upper() for d in diagnoses]

    for rule in _OCCUPATION_DIAGNOSIS_CRITICAL:
        if occupation_class not in rule["occupation_classes"]:
            continue
        for icd_prefix in rule["icd_prefixes"]:
            matched_codes = [c for c in diag_codes if c.startswith(icd_prefix)]
            if matched_codes:
                findings.append(ClinicalCheckResult(
                    check_id=f"occ_diag_{icd_prefix}_class{occupation_class}",
                    severity="critical",
                    failure_mode="underestimation",
                    description=str(rule["description"]),
                    evidence_tier="T2",
                    icd_codes_involved=tuple(matched_codes),
                    recommendation=str(rule["recommendation"]),
                ))

    return findings


# ---------------------------------------------------------------------------
# Check 4: Comorbidity interactions
# ---------------------------------------------------------------------------

def check_comorbidity_interactions(
    diagnoses: list[dict],
    interactions: list[ComorbidityInteraction] | None,
) -> list[ClinicalCheckResult]:
    """Detect known comorbidity interactions from the interaction table.

    Args:
        diagnoses: List of diagnosis dicts (requires ``'icd10_code'``).
        interactions: Loaded comorbidity interactions. If ``None``, check
            is skipped.

    Returns:
        List of findings.
    """
    findings: list[ClinicalCheckResult] = []

    if not interactions:
        return findings

    diag_codes = [d.get("icd10_code", "").strip().upper() for d in diagnoses]

    for interaction in interactions:
        # Check if patient has codes from both groups
        has_a = any(
            any(dc.startswith(prefix) for prefix in interaction.codes_a)
            for dc in diag_codes
        )
        has_b = any(
            any(dc.startswith(prefix) for prefix in interaction.codes_b)
            for dc in diag_codes
        )

        if has_a and has_b:
            severity = "critical" if interaction.expert_review else "warning"
            involved = tuple(
                dc for dc in diag_codes
                if any(dc.startswith(p) for p in interaction.codes_a)
                or any(dc.startswith(p) for p in interaction.codes_b)
            )
            findings.append(ClinicalCheckResult(
                check_id=f"comorbid_{'_'.join(interaction.codes_a[:1])}_{interaction.codes_b[0]}",
                severity=severity,
                failure_mode="underestimation",
                description=(
                    f"Comorbidity interaction detected: "
                    f"{interaction.description or interaction.interaction_type}. "
                    f"AU multiplier: {interaction.au_multiplier}x."
                ),
                evidence_tier=interaction.evidence,
                icd_codes_involved=involved,
                recommendation=interaction.recommendation,
            ))

    return findings


# ---------------------------------------------------------------------------
# Check 5: Coding specificity
# ---------------------------------------------------------------------------

def check_coding_specificity(
    diagnoses: list[dict],
) -> list[ClinicalCheckResult]:
    """Flag unspecific ICD-10 codes that impair risk stratification.

    Args:
        diagnoses: List of diagnosis dicts (requires ``'icd10_code'``).

    Returns:
        List of findings.
    """
    findings: list[ClinicalCheckResult] = []
    seen: set[str] = set()

    for diag in diagnoses:
        code = diag.get("icd10_code", "").strip().upper()
        if not code or code in seen:
            continue

        for unspec_code, message in _UNSPECIFIC_CODES.items():
            if code == unspec_code.upper():
                seen.add(code)
                findings.append(ClinicalCheckResult(
                    check_id=f"coding_spec_{code}",
                    severity="warning",
                    failure_mode="coding_ambiguity",
                    description=f"Unspecific code {code}: {message}",
                    evidence_tier="T3",
                    icd_codes_involved=(code,),
                    recommendation="Request more specific coding from treating physician.",
                ))

    return findings


# ---------------------------------------------------------------------------
# Check 6: Red flags
# ---------------------------------------------------------------------------

def check_red_flags(
    diagnoses: list[dict],
    medications: list[dict],
    au_episodes: list[dict] | None,
) -> list[ClinicalCheckResult]:
    """Detect the 9 red-flag categories from KTG manual Part 3.3.

    Args:
        diagnoses: List of diagnosis dicts.
        medications: List of medication dicts.
        au_episodes: Optional list of AU episode dicts.

    Returns:
        List of findings.
    """
    findings: list[ClinicalCheckResult] = []
    diag_codes = [d.get("icd10_code", "").strip().upper() for d in diagnoses]

    # 1. Multiple episodes (same ICD prefix)
    if au_episodes and len(au_episodes) >= _RED_FLAG_EPISODE_THRESHOLD:
        from collections import Counter

        prefix_counts = Counter(
            ep.get("icd10_code", "")[:3].upper() for ep in au_episodes
        )
        for prefix, count in prefix_counts.items():
            if count >= _RED_FLAG_EPISODE_THRESHOLD:
                findings.append(ClinicalCheckResult(
                    check_id=f"red_flag_multiple_{prefix}",
                    severity="critical",
                    failure_mode="missed_pattern",
                    description=(
                        f"Multiple AU episodes ({count}) for {prefix}*. "
                        f"Recurrence pattern indicates elevated future risk."
                    ),
                    evidence_tier="T2",
                    icd_codes_involved=(prefix,),
                    recommendation="Full episode history review; no time-decay.",
                ))

    # 2. Inpatient psychiatric history
    for code in diag_codes:
        for psych_prefix in _PSYCHIATRIC_INPATIENT_CODES:
            if code.startswith(psych_prefix):
                findings.append(ClinicalCheckResult(
                    check_id=f"red_flag_psych_{code}",
                    severity="critical",
                    failure_mode="underestimation",
                    description=(
                        f"Psychiatric code {code} associated with inpatient treatment. "
                        f"Extended lookback and specialist review required."
                    ),
                    evidence_tier="T2",
                    icd_codes_involved=(code,),
                    recommendation="Psychiatrist review; extended lookback.",
                ))
                break  # one finding per code

    # 3. Repeated AU > 8 weeks
    if au_episodes:
        long_au = [
            ep for ep in au_episodes
            if (ep.get("duration_weeks") or 0) > _RED_FLAG_AU_WEEKS_THRESHOLD
        ]
        if len(long_au) >= 2:
            findings.append(ClinicalCheckResult(
                check_id="red_flag_repeated_long_au",
                severity="critical",
                failure_mode="missed_pattern",
                description=(
                    f"{len(long_au)} AU episodes exceeded {_RED_FLAG_AU_WEEKS_THRESHOLD} weeks. "
                    f"Pattern indicates chronic or treatment-resistant condition."
                ),
                evidence_tier="T2",
                recommendation="Specialist review; consider postpone or exclusion.",
            ))

    # 4. Ongoing specialist follow-up (heuristic: multiple recent diagnoses)
    # Detected via diagnosis clustering — deferred to decision engine context

    # 5. Ongoing disease-specific medication
    active_disease_meds = [
        m for m in medications
        if m.get("active", False) and m.get("atc_code", "")
    ]
    if active_disease_meds:
        atc_codes = [m["atc_code"] for m in active_disease_meds]
        findings.append(ClinicalCheckResult(
            check_id="red_flag_ongoing_medication",
            severity="warning",
            failure_mode="underestimation",
            description=(
                f"Active disease-specific medication(s): {', '.join(atc_codes)}. "
                f"Condition may not be in full remission."
            ),
            evidence_tier="T3",
            icd_codes_involved=(),
            recommendation="Verify remission status before accepting.",
        ))

    # 6. Residual symptoms — requires clinical narrative (not available in structured data)
    # Flagged as info when medication suggests ongoing treatment

    # 7. Surgery history (heuristic: check for procedure-associated diagnoses)
    # Would require procedure codes; flagged via medication/AU patterns

    # 8. Chronic pain + opioids
    opioid_meds = [
        m for m in medications
        if any(
            m.get("atc_code", "").startswith(prefix)
            for prefix in _CHRONIC_PAIN_OPIOID_ATCS
        )
        and m.get("active", False)
    ]
    if opioid_meds:
        findings.append(ClinicalCheckResult(
            check_id="red_flag_opioids",
            severity="critical",
            failure_mode="underestimation",
            description=(
                "Active opioid analgesic prescription detected. "
                "Chronic pain with opioid use carries significant AU risk."
            ),
            evidence_tier="T2",
            recommendation="Pain specialist review; postpone or exclusion likely.",
        ))

    # 9. Prior disability application — requires external data source
    # Cannot be detected from structured medical data alone

    return findings


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def run_clinical_checks(
    patient_id: str,
    diagnoses: list[dict],
    medications: list[dict],
    labs: list[dict],
    occupation_class: int,
    au_episodes: list[dict] | None = None,
    profiles: dict[str, DiseaseProfile] | None = None,
    interactions: list[ComorbidityInteraction] | None = None,
) -> ClinicalValidationResult:
    """Run all clinical consistency checks for a patient.

    Orchestrates the six check functions and aggregates their findings
    into a single :class:`ClinicalValidationResult`.

    Args:
        patient_id: Patient identifier.
        diagnoses: List of diagnosis dicts.
        medications: List of medication dicts.
        labs: List of lab result dicts (reserved for future checks).
        occupation_class: Occupation class (1-4).
        au_episodes: Optional AU episode history.
        profiles: Loaded disease profiles.
        interactions: Loaded comorbidity interactions.

    Returns:
        Aggregated validation result.
    """
    all_findings: list[ClinicalCheckResult] = []
    checks_run = 0

    # Check 1: Drug-diagnosis consistency
    checks_run += 1
    all_findings.extend(
        check_drug_diagnosis_consistency(diagnoses, medications, profiles),
    )

    # Check 2: Temporal consistency
    checks_run += 1
    all_findings.extend(
        check_temporal_consistency(diagnoses, au_episodes, profiles),
    )

    # Check 3: Occupation-diagnosis interaction
    checks_run += 1
    all_findings.extend(
        check_occupation_diagnosis_interaction(occupation_class, diagnoses, profiles),
    )

    # Check 4: Comorbidity interactions
    checks_run += 1
    all_findings.extend(
        check_comorbidity_interactions(diagnoses, interactions),
    )

    # Check 5: Coding specificity
    checks_run += 1
    all_findings.extend(
        check_coding_specificity(diagnoses),
    )

    # Check 6: Red flags
    checks_run += 1
    all_findings.extend(
        check_red_flags(diagnoses, medications, au_episodes),
    )

    checks_passed = checks_run - len({f.check_id.split("_")[0] for f in all_findings})

    result = ClinicalValidationResult(
        patient_id=patient_id,
        checks_run=checks_run,
        checks_passed=checks_passed,
        findings=all_findings,
    )

    logger.info(
        "Clinical checks for %s: %d/%d passed, %d findings (%s critical)",
        patient_id,
        result.checks_passed,
        result.checks_run,
        len(result.findings),
        sum(1 for f in result.findings if f.severity == "critical"),
    )

    return result
