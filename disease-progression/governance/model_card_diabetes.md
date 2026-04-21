# Model Card: Diabetes Multistate Progression Model

## Model Details

| Field | Value |
|---|---|
| Model name | Diabetes Multistate Progression Model |
| Model type | Multistate survival analysis (Cox PH, Dynamic-DeepHit) |
| Version | 0.1.0 (development) |
| Framework | lifelines, PyTorch |
| License | Internal research use only |
| Contact | Disease Progression Modelling Team |

### Architecture

The model implements a multistate framework for type 2 diabetes progression:

```
Prediabetes --> T2D --> Microvascular --> Macrovascular --> ESRD --> Death
```

Microvascular complications include retinopathy, neuropathy, and early nephropathy. Macrovascular complications include MI, stroke, and peripheral vascular disease. ESRD encompasses dialysis and renal transplant. Death is an absorbing state reachable from any transient state.

1. **Cox PH**: Semiparametric proportional hazards baseline using last-observed clinical values.
2. **Dynamic-DeepHit**: Neural network combining a GRU encoder for longitudinal HbA1c trajectories with a feedforward network for static features. Outputs a probability mass function over discretised time and competing risk types. Based on Lee et al. (IEEE TBME, 2020).

### Time-Varying Covariates

HbA1c is modelled as a time-varying covariate via the GRU encoder in Dynamic-DeepHit. Up to 20 longitudinal measurements are used per patient, with zero-padding for shorter sequences. This allows the model to capture HbA1c trajectory patterns (e.g., rising, controlled, erratic) rather than relying solely on the last observed value.

## Intended Use

- **Primary use**: Research prototype for diabetes progression modelling in DACH insurance contexts.
- **Users**: Data scientists and actuaries evaluating survival-based risk stratification for diabetes.
- **Out of scope**: Clinical decision-making, automated underwriting, patient-facing tools.

## Training Data

| Property | Value |
|---|---|
| Source | Synthea (synthetic patient generator) |
| Population | US-based synthetic population with diabetes-related conditions |
| Cohort size | Variable (depends on Synthea generation parameters) |
| Features | Age, sex, HbA1c, glucose, BMI, SBP, eGFR, creatinine, total cholesterol, LDL, triglycerides |
| Longitudinal | HbA1c measurements over time (up to 20 per patient) |
| Target | Time to death, with diabetes state as multistate label |

### Data Limitations

- Synthetic data with US-centric treatment protocols (e.g., SGLT2i adoption timing differs from DACH).
- Synthea diabetes module follows fixed care pathways that may not reflect real-world variability.
- No oral glucose tolerance test (OGTT) or C-peptide data for T1D/T2D differentiation.
- Missing lifestyle factors (diet, exercise, smoking, alcohol).

## Evaluation Metrics

### Overall Performance

| Model | C-index | AUC@1y | AUC@3y | AUC@5y |
|---|---|---|---|---|
| Cox PH | TBD | TBD | TBD | TBD |
| Dynamic-DeepHit | TBD | TBD | TBD | TBD |

### Calibration

- Kaplan-Meier curves by predicted risk quartile.
- Hosmer-Lemeshow at 1, 3, 5 years.
- CIF comparison: predicted vs observed cumulative incidence for each competing risk.

### Subgroup Performance

| Subgroup | N | Events | Cox C-index | DDH C-index |
|---|---|---|---|---|
| Male | TBD | TBD | TBD | TBD |
| Female | TBD | TBD | TBD | TBD |
| Age <50 | TBD | TBD | TBD | TBD |
| Age 50-64 | TBD | TBD | TBD | TBD |
| Age 65-79 | TBD | TBD | TBD | TBD |
| Age 80+ | TBD | TBD | TBD | TBD |
| HbA1c <7% | TBD | TBD | TBD | TBD |
| HbA1c 7-9% | TBD | TBD | TBD | TBD |
| HbA1c >9% | TBD | TBD | TBD | TBD |

## Ethical Considerations

### Fairness

- Diabetes prevalence and management differ by socioeconomic status; model must not encode these as risk factors.
- HbA1c measurement frequency may correlate with healthcare access, introducing informative censoring.
- Subgroup performance gaps exceeding 0.05 C-index should be investigated.

### Privacy

- Synthetic training data; no real patients involved.
- HbA1c trajectories are highly personal health data (GDPR Art. 9 special category).
- Longitudinal data increases re-identification risk compared to cross-sectional features.

### Potential Harms

- Inaccurate progression predictions could lead to inappropriate coverage decisions for diabetes patients.
- Model may underestimate risk for patients with poor HbA1c measurement adherence (missing data bias).
- DACH-specific treatment effects (e.g., structured disease management programmes in Germany) are not captured.

## Caveats and Recommendations

1. **Validate on real DACH data before any deployment.** Synthetic models are feasibility demonstrations only.
2. **Recalibrate HbA1c trajectory model.** Measurement frequency and baseline levels differ between US and DACH populations.
3. **Consider DMP participation.** German Disease Management Programmes (DMPs) for T2D significantly affect progression; include as a feature when real data is available.
4. **Account for treatment advances.** SGLT2 inhibitors and GLP-1 receptor agonists have changed T2D prognosis substantially since 2015.
5. **Separate T1D and T2D.** Current model does not distinguish between diabetes types; this is a significant limitation for underwriting.
