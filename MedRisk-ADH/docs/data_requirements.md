# Data Requirements -- Phase 2 Validation

## Minimum
- 50,000+ patients, 5+ years follow-up, linked outcomes
- At least 2 markets/sites with different data quality

## Required Fields

### Demographics
Patient ID (pseudonymised), age, sex, BMI, smoking status

### Diagnoses
ICD-10-GM coded, date_recorded, primary/secondary flag

### Lab Results (critical for full DQS validation)
HbA1c, creatinine, eGFR, cholesterol (total/HDL/LDL), triglycerides, BP, NT-proBNP
Each with: value, unit, date_collected, reference range
NOTE: German GKV claims do NOT have lab values. Only CPRD (UK) and PKV data do.

### Medications
ATC-coded prescriptions, date, active status

### Outcomes
Event type (death/MI/stroke/HF/CKD), time to event, censoring indicator

## Recommended Sources
1. **CPRD (UK)** -- only source with labs. 60M patients. 2-4 months. GBP 25-80K.
2. **InGef (DE)** -- 8.8M GKV. German ICD-10-GM. No labs. 3-6 months. EUR 30-80K.
3. **CMBD (Spain)** -- hospital only. Free. 2-4 months.
4. **Allianz Internal** -- target. Requires partnership + DPO clearance.

## Legal Basis
- Germany: SGB X Section 75 + DSGVO Art. 89
- UK: UK GDPR + NHS Act 2006 Section 251
- Allianz: DSGVO Art. 6(1)(f) + Art. 35 DPIA

## Format
CSV/Parquet, one row per patient. See `src/medrisk/data/schemas.py` for field definitions.
