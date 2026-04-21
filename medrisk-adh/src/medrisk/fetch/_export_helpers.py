"""
_export_helpers.py — Analysis-ready reshaping helpers for exported CohortDataset tables.

Three outputs:
  1. build_survival_frame()  -- tidy survival data frame (time-to-event, event indicator)
  2. build_multistate_frame() -- transition records for multi-state models
  3. build_cgm_sequences()   -- resampled CGM time series windows
"""

from __future__ import annotations

import logging

import pandas as pd

_log = logging.getLogger(__name__)


def build_survival_frame(
    persons: pd.DataFrame,
    events: pd.DataFrame,
    event_codes: list[str],
    code_system: str | None = None,
    time_origin_col: str = "baseline_date",
    censor_date: str | None = None,
) -> pd.DataFrame:
    """
    Build a tidy right-censored survival data frame.

    Parameters
    ----------
    persons     : DataFrame with columns [person_id, baseline_date, ...]
    events      : DataFrame with columns [person_id, event_date, code, code_system, ...]
    event_codes : List of codes that count as the event of interest
    code_system : If given, only match events with this code_system
    time_origin_col : Column in persons that defines time origin (default "baseline_date")
    censor_date : ISO date string for administrative censoring (default: max event date)

    Returns
    -------
    DataFrame with columns:
        person_id, time_to_event (days), event (0=censored, 1=event), baseline_date
    """
    if events.empty or persons.empty:
        return pd.DataFrame(columns=["person_id", "time_to_event", "event"])

    # Filter events to codes of interest
    mask = events["code"].isin(event_codes)
    if code_system:
        mask &= events["code_system"] == code_system
    incident = events[mask].copy()
    incident["event_date"] = pd.to_datetime(incident["event_date"])

    # First event per person
    first_events = (
        incident.sort_values("event_date")
        .groupby("person_id")["event_date"]
        .first()
        .reset_index()
        .rename(columns={"event_date": "first_event_date"})
    )

    persons = persons.copy()
    persons["baseline_date"] = pd.to_datetime(persons[time_origin_col], errors="coerce")

    frame = persons[["person_id", "baseline_date"]].merge(first_events, on="person_id", how="left")

    if censor_date:
        censor = pd.Timestamp(censor_date)
    else:
        censor = incident["event_date"].max() if not incident.empty else pd.Timestamp.now()

    frame["event"] = frame["first_event_date"].notna().astype(int)
    frame["end_date"] = frame["first_event_date"].fillna(censor)
    frame["time_to_event"] = (frame["end_date"] - frame["baseline_date"]).dt.days

    # Drop rows with missing baseline
    frame = frame.dropna(subset=["baseline_date", "time_to_event"])
    frame = frame[frame["time_to_event"] >= 0]

    _log.debug(
        "build_survival_frame: %d persons, %d events, codes=%s",
        len(frame),
        frame["event"].sum(),
        event_codes,
    )
    return frame[["person_id", "time_to_event", "event", "baseline_date"]].reset_index(drop=True)


def build_multistate_frame(
    persons: pd.DataFrame,
    events: pd.DataFrame,
    states: list[str],
    transition_codes: dict[tuple[str, str], list[str]],
    time_origin_col: str = "baseline_date",
) -> pd.DataFrame:
    """
    Build transition records suitable for msm / mstate / pymsm.

    Parameters
    ----------
    persons           : DataFrame with [person_id, baseline_date]
    events            : DataFrame with [person_id, event_date, code, code_system]
    states            : Ordered list of state names, e.g. ["healthy", "diabetes", "CKD", "death"]
    transition_codes  : {(from_state, to_state): [code, ...]}
    time_origin_col   : Column in persons for time zero

    Returns
    -------
    DataFrame with columns:
        person_id, from_state, to_state, time (days from baseline)
    """
    persons = persons.copy()
    persons["baseline_date"] = pd.to_datetime(persons[time_origin_col], errors="coerce")
    events = events.copy()
    events["event_date"] = pd.to_datetime(events["event_date"], errors="coerce")

    baseline_map = persons.set_index("person_id")["baseline_date"].to_dict()
    rows = []

    for (from_state, to_state), codes in transition_codes.items():
        relevant = events[events["code"].isin(codes)]
        for _, ev in relevant.iterrows():
            pid = ev["person_id"]
            baseline = baseline_map.get(pid)
            if baseline is None or pd.isna(baseline):
                continue
            days = (ev["event_date"] - baseline).days
            if days < 0:
                continue
            rows.append(
                {
                    "person_id": pid,
                    "from_state": from_state,
                    "to_state": to_state,
                    "time": days,
                    "event_date": ev["event_date"],
                    "code": ev["code"],
                }
            )

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["person_id", "from_state", "to_state", "time"])

    # Sort by person and time; keep first transition per (person, from->to) pair
    df = (
        df.sort_values(["person_id", "time"])
        .drop_duplicates(subset=["person_id", "from_state", "to_state"], keep="first")
        .reset_index(drop=True)
    )
    _log.debug("build_multistate_frame: %d transitions", len(df))
    return df[["person_id", "from_state", "to_state", "time", "event_date", "code"]]


def build_cgm_sequences(
    measurements: pd.DataFrame,
    person_ids: list[str] | None = None,
    resample_freq: str = "5min",
    gap_fill_limit: str = "30min",
    window_hours: int = 24,
) -> pd.DataFrame:
    """
    Build regular CGM time series windows for sequence modeling.

    Parameters
    ----------
    measurements  : DataFrame with [person_id, measured_at, measure_type, value]
    person_ids    : Subset of person IDs to include (None = all)
    resample_freq : Resampling frequency, e.g. "5min"
    gap_fill_limit: Maximum gap to forward-fill (gaps beyond this become NaN)
    window_hours  : Length of each output window in hours

    Returns
    -------
    DataFrame indexed by (person_id, window_start) with time-step columns
    (window_step_0, window_step_1, ...) containing glucose values.
    """
    cgm = measurements[
        measurements["measure_type"].isin(["glucose_mg_dl", "glucose_mmol_l", "glucose"])
    ].copy()

    if person_ids:
        cgm = cgm[cgm["person_id"].isin(person_ids)]

    if cgm.empty:
        return pd.DataFrame()

    cgm["measured_at"] = pd.to_datetime(cgm["measured_at"])
    steps_per_window = int(window_hours * 60 / pd.Timedelta(resample_freq).total_seconds() * 60)
    all_windows = []

    for pid, grp in cgm.groupby("person_id"):
        ts = grp.set_index("measured_at")["value"].sort_index()
        ts = ts.resample(resample_freq).mean()
        # Forward-fill up to gap_fill_limit (pandas 2.x uses ffill() not fillna(method=))
        fill_limit = int(pd.Timedelta(gap_fill_limit) / pd.Timedelta(resample_freq))
        ts = ts.ffill(limit=fill_limit)

        # Slide a window of steps_per_window
        for start_idx in range(0, len(ts) - steps_per_window + 1, steps_per_window):
            window = ts.iloc[start_idx : start_idx + steps_per_window]
            row = {"person_id": pid, "window_start": window.index[0]}
            for i, val in enumerate(window.values):
                row[f"step_{i:04d}"] = val
            all_windows.append(row)

    if not all_windows:
        return pd.DataFrame()

    result = pd.DataFrame(all_windows).set_index(["person_id", "window_start"])
    _log.debug(
        "build_cgm_sequences: %d windows across %d persons",
        len(result),
        cgm["person_id"].nunique(),
    )
    return result
