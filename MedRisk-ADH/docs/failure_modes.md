# Failure Mode Analysis: Confidence-Calibrated Detection in Automated Underwriting

## 1. Background

Automated medical underwriting systems apply machine learning models to patient health records to produce risk classifications. These systems are evaluated primarily on discrimination (AUC-ROC, concordance index) and calibration (Brier score, reliability diagrams). However, these aggregate metrics obscure a critical failure mode: cases where the model produces a confident prediction that is wrong, and there is no signal in the model's output that anything is amiss.

We term this the **plausible-but-wrong** (PBW) failure mode. It is analogous to the failure mode documented in AI-generated scientific analysis pipelines (Reska et al., ISME Communications, 2024), where large language models produced syntactically correct and methodologically plausible bioinformatics workflows that were nevertheless wrong for the specific input data. The failure was dangerous precisely because the output looked correct.

In underwriting, the PBW failure mode manifests when a model classifies a patient as low-risk with high confidence, but the confidence is an artefact of missing data rather than genuine clinical evidence. The model's training distribution fills in the gaps with its learned prior — which is correct on average but wrong for the specific patient.

## 2. Mechanism

### 2.1 Data Quality as Information Content

We define the **Data Quality Score** (DQS) as a per-patient scalar in [0, 1] that quantifies the information content of the input data before any model inference. It comprises three components:

**Completeness** (weight α = 0.40): The fraction of expected clinical features that are observed. Expected features include demographics (5), Charlson comorbidity indicators (17), laboratory values (10), and medication flags (8), totalling 50 features.

$$C_i = \frac{|\text{observed features}_i|}{|\text{expected features}|}$$

**Consistency** (weight β = 0.35): The fraction of testable domain rules that pass. Rules encode clinical expectations: if diabetes is coded, HbA1c should be elevated; if CKD stage 5 is coded, eGFR should be below 30. An inconsistency indicates either a coding error or a stale record.

$$K_i = \frac{|\text{rules passed}_i|}{|\text{rules testable}_i|}$$

**Recency** (weight γ = 0.25): The mean temporal weight of laboratory results, with exponential decay:

$$R_i = \frac{1}{|L_i|} \sum_{l \in L_i} \exp\left(-\frac{\ln 2}{t_{1/2}} \cdot \text{age}(l)\right)$$

where $t_{1/2}$ = 1.4 years (the informational half-life of a lab result).

The composite DQS is:

$$\text{DQS}_i = \alpha C_i + \beta K_i + \gamma R_i$$

### 2.2 The Plausible-But-Wrong Detector

The PBW detector operates on the joint distribution of model confidence and data quality. It is triggered when:

$$\text{PBW}_i = \left(\max(p_i, 1 - p_i) > \theta_c\right) \wedge \left(\text{DQS}_i < \theta_d\right)$$

where $\theta_c$ = 0.80 (confidence threshold) and $\theta_d$ = 0.60 (DQS threshold).

**Information-theoretic justification.** By the data processing inequality, no deterministic function of the input can contain more information than the input itself. A model that outputs a probability of 0.95 encodes approximately $-\log_2(0.05) \approx 4.3$ bits of information about the outcome. If the input data contains substantially fewer bits (due to missing features, stale labs, or inconsistent coding), the confidence must come from the model's learned prior — the training distribution's marginal — rather than from the patient's data.

In a heterogeneous population, the prior is wrong for a non-trivial fraction of patients. These are the plausible-but-wrong cases: the model produces a confident answer that looks right (it matches the majority pattern) but is wrong for the specific patient whose missing data hides an atypical profile.

### 2.3 Supporting Signals

Two additional signals complement the PBW detector:

**Calibration-Confidence Mismatch (CCM).** The absolute difference between the model's raw predicted probability and its Platt-calibrated probability:

$$\text{CCM}_i = |P_{\text{raw}}(y=1|x_i) - P_{\text{cal}}(y=1|x_i)|$$

CCM > 0.20 indicates that the model's internal confidence diverges from its calibrated estimate, suggesting the prediction lies in a region of feature space where the model is unreliable.

**Epistemic Prediction Uncertainty (EPU).** The disagreement across the model ensemble (XGBoost, Cox PH, CTMC) when each model's output is mapped to a common risk decile scale:

$$\text{EPU}_i = \max_m(\text{decile}_{m,i}) - \min_m(\text{decile}_{m,i})$$

EPU > 3 deciles indicates that the models disagree substantially about the patient's risk, suggesting the case is in an ambiguous region.

## 3. Decision Logic

| Flags triggered | Recommendation | Interpretation |
|----------------|---------------|----------------|
| None | Accept | Prediction is supported by data quality and model agreement |
| CCM or EPU only | Review | Prediction may be valid but warrants human inspection |
| PBW (with or without others) | Reject prediction | Model cannot have sufficient information; escalate to human |

## 4. Validation Approach

### 4.1 Synthetic Data Experiments

The validation uses a controlled experimental design enabled by the two-stage synthetic data generator:

1. **Ground truth generation**: Disease trajectories are simulated via CTMC, producing "true" patient states.
2. **Observation degradation**: Market-specific missingness and noise models transform ground truth into observed records.

This separation allows us to measure model accuracy against ground truth while varying data quality in a controlled manner.

### 4.2 Controlled Degradation Experiment

Starting from the DE cohort (high DQS), we progressively delete features to simulate degrading data quality:

- At each degradation level (10%, 20%, ..., 70% of features removed), we measure:
  - Model confidence (mean effective confidence)
  - Model accuracy (fraction of correct classifications against ground truth)
  - DQS (which tracks the degradation by construction)

The expected finding: model confidence remains approximately stable while accuracy degrades. The DQS correctly tracks the information loss. The PBW flag fires when the gap between confidence and data quality exceeds the threshold.

### 4.3 Cross-Market Analysis

The four-market design (DE, ES, FR, INT) provides a natural gradient of data quality:

- DE (DQS ≈ 0.85): high completeness, high consistency, recent labs
- FR (DQS ≈ 0.80): good data, but diagnosis lag
- ES (DQS ≈ 0.70): moderate completeness
- INT (DQS ≈ 0.45): low completeness, sparse labs, high noise

The PBW flag should fire preferentially on INT patients where the model is confident, and rarely on DE patients.

## 5. Limitations

This analysis is conducted on fully synthetic data. The following limitations apply:

1. **Prevalence distributions** are based on published epidemiological estimates but may not match any specific insurer's portfolio.
2. **Co-occurrence patterns** are modelled using simplified conditional probabilities, not learned from real claims data.
3. **DQS thresholds** (0.60, 0.80) are set heuristically. Optimal thresholds require calibration against real underwriting outcomes (false positive/negative costs).
4. **The information-theoretic argument** is directional, not exact. The data processing inequality provides an upper bound on extractable information, but the practical relationship between DQS and model reliability is empirical and domain-specific.
5. **Consistency rules** are a curated subset. A production system would require a comprehensive clinical rule engine, ideally validated by medical advisors.

## 6. Translation to Production

For deployment in a real underwriting workflow, the following extensions are required:

- **Threshold calibration**: Use historical underwriting decisions and claims outcomes to set DQS and confidence thresholds that optimise the business-relevant loss function (cost of missed claims vs. cost of unnecessary manual review).
- **Dynamic rule engine**: Replace static consistency rules with a configurable rule set maintained by medical underwriting experts.
- **Audit trail**: Log all validation results alongside model predictions for regulatory compliance (EU AI Act, Art. 14 human oversight requirements).
- **Feedback loop**: Track whether PBW-flagged cases that were subsequently reviewed by humans were indeed misclassified, and use this signal to refine thresholds.

## References

- Quan, H. et al. (2005). Coding algorithms for defining comorbidities in ICD-9-CM and ICD-10 administrative data. *Medical Care*, 43(11), 1130-1139.
- Reska, T. et al. (2024). [Plausible-but-wrong failure modes in AI-generated scientific pipelines]. *ISME Communications*.
- European Parliament (2024). Regulation (EU) 2024/1689 (AI Act), Art. 14: Human oversight.
