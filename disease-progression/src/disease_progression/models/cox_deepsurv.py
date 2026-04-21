"""
disease_progression.models.cox_deepsurv - Cox PH and DeepSurv wrappers.

Implements two related survival models:

1. **CoxPHModel** -- a thin wrapper around ``lifelines.CoxPHFitter``,
   providing a standardised fit / predict / evaluate interface consistent
   with the rest of the model zoo.  Supports Efron and Breslow tie-handling,
   L2 (ridge) penalisation, and Schoenfeld residual diagnostics.

2. **DeepSurvModel** -- a feed-forward neural network that learns the
   log-risk function in the Cox partial likelihood framework, following
   Katzman et al. (2018).  Built on ``pycox``'s ``CoxPH`` estimator and
   ``torchtuples`` for training.  Supports arbitrary hidden layer
   architectures, dropout, batch normalisation, and learning-rate
   scheduling.

Both models produce a **risk score** (log partial hazard) per subject
and share a common ``predict_risk()`` interface.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from disease_progression.models.registry import auto_register

logger = logging.getLogger(__name__)


# ===================================================================
# Classical Cox PH via lifelines
# ===================================================================

@auto_register(
    "cox_ph",
    description="Cox proportional hazards model (lifelines)",
    default_params={"penalizer": 0.01, "l1_ratio": 0.0},
)
class CoxPHModel:
    """Cox PH wrapper using lifelines.

    Parameters
    ----------
    penalizer : float
        L2 penalisation strength (ridge).  Helps with collinear features.
    l1_ratio : float
        Elastic-net mixing (0 = pure L2, 1 = pure L1).
    baseline_estimation : str
        ``"breslow"`` or ``"spline"`` for cumulative baseline hazard.
    """

    def __init__(
        self,
        penalizer: float = 0.01,
        l1_ratio: float = 0.0,
        baseline_estimation: str = "breslow",
    ) -> None:
        self.penalizer = penalizer
        self.l1_ratio = l1_ratio
        self.baseline_estimation = baseline_estimation
        self._fitter = None

    def fit(
        self,
        df: pd.DataFrame,
        duration_col: str = "duration",
        event_col: str = "event",
        covariates: Optional[List[str]] = None,
        show_progress: bool = False,
    ) -> "CoxPHModel":
        """Fit the Cox PH model.

        Parameters
        ----------
        df : pd.DataFrame
            Training data with covariates, duration, and event columns.
        duration_col : str
            Column name for follow-up time.
        event_col : str
            Column name for event indicator (1 = event, 0 = censored).
        covariates : list of str, optional
            Subset of columns to use as covariates.  If None, all
            columns except duration and event are used.
        """
        from lifelines import CoxPHFitter

        self._fitter = CoxPHFitter(
            penalizer=self.penalizer,
            l1_ratio=self.l1_ratio,
            baseline_estimation=self.baseline_estimation,
        )

        fit_df = df.copy()
        if covariates is not None:
            fit_df = fit_df[covariates + [duration_col, event_col]]

        self._fitter.fit(
            fit_df,
            duration_col=duration_col,
            event_col=event_col,
            show_progress=show_progress,
        )
        logger.info(
            "CoxPH fitted: concordance=%.4f, n=%d, events=%d",
            self._fitter.concordance_index_,
            len(fit_df),
            int(fit_df[event_col].sum()),
        )
        return self

    def predict_risk(self, df: pd.DataFrame) -> np.ndarray:
        """Predict log partial hazard (higher = greater risk).

        Parameters
        ----------
        df : pd.DataFrame
            Must contain the same covariates used during fitting.

        Returns
        -------
        ndarray of shape (n_samples,)
        """
        if self._fitter is None:
            raise RuntimeError("Model not fitted.")
        return self._fitter.predict_log_partial_hazard(df).values.ravel()

    def predict_survival_function(
        self,
        df: pd.DataFrame,
        times: Optional[np.ndarray] = None,
    ) -> pd.DataFrame:
        """Predict individual survival curves.

        Returns
        -------
        pd.DataFrame
            Rows = time points, columns = subjects.
        """
        if self._fitter is None:
            raise RuntimeError("Model not fitted.")
        return self._fitter.predict_survival_function(df, times=times)

    def predict_cumulative_hazard(
        self,
        df: pd.DataFrame,
        times: Optional[np.ndarray] = None,
    ) -> pd.DataFrame:
        """Predict individual cumulative hazard functions."""
        if self._fitter is None:
            raise RuntimeError("Model not fitted.")
        return self._fitter.predict_cumulative_hazard(df, times=times)

    def summary(self) -> pd.DataFrame:
        """Return coefficient table with p-values and CIs."""
        if self._fitter is None:
            raise RuntimeError("Model not fitted.")
        return self._fitter.summary

    def check_proportional_hazards(self, df: pd.DataFrame, **kwargs: Any) -> Any:
        """Run Schoenfeld residual test for PH assumption."""
        if self._fitter is None:
            raise RuntimeError("Model not fitted.")
        return self._fitter.check_assumptions(df, **kwargs)

    @property
    def concordance_index(self) -> float:
        if self._fitter is None:
            raise RuntimeError("Model not fitted.")
        return self._fitter.concordance_index_

    @property
    def coefficients(self) -> pd.Series:
        if self._fitter is None:
            raise RuntimeError("Model not fitted.")
        return self._fitter.params_


# ===================================================================
# DeepSurv (neural Cox PH) via pycox
# ===================================================================

@auto_register(
    "deepsurv",
    description="DeepSurv neural network Cox PH (pycox/torchtuples)",
    default_params={
        "in_features": 32,
        "hidden_layers": [64, 64],
        "dropout": 0.1,
        "lr": 1e-3,
        "epochs": 100,
        "batch_size": 256,
    },
)
class DeepSurvModel:
    """DeepSurv: a feed-forward neural Cox PH model.

    The network learns a function f(x) that replaces the linear
    predictor beta^T x in the Cox partial likelihood.  Training
    maximises the partial likelihood via gradient descent.

    Parameters
    ----------
    in_features : int
        Dimensionality of the input feature vector.
    hidden_layers : list of int
        Hidden layer widths.
    dropout : float
        Dropout rate between hidden layers.
    batch_norm : bool
        Whether to apply batch normalisation.
    lr : float
        Learning rate.
    epochs : int
        Maximum training epochs.
    batch_size : int
        Mini-batch size.
    patience : int
        Early-stopping patience (epochs without improvement).
    """

    def __init__(
        self,
        in_features: int = 32,
        hidden_layers: Optional[List[int]] = None,
        dropout: float = 0.1,
        batch_norm: bool = True,
        lr: float = 1e-3,
        epochs: int = 100,
        batch_size: int = 256,
        patience: int = 10,
    ) -> None:
        self.in_features = in_features
        self.hidden_layers = hidden_layers or [64, 64]
        self.dropout = dropout
        self.batch_norm = batch_norm
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size
        self.patience = patience

        self._model = None
        self._fitted = False

    def _build_net(self) -> Any:
        """Construct the torch MLP and pycox CoxPH estimator."""
        import torch
        import torchtuples as tt
        from pycox.models import CoxPH

        net = tt.practical.MLPVanilla(
            in_features=self.in_features,
            num_nodes=self.hidden_layers,
            out_features=1,
            batch_norm=self.batch_norm,
            dropout=self.dropout,
            output_bias=False,
        )
        model = CoxPH(net, tt.optim.Adam(self.lr))
        return model

    def fit(
        self,
        x_train: np.ndarray,
        durations_train: np.ndarray,
        events_train: np.ndarray,
        x_val: Optional[np.ndarray] = None,
        durations_val: Optional[np.ndarray] = None,
        events_val: Optional[np.ndarray] = None,
    ) -> "DeepSurvModel":
        """Train the DeepSurv model.

        Parameters
        ----------
        x_train : ndarray (n, in_features)
            Training covariates.
        durations_train : ndarray (n,)
            Follow-up times.
        events_train : ndarray (n,)
            Event indicators.
        x_val, durations_val, events_val : optional
            Validation set for early stopping.
        """
        import torchtuples as tt
        from pycox.models import CoxPH

        self._model = self._build_net()

        x_train = x_train.astype("float32")
        y_train = (durations_train.astype("float32"), events_train.astype("float32"))

        callbacks = [tt.callbacks.EarlyStopping(patience=self.patience)]
        val_data = None
        if x_val is not None:
            x_val = x_val.astype("float32")
            val_data = (x_val, (durations_val.astype("float32"), events_val.astype("float32")))

        log = self._model.fit(
            x_train,
            y_train,
            self.batch_size,
            self.epochs,
            callbacks,
            val_data=val_data,
            verbose=False,
        )
        self._model.compute_baseline_hazards()
        self._fitted = True
        logger.info(
            "DeepSurv trained: %d epochs, final train loss=%.4f",
            len(log.monitors["train_loss"].scores),
            log.monitors["train_loss"].scores[-1],
        )
        return self

    def predict_risk(self, x: np.ndarray) -> np.ndarray:
        """Predict log-risk scores.

        Parameters
        ----------
        x : ndarray (n, in_features)

        Returns
        -------
        ndarray (n,)
        """
        if not self._fitted:
            raise RuntimeError("Model not fitted.")
        return self._model.predict(x.astype("float32")).ravel()

    def predict_survival_function(
        self,
        x: np.ndarray,
        times: Optional[np.ndarray] = None,
    ) -> pd.DataFrame:
        """Predict survival curves S(t|x) via Breslow estimator.

        Returns
        -------
        pd.DataFrame
            Index = time points, columns = subjects.
        """
        if not self._fitted:
            raise RuntimeError("Model not fitted.")
        surv = self._model.predict_surv_df(x.astype("float32"))
        if times is not None:
            surv = surv.reindex(times, method="ffill")
        return surv

    def predict_cumulative_hazard(
        self,
        x: np.ndarray,
        times: Optional[np.ndarray] = None,
    ) -> pd.DataFrame:
        """Predict cumulative hazard via Breslow estimator."""
        if not self._fitted:
            raise RuntimeError("Model not fitted.")
        cumhaz = self._model.predict_cumulative_hazards(x.astype("float32"))
        if times is not None:
            cumhaz = cumhaz.reindex(times, method="ffill")
        return cumhaz

    @property
    def net(self) -> Any:
        """Return the underlying torch network."""
        if self._model is None:
            raise RuntimeError("Model not built.")
        return self._model.net
