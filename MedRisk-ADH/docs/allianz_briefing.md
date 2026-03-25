# MedRisk-ADH
## AI-Augmented Underwriting with Failure Mode Detection
### Executive Briefing | Allianz Digital Health

---

## The Insight

Every AI model in medical underwriting makes a hidden assumption: **the input data is good enough to support the prediction.** No production system today validates this assumption at the individual level.

When a model scores a patient as "78% high risk" on 3 coded diagnoses and no lab results, it is not expressing clinical insight — it is expressing learned population priors. The output is **plausible** — it looks like a reasonable risk score — but it is **wrong** for this specific patient.

We call this failure mode **Plausible-but-Wrong (PBW)**.

At portfolio scale:
- 100,000 underwriting decisions per year
- Illustrative 2% PBW rate
- **2,000 mispriced policies annually, invisible in standard model metrics**

---

## The Solution

MedRisk-ADH introduces a **pre-inference data quality gate** — a per-patient score computed before the model runs, answering: *"Should I trust my own input?"*

### Data Quality Score (DQS)

| Component | Weight | What it measures |
|-----------|--------|-----------------|
| **Completeness** | 0.40 | Fraction of expected clinical features present |
| **Consistency** | 0.35 | Domain rules: diabetes + HbA1c, CKD + eGFR, HF + NT-proBNP |
| **Recency** | 0.25 | Lab freshness (exponential decay, t1/2 = 1.4 years) |

**Decision tiers:**

| Tier | Threshold | Action | Expected volume |
|------|-----------|--------|-----------------|
| Adequate | DQS >= 0.80 | Automate | ~60-70% |
| Caution | 0.60-0.80 | Human review | ~20-30% |
| Insufficient | < 0.60 | Reject prediction | ~5-15% |

### PBW Detection

```
IF model confidence > 0.80 AND DQS < 0.60
THEN flag: Plausible-but-Wrong → escalate to human underwriter
```

The model is highly confident, but the data is too sparse to support that confidence. This is the exact scenario that causes silent mispricing.

---

## Proof of Concept: What We Built

### Three-Model Stack

| Model | Purpose | Metric |
|-------|---------|--------|
| **XGBoost** | Binary risk classification | AUC 0.71 |
| **Cox PH** | Survival analysis (time-to-event) | C-index 0.72 |
| **CTMC** | Disease progression trajectories | 5-state Markov chain |

### Multi-Market Validation

Synthetic cohort: 4,000 patients across 4 European market profiles with controlled data quality degradation.

| Market | Coding completeness | Lab completeness | PBW flag rate |
|--------|-------------------|-----------------|---------------|
| **DE** | 95% | 92% | 0.9% |
| **FR** | 90% | 88% | 1.0% |
| **ES** | 80% | 75% | 1.3% |
| **INT** | 60% | 50% | **2.1%** |

**Result:** The market with the worst data infrastructure (INT) produces 2.4x the PBW rate of the best (DE). The detector identifies the risk differential that standard model metrics miss entirely.

### Explainability

Every prediction includes:
- SHAP feature attribution (which variables drove the decision)
- DQS decomposition (which quality component is weak)
- Validation flags with human-readable explanation
- Full PDF underwriting report

### Disease-Specific Modeling

The framework generalises beyond cardiovascular risk. An Alzheimer's disease module demonstrates the pattern:

- 7-state CTMC from normal cognition through MCI to severe AD and death
- Transition rates calibrated to published literature (Petersen et al., Brookmeyer et al.)
- Cognitive biomarkers (MMSE, MoCA, CSF amyloid-beta42, CSF p-tau181)
- ApoE4 genotype as graduated risk modifier
- New disease models are added as data configurations -- no code changes required

### Software Quality

- 231 unit tests, all passing
- 2 disease models (cardiovascular + Alzheimer), 4 European markets
- 5 executable Jupyter notebooks documenting the full pipeline
- All clinical numbers fact-checked against published literature (PubMed, WHO, LOINC)
- Comprehensive documentation (methods paper, technical guide, roadmap)
- Reproducible: fixed seeds, parametric generation, no external data dependencies

---

## What This Enables

### For Underwriting Operations

**Automate the 70% where data quality supports the decision.** Every automated decision carries a traceable quality assessment. Human underwriters focus exclusively on the 30% that actually need judgement.

| Current state | With MedRisk-ADH |
|--------------|-----------------|
| All cases reviewed manually or by model alone | Tiered: auto / review / reject |
| No per-case quality assessment | DQS for every patient |
| PBW invisible in portfolio metrics | PBW flagged before decision |
| Explanation: "the model says 78%" | Explanation: "age (+12%), hypertension (+8%), Charlson (+6%)" |

### For Risk Management

The PBW detector directly reduces exposure to mispriced risk. A single flagged case that would have been incorrectly accepted at standard terms can save multiples of the system's cost.

### For Regulatory Compliance

EU AI Act (2024) classifies insurance AI as high-risk (Art. 6). Requirements include:
- Human oversight capability (Art. 14) — **MedRisk-ADH: tiered escalation**
- Accuracy and robustness documentation (Art. 15) — **MedRisk-ADH: DQS + validation layer**
- Risk management system (Art. 9) — **MedRisk-ADH: PBW detection as systematic risk mitigation**

---

## Validation Roadmap

### Phase 1: Synthetic Proof of Concept -- COMPLETE

- Full pipeline operational on synthetic data
- DQS, PBW detection, three-model stack, SHAP explainability
- Multi-market design validated (DE/FR/ES/INT)

### Phase 2: Retrospective Validation (3-6 months)

| Step | Data source | What we validate | Timeline |
|------|------------|------------------|----------|
| 1 | **CPRD (UK)** | Full DQS incl. lab-based consistency rules | 2-4 months |
| 2 | **InGef (DE)** | German market compatibility (ICD-10-GM) | 3-6 months |
| 3 | **Allianz internal** | PKV claims data pilot | 6-12 months |

**Key finding from data source analysis:** No German claims database includes lab result values. CPRD (UK, 60M patients) is the only source that can validate the full DQS including lab-based consistency rules. German validation (InGef) covers diagnosis and medication completeness.

### Phase 3: Production Integration (12-18 months)

- REST API for real-time scoring
- Human-in-the-loop review interface
- Model drift monitoring and DQS recalibration
- Full EU AI Act compliance package (DPIA, model cards, audit trail)

---

## The Ask

To move from PoC to retrospective validation, we need:

| Requirement | Purpose | Owner |
|-------------|---------|-------|
| **Pseudonymised claims data** | 50,000+ records, 5+ years, linked outcomes | Data partnership (PKV/InGef) |
| **DPO clearance** | DSGVO Art. 89 research exemption or Art. 6(1)(f) | Allianz Legal/DPO |
| **3-month validation sprint** | Retrain on real data, calibrate DQS thresholds | Tim Reska + Allianz Data Science |
| **Clinical advisory** | Validate consistency rules with medical underwriter | Allianz Medical |

---

## Why Now

1. **Regulatory pressure:** EU AI Act enforcement begins 2026. High-risk AI systems (including insurance) require documented quality assurance mechanisms. MedRisk-ADH provides exactly this.

2. **Competitive advantage:** To our knowledge, no published approach combines a pre-inference data quality gate with cost-optimal reliability scoring for underwriting.

3. **Scalable risk reduction:** The validation layer is model-agnostic. It works with any downstream classifier. Invest once, apply across all underwriting AI.

4. **Scientific foundation:** The PBW failure mode is documented in peer-reviewed literature (ISME Communications 2024). The DQS framework aligns with the Kahn et al. (2016) consensus framework for EHR data quality. This is not a black box — it is a principled, auditable approach.

---

*Tim Reska | Helmholtz Munich | tim.reska@helmholtz-munich.de*

*MedRisk-ADH v2.0.0 | Synthetic Data Only | March 2026*
