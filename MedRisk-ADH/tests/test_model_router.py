"""Tests for model router."""

import numpy as np

from medrisk.data.synthetic import cohort_to_dataframe, generate_cohort
from medrisk.features.engineering import build_feature_matrix, get_targets
from medrisk.models.model_router import ModelRouter, RouterPrediction


class TestModelRouter:
    def _make_router_df(self, n=500):
        cohort = generate_cohort(n_per_market=n, markets=["DE"], seed=42)
        df = cohort_to_dataframe(cohort)
        X, feat = build_feature_matrix(df, impute_strategy="none")
        events, _ = get_targets(df)
        rdf = X.copy()
        rdf["event_occurred"] = events
        rdf["patient_id"] = df["patient_id"].values
        rdf["market"] = df["market"].values
        return rdf, feat

    def test_train_creates_models(self):
        rdf, feat = self._make_router_df()
        router = ModelRouter()
        router.train(rdf, feat)
        assert len(router.models) > 0

    def test_predict_returns_router_prediction(self):
        rdf, feat = self._make_router_df()
        router = ModelRouter()
        router.train(rdf, feat)
        result = router.predict(rdf)
        assert isinstance(result, RouterPrediction)
        assert len(result.probabilities) == len(rdf)

    def test_predictions_bounded(self):
        rdf, feat = self._make_router_df()
        router = ModelRouter()
        router.train(rdf, feat)
        result = router.predict(rdf)
        valid = ~np.isnan(result.probabilities)
        assert all(0 <= p <= 1 for p in result.probabilities[valid])

    def test_model_ids_assigned(self):
        rdf, feat = self._make_router_df()
        router = ModelRouter()
        router.train(rdf, feat)
        result = router.predict(rdf)
        assert all(mid != "none" for mid in result.model_ids)

    def test_profile_summary(self):
        rdf, feat = self._make_router_df()
        router = ModelRouter()
        router.train(rdf, feat)
        summary = router.get_profile_summary()
        assert len(summary) > 0
        for _profile, info in summary.items():
            assert "n_features" in info
            assert info["n_features"] > 0
