# What We Built -- MedRisk-ADH Technical Summary

## Project
MedRisk-ADH v2.0 -- AI-driven medical underwriting with confidence-calibrated failure mode detection.

## v2 Architecture
```
Patient Record -> Data Profile -> DQS v2 -> Model Router -> Reliability Head -> Decision + Audit
```

## Source Modules (v2 additions)
- `validation/range_checks.py` -- physiological range validation
- `features/data_profile.py` -- FULL/NO_LABS/NO_MEDS/MINIMAL classification
- `models/model_router.py` -- one XGBoost per profile, no imputation
- `validation/reliability_head.py` -- learned P(wrong), cost-optimal decisions
- `evaluation/subgroup_eval.py` + `plots.py` -- calibration slope, DCA, subgroups
- `governance/audit_log.py` + `human_override.py` -- JSON Lines audit trail
- `validation/shift_detection.py` -- PSI/JS divergence
- `pipeline.py` -- end-to-end orchestrator
- `models/disease_configs.py` -- disease config registry (cardiovascular + Alzheimer)

## Alzheimer's Disease Extension
- 7-state CTMC: NC -> SCD -> MCI -> Mild AD -> Moderate AD -> Severe AD -> Death
- Transition rates calibrated to published literature (Petersen et al., Brookmeyer et al.)
- 8 ICD-10 codes: G30.0/G30.1/G30.8/G30.9, F00.0/F00.1/F00.2/F00.9
- Biomarkers: MMSE (72106-8), MoCA (72172-0), CSF Abeta42 (33203-1), CSF p-tau181 (72260-3)
- Medications: Donepezil, Rivastigmine, Galantamine, Memantine
- ApoE4 graduated risk modifier, AD-specific synthetic cohort generator
- All clinical numbers fact-checked against published literature

## Testing
231 tests, all passing. Lint clean.

## Demo Apps
- Streamlit: `make app` -> localhost:8501 (4 pages)
- Page 1: Patient Assessment | Page 2: PBW Comparison | Page 3: Portfolio Dashboard | Page 4: Alzheimer Progression
- HTML technical: `app/static/index.html`
- HTML executive: `app/static/executive.html` (plain English)
- Design: Doctolib Oxygen (light, #107ACA blue)

## Metrics (synthetic)
AUC 0.71 | Brier 0.010 | C-index 0.72 | 4,000 patients, 4 markets, 2 disease models
