# Data Sheet: Synthea Synthetic Patient Dataset

## Motivation

### Purpose
This dataset was generated to support the development and validation of multistate disease progression models for cardiovascular disease (CVD) and type 2 diabetes (T2D). The models are intended as research prototypes for DACH insurance underwriting applications.

### Creator
The dataset was generated using Synthea, an open-source synthetic patient generator developed by the MITRE Corporation. The generation configuration and cohort selection were performed by the Disease Progression Modelling Team.

### Funding
Internal research project; no external funding.

## Composition

### Structure
The dataset consists of synthetic electronic health records in CSV format, following the Synthea output schema:

| File | Description | Key Fields |
|---|---|---|
| patients.csv | Patient demographics | Id, BIRTHDATE, DEATHDATE, GENDER, RACE, ETHNICITY |
| conditions.csv | Diagnoses (SNOMED CT) | PATIENT, CODE, DESCRIPTION, START, STOP |
| observations.csv | Lab results and vitals | PATIENT, DATE, CODE, DESCRIPTION, VALUE, UNITS |
| medications.csv | Prescriptions (RxNorm) | PATIENT, CODE, DESCRIPTION, START, STOP, TOTALCOST |
| encounters.csv | Clinical encounters | PATIENT, ENCOUNTERCLASS, START, STOP, TOTAL_CLAIM_COST |
| procedures.csv | Procedures (SNOMED CT) | PATIENT, CODE, DESCRIPTION, DATE |

### Instances
The number of patients depends on Synthea generation parameters. Typical configurations produce 10,000-100,000 synthetic patients with full longitudinal records spanning birth to present (or death).

### Coding Systems
- Diagnoses: SNOMED CT (mapped to ICD-10-CM where available)
- Labs: LOINC
- Medications: RxNorm (mapped to ATC for DACH compatibility)
- Procedures: SNOMED CT

### Sensitive Data
No real patient data is included. All records are algorithmically generated. However, the synthetic data mimics real health record patterns and should be handled with appropriate care.

### Representativeness
Synthea generates data based on US population demographics and healthcare utilisation patterns. The synthetic population does not represent DACH populations in terms of:
- Disease prevalence and incidence rates
- Treatment protocols and prescribing patterns
- Healthcare system structure (e.g., German DMP, Swiss mandatory insurance)
- Coding practices (SNOMED CT vs ICD-10-GM)

## Collection Process

### Generation Method
1. Synthea was configured with default US population parameters.
2. Patient records were generated using Synthea's disease modules (cardiovascular, diabetes, metabolic syndrome, etc.).
3. Records were exported in CSV format.
4. No manual curation or annotation was performed on the raw output.

### Time Coverage
Synthetic records span from approximately 1920 to 2024, covering full patient lifetimes. Calendar time effects (e.g., introduction of new treatments) are modelled by Synthea's care pathway modules.

### Validation
- Record counts and distributions were compared against expected US prevalence figures.
- Code validity was checked against SNOMED CT and LOINC reference tables.
- Temporal consistency was verified (no events after death, no negative durations).

## Preprocessing

### Steps Applied
1. **Cohort selection**: Patients filtered to those with at least one CVD- or diabetes-related condition code.
2. **Feature engineering**: Last-observed lab values extracted per patient. Age computed from birth date.
3. **Missing data**: Median imputation applied to missing lab values after cohort construction.
4. **Scaling**: StandardScaler applied to all continuous features before model training.
5. **Label construction**: Multistate labels assigned based on the most advanced disease state observed per patient.

### Exclusions
- Patients with no condition records were excluded.
- Observations with non-numeric values for lab results were coerced to NaN and imputed.

## Uses

### Intended Uses
- Training and evaluating multistate survival models.
- Developing and testing data pipelines for disease progression analysis.
- Prototyping underwriting risk stratification approaches.

### Not Suitable For
- Clinical decision support (synthetic data does not reflect real patient outcomes).
- Actuarial pricing (prevalence and cost figures are US-based and synthetic).
- Epidemiological studies (disease patterns are algorithmically generated, not observed).

## Distribution

### Access
The raw Synthea data is generated locally and not distributed externally. Synthea itself is freely available at https://github.com/synthetichealth/synthea under the Apache 2.0 licence.

### Licence
Synthea output is available under the Apache 2.0 licence. Derived datasets and models are subject to internal research use restrictions.

## Maintenance

### Updates
- Synthea version should be documented with each data generation run.
- Regeneration may be needed when Synthea updates its disease modules or demographic models.
- SNOMED CT and LOINC mappings should be reviewed annually for changes.

### Known Issues
- Synthea's cardiovascular module may over-represent certain care pathways.
- Cost data is based on US healthcare pricing and is not directly applicable to DACH markets.
- Some rare conditions may have insufficient representation for meaningful statistical analysis.
- The diabetes module does not distinguish T1D from LADA or monogenic forms.

### Point of Contact
Disease Progression Modelling Team - internal repository issue tracker.
