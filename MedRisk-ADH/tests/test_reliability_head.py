"""Tests for reliability head."""


from medrisk.data.schemas import MARKET_CONFIGS
from medrisk.data.synthetic import cohort_to_dataframe, generate_cohort
from medrisk.features.data_profile import classify_cohort_profiles
from medrisk.features.engineering import build_feature_matrix, get_targets
from medrisk.models.model_router import ModelRouter
from medrisk.validation.data_quality import compute_dqs_v2
from medrisk.validation.reliability_head import (
    ReliabilityConfig,
    ReliabilityDecision,
    ReliabilityHead,
)


def _setup():
    cohort = generate_cohort(n_per_market=300, markets=["DE", "INT"], seed=42)
    df = cohort_to_dataframe(cohort)
    X, feat = build_feature_matrix(df, impute_strategy="none")
    events, _ = get_targets(df)
    rdf = X.copy()
    rdf["event_occurred"] = events
    rdf["patient_id"] = df["patient_id"].values
    profiles = classify_cohort_profiles(rdf)
    router = ModelRouter()
    router.train(rdf, feat, profiles=profiles)
    result = router.predict(rdf, profiles=profiles)
    dqs_results = [compute_dqs_v2(p, MARKET_CONFIGS.get(p.market.value)) for p in cohort]
    return result, events, dqs_results, list(profiles), result.patient_ids


class TestReliabilityHead:
    def test_fit_succeeds(self):
        result, events, dqs, profiles, pids = _setup()
        head = ReliabilityHead()
        head.fit(result.probabilities, events, dqs, profiles)
        assert head.is_fitted

    def test_predict_returns_decisions(self):
        result, events, dqs, profiles, pids = _setup()
        head = ReliabilityHead()
        head.fit(result.probabilities, events, dqs, profiles)
        decisions = head.predict(result.probabilities, dqs, profiles, pids)
        assert len(decisions) == len(events)
        assert all(isinstance(d, ReliabilityDecision) for d in decisions)

    def test_decisions_are_valid(self):
        result, events, dqs, profiles, pids = _setup()
        head = ReliabilityHead()
        head.fit(result.probabilities, events, dqs, profiles)
        decisions = head.predict(result.probabilities, dqs, profiles, pids)
        for d in decisions:
            assert d.decision in ("accept", "reject", "human_review")
            assert 0 <= d.p_wrong <= 1
            assert d.explanation != ""

    def test_coefficient_table(self):
        result, events, dqs, profiles, pids = _setup()
        head = ReliabilityHead()
        head.fit(result.probabilities, events, dqs, profiles)
        table = head.get_coefficient_table()
        assert len(table) > 0
        assert "feature" in table.columns
        assert "coefficient" in table.columns

    def test_cost_affects_decisions(self):
        result, events, dqs, profiles, pids = _setup()
        # High cost_fn -> more rejections/reviews
        head_strict = ReliabilityHead(ReliabilityConfig(cost_fn=20.0, cost_fp=1.0, cost_review=0.5))
        head_strict.fit(result.probabilities, events, dqs, profiles)
        d_strict = head_strict.predict(result.probabilities, dqs, profiles, pids)

        # Low cost_fn -> more accepts
        head_lenient = ReliabilityHead(ReliabilityConfig(cost_fn=0.1, cost_fp=1.0, cost_review=0.5))
        head_lenient.fit(result.probabilities, events, dqs, profiles)
        d_lenient = head_lenient.predict(result.probabilities, dqs, profiles, pids)

        n_accept_strict = sum(1 for d in d_strict if d.decision == "accept")
        n_accept_lenient = sum(1 for d in d_lenient if d.decision == "accept")
        # Lenient should accept more
        assert n_accept_lenient >= n_accept_strict

    def test_v1_pbw_flag_populated(self):
        result, events, dqs, profiles, pids = _setup()
        head = ReliabilityHead()
        head.fit(result.probabilities, events, dqs, profiles)
        decisions = head.predict(result.probabilities, dqs, profiles, pids)
        # All decisions should have the v1 flag (True or False)
        assert all(isinstance(d.v1_pbw_flag, bool) for d in decisions)
