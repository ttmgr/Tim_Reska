# Risk Register: Disease Progression Modelling Project

## Overview

This risk register identifies and tracks risks associated with the development and potential deployment of multistate disease progression models for insurance underwriting in the DACH region. Each risk is assessed on likelihood (L) and impact (I) on a 1-5 scale, yielding a risk score (L x I).

---

## 1. Bias Risks

### 1.1 Historical Care Inequalities

| Field | Value |
|---|---|
| Risk ID | BIAS-001 |
| Description | Training data may encode historical disparities in healthcare access and treatment quality across demographic groups. Patients from underserved populations may have later diagnoses, fewer lab measurements, and worse outcomes independent of their underlying disease biology. |
| Likelihood | 4 |
| Impact | 5 |
| Risk Score | 20 (Critical) |
| Affected Groups | Lower socioeconomic status, ethnic minorities, rural populations, women (historically underrepresented in CVD trials) |

**Mitigation Strategies:**
- Conduct subgroup performance analysis across all available demographic dimensions.
- Flag C-index differences exceeding 0.05 between subgroups for mandatory review.
- Consider fairness-aware training objectives (e.g., equalised odds constraints).
- Document known limitations in model cards.

### 1.2 Demographic Imbalances in Training Data

| Field | Value |
|---|---|
| Risk ID | BIAS-002 |
| Description | Synthea generates US-based synthetic populations that do not reflect DACH demographics. Age distributions, sex ratios, ethnic composition, and comorbidity patterns differ substantially. |
| Likelihood | 5 |
| Impact | 4 |
| Risk Score | 20 (Critical) |

**Mitigation Strategies:**
- Validate and recalibrate models on DACH-representative data before any deployment.
- Use importance weighting to adjust for demographic shifts between training and target populations.
- Explicitly document the US-to-DACH transfer gap in all model documentation.

### 1.3 Label Bias from Disease State Assignment

| Field | Value |
|---|---|
| Risk ID | BIAS-003 |
| Description | Multistate labels are assigned based on diagnosis codes, which depend on coding completeness. Patients with more healthcare encounters are more likely to have advanced states documented, creating informative observation bias. |
| Likelihood | 3 |
| Impact | 3 |
| Risk Score | 9 (Moderate) |

**Mitigation Strategies:**
- Use time-to-first-code rather than presence/absence for state assignment.
- Sensitivity analysis: vary code lists and assess impact on model performance.
- Consider interval censoring models that account for unknown state entry times.

---

## 2. Data Drift Risks

### 2.1 Coding Practice Changes

| Field | Value |
|---|---|
| Risk ID | DRIFT-001 |
| Description | Diagnosis coding practices evolve over time. ICD-10-GM revisions occur annually in Germany. New codes are introduced, existing codes are split or merged, and coding guidelines change. This can cause apparent changes in disease prevalence and progression patterns. |
| Likelihood | 4 |
| Impact | 4 |
| Risk Score | 16 (High) |

**Mitigation Strategies:**
- Maintain versioned code lists with effective date ranges.
- Monitor code frequency distributions over time (code drift analysis in notebook 00).
- Implement automated alerts when code distributions shift beyond predefined thresholds.
- Map all codes to stable clinical concepts (e.g., SNOMED CT) as an abstraction layer.

### 2.2 ICD Revision Transitions

| Field | Value |
|---|---|
| Risk ID | DRIFT-002 |
| Description | Transition from ICD-10 to ICD-11 is planned in several countries. Germany uses ICD-10-GM with annual updates. Any major revision will break code-based feature extraction and label assignment. |
| Likelihood | 3 |
| Impact | 5 |
| Risk Score | 15 (High) |

**Mitigation Strategies:**
- Build code lists using SNOMED CT as the primary terminology, with ICD mappings as secondary.
- Prepare ICD-10 to ICD-11 crosswalk tables in advance.
- Design the data pipeline to be terminology-agnostic where possible.

### 2.3 Treatment Guideline Changes

| Field | Value |
|---|---|
| Risk ID | DRIFT-003 |
| Description | Medical treatment guidelines evolve. For example, the introduction of SGLT2 inhibitors and GLP-1 RAs has significantly changed T2D progression. New ESC guidelines for heart failure may alter treatment pathways. Models trained on historical data may not reflect current standard of care. |
| Likelihood | 4 |
| Impact | 3 |
| Risk Score | 12 (High) |

**Mitigation Strategies:**
- Include treatment/medication features in models to capture guideline effects.
- Retrain models at least annually to incorporate recent data.
- Monitor model calibration over time; degradation may signal guideline-driven concept drift.

---

## 3. Privacy Risks

### 3.1 Re-identification Risk

| Field | Value |
|---|---|
| Risk ID | PRIV-001 |
| Description | Longitudinal health records with detailed diagnosis sequences, lab trajectories, and demographic information may allow re-identification even after pseudonymisation. Rare disease combinations or unusual lab value sequences can act as quasi-identifiers. |
| Likelihood | 3 |
| Impact | 5 |
| Risk Score | 15 (High) |

**Mitigation Strategies:**
- Current development uses synthetic data only (no re-identification risk).
- For real data: conduct formal k-anonymity and l-diversity assessments.
- Apply differential privacy mechanisms to model training if deploying on real data.
- Limit feature granularity (e.g., age bands instead of exact age, lab value ranges instead of exact values).

### 3.2 GDPR Article 9 Compliance

| Field | Value |
|---|---|
| Risk ID | PRIV-002 |
| Description | Health data is classified as special category data under GDPR Art. 9. Processing requires explicit consent or a specific legal basis (e.g., Art. 9(2)(g) substantial public interest, Art. 9(2)(j) scientific research). Insurance underwriting with health data must comply with member state derogations. |
| Likelihood | 4 |
| Impact | 5 |
| Risk Score | 20 (Critical) |

**Mitigation Strategies:**
- Obtain legal review of the applicable legal basis in each DACH jurisdiction before processing real data.
- In Germany: consider VVG (Insurance Contract Act) provisions for health data in underwriting.
- In Switzerland: align with revDSG (revised Data Protection Act, effective September 2023).
- In Austria: consult DSG and sector-specific insurance regulations.
- Implement data protection impact assessment (DPIA) as required by GDPR Art. 35.

### 3.3 Cross-Border Data Transfers

| Field | Value |
|---|---|
| Risk ID | PRIV-003 |
| Description | DACH operations may involve data transfers between Germany, Austria, and Switzerland. While DE-AT transfers are intra-EU (GDPR), Switzerland has an adequacy decision but operates under its own DSG. Cloud processing may involve non-EU data centres. |
| Likelihood | 3 |
| Impact | 4 |
| Risk Score | 12 (High) |

**Mitigation Strategies:**
- Use EU-based cloud infrastructure for all data processing.
- Implement standard contractual clauses (SCCs) for any non-EU transfers.
- Consider data localisation requirements for Swiss health data.
- Document all data flows in the DPIA.

---

## 4. Model Risks

### 4.1 Miscalibration

| Field | Value |
|---|---|
| Risk ID | MODEL-001 |
| Description | Model-predicted probabilities may not align with observed event rates, especially when transferring from synthetic to real data or from US to DACH populations. Miscalibrated models lead to systematically biased risk assessments. |
| Likelihood | 4 |
| Impact | 5 |
| Risk Score | 20 (Critical) |

**Mitigation Strategies:**
- Assess calibration at multiple time horizons (1, 3, 5 years) using calibration plots and Hosmer-Lemeshow tests.
- Apply Platt scaling or isotonic regression for post-hoc recalibration.
- Validate on held-out DACH data with known outcomes before deployment.
- Establish calibration thresholds: reject models with calibration slope outside [0.8, 1.2].

### 4.2 Concept Drift

| Field | Value |
|---|---|
| Risk ID | MODEL-002 |
| Description | The relationship between features and outcomes may change over time due to new treatments, population changes, or environmental factors. A model trained on historical data may degrade in performance on future patients. |
| Likelihood | 4 |
| Impact | 4 |
| Risk Score | 16 (High) |

**Mitigation Strategies:**
- Implement continuous model monitoring: track C-index, calibration, and feature distributions monthly.
- Set performance degradation thresholds (e.g., C-index drop > 0.03 triggers retraining).
- Maintain a retraining pipeline that can be executed on updated data within 2 weeks.
- Use time-aware validation (temporal cross-validation, not random splits).

### 4.3 Overfitting of Deep Learning Models

| Field | Value |
|---|---|
| Risk ID | MODEL-003 |
| Description | DeepSurv and Dynamic-DeepHit have many parameters relative to the number of events in typical insurance datasets. Overfitting may produce optimistic in-sample metrics that do not generalise. |
| Likelihood | 3 |
| Impact | 3 |
| Risk Score | 9 (Moderate) |

**Mitigation Strategies:**
- Use regularisation (dropout, weight decay, early stopping).
- Compare deep learning models against Cox PH baseline; reject if no meaningful improvement.
- Use nested cross-validation for hyperparameter tuning.
- Report both in-sample and out-of-sample metrics.

### 4.4 Missing Data and Informative Censoring

| Field | Value |
|---|---|
| Risk ID | MODEL-004 |
| Description | Survival models assume non-informative censoring (censoring is independent of the event process). In insurance data, lapse (policy termination) may be informative: sicker patients may be less likely to lapse. Similarly, missing lab values may correlate with disease severity. |
| Likelihood | 4 |
| Impact | 3 |
| Risk Score | 12 (High) |

**Mitigation Strategies:**
- Test the non-informative censoring assumption using inverse probability of censoring weighting (IPCW).
- Model lapse as a competing risk rather than treating it as non-informative censoring.
- Use multiple imputation (MICE) rather than single imputation for missing features.
- Conduct sensitivity analyses under different censoring assumptions.

---

## Risk Summary Matrix

| Risk Score | Count | Risk IDs |
|---|---|---|
| 20 (Critical) | 3 | BIAS-001, PRIV-002, MODEL-001 |
| 16 (High) | 2 | DRIFT-001, MODEL-002 |
| 15 (High) | 2 | DRIFT-002, PRIV-001 |
| 12 (High) | 3 | DRIFT-003, PRIV-003, MODEL-004 |
| 9 (Moderate) | 2 | BIAS-003, MODEL-003 |

## Review Schedule

- This risk register should be reviewed quarterly.
- Critical risks (score >= 20) require active mitigation plans with named owners.
- New risks should be added as they are identified during development.
- Risk scores should be updated as mitigations are implemented and validated.
