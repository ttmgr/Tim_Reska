"""
disease_progression.features.tokenizer - EHR code tokenization.

Converts heterogeneous medical event sequences (ICD-10 diagnoses,
ATC medications, LOINC observations) into integer token sequences
with associated positional and temporal embeddings, suitable for
transformer-based survival models such as SurvTRACE.

Design follows the approach from BEHRT (Li et al. 2020) and Med-BERT
(Rasmy et al. 2021):

    1. Each medical code is mapped to a unique token ID via a learned
       vocabulary.
    2. Special tokens: [CLS] (sequence start / classification token),
       [SEP] (visit separator), [PAD] (padding), [MASK] (for MLM
       pre-training), [UNK] (unknown codes).
    3. Temporal embeddings encode the absolute calendar position and
       the time delta between consecutive events, allowing the model
       to learn time-aware representations.
    4. Binned numeric values (e.g. lab results) are discretised into
       quantile buckets and appended as value tokens.
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Special tokens
# -------------------------------------------------------------------
PAD_TOKEN = "[PAD]"
CLS_TOKEN = "[CLS]"
SEP_TOKEN = "[SEP]"
MASK_TOKEN = "[MASK]"
UNK_TOKEN = "[UNK]"

SPECIAL_TOKENS = [PAD_TOKEN, CLS_TOKEN, SEP_TOKEN, MASK_TOKEN, UNK_TOKEN]

# -------------------------------------------------------------------
# Time-delta bins (in days)
# -------------------------------------------------------------------
TIME_DELTA_BINS = [0, 1, 7, 14, 30, 60, 90, 180, 365, 730, 1825, np.inf]
TIME_DELTA_LABELS = [
    "same_day", "1d", "1w", "2w", "1m", "2m", "3m", "6m", "1y", "2y", "5y+"
]

# -------------------------------------------------------------------
# Lab value quantile bin count
# -------------------------------------------------------------------
DEFAULT_N_VALUE_BINS = 10


@dataclass
class TokenizedSequence:
    """Container for a single patient's tokenized EHR sequence.

    Attributes
    ----------
    patient_id : int or str
        Patient identifier.
    token_ids : list of int
        Integer token IDs.
    time_delta_ids : list of int
        Binned inter-event time deltas.
    absolute_position_days : list of float
        Days since the first event (absolute time embedding input).
    segment_ids : list of int
        Visit segment identifiers (incremented at each [SEP] token).
    attention_mask : list of int
        1 for real tokens, 0 for padding.
    """
    patient_id: Any = None
    token_ids: List[int] = field(default_factory=list)
    time_delta_ids: List[int] = field(default_factory=list)
    absolute_position_days: List[float] = field(default_factory=list)
    segment_ids: List[int] = field(default_factory=list)
    attention_mask: List[int] = field(default_factory=list)


class EHRTokenizer:
    """Tokenize EHR event sequences for transformer input.

    Parameters
    ----------
    max_seq_len : int
        Maximum sequence length (truncation / padding boundary).
    min_code_freq : int
        Minimum frequency for a code to receive its own token; rarer
        codes are mapped to [UNK].
    n_value_bins : int
        Number of quantile bins for discretising numeric lab values.
    code_prefixes : dict mapping str -> str, optional
        Prefixes prepended to codes by domain to avoid collisions,
        e.g. ``{"condition": "DX_", "drug": "RX_", "measurement": "LAB_"}``.
    """

    def __init__(
        self,
        max_seq_len: int = 512,
        min_code_freq: int = 5,
        n_value_bins: int = DEFAULT_N_VALUE_BINS,
        code_prefixes: Optional[Dict[str, str]] = None,
    ) -> None:
        self.max_seq_len = max_seq_len
        self.min_code_freq = min_code_freq
        self.n_value_bins = n_value_bins
        self.code_prefixes = code_prefixes or {
            "condition": "DX_",
            "drug": "RX_",
            "measurement": "LAB_",
        }

        # Vocabulary (built by .fit())
        self.token2id: Dict[str, int] = {}
        self.id2token: Dict[int, str] = {}
        self.vocab_size: int = 0
        self._fitted: bool = False

        # Lab value bin edges per LOINC code
        self._value_bin_edges: Dict[str, np.ndarray] = {}

    # ------------------------------------------------------------------
    # Fit vocabulary
    # ------------------------------------------------------------------

    def fit(
        self,
        conditions: pd.DataFrame,
        drugs: pd.DataFrame,
        measurements: pd.DataFrame,
    ) -> "EHRTokenizer":
        """Learn vocabulary and value bins from training data.

        Parameters
        ----------
        conditions : pd.DataFrame
            Must have ``condition_source_value`` column.
        drugs : pd.DataFrame
            Must have ``drug_source_value`` column.
        measurements : pd.DataFrame
            Must have ``measurement_source_value`` and ``value_as_number``.

        Returns self for chaining.
        """
        counter: Counter = Counter()

        dx_prefix = self.code_prefixes.get("condition", "DX_")
        rx_prefix = self.code_prefixes.get("drug", "RX_")
        lab_prefix = self.code_prefixes.get("measurement", "LAB_")

        if not conditions.empty and "condition_source_value" in conditions.columns:
            for code in conditions["condition_source_value"].dropna():
                counter[f"{dx_prefix}{code}"] += 1

        if not drugs.empty and "drug_source_value" in drugs.columns:
            for code in drugs["drug_source_value"].dropna():
                counter[f"{rx_prefix}{code}"] += 1

        if not measurements.empty and "measurement_source_value" in measurements.columns:
            for code in measurements["measurement_source_value"].dropna():
                counter[f"{lab_prefix}{code}"] += 1

        # Build vocabulary: special tokens + frequent codes + value bin tokens
        self.token2id = {}
        for tok in SPECIAL_TOKENS:
            self.token2id[tok] = len(self.token2id)

        for token, freq in counter.most_common():
            if freq >= self.min_code_freq:
                self.token2id[token] = len(self.token2id)

        # Add value bin tokens (e.g. LAB_4548-4_Q3)
        if not measurements.empty and "measurement_source_value" in measurements.columns:
            for lab_code, group in measurements.groupby("measurement_source_value"):
                vals = group["value_as_number"].dropna().values
                if len(vals) < self.n_value_bins:
                    continue
                edges = np.quantile(vals, np.linspace(0, 1, self.n_value_bins + 1))
                edges = np.unique(edges)
                self._value_bin_edges[str(lab_code)] = edges
                for q in range(len(edges) - 1):
                    vtok = f"{lab_prefix}{lab_code}_Q{q}"
                    self.token2id[vtok] = len(self.token2id)

        # Add time-delta tokens
        for label in TIME_DELTA_LABELS:
            td_tok = f"TD_{label}"
            if td_tok not in self.token2id:
                self.token2id[td_tok] = len(self.token2id)

        self.id2token = {v: k for k, v in self.token2id.items()}
        self.vocab_size = len(self.token2id)
        self._fitted = True

        logger.info("Vocabulary built: %d tokens (min_freq=%d)", self.vocab_size, self.min_code_freq)
        return self

    # ------------------------------------------------------------------
    # Tokenize one patient
    # ------------------------------------------------------------------

    def tokenize_patient(
        self,
        patient_id: Any,
        events: pd.DataFrame,
    ) -> TokenizedSequence:
        """Tokenize a single patient's event stream.

        Parameters
        ----------
        patient_id : any
            Patient identifier.
        events : pd.DataFrame
            Columns: ``event_date`` (datetime), ``domain`` (str: condition /
            drug / measurement), ``code`` (str), ``value`` (float or NaN).

        Returns
        -------
        TokenizedSequence
        """
        if not self._fitted:
            raise RuntimeError("Tokenizer has not been fitted. Call .fit() first.")

        events = events.sort_values("event_date").reset_index(drop=True)
        events["event_date"] = pd.to_datetime(events["event_date"], errors="coerce")
        events = events.dropna(subset=["event_date"])

        token_ids: List[int] = [self.token2id[CLS_TOKEN]]
        time_delta_ids: List[int] = [0]
        abs_days: List[float] = [0.0]
        segment_ids: List[int] = [0]
        attention_mask: List[int] = [1]

        if events.empty:
            return self._pad(TokenizedSequence(
                patient_id=patient_id,
                token_ids=token_ids,
                time_delta_ids=time_delta_ids,
                absolute_position_days=abs_days,
                segment_ids=segment_ids,
                attention_mask=attention_mask,
            ))

        first_date = events["event_date"].iloc[0]
        prev_date = first_date
        current_segment = 0

        # Group by date to form "visits"
        for visit_date, visit_events in events.groupby("event_date"):
            # Insert [SEP] between visits
            if visit_date != first_date:
                current_segment += 1
                delta_days = (visit_date - prev_date).days
                td_id = self._bin_time_delta(delta_days)

                token_ids.append(self.token2id[SEP_TOKEN])
                time_delta_ids.append(td_id)
                abs_days.append((visit_date - first_date).days)
                segment_ids.append(current_segment)
                attention_mask.append(1)

            for _, event in visit_events.iterrows():
                domain = str(event.get("domain", ""))
                code = str(event.get("code", ""))
                value = event.get("value")
                prefix = self.code_prefixes.get(domain, "")
                full_code = f"{prefix}{code}"

                tid = self.token2id.get(full_code, self.token2id[UNK_TOKEN])
                delta_days = (visit_date - prev_date).days
                td_id = self._bin_time_delta(delta_days)

                token_ids.append(tid)
                time_delta_ids.append(td_id)
                abs_days.append(float((visit_date - first_date).days))
                segment_ids.append(current_segment)
                attention_mask.append(1)

                # Append value bin token if numeric
                if pd.notna(value) and code in self._value_bin_edges:
                    vbin = self._discretise_value(code, float(value))
                    if vbin is not None:
                        vtok = f"{prefix}{code}_Q{vbin}"
                        vtid = self.token2id.get(vtok, self.token2id[UNK_TOKEN])
                        token_ids.append(vtid)
                        time_delta_ids.append(td_id)
                        abs_days.append(float((visit_date - first_date).days))
                        segment_ids.append(current_segment)
                        attention_mask.append(1)

            prev_date = visit_date

        seq = TokenizedSequence(
            patient_id=patient_id,
            token_ids=token_ids,
            time_delta_ids=time_delta_ids,
            absolute_position_days=abs_days,
            segment_ids=segment_ids,
            attention_mask=attention_mask,
        )
        return self._pad(seq)

    # ------------------------------------------------------------------
    # Batch tokenization from OMOP tables
    # ------------------------------------------------------------------

    def tokenize_omop(self, omop_tables: Any) -> List[TokenizedSequence]:
        """Tokenize all patients from OMOP tables.

        Merges conditions, drugs, and measurements into a unified event
        stream per patient, then tokenizes each.
        """
        events_frames: List[pd.DataFrame] = []

        cond = omop_tables.condition_occurrence
        if not cond.empty and "condition_start_date" in cond.columns:
            df = cond[["person_id", "condition_start_date", "condition_source_value"]].copy()
            df = df.rename(columns={
                "person_id": "patient_id",
                "condition_start_date": "event_date",
                "condition_source_value": "code",
            })
            df["domain"] = "condition"
            df["value"] = np.nan
            events_frames.append(df)

        drug = omop_tables.drug_exposure
        if not drug.empty and "drug_exposure_start_date" in drug.columns:
            df = drug[["person_id", "drug_exposure_start_date", "drug_source_value"]].copy()
            df = df.rename(columns={
                "person_id": "patient_id",
                "drug_exposure_start_date": "event_date",
                "drug_source_value": "code",
            })
            df["domain"] = "drug"
            df["value"] = np.nan
            events_frames.append(df)

        meas = omop_tables.measurement
        if not meas.empty and "measurement_date" in meas.columns:
            df = meas[["person_id", "measurement_date", "measurement_source_value", "value_as_number"]].copy()
            df = df.rename(columns={
                "person_id": "patient_id",
                "measurement_date": "event_date",
                "measurement_source_value": "code",
                "value_as_number": "value",
            })
            df["domain"] = "measurement"
            events_frames.append(df)

        if not events_frames:
            return []

        all_events = pd.concat(events_frames, ignore_index=True)
        all_events["event_date"] = pd.to_datetime(all_events["event_date"], errors="coerce")
        all_events = all_events.dropna(subset=["event_date"])

        sequences: List[TokenizedSequence] = []
        for pid, group in all_events.groupby("patient_id"):
            seq = self.tokenize_patient(pid, group)
            sequences.append(seq)

        logger.info("Tokenized %d patients, vocab_size=%d", len(sequences), self.vocab_size)
        return sequences

    # ------------------------------------------------------------------
    # Batch collation for PyTorch
    # ------------------------------------------------------------------

    def collate(
        self,
        sequences: Sequence[TokenizedSequence],
    ) -> Dict[str, np.ndarray]:
        """Collate a batch of TokenizedSequences into numpy arrays.

        Returns
        -------
        dict with keys:
            token_ids : (batch, max_seq_len) int32
            time_delta_ids : (batch, max_seq_len) int32
            absolute_position_days : (batch, max_seq_len) float32
            segment_ids : (batch, max_seq_len) int32
            attention_mask : (batch, max_seq_len) int32
        """
        batch_size = len(sequences)
        token_ids = np.zeros((batch_size, self.max_seq_len), dtype=np.int32)
        time_delta_ids = np.zeros((batch_size, self.max_seq_len), dtype=np.int32)
        abs_pos = np.zeros((batch_size, self.max_seq_len), dtype=np.float32)
        seg_ids = np.zeros((batch_size, self.max_seq_len), dtype=np.int32)
        att_mask = np.zeros((batch_size, self.max_seq_len), dtype=np.int32)

        for i, seq in enumerate(sequences):
            sl = min(len(seq.token_ids), self.max_seq_len)
            token_ids[i, :sl] = seq.token_ids[:sl]
            time_delta_ids[i, :sl] = seq.time_delta_ids[:sl]
            abs_pos[i, :sl] = seq.absolute_position_days[:sl]
            seg_ids[i, :sl] = seq.segment_ids[:sl]
            att_mask[i, :sl] = seq.attention_mask[:sl]

        return {
            "token_ids": token_ids,
            "time_delta_ids": time_delta_ids,
            "absolute_position_days": abs_pos,
            "segment_ids": seg_ids,
            "attention_mask": att_mask,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _pad(self, seq: TokenizedSequence) -> TokenizedSequence:
        """Truncate or pad sequence to max_seq_len."""
        length = len(seq.token_ids)
        if length > self.max_seq_len:
            seq.token_ids = seq.token_ids[: self.max_seq_len]
            seq.time_delta_ids = seq.time_delta_ids[: self.max_seq_len]
            seq.absolute_position_days = seq.absolute_position_days[: self.max_seq_len]
            seq.segment_ids = seq.segment_ids[: self.max_seq_len]
            seq.attention_mask = seq.attention_mask[: self.max_seq_len]
        elif length < self.max_seq_len:
            pad_len = self.max_seq_len - length
            pad_id = self.token2id[PAD_TOKEN]
            seq.token_ids += [pad_id] * pad_len
            seq.time_delta_ids += [0] * pad_len
            seq.absolute_position_days += [0.0] * pad_len
            seq.segment_ids += [0] * pad_len
            seq.attention_mask += [0] * pad_len
        return seq

    def _bin_time_delta(self, days: int) -> int:
        """Bin a time delta in days and return the token ID."""
        bin_idx = int(np.searchsorted(TIME_DELTA_BINS[1:], days, side="right"))
        bin_idx = min(bin_idx, len(TIME_DELTA_LABELS) - 1)
        label = TIME_DELTA_LABELS[bin_idx]
        return self.token2id.get(f"TD_{label}", 0)

    def _discretise_value(self, lab_code: str, value: float) -> Optional[int]:
        """Bin a numeric lab value into its quantile bucket."""
        edges = self._value_bin_edges.get(lab_code)
        if edges is None:
            return None
        bin_idx = int(np.searchsorted(edges[1:], value, side="right"))
        bin_idx = min(bin_idx, len(edges) - 2)
        return max(bin_idx, 0)
