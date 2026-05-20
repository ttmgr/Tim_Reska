"""
medrisk.fetch — Public health cohort data fetcher for disease progression modeling.

Ported from cohort_fetch to integrate with the MedRisk pipeline.
"""

__version__ = "0.1.0"

from medrisk.fetch._schema import CohortDataset, Event, Measurement, Person, Treatment
from medrisk.fetch.adapters.base import AbstractAdapter, DatasetInfo, DownloadOptions

__all__ = [
    "CohortDataset",
    "Person",
    "Measurement",
    "Event",
    "Treatment",
    "AbstractAdapter",
    "DatasetInfo",
    "DownloadOptions",
]
