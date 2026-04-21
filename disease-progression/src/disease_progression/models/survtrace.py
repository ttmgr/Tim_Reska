"""
disease_progression.models.survtrace - SurvTRACE-style transformer survival model.

Implements a transformer-based survival model inspired by SurvTRACE
(Wang & Sun, 2022) that uses self-attention to learn representations
from heterogeneous EHR token sequences, then predicts discrete-time
survival probabilities through a survival head supporting single-event
and competing-risks settings.

Architecture overview:

    EHR tokens  -->  Embedding Layer  -->  Transformer Encoder  -->  [CLS] repr
                     (code + time +          (multi-head self-        |
                      segment emb.)           attention layers)       v
                                                                  Survival Head
                                                                      |
                                                                      v
                                                          P(T in bin_k | X)
                                                          or CIF per risk

Key design choices:
    - **Token embeddings**: Learned code embeddings + sinusoidal absolute
      time embeddings + segment (visit) embeddings.
    - **Survival head**: A linear projection from [CLS] to K time bins,
      followed by softmax to produce a proper PMF.  For competing risks,
      the output is (n_risks, K) per sample.
    - **Loss**: Combines negative log-likelihood (event / censoring) with
      an optional concordance ranking regulariser.
    - **Calibration**: Temperature scaling can be applied post-hoc.

This is a pure PyTorch implementation with no dependency on pycox.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

from disease_progression.models.registry import auto_register

logger = logging.getLogger(__name__)


# ===================================================================
# Sinusoidal time embedding
# ===================================================================

class SinusoidalTimeEmbedding(nn.Module):
    """Sinusoidal positional encoding for absolute time (in days).

    Maps a scalar time value to a d-dimensional vector using sin/cos
    functions at exponentially-spaced frequencies, analogous to the
    positional encoding in Vaswani et al. (2017) but applied to
    continuous calendar time.
    """

    def __init__(self, d_model: int, max_period: float = 10000.0) -> None:
        super().__init__()
        self.d_model = d_model
        half = d_model // 2
        freqs = torch.exp(
            -math.log(max_period) * torch.arange(half, dtype=torch.float32) / half
        )
        self.register_buffer("freqs", freqs)

    def forward(self, time_days: torch.Tensor) -> torch.Tensor:
        """
        Parameters
        ----------
        time_days : Tensor of shape (...,)
            Absolute time in days.

        Returns
        -------
        Tensor of shape (..., d_model)
        """
        args = time_days.unsqueeze(-1).float() * self.freqs
        emb = torch.cat([torch.sin(args), torch.cos(args)], dim=-1)
        if emb.size(-1) < self.d_model:
            emb = F.pad(emb, (0, self.d_model - emb.size(-1)))
        return emb


# ===================================================================
# SurvTRACE model
# ===================================================================

@auto_register(
    "survtrace",
    description="SurvTRACE transformer survival model with competing risks",
    default_params={
        "vocab_size": 5000,
        "d_model": 128,
        "n_heads": 4,
        "n_layers": 3,
        "num_durations": 100,
        "num_risks": 1,
        "lr": 1e-4,
        "epochs": 50,
        "batch_size": 64,
    },
)
class SurvTRACEModel(nn.Module):
    """SurvTRACE: Transformer-based survival analysis with competing risks.

    Parameters
    ----------
    vocab_size : int
        Size of the EHR code vocabulary (from ``EHRTokenizer.vocab_size``).
    d_model : int
        Transformer hidden dimension.
    n_heads : int
        Number of attention heads.
    n_layers : int
        Number of transformer encoder layers.
    d_ff : int
        Feed-forward inner dimension (default: 4 * d_model).
    dropout : float
        Dropout rate throughout the model.
    max_seq_len : int
        Maximum input sequence length.
    num_durations : int
        Number of discrete output time bins.
    num_risks : int
        Number of competing risks (1 for standard survival).
    max_segments : int
        Maximum number of visit segments.
    alpha : float
        Ranking loss weight (0 = pure NLL).
    sigma : float
        Ranking loss bandwidth parameter.
    lr : float
        Learning rate for Adam optimiser.
    epochs : int
        Training epochs.
    batch_size : int
        Mini-batch size.
    """

    def __init__(
        self,
        vocab_size: int = 5000,
        d_model: int = 128,
        n_heads: int = 4,
        n_layers: int = 3,
        d_ff: Optional[int] = None,
        dropout: float = 0.1,
        max_seq_len: int = 512,
        num_durations: int = 100,
        num_risks: int = 1,
        max_segments: int = 200,
        alpha: float = 0.1,
        sigma: float = 0.1,
        lr: float = 1e-4,
        epochs: int = 50,
        batch_size: int = 64,
    ) -> None:
        super().__init__()

        self.vocab_size = vocab_size
        self.d_model = d_model
        self.n_heads = n_heads
        self.n_layers = n_layers
        self.d_ff = d_ff or 4 * d_model
        self.dropout_rate = dropout
        self.max_seq_len = max_seq_len
        self.num_durations = num_durations
        self.num_risks = num_risks
        self.max_segments = max_segments
        self.alpha = alpha
        self.sigma = sigma
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size

        # --- Embedding layers ---
        self.token_emb = nn.Embedding(vocab_size, d_model, padding_idx=0)
        self.segment_emb = nn.Embedding(max_segments, d_model)
        self.time_emb = SinusoidalTimeEmbedding(d_model)
        self.emb_dropout = nn.Dropout(dropout)
        self.emb_layer_norm = nn.LayerNorm(d_model)

        # --- Transformer encoder ---
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=self.d_ff,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=n_layers,
        )

        # --- Survival head ---
        self.survival_head = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, num_durations * max(num_risks, 1)),
        )

        # Temperature for post-hoc calibration
        self.temperature = nn.Parameter(torch.ones(1))

        # Duration cut points (set during fit)
        self._cuts: Optional[np.ndarray] = None
        self._fitted = False

        # Initialize weights
        self._init_weights()

    def _init_weights(self) -> None:
        """Xavier uniform initialization for linear layers."""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, nn.Embedding):
                nn.init.normal_(module.weight, std=0.02)
                if module.padding_idx is not None:
                    nn.init.zeros_(module.weight[module.padding_idx])

    def forward(
        self,
        token_ids: torch.Tensor,
        time_days: torch.Tensor,
        segment_ids: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> torch.Tensor:
        """Forward pass.

        Parameters
        ----------
        token_ids : (batch, seq_len) LongTensor
        time_days : (batch, seq_len) FloatTensor
            Absolute time in days since first event.
        segment_ids : (batch, seq_len) LongTensor
            Visit segment indices.
        attention_mask : (batch, seq_len) {0, 1} tensor
            1 for real tokens, 0 for padding.

        Returns
        -------
        pmf : (batch, num_risks, num_durations) or (batch, num_durations)
            Predicted probability mass function over time bins.
        """
        # Embedding
        tok_emb = self.token_emb(token_ids)
        seg_emb = self.segment_emb(segment_ids.clamp(max=self.max_segments - 1))
        time_emb = self.time_emb(time_days)
        h = tok_emb + seg_emb + time_emb
        h = self.emb_layer_norm(h)
        h = self.emb_dropout(h)

        # Transformer encoder
        # Convert attention_mask: 1=attend, 0=mask -> True=masked for PyTorch
        key_padding_mask = attention_mask == 0
        h = self.transformer_encoder(h, src_key_padding_mask=key_padding_mask)

        # Extract [CLS] representation (position 0)
        cls_repr = h[:, 0, :]

        # Survival head
        logits = self.survival_head(cls_repr) / self.temperature

        if self.num_risks > 1:
            logits = logits.view(-1, self.num_risks, self.num_durations)
            pmf = F.softmax(
                logits.view(-1, self.num_risks * self.num_durations), dim=-1
            ).view(-1, self.num_risks, self.num_durations)
        else:
            pmf = F.softmax(logits, dim=-1)

        return pmf

    # ------------------------------------------------------------------
    # Loss function
    # ------------------------------------------------------------------

    def compute_loss(
        self,
        pmf: torch.Tensor,
        duration_bins: torch.Tensor,
        events: torch.Tensor,
    ) -> torch.Tensor:
        """Combined NLL + ranking loss.

        Parameters
        ----------
        pmf : (batch, num_durations) or (batch, num_risks, num_durations)
        duration_bins : (batch,) LongTensor
            Discretised duration indices.
        events : (batch,) FloatTensor
            Event indicator (0 = censored, 1..K = event type).
        """
        eps = 1e-8
        if pmf.ndim == 3:
            pmf_all = pmf.sum(dim=1)  # all-cause PMF
        else:
            pmf_all = pmf

        event_mask = events > 0
        censor_mask = ~event_mask

        # NLL for observed events
        nll = torch.tensor(0.0, device=pmf.device)
        if event_mask.any():
            idx = duration_bins[event_mask].long().clamp(0, self.num_durations - 1)
            if pmf.ndim == 3:
                # Use cause-specific PMF
                risk_idx = (events[event_mask].long() - 1).clamp(0, self.num_risks - 1)
                event_probs = pmf[event_mask, risk_idx, idx]
            else:
                event_probs = pmf_all[event_mask, idx]
            nll = -torch.log(event_probs + eps).mean()

        # Censored: survival probability beyond censoring time
        if censor_mask.any():
            surv = torch.zeros(censor_mask.sum(), device=pmf.device)
            censor_bins = duration_bins[censor_mask].long().clamp(0, self.num_durations - 1)
            for i, db in enumerate(censor_bins):
                surv[i] = pmf_all[censor_mask][i, db:].sum()
            nll_censor = -torch.log(surv + eps).mean()
            nll = nll + nll_censor

        # Ranking regularisation
        ranking = torch.tensor(0.0, device=pmf.device)
        if self.alpha > 0 and event_mask.sum() > 1:
            cif = torch.cumsum(pmf_all, dim=-1)
            event_idx = event_mask.nonzero(as_tuple=True)[0]
            n_pairs = min(len(event_idx) * (len(event_idx) - 1) // 2, 256)
            if n_pairs > 0:
                pi = event_idx[torch.randint(len(event_idx), (n_pairs,))]
                pj = event_idx[torch.randint(len(event_idx), (n_pairs,))]
                valid = duration_bins[pi] < duration_bins[pj]
                if valid.any():
                    t_i = duration_bins[pi[valid]].long().clamp(0, self.num_durations - 1)
                    diff = cif[pj[valid], t_i] - cif[pi[valid], t_i]
                    ranking = torch.exp(diff / self.sigma).mean()

        return (1.0 - self.alpha) * nll + self.alpha * ranking

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def fit(
        self,
        token_ids: np.ndarray,
        time_days: np.ndarray,
        segment_ids: np.ndarray,
        attention_mask: np.ndarray,
        durations: np.ndarray,
        events: np.ndarray,
        val_data: Optional[Dict[str, np.ndarray]] = None,
    ) -> "SurvTRACEModel":
        """Train the SurvTRACE model.

        Parameters
        ----------
        token_ids : (n, max_seq_len) int
        time_days : (n, max_seq_len) float
        segment_ids : (n, max_seq_len) int
        attention_mask : (n, max_seq_len) int
        durations : (n,) float
            Continuous follow-up times.
        events : (n,) float
            Event indicators.
        val_data : dict, optional
            Validation data with the same keys.
        """
        # Discretise durations
        self._cuts = np.linspace(
            durations.min(), durations.max(), self.num_durations + 1
        )
        duration_bins = np.digitize(durations, self._cuts[1:]).clip(0, self.num_durations - 1)

        # Build DataLoader
        dataset = TensorDataset(
            torch.tensor(token_ids, dtype=torch.long),
            torch.tensor(time_days, dtype=torch.float32),
            torch.tensor(segment_ids, dtype=torch.long),
            torch.tensor(attention_mask, dtype=torch.long),
            torch.tensor(duration_bins, dtype=torch.long),
            torch.tensor(events, dtype=torch.float32),
        )
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        optimiser = torch.optim.AdamW(self.parameters(), lr=self.lr, weight_decay=1e-4)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimiser, T_max=self.epochs)

        best_loss = float("inf")
        patience_counter = 0
        patience = 10

        self.train()
        for epoch in range(self.epochs):
            epoch_loss = 0.0
            for batch in loader:
                tok, td, seg, mask, db, ev = batch
                pmf = self.forward(tok, td, seg, mask)
                loss = self.compute_loss(pmf, db, ev)
                optimiser.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.parameters(), 1.0)
                optimiser.step()
                epoch_loss += loss.item() * len(tok)

            scheduler.step()
            avg_loss = epoch_loss / len(dataset)

            if (epoch + 1) % 10 == 0:
                logger.info("Epoch %d/%d  loss=%.4f  lr=%.2e", epoch + 1, self.epochs, avg_loss, scheduler.get_last_lr()[0])

            # Early stopping
            if avg_loss < best_loss - 1e-4:
                best_loss = avg_loss
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    logger.info("Early stopping at epoch %d", epoch + 1)
                    break

        self._fitted = True
        logger.info("SurvTRACE training complete")
        return self

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    @torch.no_grad()
    def predict_pmf(
        self,
        token_ids: np.ndarray,
        time_days: np.ndarray,
        segment_ids: np.ndarray,
        attention_mask: np.ndarray,
    ) -> np.ndarray:
        """Predict PMF over discrete time bins.

        Returns
        -------
        ndarray (n, num_durations) or (n, num_risks, num_durations)
        """
        self.eval()
        tok = torch.tensor(token_ids, dtype=torch.long)
        td = torch.tensor(time_days, dtype=torch.float32)
        seg = torch.tensor(segment_ids, dtype=torch.long)
        mask = torch.tensor(attention_mask, dtype=torch.long)
        pmf = self.forward(tok, td, seg, mask)
        return pmf.numpy()

    @torch.no_grad()
    def predict_survival(
        self,
        token_ids: np.ndarray,
        time_days: np.ndarray,
        segment_ids: np.ndarray,
        attention_mask: np.ndarray,
    ) -> np.ndarray:
        """Predict all-cause survival function S(t) = 1 - CIF(t).

        Returns
        -------
        ndarray (n, num_durations)
        """
        pmf = self.predict_pmf(token_ids, time_days, segment_ids, attention_mask)
        if pmf.ndim == 3:
            pmf_all = pmf.sum(axis=1)
        else:
            pmf_all = pmf
        cif = np.cumsum(pmf_all, axis=-1)
        return 1.0 - cif

    @torch.no_grad()
    def predict_cif(
        self,
        token_ids: np.ndarray,
        time_days: np.ndarray,
        segment_ids: np.ndarray,
        attention_mask: np.ndarray,
    ) -> np.ndarray:
        """Predict cumulative incidence functions.

        For competing risks, returns (n, num_risks, num_durations).
        For single-risk, returns (n, num_durations).
        """
        pmf = self.predict_pmf(token_ids, time_days, segment_ids, attention_mask)
        return np.cumsum(pmf, axis=-1)

    def predict_risk_score(
        self,
        token_ids: np.ndarray,
        time_days: np.ndarray,
        segment_ids: np.ndarray,
        attention_mask: np.ndarray,
        time_horizon: Optional[float] = None,
        risk: int = 0,
    ) -> np.ndarray:
        """Predict a scalar risk score per subject (for C-index evaluation).

        By default, uses CIF at the median follow-up time.

        Parameters
        ----------
        time_horizon : float, optional
            Specific time at which to evaluate CIF.  If None, uses
            the midpoint of the duration grid.
        risk : int
            Risk index for competing risks.

        Returns
        -------
        ndarray (n,)
        """
        cif = self.predict_cif(token_ids, time_days, segment_ids, attention_mask)

        if time_horizon is not None and self._cuts is not None:
            idx = int(np.searchsorted(self._cuts[1:], time_horizon, side="right")) - 1
        else:
            idx = cif.shape[-1] // 2
        idx = max(0, min(idx, cif.shape[-1] - 1))

        if cif.ndim == 3:
            return cif[:, risk, idx]
        return cif[:, idx]

    # ------------------------------------------------------------------
    # Attention extraction (for interpretability)
    # ------------------------------------------------------------------

    @torch.no_grad()
    def extract_attention_weights(
        self,
        token_ids: np.ndarray,
        time_days: np.ndarray,
        segment_ids: np.ndarray,
        attention_mask: np.ndarray,
    ) -> List[np.ndarray]:
        """Extract self-attention weights from all transformer layers.

        Returns
        -------
        list of ndarray
            Each element has shape (batch, n_heads, seq_len, seq_len).
        """
        self.eval()
        tok = torch.tensor(token_ids, dtype=torch.long)
        td = torch.tensor(time_days, dtype=torch.float32)
        seg = torch.tensor(segment_ids, dtype=torch.long)
        mask = torch.tensor(attention_mask, dtype=torch.long)

        # Compute embeddings
        h = self.token_emb(tok) + self.segment_emb(seg.clamp(max=self.max_segments - 1)) + self.time_emb(td)
        h = self.emb_layer_norm(h)
        h = self.emb_dropout(h)

        key_padding_mask = mask == 0
        attentions: List[np.ndarray] = []

        for layer in self.transformer_encoder.layers:
            # Use the self_attn module directly to capture weights
            attn_out, attn_weights = layer.self_attn(
                h, h, h,
                key_padding_mask=key_padding_mask,
                need_weights=True,
                average_attn_weights=False,
            )
            attentions.append(attn_weights.numpy())
            # Continue forward pass through the layer
            h = layer(h, src_key_padding_mask=key_padding_mask)

        return attentions

    @property
    def duration_index(self) -> Optional[np.ndarray]:
        """The discrete time grid (cut points)."""
        return self._cuts
