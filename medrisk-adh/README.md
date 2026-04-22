# MedRisk-ADH

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](../LICENSE)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)

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

**Risk models** (`src/medrisk/models/`):
- **XGBoost** binary risk classifier with Platt calibration
- **Cox PH** survival model (lifelines) for time-to-event analysis
- **CTMC** multistate Markov chain for disease progression trajectories
- **Actuarial rating engine** with debits/credits and Standard / Substandard / Decline profiles
- **Krankentagegeld (KTG)** — German sickness-absence premium calculator
- **Sickness-absence prediction** — supervised model for absence duration
- **Model router** — selects the appropriate model per case profile

**Validation layer** (`src/medrisk/validation/`):
- **DQS** (Data Quality Score): completeness + consistency + recency → [0, 1]
- **CCM** (Calibration-Confidence Mismatch): raw vs calibrated probability gap
- **EPU** (Epistemic Prediction Uncertainty): model ensemble disagreement
- **PBW** (Plausible-But-Wrong): high confidence + low DQS → hard flag
- **Conformal prediction intervals** for distribution-free uncertainty bounds
- **Shift detection** for input-distribution drift between training and inference
- **Reliability head** for per-prediction reliability scoring
- **Range checks** for out-of-distribution feature values

**Underwriting layer** (`src/medrisk/underwriting/`):
- Clinical-rule checks (domain-specific validators)
- Decision engine (accept / review / reject routing)
- Risk profiles (Standard / Substandard / Decline)
- Temporal rules (age limits, waiting periods, recency windows)

**Governance layer** (`src/medrisk/governance/`):
- Append-only audit log of every decision
- Human-override workflow for cases routed to manual review

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
streamlit run app/app.py           # launch the 7-page Streamlit application
make test                          # 231 tests, ~10 seconds
make lint                          # ruff
make notebooks                     # execute all 5 notebooks
```

## Application Pages

The Streamlit application (`app/app.py`) ships with seven operational pages:

| # | Page | Purpose |
|---|------|---------|
| 1 | Patient Assessment | Per-patient risk scoring with DQS, model output, PBW flag, and SHAP explanation |
| 2 | PBW Comparison | Side-by-side comparison of confident-correct vs plausible-but-wrong cases |
| 3 | Portfolio Dashboard | Aggregate metrics across a portfolio (acceptance rate, flag rate, calibration) |
| 4 | Alzheimer Progression | Disease-specific trajectory module for neurodegenerative cases |
| 5 | KTG Kalkulation | German Krankentagegeld (sickness-absence) premium calculator |
| 6 | Underwriting Simulator | Scenario builder — toggle data quality, comorbidities, and policy parameters |
| 7 | KTG Flashcards | Interactive training module on German sickness-absence underwriting |

## Real-World Data Adapters

`src/medrisk/fetch/` includes eight adapters for ingesting public clinical and population datasets, with caching, schema validation, and authentication helpers:

NHANES · UK Biobank · BioLinCC · Zenodo · CDC PLACES · data.gov · Glucose-ML (T1DM CGM) · Granada T1D cohort

These let the platform be evaluated against real-world data for validation studies, while the synthetic cohort remains the default for failure-mode experiments.

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
medrisk-adh/
├── app/                    # 7-page Streamlit application + UI components
│   ├── app.py
│   ├── pages/              # 1_Patient_Assessment ... 7_KTG_Flashcards
│   ├── components/         # DQS gauge, metrics cards, SHAP chart, progression chart
│   └── data_cache.py
├── src/medrisk/            # Python ML library
│   ├── data/               # Schemas, ICD-10, Charlson, synthetic generator
│   ├── features/           # Encoding, engineering, data profiling
│   ├── models/             # XGBoost, Cox PH, multistate, actuarial, KTG, model router
│   ├── fetch/              # 8 adapters: NHANES, UK Biobank, BioLinCC, CDC PLACES, …
│   ├── validation/         # DQS, conformal, shift detection, reliability head, PBW
│   ├── underwriting/       # Clinical checks, decision engine, profiles, temporal rules
│   ├── governance/         # Audit log, human override
│   ├── explain/            # SHAP explainability layer
│   ├── evaluation/         # Discrimination, calibration, fairness, treatment effects
│   ├── reporting/          # PDF report generation
│   └── pipeline.py         # End-to-end ML pipeline
├── docs/                   # failure_modes, ktg_underwriting_manual, study_guide (DE/EN)
├── notebooks/              # 5 self-contained notebooks
├── scripts/                # PPTX deck generation (clinical, KTG, ML methodology)
├── tests/                  # 231 tests across 37 files
└── ROADMAP.md
```

## Documentation

- [`docs/failure_modes.md`](docs/failure_modes.md) — Methods-section treatment of the PBW failure taxonomy with worked case studies
- [`docs/guide_medrisk_adh.md`](docs/guide_medrisk_adh.md) — End-to-end user guide
- [`docs/ktg_underwriting_manual.md`](docs/ktg_underwriting_manual.md) — German Krankentagegeld underwriting reference
- [`docs/study_guide.md`](docs/study_guide.md) / [`docs/study_guide_de.md`](docs/study_guide_de.md) — Long-form study guides (English / German) covering epidemiology, actuarial foundations, and ML
- [`docs/data_requirements.md`](docs/data_requirements.md) — Input data schemas
- [`docs/sources.md`](docs/sources.md) — Data source documentation (NHANES, UK Biobank, CDC PLACES, …)
- [`docs/what_we_built.md`](docs/what_we_built.md) — Architecture summary
- [`ROADMAP.md`](ROADMAP.md) — Phase 1 (complete), Phase 2 (validation), Phase 3 (production), with DSGVO / EU AI Act compliance milestones

## Limitations

All results are on synthetic data. DQS thresholds are heuristic. This is a mechanism demonstration, not a production system — see [ROADMAP.md](ROADMAP.md) for the path to validation and deployment.

## Author

Built by [Tim Reska](https://linkedin.com/in/tim-r-ai) — PhD candidate, Genomics & Bioinformatics, Helmholtz Munich & TUM (expected Jun 2026).
