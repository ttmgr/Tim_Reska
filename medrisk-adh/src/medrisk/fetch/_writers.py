"""
_writers.py — Parquet/feather export for CohortDataset tables.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

from medrisk.fetch._schema import CohortDataset

_log = logging.getLogger(__name__)

_TABLE_NAMES = ("persons", "measurements", "events", "treatments")


def _serialise_extras(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert any 'extra' column from dict to JSON string so pyarrow can write it.
    Parquet cannot serialise struct types with no fields (empty dicts become
    zero-field Arrow structs, which are unsupported).
    """
    if "extra" in df.columns:
        df = df.copy()
        df["extra"] = df["extra"].apply(json.dumps)
    return df


def _deserialise_extras(df: pd.DataFrame) -> pd.DataFrame:
    """Convert 'extra' column back from JSON string to dict."""
    if "extra" in df.columns:
        df = df.copy()
        df["extra"] = df["extra"].apply(
            lambda v: json.loads(v) if isinstance(v, str) else (v or {})
        )
    return df


def write_cohort_dataset(
    dataset: CohortDataset, dest_dir: Path, fmt: str = "parquet"
) -> dict[str, Path]:
    """
    Write all four tables in dataset to dest_dir as parquet (default) or feather files.
    Returns a dict of table_name -> file_path.
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    for table_name in _TABLE_NAMES:
        records = getattr(dataset, table_name)
        if not records:
            _log.debug("Skipping empty table %s", table_name)
            continue
        df = pd.DataFrame([r.model_dump() for r in records])
        df = _serialise_extras(df)
        ext = ".parquet" if fmt == "parquet" else ".feather"
        fpath = dest_dir / f"{table_name}{ext}"
        if fmt == "parquet":
            df.to_parquet(fpath, index=False)
        else:
            df.to_feather(fpath)
        written[table_name] = fpath
        _log.info("Wrote %d rows to %s", len(df), fpath)

    return written


def read_cohort_dataset(src_dir: Path, fmt: str = "parquet") -> CohortDataset:
    """
    Read parquet/feather files from src_dir and reconstruct a CohortDataset.
    """
    from medrisk.fetch._schema import Event, Measurement, Person, Treatment

    src_dir = Path(src_dir)
    ext = ".parquet" if fmt == "parquet" else ".feather"
    _MODEL_MAP = {
        "persons": Person,
        "measurements": Measurement,
        "events": Event,
        "treatments": Treatment,
    }

    kwargs: dict = {}
    for table_name, model_cls in _MODEL_MAP.items():
        fpath = src_dir / f"{table_name}{ext}"
        if not fpath.exists():
            kwargs[table_name] = []
            continue
        df = pd.read_parquet(fpath) if fmt == "parquet" else pd.read_feather(fpath)
        df = _deserialise_extras(df)
        kwargs[table_name] = [model_cls(**row) for row in df.to_dict(orient="records")]

    return CohortDataset(**kwargs)
