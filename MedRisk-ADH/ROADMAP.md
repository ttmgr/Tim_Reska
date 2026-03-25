# Roadmap

## Phase 1 — Synthetic Proof of Concept (current)

**Status:** Complete.

**What it demonstrates:**
- XGBoost risk classifier, Cox PH survival model, and CTMC multistate disease progression
- Multi-market synthetic cohort generator (DE, ES, FR, INT) with realistic data quality variance
- Data Quality Score (DQS): per-patient input quality assessment
- Plausible-but-wrong (PBW) detection: flags confident predictions on insufficient data
- SHAP explainability for all model types
- PDF report generation with validation status
- Five narrative notebooks documenting the full pipeline

**What it does NOT demonstrate:**
- Performance on real patient data. All metrics are on synthetic distributions.
- Calibrated DQS thresholds. The 0.60/0.80 boundaries are heuristic, not empirically validated.
- Regulatory compliance. No DPIA, no model risk management framework, no audit trail.

**Honest assessment:** This is a mechanism demonstration, not a production system. The synthetic data proves the detection logic works; it does not prove the thresholds are correct for any specific insurer's portfolio.

---

## Phase 2 — Retrospective Validation

**Goal:** Validate DQS thresholds and PBW detection against real underwriting outcomes.

**Data requirements:**
- Pseudonymised claims dataset with linked underwriting decisions and outcomes
- Germany: InGef (~8M GKV), GePaRD (~20M GKV), or PKV partner data
- Minimum 50,000 patients with 5+ years follow-up and known outcomes

**DSGVO path (Germany):**
- GKV research data: §75 SGB X (secondary use for research), requires BIPS/InGef application + institutional ethics vote
- PKV data: Art. 6(1)(f) DSGVO legitimate interest for actuarial modelling, or Art. 89 research exemption with DPIA
- Insurer internal: data stays within insurer infrastructure, DPO clearance under existing data governance

**Technical tasks:**
1. Retrain models on real prevalence distributions
2. Calibrate DQS thresholds against actual claims outcomes (optimise cost function: false positive review cost vs. false negative claim cost)
3. Validate PBW detector: do flagged patients have higher claim rates than the model predicts?
4. Benchmark against existing underwriting rules (lift analysis)

**Gating factor:** Data access. This is a regulatory and partnership process, not a technical bottleneck.

---

## Phase 3 — Production Integration

**Goal:** Deploy as a validation layer in a live underwriting workflow.

**Requirements:**
- Insurance partner commitment
- EU AI Act compliance framework (Art. 6 risk classification, Art. 14 human oversight)
- DPIA (Datenschutz-Folgenabschätzung, Art. 35 DSGVO) for health data processing at scale

**Technical tasks:**
1. REST API layer for real-time risk scoring and validation
2. Human-in-the-loop review interface for PBW-flagged cases
3. Model monitoring: drift detection, recalibration triggers, performance dashboards
4. Extended model zoo: DeepSurv, SurvTRACE for comparison against classical models
5. Multi-market deployment: market-specific DQS calibration and consistency rules
6. Audit trail and explainability reports for regulatory submission

**Governance:**
- Model card and data sheet per EU AI Act requirements
- Risk register aligned with Solvency II model risk framework
- Regular model validation cycle (annual minimum)

**Timeline estimate:** 12–18 months from data access to production pilot. The bottleneck is not engineering — it is data partnership, regulatory clearance, and organisational alignment.
