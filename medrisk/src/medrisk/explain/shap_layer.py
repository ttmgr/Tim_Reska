"""SHAP explainability layer for all model types.

Provides a unified interface for computing SHAP values across XGBoost
(TreeExplainer) and other model types (KernelExplainer fallback).
"""

from __future__ import annotations

import logging
from io import BytesIO

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

logger = logging.getLogger(__name__)

# Use non-interactive backend for PDF/notebook rendering
matplotlib.use("Agg")

# ---------------------------------------------------------------------------
# SHAP / XGBoost compatibility fix
# Newer XGBoost (>=2.0) stores base_score as a bracketed string e.g.
# "[1.0625E-2]" in the UBJSON model dump. SHAP's XGBTreeModelLoader
# calls float() on this and crashes. We patch SHAP's decode_ubjson_buffer
# to strip brackets from learner_model_param values before SHAP sees them.
# ---------------------------------------------------------------------------
import shap.explainers._tree as _shap_tree  # noqa: E402

_orig_decode_ubjson = _shap_tree.decode_ubjson_buffer


def _clean_decode_ubjson(fd):
    result = _orig_decode_ubjson(fd)
    lmp = result.get("learner", {}).get("learner_model_param", {})
    for k, v in list(lmp.items()):
        if isinstance(v, str) and v.startswith("[") and v.endswith("]"):
            lmp[k] = v.strip("[]")
    return result


_shap_tree.decode_ubjson_buffer = _clean_decode_ubjson


def explain_xgboost(
    model,
    X: pd.DataFrame | np.ndarray,
    feature_names: list[str] | None = None,
) -> shap.Explanation:
    """Compute SHAP values for an XGBoost model using TreeExplainer.

    Args:
        model: Trained XGBClassifier or XGBRegressor.
        X: Feature matrix.
        feature_names: Feature names for labelling.

    Returns:
        shap.Explanation object with values, base values, and data.
    """
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X)

    if feature_names is not None and isinstance(X, np.ndarray):
        shap_values.feature_names = feature_names

    logger.info("SHAP values computed: %d samples x %d features", X.shape[0], X.shape[1])
    return shap_values


def explain_generic(
    predict_fn,
    X: pd.DataFrame | np.ndarray,
    background: pd.DataFrame | np.ndarray | None = None,
    n_background: int = 50,
    feature_names: list[str] | None = None,
) -> shap.Explanation:
    """Compute SHAP values using KernelExplainer for any model.

    Slower than TreeExplainer but works with any predict function.

    Args:
        predict_fn: Callable that takes X and returns predictions.
        X: Feature matrix to explain.
        background: Background dataset for KernelExplainer.
        n_background: Number of background samples to use.
        feature_names: Feature names for labelling.

    Returns:
        shap.Explanation object.
    """
    if background is None:
        background = X

    if len(background) > n_background:
        idx = np.random.default_rng(42).choice(len(background), n_background, replace=False)
        if isinstance(background, pd.DataFrame):
            background = background.iloc[idx]
        else:
            background = background[idx]

    explainer = shap.KernelExplainer(predict_fn, background)
    shap_values = explainer.shap_values(X)

    if isinstance(shap_values, list):
        shap_values = shap_values[1]  # class 1 for binary classification

    base_value = explainer.expected_value
    if isinstance(base_value, (list, np.ndarray)):
        base_value = base_value[1] if len(base_value) > 1 else base_value[0]

    explanation = shap.Explanation(
        values=shap_values,
        base_values=np.full(len(X), base_value),
        data=X.values if isinstance(X, pd.DataFrame) else X,
        feature_names=feature_names or (list(X.columns) if isinstance(X, pd.DataFrame) else None),
    )

    return explanation


def get_top_features(
    shap_values: shap.Explanation,
    n_top: int = 10,
) -> list[tuple[str, float]]:
    """Get top features by mean absolute SHAP value.

    Args:
        shap_values: SHAP Explanation object.
        n_top: Number of top features to return.

    Returns:
        List of (feature_name, mean_abs_shap) tuples, sorted descending.
    """
    if hasattr(shap_values.values, "shape") and len(shap_values.values.shape) > 2:
        vals = shap_values.values[:, :, 1]
    else:
        vals = shap_values.values

    mean_abs = np.abs(vals).mean(axis=0)
    names = shap_values.feature_names or [f"f{i}" for i in range(len(mean_abs))]

    ranked = sorted(zip(names, mean_abs, strict=True), key=lambda x: x[1], reverse=True)
    return ranked[:n_top]


def plot_waterfall(
    shap_values: shap.Explanation,
    sample_idx: int = 0,
) -> BytesIO:
    """Generate a waterfall plot for a single sample.

    Args:
        shap_values: SHAP Explanation object.
        sample_idx: Index of the sample to plot.

    Returns:
        BytesIO containing the plot as PNG.
    """
    fig = plt.figure(figsize=(10, 6))
    single = shap_values[sample_idx]
    if hasattr(single.values, "shape") and len(single.values.shape) > 1:
        single = shap.Explanation(
            values=single.values[:, 1],
            base_values=single.base_values[1]
            if hasattr(single.base_values, "__len__")
            else single.base_values,
            data=single.data,
            feature_names=single.feature_names,
        )
    shap.plots.waterfall(single, show=False)
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def plot_beeswarm(
    shap_values: shap.Explanation,
) -> BytesIO:
    """Generate a beeswarm plot for global feature importance.

    Args:
        shap_values: SHAP Explanation object.

    Returns:
        BytesIO containing the plot as PNG.
    """
    fig = plt.figure(figsize=(10, 8))
    sv = shap_values
    if hasattr(sv.values, "shape") and len(sv.values.shape) > 2:
        sv = shap.Explanation(
            values=sv.values[:, :, 1],
            base_values=sv.base_values[:, 1]
            if hasattr(sv.base_values, "shape") and len(sv.base_values.shape) > 1
            else sv.base_values,
            data=sv.data,
            feature_names=sv.feature_names,
        )
    shap.plots.beeswarm(sv, show=False)
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf
