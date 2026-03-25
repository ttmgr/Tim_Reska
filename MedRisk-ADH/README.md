# MedRisk-ADH

AI-driven medical underwriting with confidence-calibrated failure mode detection.

## The Problem

Automated underwriting AI fails most dangerously not when it is obviously wrong — but when it is **confidently wrong on low-quality data**. Most systems have no mechanism to detect this. A model that classifies a patient as low-risk with 95% confidence on 40% missing data is running on priors, not evidence.

## The Solution

MedRisk-ADH proposes a validation layer that sits between the risk models and the underwriting decision. It computes a **Data Quality Score** (DQS) for each patient before inference, then flags cases where model confidence exceeds what the input data can support — the **plausible-but-wrong** (PBW) detection.

This does not improve model accuracy. It identifies when the model's predictions should not be trusted. The distinction matters: it enables automation for the 80% of cases where data quality supports the decision, and escalates only the cases that need a human.

## Architecture

```
Patient Record → [DQS Assessment] → [Risk Models] → [Validation Layer] → Decision
                       ↓                   ↓                ↓
                  Completeness        XGBoost           CCM check
                  Consistency         Cox PH            EPU check
                  Recency             CTMC              PBW flag
                                                           ↓
                                              accept | review | reject
```

**Three models:**
- **XGBoost** binary risk classifier with Platt calibration
- **Cox PH** survival model (lifelines) for time-to-event analysis
- **CTMC** multistate Markov chain for disease progression trajectories

**Validation layer:**
- **DQS** (Data Quality Score): completeness + consistency + recency → [0, 1]
- **CCM** (Calibration-Confidence Mismatch): raw vs calibrated probability gap
- **EPU** (Epistemic Prediction Uncertainty): model ensemble disagreement
- **PBW** (Plausible-But-Wrong): high confidence + low DQS → hard flag

## Synthetic Data

GDPR-safe multi-market cohort generator with four market profiles:

| Market | Coding completeness | Lab completeness | Role |
|--------|-------------------|-----------------|------|
| DE | 95% | 92% | Clean reference |
| FR | 90% | 88% | Good data, diagnosis lag |
| ES | 80% | 75% | Mid-range quality |
| INT | 60% | 50% | The hard case |

The generator first simulates ground truth disease trajectories via CTMC, then degrades them with market-specific missingness and noise. This separation enables controlled failure mode experiments.

## Installation

```bash
pip install -e ".[dev]"
```

Requires Python 3.11+.

## Usage

```bash
make test        # 119 tests, ~4 seconds
make lint        # ruff
make notebooks   # execute all 5 notebooks
```

## Notebooks

| # | Title | Story |
|---|-------|-------|
| 01 | Synthetic Cohort | Data generation, quality variance across markets |
| 02 | Risk Classification | XGBoost training, SHAP explainability |
| 03 | Disease Progression | Cox PH survival curves, CTMC state transitions |
| 04 | Failure Modes | PBW demonstration — the core argument |
| 05 | Underwriting Report | PDF report generation for clean and flagged cases |

## Project Structure

```
src/medrisk/
├── data/           # Schemas, ICD-10, Charlson, synthetic generator
├── features/       # ICD-10 encoding, feature matrix construction
├── models/         # XGBoost, Cox PH, multistate Markov
├── explain/        # SHAP explainability layer
├── validation/     # DQS, confidence calibration, PBW detection
├── reporting/      # PDF report generation
└── evaluation/     # Discrimination and calibration metrics
```

## Limitations

All results are on synthetic data. DQS thresholds are heuristic. This is a mechanism demonstration, not a production system. See [ROADMAP.md](ROADMAP.md) for the path to validation and deployment, and [docs/failure_modes.md](docs/failure_modes.md) for the full methods-section treatment.

## Author

Tim Reska — PhD candidate, Genomics & Bioinformatics, Helmholtz Munich.
