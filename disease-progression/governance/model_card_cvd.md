# Model Card: CVD Multistate Progression Model

## Model Details

| Field | Value |
|---|---|
| Model name | CVD Multistate Progression Model |
| Model type | Multistate survival analysis (Cox PH, Fine-Gray, DeepSurv, SurvTRACE) |
| Version | 0.1.0 (development) |
| Framework | lifelines, PyTorch, scikit-survival, SurvTRACE |
| License | Internal research use only |
| Contact | Disease Progression Modelling Team |

### Architecture

The model implements a multistate framework with the following states:

```
Risk Factors --> Stable CHD --> MI/Stroke --> Post-event --> HF (NYHA) --> Death
```

Death acts as an absorbing state reachable from any transient state (competing risk). Transition-specific hazards are estimated using:

1. **Cox PH**: Semiparametric proportional hazards (baseline model).
2. **Fine-Gray**: Sub-distribution hazards for competing risks between CVD death and non-CVD death.
3. **DeepSurv**: Neural network with 3 hidden layers (64-32-16), ReLU activation, batch normalisation, and dropout (0.3). Optimises the negative log partial likelihood.
4. **SurvTRACE**: Transformer encoder with 4 attention heads, 2 layers, hidden size 64. Predicts discrete-time survival probabilities.

## Intended Use

- **Primary use**: Research prototype exploring disease progression modelling for DACH insurance underwriting.
- **Users**: Data scientists and actuaries evaluating feasibility of survival-based risk stratification.
- **Out of scope**: Clinical decision-making, automated underwriting decisions, patient-facing applications.

## Training Data

| Property | Value |
|---|---|
| Source | Synthea (synthetic patient generator) |
| Population | US-based synthetic population with CVD-related conditions |
| Cohort size | Variable (depends on Synthea generation parameters) |
| Time span | ~1950-2024 (synthetic birth-to-death records) |
| Features | Age, sex, SBP, DBP, LDL, HDL, total cholesterol, triglycerides, BMI, HbA1c, eGFR |
| Target | Time to death (all-cause), with CVD state as multistate label |

### Data Limitations

- Synthetic data does not capture real-world correlations between comorbidities.
- US-centric disease patterns and treatment protocols.
- No social determinants of health, lifestyle factors, or genetic data.
- Synthea generates data according to predefined care pathways, which may introduce artificial patterns.

## Evaluation Metrics

### Overall Performance

| Model | C-index | AUC@1y | AUC@3y | AUC@5y |
|---|---|---|---|---|
| Cox PH | TBD | TBD | TBD | TBD |
| Fine-Gray | TBD | TBD | TBD | TBD |
| DeepSurv | TBD | TBD | TBD | TBD |
| SurvTRACE | TBD | TBD | TBD | TBD |

### Calibration

Calibration assessed via:
- Kaplan-Meier curves stratified by predicted risk quartile.
- Hosmer-Lemeshow goodness-of-fit at 1, 3, and 5-year horizons.
- Calibration slope and intercept (Cox recalibration).

### Subgroup Performance

| Subgroup | N | Events | Cox C-index | DeepSurv C-index |
|---|---|---|---|---|
| Male | TBD | TBD | TBD | TBD |
| Female | TBD | TBD | TBD | TBD |
| Age <50 | TBD | TBD | TBD | TBD |
| Age 50-64 | TBD | TBD | TBD | TBD |
| Age 65-79 | TBD | TBD | TBD | TBD |
| Age 80+ | TBD | TBD | TBD | TBD |

## Ethical Considerations

### Fairness

- The model must not systematically disadvantage any demographic group in risk prediction accuracy.
- Subgroup C-index differences exceeding 0.05 should trigger review.
- Age-based risk differentiation is actuarially justified but must comply with anti-discrimination law (AGG in Germany, GlBG in Austria).

### Privacy

- Model trained on synthetic data; no real patient data involved in development.
- Deployment on real data requires GDPR Art. 9 legal basis (health data is special category).
- Re-identification risk assessment required before any deployment.

### Potential Harms

- Miscalibrated predictions could lead to unfair premium loading or coverage denial.
- Over-reliance on model outputs without clinical context may produce inappropriate underwriting decisions.
- Historical care inequalities embedded in training data may perpetuate bias.

## Caveats and Recommendations

1. **Do not deploy without validation on real DACH population data.** Synthea-trained models are proof-of-concept only.
2. **Recalibrate before use.** Base hazard rates will differ between US synthetic and DACH real populations.
3. **Monitor for drift.** Coding practices (ICD-10-GM vs ICD-10-CM), treatment guidelines, and population demographics change over time.
4. **Ensemble with actuarial judgement.** Model outputs should inform, not replace, underwriter decisions.
5. **Document all overrides.** When underwriters deviate from model recommendations, log the reason for audit trails.
