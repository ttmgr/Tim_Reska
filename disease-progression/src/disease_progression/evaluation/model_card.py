"""
disease_progression.evaluation.model_card - Automated model card generation.

Generates a structured model card in Markdown format following the
template proposed by Mitchell et al. (2019, "Model Cards for Model
Reporting").  Tailored for survival analysis models in clinical /
health-insurance contexts.

Sections:
    1. Model Details (name, version, type, framework)
    2. Intended Use (primary use, out-of-scope uses)
    3. Training Data (source, size, inclusion/exclusion criteria)
    4. Evaluation Data (test set description)
    5. Metrics (C-index, AUC, Brier score, calibration)
    6. Fairness Analysis (subgroup performance, disparity)
    7. Ethical Considerations
    8. Caveats and Recommendations
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def generate_model_card(
    model_name: str,
    model_type: str,
    version: str = "0.1.0",
    description: str = "",
    intended_use: str = "",
    out_of_scope: str = "",
    training_data_description: str = "",
    training_data_size: Optional[int] = None,
    evaluation_data_description: str = "",
    evaluation_data_size: Optional[int] = None,
    metrics: Optional[Dict[str, Any]] = None,
    fairness_audit: Optional[pd.DataFrame] = None,
    fairness_disparity: Optional[pd.DataFrame] = None,
    ethical_considerations: Optional[List[str]] = None,
    caveats: Optional[List[str]] = None,
    hyperparameters: Optional[Dict[str, Any]] = None,
    output_path: Optional[str] = None,
) -> str:
    """Generate a model card in Markdown format.

    Parameters
    ----------
    model_name : str
        Display name of the model.
    model_type : str
        Type (e.g. "Cox PH", "DeepSurv", "SurvTRACE").
    version : str
    description : str
        Brief model description.
    intended_use : str
        Description of the intended deployment context.
    out_of_scope : str
        Use cases the model is NOT designed for.
    training_data_description : str
    training_data_size : int, optional
    evaluation_data_description : str
    evaluation_data_size : int, optional
    metrics : dict, optional
        Evaluation metrics (from ``evaluate_survival_model``).
    fairness_audit : pd.DataFrame, optional
        Output from ``FairnessAuditor.audit()``.
    fairness_disparity : pd.DataFrame, optional
        Output from ``FairnessAuditor.disparity_report()``.
    ethical_considerations : list of str, optional
    caveats : list of str, optional
    hyperparameters : dict, optional
        Model hyperparameters to document.
    output_path : str, optional
        If provided, write the card to this file.

    Returns
    -------
    str
        Complete model card in Markdown.
    """
    lines: List[str] = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ---- Header ----
    lines.append(f"# Model Card: {model_name}\n")
    lines.append(f"*Generated: {now}*\n")

    # ---- 1. Model Details ----
    lines.append("## 1. Model Details\n")
    lines.append(f"- **Model name**: {model_name}")
    lines.append(f"- **Model type**: {model_type}")
    lines.append(f"- **Version**: {version}")
    lines.append(f"- **Framework**: disease_progression v0.1.0")
    if description:
        lines.append(f"- **Description**: {description}")
    lines.append("")

    if hyperparameters:
        lines.append("### Hyperparameters\n")
        lines.append("| Parameter | Value |")
        lines.append("|-----------|-------|")
        for k, v in hyperparameters.items():
            lines.append(f"| {k} | {v} |")
        lines.append("")

    # ---- 2. Intended Use ----
    lines.append("## 2. Intended Use\n")
    if intended_use:
        lines.append(f"**Primary use**: {intended_use}\n")
    else:
        lines.append(
            "**Primary use**: Risk stratification and disease progression "
            "prediction in clinical research settings. Not intended for "
            "direct clinical decision-making without expert oversight.\n"
        )
    if out_of_scope:
        lines.append(f"**Out of scope**: {out_of_scope}\n")
    else:
        lines.append(
            "**Out of scope**: Individual-level clinical decisions, "
            "populations not represented in training data, real-time "
            "bedside prediction without clinical validation.\n"
        )

    # ---- 3. Training Data ----
    lines.append("## 3. Training Data\n")
    if training_data_description:
        lines.append(f"{training_data_description}\n")
    if training_data_size is not None:
        lines.append(f"- **Training set size**: {training_data_size:,} subjects\n")

    # ---- 4. Evaluation Data ----
    lines.append("## 4. Evaluation Data\n")
    if evaluation_data_description:
        lines.append(f"{evaluation_data_description}\n")
    if evaluation_data_size is not None:
        lines.append(f"- **Evaluation set size**: {evaluation_data_size:,} subjects\n")

    # ---- 5. Metrics ----
    lines.append("## 5. Performance Metrics\n")
    if metrics:
        # Scalar metrics
        scalar_metrics = {k: v for k, v in metrics.items() if isinstance(v, (int, float, np.floating))}
        if scalar_metrics:
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            for k, v in scalar_metrics.items():
                if isinstance(v, float):
                    lines.append(f"| {k} | {v:.4f} |")
                else:
                    lines.append(f"| {k} | {v} |")
            lines.append("")

        # Time-dependent AUC table
        if "td_auc" in metrics and isinstance(metrics["td_auc"], pd.DataFrame):
            lines.append("### Time-Dependent AUC\n")
            auc_df = metrics["td_auc"]
            lines.append("| Time | AUC | Cases | Controls |")
            lines.append("|------|-----|-------|----------|")
            for _, row in auc_df.iterrows():
                auc_val = f"{row['auc']:.4f}" if not np.isnan(row['auc']) else "N/A"
                lines.append(f"| {row['time']:.1f} | {auc_val} | {int(row['n_cases'])} | {int(row['n_controls'])} |")
            lines.append("")

        # Calibration table
        if "cif_calibration" in metrics and isinstance(metrics["cif_calibration"], pd.DataFrame):
            lines.append("### CIF Calibration\n")
            cal_df = metrics["cif_calibration"]
            lines.append("| Group | N | Predicted | Observed | |Diff| |")
            lines.append("|-------|---|-----------|----------|-------|")
            for _, row in cal_df.iterrows():
                lines.append(
                    f"| {int(row['group'])} | {int(row['n'])} | "
                    f"{row['predicted_mean']:.4f} | {row['observed_rate']:.4f} | "
                    f"{row['abs_diff']:.4f} |"
                )
            lines.append("")
    else:
        lines.append("*No metrics provided.*\n")

    # ---- 6. Fairness Analysis ----
    lines.append("## 6. Fairness Analysis\n")
    if fairness_audit is not None and not fairness_audit.empty:
        lines.append("### Subgroup Performance\n")
        display_cols = ["attribute", "group", "n", "n_events", "c_index"]
        if "mean_td_auc" in fairness_audit.columns:
            display_cols.append("mean_td_auc")
        lines.append(fairness_audit[display_cols].to_markdown(index=False))
        lines.append("")

        if fairness_disparity is not None and not fairness_disparity.empty:
            lines.append("### Disparity Summary\n")
            lines.append(fairness_disparity.to_markdown(index=False))
            lines.append("")

            failing = fairness_disparity[~fairness_disparity["passes_80_rule"]]
            if not failing.empty:
                lines.append(
                    "> **Warning**: The following attributes fail the 80% "
                    "parity rule, indicating potential unfairness:\n"
                )
                for _, row in failing.iterrows():
                    lines.append(f"> - {row['attribute']}: disparity ratio = {row['disparity_ratio']:.3f}")
                lines.append("")
    else:
        lines.append("*No fairness audit data provided.*\n")

    # ---- 7. Ethical Considerations ----
    lines.append("## 7. Ethical Considerations\n")
    default_ethics = [
        "This model is trained on synthetic or retrospective data and has "
        "not been validated in a prospective clinical trial.",
        "Survival predictions should not be communicated to patients without "
        "clinical context and expert interpretation.",
        "Performance may degrade on populations not represented in the "
        "training data (distribution shift).",
        "The model does not account for social determinants of health that "
        "may influence outcomes but are not captured in EHR data.",
    ]
    ethics = ethical_considerations if ethical_considerations else default_ethics
    for item in ethics:
        lines.append(f"- {item}")
    lines.append("")

    # ---- 8. Caveats and Recommendations ----
    lines.append("## 8. Caveats and Recommendations\n")
    default_caveats = [
        "External validation on an independent cohort is required before "
        "any deployment.",
        "The model assumes non-informative censoring; violation of this "
        "assumption may bias results.",
        "Competing risks are handled under a cause-specific framework; "
        "interpretation of CIFs requires care in the presence of "
        "dependent competing events.",
        "Regular monitoring for performance drift is recommended if the "
        "model is deployed in a production setting.",
    ]
    cavs = caveats if caveats else default_caveats
    for item in cavs:
        lines.append(f"- {item}")
    lines.append("")

    card_text = "\n".join(lines)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(card_text)
        logger.info("Model card written to %s", output_path)

    return card_text
