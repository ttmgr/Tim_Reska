"""Structured audit logging for underwriting decisions.

Every model-assisted decision is logged as a JSON Lines entry with full
traceability: input quality, model used, prediction, reliability assessment,
and any human overrides.

Designed for EU AI Act Art. 12 (record-keeping) compliance.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    """Single decision audit record.

    Attributes:
        timestamp: ISO 8601 timestamp.
        patient_id: Patient identifier.
        run_id: UUID for this pipeline run.
        model_version: System version string.
        data_profile: DataProfile used for routing.
        model_id: Which sub-model produced the prediction.
        features_used: List of feature columns.
        features_missing: Features that were absent.
        dqs_score: Composite DQS value.
        dqs_tier: DQS tier classification.
        dqs_components: Dict of DQS component scores.
        predicted_probability: Model's predicted P(high_risk).
        reliability_decision: Cost-optimal decision.
        p_wrong: Estimated P(model is wrong).
        explanation: Human-readable decision explanation.
        human_override: Override info if decision was overridden.
    """

    timestamp: str = ""
    patient_id: str = ""
    run_id: str = ""
    model_version: str = "v2.0.0"
    data_profile: str = ""
    model_id: str = ""
    features_used: list[str] = field(default_factory=list)
    features_missing: list[str] = field(default_factory=list)
    dqs_score: float = 0.0
    dqs_tier: str = ""
    dqs_components: dict[str, float] = field(default_factory=dict)
    predicted_probability: float = 0.0
    reliability_decision: str = ""
    p_wrong: float = 0.0
    explanation: str = ""
    human_override: dict | None = None


class AuditLogger:
    """Append-only JSON Lines audit logger.

    Writes one JSON object per line to an audit log file. Supports
    querying by patient_id, run_id, or date range.

    Attributes:
        log_path: Path to the audit log file.
    """

    def __init__(self, log_path: str | Path) -> None:
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_decision(self, entry: AuditEntry) -> None:
        """Append a single decision to the audit log.

        Args:
            entry: AuditEntry to log.
        """
        if not entry.timestamp:
            entry.timestamp = datetime.now(tz=UTC).isoformat()
        if not entry.run_id:
            entry.run_id = str(uuid.uuid4())

        record = asdict(entry)
        with self.log_path.open("a") as f:
            f.write(json.dumps(record, default=str) + "\n")

        logger.debug("Logged decision for patient %s", entry.patient_id)

    def log_batch(self, entries: list[AuditEntry]) -> None:
        """Append multiple decisions to the audit log.

        Args:
            entries: List of AuditEntry objects.
        """
        run_id = str(uuid.uuid4())
        timestamp = datetime.now(tz=UTC).isoformat()

        with self.log_path.open("a") as f:
            for entry in entries:
                if not entry.timestamp:
                    entry.timestamp = timestamp
                if not entry.run_id:
                    entry.run_id = run_id
                record = asdict(entry)
                f.write(json.dumps(record, default=str) + "\n")

        logger.info("Logged %d decisions (run_id=%s)", len(entries), run_id)

    def query(
        self,
        patient_id: str | None = None,
        run_id: str | None = None,
        decision: str | None = None,
        limit: int = 1000,
    ) -> list[AuditEntry]:
        """Query audit log entries.

        Args:
            patient_id: Filter by patient ID.
            run_id: Filter by run ID.
            decision: Filter by reliability decision.
            limit: Maximum entries to return.

        Returns:
            List of matching AuditEntry objects.
        """
        if not self.log_path.exists():
            return []

        results: list[AuditEntry] = []

        with self.log_path.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                record = json.loads(line)

                if patient_id and record.get("patient_id") != patient_id:
                    continue
                if run_id and record.get("run_id") != run_id:
                    continue
                if decision and record.get("reliability_decision") != decision:
                    continue

                results.append(
                    AuditEntry(
                        **{k: v for k, v in record.items() if k in AuditEntry.__dataclass_fields__}
                    )
                )

                if len(results) >= limit:
                    break

        return results

    def count(self) -> int:
        """Count total entries in the audit log."""
        if not self.log_path.exists():
            return 0
        with self.log_path.open() as f:
            return sum(1 for line in f if line.strip())
