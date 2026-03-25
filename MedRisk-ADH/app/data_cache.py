"""Cached data generation and model training for the Streamlit app.

Runs the full MedRisk-ADH v2 pipeline once on startup and caches all
results for interactive exploration.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from medrisk.data.schemas import MARKET_CONFIGS
from medrisk.data.synthetic import cohort_to_dataframe, generate_cohort
from medrisk.features.data_profile import classify_cohort_profiles
from medrisk.features.engineering import build_feature_matrix, get_targets
from medrisk.models.model_router import ModelRouter
from medrisk.models.multistate import MultistateModel
from medrisk.validation.data_quality import compute_dqs_v2
from medrisk.validation.reliability_head import ReliabilityConfig, ReliabilityHead


@st.cache_resource(show_spinner="Generating synthetic cohort and training models...")
def load_app_data(n_per_market: int = 1000, seed: int = 42) -> dict:
    """Generate cohort, train models, compute all scores.

    Returns a dict (not dataclass) for Streamlit cache compatibility.
    """
    # Generate cohort
    cohort = generate_cohort(n_per_market=n_per_market, seed=seed)
    df = cohort_to_dataframe(cohort)

    # Features (no imputation for router)
    X, feature_names = build_feature_matrix(df, impute_strategy="none")
    events, times = get_targets(df)

    # Router DataFrame
    router_df = X.copy()
    router_df["event_occurred"] = events
    router_df["patient_id"] = df["patient_id"].values
    router_df["market"] = df["market"].values

    # Data profiles
    profiles = classify_cohort_profiles(router_df)

    # DQS v2
    dqs_results = []
    for p in cohort:
        mc = MARKET_CONFIGS.get(p.market.value)
        dqs_results.append(compute_dqs_v2(p, market_config=mc))

    # Train router
    router = ModelRouter()
    router.train(router_df, feature_names, profiles=profiles)

    # Predict
    router_result = router.predict(router_df, profiles=profiles)

    # Train reliability head
    rhead = ReliabilityHead(ReliabilityConfig(cost_fp=1.0, cost_fn=5.0, cost_review=0.5))
    rhead.fit(router_result.probabilities, events, dqs_results, list(profiles))

    # Get decisions
    decisions = rhead.predict(
        router_result.probabilities,
        dqs_results,
        list(profiles),
        router_result.patient_ids,
    )

    # CTMC model
    msm = MultistateModel()
    msm.set_intensities({
        (0, 1): 0.08, (1, 0): 0.02, (1, 2): 0.06,
        (2, 3): 0.04, (2, 4): 0.01, (3, 4): 0.03,
    })

    return {
        "cohort": cohort,
        "df": df,
        "feature_matrix": X,
        "feature_names": feature_names,
        "events": events,
        "profiles": profiles,
        "dqs_results": dqs_results,
        "router": router,
        "reliability_head": rhead,
        "predictions": router_result.probabilities,
        "decisions": decisions,
        "model_ids": router_result.model_ids,
        "msm": msm,
        "router_df": router_df,
    }
