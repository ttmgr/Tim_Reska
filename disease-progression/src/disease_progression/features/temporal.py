"""
disease_progression.features.temporal - Time-varying covariate engineering.

Constructs rolling-window features from longitudinal OMOP measurement and
condition data.  Designed for panel-data survival models, joint models,
and sequence-based architectures that consume time-stamped feature vectors.

Key capabilities:
    - Rolling aggregates (mean, min, max, slope, count) over 30-, 90-,
      and 365-day windows for lab measurements.
    - Visit-sequence encoding: inter-visit intervals, visit counts, gap
      flags for care fragmentation.
    - Time-varying binary indicators for new-onset comorbidities and
      medication exposure windows.
    - Flexible output as a long-format panel or a 3-D tensor
      (patient x time-step x feature) for sequence models.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from disease_progression.data.omop_etl import OMOPTables

logger = logging.getLogger(__name__)

DEFAULT_WINDOWS = [30, 90, 365]

# LOINC codes to track longitudinally (subset of clinically important labs)
DEFAULT_LAB_CODES: List[str] = [
    "4548-4",   # HbA1c
    "2160-0",   # Creatinine
    "48642-3",  # eGFR
    "33762-6",  # NT-proBNP
    "2093-3",   # Total Cholesterol
    "13457-7",  # LDL
    "2085-9",   # HDL
    "2571-8",   # Triglycerides
    "8480-6",   # Systolic BP
    "8462-4",   # Diastolic BP
]


def _linear_slope(values: pd.Series) -> float:
    """Compute simple linear slope over an index-aligned numeric series."""
    if len(values) < 2:
        return 0.0
    x = np.arange(len(values), dtype=float)
    y = values.values.astype(float)
    mask = ~np.isnan(y)
    if mask.sum() < 2:
        return 0.0
    x, y = x[mask], y[mask]
    slope = np.polyfit(x, y, 1)[0]
    return float(slope)


class TemporalFeatureExtractor:
    """Build time-varying features from longitudinal OMOP data.

    Parameters
    ----------
    windows : list of int
        Rolling window sizes in days (default: [30, 90, 365]).
    lab_codes : list of str
        LOINC codes for which to compute rolling statistics.
    time_step_days : int
        Spacing of the output time grid in days.  E.g. 30 produces
        monthly snapshots.  Used only by ``to_panel`` / ``to_tensor``.
    """

    def __init__(
        self,
        windows: Sequence[int] = DEFAULT_WINDOWS,
        lab_codes: Sequence[str] = DEFAULT_LAB_CODES,
        time_step_days: int = 30,
    ) -> None:
        self.windows = list(windows)
        self.lab_codes = list(lab_codes)
        self.time_step_days = time_step_days

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_lab_features(self, omop: OMOPTables) -> pd.DataFrame:
        """Compute rolling-window statistics for lab measurements.

        For each (person, lab_code, window) triple, computes:
            mean, min, max, last, count, slope

        Returns a long-format DataFrame with columns:
            person_id, measurement_date, feature_name, value
        """
        meas = omop.measurement.copy()
        if meas.empty:
            return pd.DataFrame(columns=["person_id", "measurement_date", "feature_name", "value"])

        meas["measurement_date"] = pd.to_datetime(meas["measurement_date"], errors="coerce")
        meas = meas.dropna(subset=["measurement_date", "value_as_number"])
        meas = meas.sort_values(["person_id", "measurement_date"])

        records: List[Dict[str, Any]] = []

        for pid, pid_group in meas.groupby("person_id"):
            for lab_code in self.lab_codes:
                lab_df = pid_group[pid_group["measurement_source_value"] == lab_code].copy()
                if lab_df.empty:
                    continue

                lab_df = lab_df.set_index("measurement_date").sort_index()
                values = lab_df["value_as_number"]

                # For each measurement date, compute rolling windows looking backward
                for ref_date in lab_df.index.unique():
                    for win in self.windows:
                        window_start = ref_date - pd.Timedelta(days=win)
                        window_vals = values.loc[window_start:ref_date]
                        if window_vals.empty:
                            continue

                        prefix = f"{lab_code}_w{win}d"
                        records.extend(
                            [
                                {"person_id": pid, "measurement_date": ref_date, "feature_name": f"{prefix}_mean", "value": float(window_vals.mean())},
                                {"person_id": pid, "measurement_date": ref_date, "feature_name": f"{prefix}_min", "value": float(window_vals.min())},
                                {"person_id": pid, "measurement_date": ref_date, "feature_name": f"{prefix}_max", "value": float(window_vals.max())},
                                {"person_id": pid, "measurement_date": ref_date, "feature_name": f"{prefix}_last", "value": float(window_vals.iloc[-1])},
                                {"person_id": pid, "measurement_date": ref_date, "feature_name": f"{prefix}_count", "value": float(len(window_vals))},
                                {"person_id": pid, "measurement_date": ref_date, "feature_name": f"{prefix}_slope", "value": _linear_slope(window_vals)},
                            ]
                        )

        result = pd.DataFrame(records)
        logger.info("Built %d lab feature records for %d patients", len(result), meas["person_id"].nunique())
        return result

    def build_visit_features(self, omop: OMOPTables) -> pd.DataFrame:
        """Derive visit-level features from measurement and condition dates.

        Features per person snapshot:
            visit_count_30d, visit_count_90d, visit_count_365d,
            days_since_last_visit, mean_inter_visit_interval,
            care_gap_flag (>90 days without a visit).

        Returns long-format DataFrame.
        """
        # Approximate "visits" from distinct measurement dates
        meas = omop.measurement.copy()
        cond = omop.condition_occurrence.copy()

        visit_dates: List[Dict[str, Any]] = []
        if not meas.empty and "measurement_date" in meas.columns:
            for _, row in meas[["person_id", "measurement_date"]].drop_duplicates().iterrows():
                visit_dates.append({"person_id": row["person_id"], "visit_date": row["measurement_date"]})
        if not cond.empty and "condition_start_date" in cond.columns:
            for _, row in cond[["person_id", "condition_start_date"]].drop_duplicates().iterrows():
                visit_dates.append({"person_id": row["person_id"], "visit_date": row["condition_start_date"]})

        if not visit_dates:
            return pd.DataFrame(columns=["person_id", "snapshot_date", "feature_name", "value"])

        visits = pd.DataFrame(visit_dates)
        visits["visit_date"] = pd.to_datetime(visits["visit_date"], errors="coerce")
        visits = visits.dropna(subset=["visit_date"]).drop_duplicates()
        visits = visits.sort_values(["person_id", "visit_date"])

        records: List[Dict[str, Any]] = []
        for pid, group in visits.groupby("person_id"):
            dates = group["visit_date"].sort_values()
            unique_dates = dates.drop_duplicates().reset_index(drop=True)

            if len(unique_dates) < 2:
                continue

            intervals = unique_dates.diff().dt.days.dropna()
            mean_interval = float(intervals.mean()) if len(intervals) > 0 else np.nan

            for ref_date in unique_dates:
                for win in self.windows:
                    window_start = ref_date - pd.Timedelta(days=win)
                    count = int(((unique_dates >= window_start) & (unique_dates <= ref_date)).sum())
                    records.append(
                        {"person_id": pid, "snapshot_date": ref_date,
                         "feature_name": f"visit_count_{win}d", "value": float(count)}
                    )

                # Days since last visit
                prior = unique_dates[unique_dates < ref_date]
                if len(prior) > 0:
                    gap = (ref_date - prior.iloc[-1]).days
                    records.append(
                        {"person_id": pid, "snapshot_date": ref_date,
                         "feature_name": "days_since_last_visit", "value": float(gap)}
                    )
                    records.append(
                        {"person_id": pid, "snapshot_date": ref_date,
                         "feature_name": "care_gap_flag", "value": 1.0 if gap > 90 else 0.0}
                    )

                records.append(
                    {"person_id": pid, "snapshot_date": ref_date,
                     "feature_name": "mean_inter_visit_interval", "value": mean_interval}
                )

        return pd.DataFrame(records)

    def build_condition_trajectory(self, omop: OMOPTables) -> pd.DataFrame:
        """Create time-varying binary indicators for new-onset conditions.

        At each snapshot date, a condition flag is 1 if the condition has
        been recorded on or before that date.  This encodes the
        irreversible ``healthy -> diagnosed`` transition for each
        comorbidity.

        Returns wide-format DataFrame: person_id, snapshot_date, <condition flags>.
        """
        cond = omop.condition_occurrence.copy()
        if cond.empty:
            return pd.DataFrame()

        cond["condition_start_date"] = pd.to_datetime(cond["condition_start_date"], errors="coerce")
        cond = cond.dropna(subset=["condition_start_date"])

        # Use 3-char ICD prefix to define condition groups
        cond["icd3"] = cond["condition_source_value"].str[:3]

        # Build a person-level timeline
        records: List[Dict[str, Any]] = []
        for pid, group in cond.groupby("person_id"):
            # All distinct condition onset dates as snapshot dates
            snapshot_dates = sorted(group["condition_start_date"].unique())
            codes_by_date: Dict[pd.Timestamp, set] = {}
            for _, row in group.iterrows():
                dt = row["condition_start_date"]
                codes_by_date.setdefault(dt, set()).add(row["icd3"])

            cumulative: set = set()
            for sd in snapshot_dates:
                cumulative = cumulative | codes_by_date.get(sd, set())
                row_dict: Dict[str, Any] = {"person_id": pid, "snapshot_date": sd}
                for code in cumulative:
                    row_dict[f"cond_{code}"] = 1
                records.append(row_dict)

        result = pd.DataFrame(records).fillna(0)
        return result

    def to_panel(self, omop: OMOPTables) -> pd.DataFrame:
        """Assemble all temporal features into a regular-grid panel.

        Produces a DataFrame indexed by (person_id, time_step) where
        time_step is a calendar date sampled at ``self.time_step_days``
        intervals within each person's observation period.

        Missing values are forward-filled (LOCF -- last observation
        carried forward), a standard approach in clinical data.
        """
        obs_period = omop.observation_period
        if obs_period.empty:
            logger.warning("No observation periods; cannot build panel.")
            return pd.DataFrame()

        # Build lab features in wide form
        lab_long = self.build_lab_features(omop)
        if lab_long.empty:
            logger.warning("No lab features; panel will be empty.")
            return pd.DataFrame()

        lab_wide = lab_long.pivot_table(
            index=["person_id", "measurement_date"],
            columns="feature_name",
            values="value",
            aggfunc="last",
        ).reset_index()

        # Create regular time grid per person
        panel_rows: List[pd.DataFrame] = []
        for _, op in obs_period.iterrows():
            pid = op["person_id"]
            start = pd.Timestamp(op["observation_period_start_date"])
            end = pd.Timestamp(op["observation_period_end_date"])
            if pd.isna(start) or pd.isna(end):
                continue
            grid = pd.date_range(start, end, freq=f"{self.time_step_days}D")
            if len(grid) == 0:
                continue
            grid_df = pd.DataFrame({"person_id": pid, "time_step": grid})
            panel_rows.append(grid_df)

        if not panel_rows:
            return pd.DataFrame()

        panel = pd.concat(panel_rows, ignore_index=True)

        # Merge lab features (asof join -- LOCF)
        lab_wide = lab_wide.rename(columns={"measurement_date": "time_step"})
        lab_wide["time_step"] = pd.to_datetime(lab_wide["time_step"])
        panel["time_step"] = pd.to_datetime(panel["time_step"])

        panel = panel.sort_values(["person_id", "time_step"])
        lab_wide = lab_wide.sort_values(["person_id", "time_step"])

        merged = pd.merge_asof(
            panel,
            lab_wide,
            on="time_step",
            by="person_id",
            direction="backward",
        )
        merged = merged.set_index(["person_id", "time_step"]).sort_index()
        merged = merged.groupby("person_id", group_keys=False).ffill()

        logger.info("Panel: %d rows, %d features", len(merged), merged.shape[1])
        return merged

    def to_tensor(self, omop: OMOPTables) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Convert panel data into a 3-D numpy array for sequence models.

        Returns
        -------
        X : ndarray of shape (n_patients, max_seq_len, n_features)
            Zero-padded feature tensor.
        lengths : ndarray of shape (n_patients,)
            Actual sequence length per patient.
        feature_names : list of str
            Column names for the feature dimension.
        """
        panel = self.to_panel(omop)
        if panel.empty:
            return np.empty((0, 0, 0)), np.array([]), []

        feature_cols = [c for c in panel.columns if c not in ("person_id", "time_step")]
        panel = panel[feature_cols].astype(float)

        person_ids = panel.index.get_level_values("person_id").unique()
        max_len = panel.groupby("person_id").size().max()
        n_features = len(feature_cols)

        X = np.zeros((len(person_ids), max_len, n_features), dtype=np.float32)
        lengths = np.zeros(len(person_ids), dtype=np.int64)

        for i, pid in enumerate(person_ids):
            seq = panel.loc[pid].values
            seq_len = len(seq)
            X[i, :seq_len, :] = np.nan_to_num(seq, nan=0.0)
            lengths[i] = seq_len

        logger.info("Tensor shape: %s, mean seq length: %.1f", X.shape, lengths.mean())
        return X, lengths, feature_cols
