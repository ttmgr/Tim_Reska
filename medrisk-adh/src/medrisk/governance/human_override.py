"""Human override support for model-assisted decisions.

Provides schema and application logic for when a human underwriter
overrides the model's recommendation. All overrides are logged to
the audit trail for compliance.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from medrisk.governance.audit_log import AuditEntry, AuditLogger

logger = logging.getLogger(__name__)


@dataclass
class HumanOverride:
    """Record of a human override on a model decision.

    Attributes:
        override_id: Unique identifier for this override.
        patient_id: Patient whose decision was overridden.
        original_decision: The model's recommendation.
        override_decision: The human's decision.
        override_reason: Free-text reason for the override.
        overrider_id: Anonymized identifier for the overriding person.
        timestamp: When the override was made.
    """

    override_id: str = ""
    patient_id: str = ""
    original_decision: str = ""
    override_decision: str = ""
    override_reason: str = ""
    overrider_id: str = "anonymous"
    timestamp: str = ""


def apply_override(
    audit_entry: AuditEntry,
    override: HumanOverride,
    audit_logger: AuditLogger,
) -> AuditEntry:
    """Apply a human override and log it.

    Creates a new audit entry recording the override, linked to the
    original decision.

    Args:
        audit_entry: The original model decision.
        override: The human override details.
        audit_logger: Logger to record the override.

    Returns:
        Updated AuditEntry with override information.
    """
    if not override.override_id:
        override.override_id = str(uuid.uuid4())
    if not override.timestamp:
        override.timestamp = datetime.now(tz=UTC).isoformat()
    if not override.patient_id:
        override.patient_id = audit_entry.patient_id

    override.original_decision = audit_entry.reliability_decision

    # Create override audit entry
    override_entry = AuditEntry(
        patient_id=audit_entry.patient_id,
        run_id=audit_entry.run_id,
        model_version=audit_entry.model_version,
        data_profile=audit_entry.data_profile,
        model_id=audit_entry.model_id,
        dqs_score=audit_entry.dqs_score,
        dqs_tier=audit_entry.dqs_tier,
        predicted_probability=audit_entry.predicted_probability,
        reliability_decision=override.override_decision,
        p_wrong=audit_entry.p_wrong,
        explanation=f"HUMAN OVERRIDE: {override.override_reason}",
        human_override={
            "override_id": override.override_id,
            "original_decision": override.original_decision,
            "override_decision": override.override_decision,
            "reason": override.override_reason,
            "overrider_id": override.overrider_id,
            "timestamp": override.timestamp,
        },
    )

    audit_logger.log_decision(override_entry)

    logger.info(
        "Override applied: patient=%s, %s -> %s, reason=%s",
        override.patient_id,
        override.original_decision,
        override.override_decision,
        override.override_reason,
    )

    return override_entry
