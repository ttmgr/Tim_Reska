"""
disease_progression.models.deephit - DeepHit and Dynamic-DeepHit wrappers.

Implements the DeepHit family of discrete-time survival models that
directly learn the joint distribution of event time and competing risk
type, without assuming any particular stochastic process for the
underlying data-generating mechanism.

**DeepHit** (Lee et al., AAAI 2018):
    - Models the probability mass function (PMF) over a pre-defined
      discrete time grid.
    - The loss combines a log-likelihood term with a ranking loss that
      encourages correct ordering of predicted risk.
    - Naturally supports competing risks by predicting cause-specific
      PMFs that sum to the all-cause PMF.

**Dynamic-DeepHit** (Lee et al., IEEE TBME 2020):
    - Extends DeepHit to longitudinal (time-varying) covariates via
      an RNN encoder that processes sequential patient data.
    - Predictions are updated dynamically as new observations arrive.

Both models produce **cumulative incidence functions (CIFs)** per cause,
enabling direct probability statements such as "P(MI within 5 years)".
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from disease_progression.models.registry import auto_register

logger = logging.getLogger(__name__)


# ===================================================================
# DeepHit (single-risk and competing-risk)
# ===================================================================

@auto_register(
    "deephit",
    description="DeepHit discrete-time survival with competing risks (pycox)",
    default_params={
        "in_features": 32,
        "hidden_layers": [64, 64],
        "num_durations": 100,
        "num_risks": 1,
        "alpha": 0.2,
        "sigma": 0.1,
        "lr": 1e-3,
        "epochs": 100,
        "batch_size": 256,
    },
)
class DeepHitModel:
    """DeepHit wrapper using pycox.

    Parameters
    ----------
    in_features : int
        Input feature dimension.
    hidden_layers : list of int
        Shared sub-network hidden layer widths.
    num_durations : int
        Number of discrete time bins for the output PMF.
    num_risks : int
        Number of competing risks (1 = single-risk DeepHit).
    alpha : float
        Weight for the ranking (concordance) loss term.
        Range [0, 1]; 0 = pure likelihood, 1 = pure ranking.
    sigma : float
        Bandwidth parameter for the ranking loss kernel.
    lr : float
        Learning rate.
    epochs : int
        Training epochs.
    batch_size : int
        Mini-batch size.
    patience : int
        Early-stopping patience.
    """

    def __init__(
        self,
        in_features: int = 32,
        hidden_layers: Optional[List[int]] = None,
        num_durations: int = 100,
        num_risks: int = 1,
        alpha: float = 0.2,
        sigma: float = 0.1,
        lr: float = 1e-3,
        epochs: int = 100,
        batch_size: int = 256,
        patience: int = 10,
        dropout: float = 0.1,
        batch_norm: bool = True,
    ) -> None:
        self.in_features = in_features
        self.hidden_layers = hidden_layers or [64, 64]
        self.num_durations = num_durations
        self.num_risks = num_risks
        self.alpha = alpha
        self.sigma = sigma
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size
        self.patience = patience
        self.dropout = dropout
        self.batch_norm = batch_norm

        self._model = None
        self._label_transform = None
        self._fitted = False

    def fit(
        self,
        x_train: np.ndarray,
        durations_train: np.ndarray,
        events_train: np.ndarray,
        x_val: Optional[np.ndarray] = None,
        durations_val: Optional[np.ndarray] = None,
        events_val: Optional[np.ndarray] = None,
    ) -> "DeepHitModel":
        """Train the DeepHit model.

        Parameters
        ----------
        x_train : ndarray (n, in_features)
        durations_train : ndarray (n,)
            Continuous follow-up times (will be discretised internally).
        events_train : ndarray (n,)
            Event indicator.  For single-risk: 0 = censored, 1 = event.
            For competing risks: 0 = censored, 1..K = risk types.
        """
        import torchtuples as tt

        if self.num_risks <= 1:
            from pycox.models import DeepHitSingle as DeepHitCls
        else:
            from pycox.models import DeepHit as DeepHitCls

        # Discretise durations
        labtrans = DeepHitCls.label_transforms()
        target_train = labtrans.fit_transform(
            durations_train.astype("float32"),
            events_train.astype("float32"),
        )
        self._label_transform = labtrans
        out_features = labtrans.out_features

        # Build network
        net = tt.practical.MLPVanilla(
            in_features=self.in_features,
            num_nodes=self.hidden_layers,
            out_features=out_features,
            batch_norm=self.batch_norm,
            dropout=self.dropout,
        )

        self._model = DeepHitCls(
            net,
            tt.optim.Adam(self.lr),
            alpha=self.alpha,
            sigma=self.sigma,
            duration_index=labtrans.cuts,
        )

        callbacks = [tt.callbacks.EarlyStopping(patience=self.patience)]
        val_data = None
        if x_val is not None:
            target_val = labtrans.transform(
                durations_val.astype("float32"),
                events_val.astype("float32"),
            )
            val_data = (x_val.astype("float32"), target_val)

        log = self._model.fit(
            x_train.astype("float32"),
            target_train,
            self.batch_size,
            self.epochs,
            callbacks,
            val_data=val_data,
            verbose=False,
        )
        self._fitted = True
        logger.info("DeepHit trained: %d time bins", len(labtrans.cuts))
        return self

    def predict_cif(self, x: np.ndarray) -> np.ndarray:
        """Predict cumulative incidence functions.

        Returns
        -------
        ndarray of shape (n_samples, num_durations) for single-risk, or
        (n_risks, n_samples, num_durations) for competing risks.
        """
        if not self._fitted:
            raise RuntimeError("Model not fitted.")
        cif = self._model.predict_cif(x.astype("float32"))
        return np.array(cif)

    def predict_survival_function(self, x: np.ndarray) -> pd.DataFrame:
        """Predict all-cause survival function S(t) = 1 - sum(CIF_k(t)).

        Returns
        -------
        pd.DataFrame
            Index = time points, columns = subjects.
        """
        if not self._fitted:
            raise RuntimeError("Model not fitted.")
        surv = self._model.predict_surv_df(x.astype("float32"))
        return surv

    def predict_pmf(self, x: np.ndarray) -> np.ndarray:
        """Predict probability mass function over discrete time bins.

        Returns
        -------
        ndarray of shape (n_samples, num_durations)
        """
        if not self._fitted:
            raise RuntimeError("Model not fitted.")
        pmf = self._model.predict_pmf(x.astype("float32"))
        return np.array(pmf)

    @property
    def duration_index(self) -> np.ndarray:
        """The discrete time grid (cut points)."""
        if self._label_transform is None:
            raise RuntimeError("Model not fitted.")
        return self._label_transform.cuts

    def predict_risk_at(self, x: np.ndarray, time: float, risk: int = 0) -> np.ndarray:
        """Predict CIF at a specific time point for a given risk.

        Parameters
        ----------
        x : ndarray (n, in_features)
        time : float
            Target prediction horizon.
        risk : int
            Risk index (0-based).  Only used in competing-risks mode.

        Returns
        -------
        ndarray (n,)
            CIF values at the specified time.
        """
        cif = self.predict_cif(x)
        cuts = self.duration_index
        # Find nearest time index
        idx = int(np.searchsorted(cuts, time, side="right")) - 1
        idx = max(0, min(idx, len(cuts) - 1))

        if cif.ndim == 3:
            return cif[risk, :, idx]
        return cif[:, idx]


# ===================================================================
# Dynamic-DeepHit (longitudinal / sequence-based)
# ===================================================================

@auto_register(
    "dynamic_deephit",
    description="Dynamic-DeepHit with RNN encoder for longitudinal data",
    default_params={
        "in_features": 32,
        "hidden_rnn": 64,
        "hidden_fc": [32],
        "num_durations": 50,
        "rnn_type": "LSTM",
        "lr": 1e-3,
        "epochs": 100,
        "batch_size": 64,
    },
)
class DynamicDeepHitModel:
    """Dynamic-DeepHit: recurrent DeepHit for longitudinal data.

    Encodes time-varying covariate sequences with an RNN (LSTM/GRU),
    then predicts cause-specific PMFs at each time step.

    This implementation provides a simplified but functional version
    built on PyTorch, following the architecture described in
    Lee et al. (2020).

    Parameters
    ----------
    in_features : int
        Per-time-step input dimension.
    hidden_rnn : int
        RNN hidden state dimension.
    hidden_fc : list of int
        Fully connected layers after the RNN encoder.
    num_durations : int
        Number of discrete output time bins.
    rnn_type : str
        ``"LSTM"`` or ``"GRU"``.
    num_risks : int
        Number of competing risks.
    alpha : float
        Ranking loss weight.
    sigma : float
        Ranking loss bandwidth.
    lr : float
        Learning rate.
    epochs : int
        Training epochs.
    batch_size : int
        Mini-batch size.
    """

    def __init__(
        self,
        in_features: int = 32,
        hidden_rnn: int = 64,
        hidden_fc: Optional[List[int]] = None,
        num_durations: int = 50,
        rnn_type: str = "LSTM",
        num_risks: int = 1,
        alpha: float = 0.2,
        sigma: float = 0.1,
        lr: float = 1e-3,
        epochs: int = 100,
        batch_size: int = 64,
    ) -> None:
        self.in_features = in_features
        self.hidden_rnn = hidden_rnn
        self.hidden_fc = hidden_fc or [32]
        self.num_durations = num_durations
        self.rnn_type = rnn_type
        self.num_risks = num_risks
        self.alpha = alpha
        self.sigma = sigma
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size

        self._net = None
        self._cuts: Optional[np.ndarray] = None
        self._fitted = False

    def _build_net(self) -> Any:
        """Construct the RNN + FC network in PyTorch."""
        import torch
        import torch.nn as nn

        rnn_cls = nn.LSTM if self.rnn_type == "LSTM" else nn.GRU

        class DynamicDeepHitNet(nn.Module):
            def __init__(
                self,
                in_features: int,
                hidden_rnn: int,
                hidden_fc: List[int],
                num_durations: int,
                num_risks: int,
                rnn_cls: type,
            ):
                super().__init__()
                self.rnn = rnn_cls(in_features, hidden_rnn, batch_first=True)
                layers: List[nn.Module] = []
                prev_dim = hidden_rnn
                for h in hidden_fc:
                    layers.extend([nn.Linear(prev_dim, h), nn.ReLU(), nn.Dropout(0.1)])
                    prev_dim = h
                self.fc = nn.Sequential(*layers)
                self.output = nn.Linear(prev_dim, num_durations * max(num_risks, 1))
                self.num_durations = num_durations
                self.num_risks = num_risks

            def forward(self, x: torch.Tensor, lengths: Optional[torch.Tensor] = None) -> torch.Tensor:
                # x: (batch, seq_len, in_features)
                rnn_out, _ = self.rnn(x)
                # Use last valid hidden state
                if lengths is not None:
                    idx = (lengths - 1).long().clamp(min=0)
                    batch_idx = torch.arange(x.size(0), device=x.device)
                    h = rnn_out[batch_idx, idx]
                else:
                    h = rnn_out[:, -1, :]
                h = self.fc(h)
                logits = self.output(h)
                # Reshape to (batch, num_risks, num_durations) if competing
                if self.num_risks > 1:
                    logits = logits.view(-1, self.num_risks, self.num_durations)
                    pmf = torch.softmax(logits.view(-1, self.num_risks * self.num_durations), dim=-1)
                    pmf = pmf.view(-1, self.num_risks, self.num_durations)
                else:
                    pmf = torch.softmax(logits, dim=-1)
                return pmf

        return DynamicDeepHitNet(
            self.in_features,
            self.hidden_rnn,
            self.hidden_fc,
            self.num_durations,
            self.num_risks,
            rnn_cls,
        )

    def fit(
        self,
        x_train: np.ndarray,
        lengths_train: np.ndarray,
        durations_train: np.ndarray,
        events_train: np.ndarray,
    ) -> "DynamicDeepHitModel":
        """Train Dynamic-DeepHit.

        Parameters
        ----------
        x_train : ndarray (n, max_seq_len, in_features)
        lengths_train : ndarray (n,)
            Actual sequence lengths.
        durations_train : ndarray (n,)
            Follow-up times.
        events_train : ndarray (n,)
            Event indicators.
        """
        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader, TensorDataset

        # Discretise durations
        self._cuts = np.linspace(
            durations_train.min(),
            durations_train.max(),
            self.num_durations + 1,
        )
        bin_indices = np.digitize(durations_train, self._cuts[1:]).clip(0, self.num_durations - 1)

        self._net = self._build_net()
        optimiser = torch.optim.Adam(self._net.parameters(), lr=self.lr)

        x_t = torch.tensor(x_train, dtype=torch.float32)
        l_t = torch.tensor(lengths_train, dtype=torch.long)
        d_t = torch.tensor(bin_indices, dtype=torch.long)
        e_t = torch.tensor(events_train, dtype=torch.float32)

        dataset = TensorDataset(x_t, l_t, d_t, e_t)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        self._net.train()
        for epoch in range(self.epochs):
            epoch_loss = 0.0
            for xb, lb, db, eb in loader:
                pmf = self._net(xb, lb)
                loss = self._deephit_loss(pmf, db, eb)
                optimiser.zero_grad()
                loss.backward()
                optimiser.step()
                epoch_loss += loss.item() * len(xb)

            if (epoch + 1) % 20 == 0:
                logger.debug("Epoch %d/%d  loss=%.4f", epoch + 1, self.epochs, epoch_loss / len(dataset))

        self._fitted = True
        logger.info("Dynamic-DeepHit trained: %d epochs", self.epochs)
        return self

    def _deephit_loss(
        self,
        pmf: Any,  # torch.Tensor
        duration_bins: Any,
        events: Any,
    ) -> Any:
        """Combined NLL + ranking loss for DeepHit.

        The negative log-likelihood is computed for uncensored subjects
        at their event time bin, while censored subjects contribute via
        the survival function (sum of PMF beyond their censoring bin).

        The ranking loss penalises incorrect orderings: for pairs
        (i, j) where t_i < t_j and i experienced the event, the model
        should assign higher CIF at t_i for subject i than for subject j.
        """
        import torch

        batch_size = pmf.size(0)
        if pmf.ndim == 3:
            # Competing risks: use first risk for loss (simplified)
            pmf_flat = pmf[:, 0, :]
        else:
            pmf_flat = pmf

        # NLL component
        eps = 1e-8
        event_mask = events > 0
        nll = torch.tensor(0.0, device=pmf.device)
        if event_mask.any():
            event_probs = pmf_flat[event_mask, duration_bins[event_mask].long()]
            nll = -torch.log(event_probs + eps).mean()

        # Censored: should have high survival beyond censoring time
        censor_mask = events == 0
        if censor_mask.any():
            surv_probs = torch.zeros(censor_mask.sum(), device=pmf.device)
            for i, (idx, db) in enumerate(
                zip(censor_mask.nonzero(as_tuple=True)[0], duration_bins[censor_mask])
            ):
                surv_probs[i] = pmf_flat[idx, db.long():].sum()
            nll_censor = -torch.log(surv_probs + eps).mean()
            nll = nll + nll_censor

        # Ranking loss (simplified pairwise)
        cif = torch.cumsum(pmf_flat, dim=-1)
        ranking_loss = torch.tensor(0.0, device=pmf.device)
        if event_mask.sum() > 1:
            event_idx = event_mask.nonzero(as_tuple=True)[0]
            n_pairs = min(len(event_idx) * (len(event_idx) - 1) // 2, 500)
            if n_pairs > 0:
                pairs_i = event_idx[torch.randint(len(event_idx), (n_pairs,))]
                pairs_j = event_idx[torch.randint(len(event_idx), (n_pairs,))]
                valid = duration_bins[pairs_i] < duration_bins[pairs_j]
                if valid.any():
                    t_i = duration_bins[pairs_i[valid]].long()
                    diff = cif[pairs_j[valid], t_i] - cif[pairs_i[valid], t_i]
                    ranking_loss = torch.exp(diff / self.sigma).mean()

        total = (1.0 - self.alpha) * nll + self.alpha * ranking_loss
        return total

    def predict_cif(
        self,
        x: np.ndarray,
        lengths: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Predict cumulative incidence function.

        Parameters
        ----------
        x : ndarray (n, max_seq_len, in_features)
        lengths : ndarray (n,), optional

        Returns
        -------
        ndarray of shape (n, num_durations) or (n, num_risks, num_durations)
        """
        if not self._fitted:
            raise RuntimeError("Model not fitted.")
        import torch

        self._net.eval()
        with torch.no_grad():
            x_t = torch.tensor(x, dtype=torch.float32)
            l_t = torch.tensor(lengths, dtype=torch.long) if lengths is not None else None
            pmf = self._net(x_t, l_t).numpy()

        return np.cumsum(pmf, axis=-1)

    def predict_survival(
        self,
        x: np.ndarray,
        lengths: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Predict all-cause survival S(t) = 1 - sum(CIF_k(t))."""
        cif = self.predict_cif(x, lengths)
        if cif.ndim == 3:
            return 1.0 - cif.sum(axis=1)
        return 1.0 - cif
