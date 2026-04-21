"""
disease_progression.evaluation.fairness - Subgroup performance audits.

Provides tools for assessing model fairness across demographic and
clinically relevant subgroups.  In healthcare ML, equitable performance
is not merely desirable but often a regulatory requirement
(e.g. FDA guidance on AI/ML in medical devices, EU AI Act).

Key capabilities:
    - Compute discrimination metrics (C-index, AUC) per subgroup defined
      by age, sex, race/ethnicity, socioeconomic proxies, or any
      categorical attribute.
    - Identify performance gaps between privileged and unprivileged
      groups.
    - Generate structured audit reports suitable for model cards,
      regulatory submissions, and internal review boards.
    - Parity ratio and disparity metrics (e.g. the ratio of worst-group
      C-index to best-group C-index).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from disease_progression.evaluation.metrics import (
    concordance_index,
    time_dependent_auc,
)

logger = logging.getLogger(__name__)


class FairnessAuditor:
    """Audit survival model performance across demographic subgroups.

    Parameters
    ----------
    protected_attributes : list of str
        Column names in the evaluation DataFrame that define subgroups
        (e.g. ``["sex_male", "age_group", "race_concept_id"]``).
    min_group_size : int
        Minimum number of subjects in a subgroup to include it in the
        report.  Small groups yield unreliable metrics.
    """

    def __init__(
        self,
        protected_attributes: Sequence[str],
        min_group_size: int = 30,
    ) -> None:
        self.protected_attributes = list(protected_attributes)
        self.min_group_size = min_group_size

    def audit(
        self,
        df: pd.DataFrame,
        event_time_col: str = "duration",
        event_col: str = "event",
        risk_col: str = "predicted_risk",
        eval_times: Optional[np.ndarray] = None,
    ) -> pd.DataFrame:
        """Run the full fairness audit.

        Parameters
        ----------
        df : pd.DataFrame
            Must contain event times, event indicators, predicted risk
            scores, and protected attribute columns.
        event_time_col : str
        event_col : str
        risk_col : str
        eval_times : ndarray, optional
            Time points for time-dependent AUC.  If None, uses quartiles
            of the event time distribution.

        Returns
        -------
        pd.DataFrame
            Audit results with columns: attribute, group, n, n_events,
            c_index, mean_td_auc (if eval_times provided).
        """
        if eval_times is None:
            event_times_all = df[event_time_col].values
            eval_times = np.quantile(event_times_all[event_times_all > 0], [0.25, 0.5, 0.75])

        rows: List[Dict[str, Any]] = []

        # Overall performance
        overall_ci = concordance_index(
            df[event_time_col].values,
            df[risk_col].values,
            df[event_col].values,
        )
        rows.append({
            "attribute": "overall",
            "group": "all",
            "n": len(df),
            "n_events": int(df[event_col].sum()),
            "c_index": overall_ci,
            "mean_td_auc": np.nan,
        })

        # Per-attribute, per-group
        for attr in self.protected_attributes:
            if attr not in df.columns:
                logger.warning("Attribute '%s' not in DataFrame; skipping.", attr)
                continue

            for group_val, group_df in df.groupby(attr):
                if len(group_df) < self.min_group_size:
                    logger.debug(
                        "Skipping %s=%s (n=%d < min_group_size=%d)",
                        attr, group_val, len(group_df), self.min_group_size,
                    )
                    continue

                event_times = group_df[event_time_col].values
                events = group_df[event_col].values
                risk = group_df[risk_col].values

                ci = concordance_index(event_times, risk, events)

                mean_auc = np.nan
                if eval_times is not None and len(eval_times) > 0:
                    try:
                        auc_df = time_dependent_auc(event_times, events, risk, eval_times)
                        mean_auc = float(auc_df["auc"].dropna().mean())
                    except Exception as exc:
                        logger.debug("AUC computation failed for %s=%s: %s", attr, group_val, exc)

                rows.append({
                    "attribute": attr,
                    "group": str(group_val),
                    "n": len(group_df),
                    "n_events": int(events.sum()),
                    "c_index": ci,
                    "mean_td_auc": mean_auc,
                })

        result = pd.DataFrame(rows)
        logger.info("Fairness audit: %d groups evaluated", len(result))
        return result

    def disparity_report(
        self,
        audit_df: pd.DataFrame,
        metric: str = "c_index",
    ) -> pd.DataFrame:
        """Compute parity ratios and disparity metrics from audit results.

        For each protected attribute, computes:
            - Best-group and worst-group performance
            - Disparity ratio = worst / best
            - Absolute gap = best - worst
            - Whether the attribute passes a parity threshold (default 0.8)

        Parameters
        ----------
        audit_df : pd.DataFrame
            Output of ``audit()``.
        metric : str
            Which metric column to assess (default ``"c_index"``).

        Returns
        -------
        pd.DataFrame
            Columns: attribute, best_group, best_value, worst_group,
            worst_value, disparity_ratio, absolute_gap, passes_80_rule.
        """
        rows: List[Dict[str, Any]] = []
        non_overall = audit_df[audit_df["attribute"] != "overall"]

        for attr, group in non_overall.groupby("attribute"):
            valid = group.dropna(subset=[metric])
            if valid.empty:
                continue

            best_idx = valid[metric].idxmax()
            worst_idx = valid[metric].idxmin()
            best_val = float(valid.loc[best_idx, metric])
            worst_val = float(valid.loc[worst_idx, metric])

            ratio = worst_val / best_val if best_val > 0 else 0.0

            rows.append({
                "attribute": attr,
                "best_group": valid.loc[best_idx, "group"],
                "best_value": best_val,
                "worst_group": valid.loc[worst_idx, "group"],
                "worst_value": worst_val,
                "disparity_ratio": ratio,
                "absolute_gap": best_val - worst_val,
                "passes_80_rule": ratio >= 0.8,
            })

        result = pd.DataFrame(rows)
        logger.info(
            "Disparity report: %d attributes, %d pass 80%% rule",
            len(result),
            int(result["passes_80_rule"].sum()) if not result.empty else 0,
        )
        return result

    def generate_report_text(
        self,
        audit_df: pd.DataFrame,
        disparity_df: pd.DataFrame,
    ) -> str:
        """Generate a human-readable fairness report.

        Parameters
        ----------
        audit_df : pd.DataFrame
            Output of ``audit()``.
        disparity_df : pd.DataFrame
            Output of ``disparity_report()``.

        Returns
        -------
        str
            Markdown-formatted report text.
        """
        lines: List[str] = []
        lines.append("## Fairness Audit Report\n")

        # Overall
        overall = audit_df[audit_df["attribute"] == "overall"]
        if not overall.empty:
            ov = overall.iloc[0]
            lines.append(f"**Overall Performance**: C-index = {ov['c_index']:.4f} "
                         f"(n={int(ov['n'])}, events={int(ov['n_events'])})\n")

        # Per-attribute summary
        lines.append("### Subgroup Performance\n")
        non_overall = audit_df[audit_df["attribute"] != "overall"]
        if not non_overall.empty:
            lines.append(non_overall.to_markdown(index=False))
            lines.append("")

        # Disparity
        lines.append("### Disparity Analysis\n")
        if not disparity_df.empty:
            lines.append(disparity_df.to_markdown(index=False))
            lines.append("")

            failing = disparity_df[~disparity_df["passes_80_rule"]]
            if not failing.empty:
                lines.append("**Attributes failing the 80% parity rule:**\n")
                for _, row in failing.iterrows():
                    lines.append(
                        f"- **{row['attribute']}**: worst group '{row['worst_group']}' "
                        f"({row['worst_value']:.4f}) vs best '{row['best_group']}' "
                        f"({row['best_value']:.4f}), ratio = {row['disparity_ratio']:.3f}"
                    )
                lines.append("")
            else:
                lines.append("All attributes pass the 80% parity rule.\n")
        else:
            lines.append("No disparity data available.\n")

        return "\n".join(lines)
