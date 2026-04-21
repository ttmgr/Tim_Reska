"""
disease_progression.evaluation - Model evaluation and reporting.

Submodules:
    - ``metrics``: Concordance index, time-dependent AUC, integrated
      Brier score, CIF calibration metrics.
    - ``fairness``: Subgroup performance audits by demographic attributes.
    - ``model_card``: Automated model card generation in Markdown format.
"""

from disease_progression.evaluation.metrics import (
    concordance_index,
    time_dependent_auc,
    integrated_brier_score,
    cif_calibration,
)
from disease_progression.evaluation.fairness import FairnessAuditor
from disease_progression.evaluation.model_card import generate_model_card

__all__ = [
    "concordance_index",
    "time_dependent_auc",
    "integrated_brier_score",
    "cif_calibration",
    "FairnessAuditor",
    "generate_model_card",
]
