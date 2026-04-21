# Medical Underwriting Study Guide

## Using MedRisk-ADH as a Learning Laboratory

### About This Guide

This guide teaches what a medical underwriting expert does as a job — how risk decisions are made, where data comes from, how models work, and when to trust (or override) an automated decision. Every concept is grounded in the MedRisk-ADH codebase with concrete code references, real numbers, and hands-on exercises.

**Who it's for:** Someone with strong ML/data science skills who is new to insurance underwriting.

**Prerequisites:** Python, basic ML concepts, MedRisk-ADH installed (`make install`).

**Total estimated time:** ~120 minutes reading + exercises.

**Difficulty progression:**
- Chapters 1-3: Beginner (domain foundations)
- Chapters 4-7: Intermediate (models and quality)
- Chapters 8-12: Advanced (decisions, pricing, and validation)

---

## Chapter 1: What Is Medical Underwriting?

*~8 min | Beginner*

**Learning Objectives:**
- Define medical underwriting and its role in the insurance value chain
- Understand the daily workflow: application intake, risk assessment, pricing decision
- Distinguish underwriting from claims adjudication and actuarial science

### 1.1 The Underwriter's Job

A medical underwriter receives an insurance application and answers one question: **what is the expected cost of insuring this person?**

The workflow is:
1. **Receive application** — demographics, medical history, sometimes lab results
2. **Assess risk** — map diagnoses to severity, check comorbidities, evaluate data completeness
3. **Decide** — accept at standard terms, accept with a premium loading, defer for more information, or decline

In MedRisk-ADH, this maps directly to the three-outcome decision in `src/medrisk/validation/reliability_head.py`:
- **accept** — auto-process at standard or loaded premium
- **human_review** — escalate to a senior underwriter for manual assessment
- **reject** — decline coverage or request additional medical evidence

At scale, this matters enormously. A large insurer processes ~100,000 policies per year. If 2% of automated decisions are plausible-but-wrong (PBW), that's 2,000 mispriced policies annually — each potentially costing tens of thousands in unexpected claims.

### 1.2 Underwriting vs. Actuarial Science vs. Claims

These three roles are often confused:

| Role | Question | Timeframe | MedRisk-ADH Analog |
|------|----------|-----------|-------------------|
| **Underwriter** | Should we insure this person, and at what price? | Before policy issuance | `ReliabilityHead.predict()` |
| **Actuary** | What premium covers expected losses for this portfolio? | Portfolio-level pricing | KTG pricing in Page 5, actuarial reserving |
| **Claims adjuster** | Is this claim valid and how much should we pay? | After a claim is filed | Not modeled |

The underwriter operates at the **individual** level. The actuary operates at the **portfolio** level. MedRisk-ADH bridges both: individual risk scoring (XGBoost) feeds into portfolio-level KTG pricing (CTMC).

### 1.3 Types of Insurance Products

Medical underwriting applies to several product lines:

- **Life insurance (Lebensversicherung)** — pays on death. Key question: mortality risk.
- **Health insurance (Krankenversicherung)** — pays for treatment. Key question: morbidity burden.
- **Disability/sickness benefit (Krankentagegeld, KTG)** — pays a daily rate when unable to work. Key question: how likely is work incapacity (Arbeitsunfähigkeit, AU), how long will it last?

MedRisk-ADH demonstrates all three through its models:
- Cox PH survival model → mortality/event timing (`src/medrisk/models/cox_ph.py`)
- XGBoost classifier → binary morbidity risk (`src/medrisk/models/xgb_classifier.py`)
- CTMC multistate model → disease progression and KTG pricing (`src/medrisk/models/multistate.py`)
- Sickness absence models → AU frequency and duration (`src/medrisk/models/sickness_absence.py`)
- Underwriting decision engine → automated risk decisions (`src/medrisk/underwriting/decision_engine.py`)

### 1.4 The Regulatory Landscape

Medical underwriting in Europe operates under three overlapping frameworks:

**EU AI Act (2024, enforcement 2026)**
- Art. 6: AI systems in insurance underwriting are classified as **high-risk**
- Art. 12: Record-keeping — every decision must be logged → `src/medrisk/governance/audit_log.py`
- Art. 14: Human oversight — flagged cases must reach a human → `src/medrisk/governance/human_override.py`
- Art. 15: Accuracy — documented performance metrics and known limitations

**DSGVO/GDPR**
- Health data is special category (Art. 9) — requires explicit consent or legal basis
- Automated decision-making (Art. 22) — individuals have the right to human review
- Research exemption (Art. 89) — allows processing for scientific research with safeguards

**Solvency II**
- Capital adequacy requirements for insurers
- Actuarial function must validate underwriting assumptions annually
- Model risk management: documented model validation cycle

### 1.5 German Terms Glossary

| German | English | Context |
|--------|---------|---------|
| Krankentagegeld (KTG) | Daily sickness benefit | Insurance product |
| Arbeitsunfähigkeit (AU) | Work incapacity | The insured event |
| Risikoprüfung | Risk assessment | The underwriting process |
| Stadien | Stages | Disease severity levels |
| PKV | Private health insurance | Voluntary, premium-based |
| GKV | Statutory health insurance | Mandatory, income-based |
| DSGVO | GDPR (German implementation) | Data protection regulation |
| Versicherungsnehmer | Policyholder | The insured person |
| Leistungsfall | Benefit event/claim | When the insurer pays |

> **Try it yourself:** Open the Streamlit app (`make app`) and navigate to Page 5: KTG-Kalkulation. Select "Hypertonie" and observe how disease stages map to AU probabilities. This is what an underwriter prices. Then try Page 6: Underwriting Simulator — it presents case studies where you make the decision before seeing the expert answer. Page 7: KTG Flashcards provides quick-reference cards for self-study.

---

## Chapter 2: Where Medical Data Comes From

*~9 min | Beginner*

**Learning Objectives:**
- Understand data sources available to underwriters (claims, EHR, lab feeds, questionnaires)
- Recognize market-level variation in data availability
- Map the PatientRecord schema to real-world medical records

### 2.1 Data Sources in Practice

Underwriters work with several data types, each with different completeness and reliability:

| Source | Coverage | Strengths | Weaknesses |
|--------|----------|-----------|------------|
| **Claims databases** (InGef, GePaRD) | 8.8M+ GKV patients (DE) | Large population, longitudinal | No lab values in GKV claims |
| **EHR systems** (CPRD, UK) | 60M patients | Labs + diagnoses + prescriptions | UK-specific, access costs £25-80K |
| **Lab feeds** | Direct from lab providers | Precise, timestamped | Not always linked to diagnoses |
| **Self-reported questionnaires** | 100% of applicants | Always available | Subjective, under-reporting |
| **PKV internal data** (a major European insurer) | Company portfolio | Claims outcomes linked | Small sample, selection bias |

The critical insight for German underwriting: **GKV claims data (InGef, GePaRD) does not contain laboratory values.** Only PKV data and CPRD (UK) have linked labs + diagnoses. This is why the DQS framework (Chapter 7) matters — different data sources have fundamentally different completeness levels.

See `docs/data_requirements.md` for the full data source comparison with costs and timelines.

### 2.2 The PatientRecord Schema

In MedRisk-ADH, every patient is represented as a `PatientRecord` (`src/medrisk/data/schemas.py`). This schema mirrors what a real-world underwriting system receives:

**Demographics (5 fields — always present):**
- `age` (18-100), `sex` (M/F), `bmi` (12.0-60.0), `smoking_status` (never/former/current), `market` (DE/ES/FR/INT)

**Diagnoses (ICD-10 coded):**
- `icd10_code` — validated against pattern `^[A-Z]\d{2}(\.\d{1,4})?$`
- `description`, `date_recorded`, `is_primary` flag

**Lab results (LOINC coded):**
- `loinc_code`, `name`, `value`, `unit`, `date_collected`
- `reference_low`, `reference_high` for context

**Medications (ATC coded):**
- `atc_code` — validated against pattern `^[A-Z]\d{2}[A-Z]{2}\d{2}$`
- `name`, `date_prescribed`, `active` status

**Ground truth fields (synthetic only, never visible to models):**
- `gt_true_conditions` — what the patient actually has
- `gt_true_risk_score` — their true underlying risk
- `gt_data_quality_score` — how complete their synthetic record is

This separation between observed data and ground truth is what enables MedRisk-ADH to measure when models are confidently wrong.

### 2.3 Market Variation

Healthcare systems differ dramatically in what data they produce. The `MARKET_CONFIGS` in `src/medrisk/data/schemas.py` (line 133) encode this:

| Parameter | Germany (DE) | Spain (ES) | France (FR) | International (INT) |
|-----------|:---:|:---:|:---:|:---:|
| **Coding completeness** | 95% | 80% | 90% | 60% |
| **Lab completeness** | 92% | 75% | 88% | 50% |
| **Lab noise (sigma)** | ±2% | ±5% | ±3% | ±10% |
| **Diagnosis lag (mean)** | 14 days | 30 days | 60 days | 90 days |
| **Medication recording** | 95% | 80% | 88% | 60% |
| **Population age (mean ± std)** | 52 ± 14 | 56 ± 16 | 54 ± 15 | 50 ± 18 |

**What this means for an underwriter:**
- A German record with 10 diagnoses likely represents 10 actual conditions
- A Spanish record with 10 diagnoses represents ~12.5 actual conditions (20% missing)
- An International record with 10 diagnoses could represent ~17 actual conditions (40% missing)
- French diagnosis dates are typically 60 days stale — the recorded date is not the event date

### 2.4 Ground Truth vs. Observed Data

The synthetic cohort generator (`src/medrisk/data/synthetic.py`) operates in two stages:

1. **Ground truth simulation** — generate true disease states using epidemiological prevalence rates and CTMC progression
2. **Observation degradation** — apply market-specific missingness, noise, and lag to simulate real-world data quality

This two-stage process is not an engineering trick — it mirrors reality. Every patient has a true disease state, but the underwriter only sees a noisy, incomplete observation of that state. The gap between truth and observation is where underwriting errors live.

> **Try it yourself:**
> 1. Open `src/medrisk/data/schemas.py` and count the fields in `PatientRecord`. How many are demographics vs. diagnoses vs. labs vs. medications?
> 2. Compare the DE and INT market configs. If a patient has 10 lab values in truth, how many would typically be observed in DE vs. INT?
> 3. Run Notebook 01 (`notebooks/01_synthetic_cohort.ipynb`) and compare the DQS distribution across markets.

### 2.5 External Data Fetching

Beyond synthetic data, MedRisk-ADH includes a production-grade data fetching pipeline (`src/medrisk/fetch/`) for ingesting real-world cohort data from 8 external sources. All adapters harmonize into a unified 4-table schema (`Person`, `Measurement`, `Event`, `Treatment`) defined in `src/medrisk/fetch/_schema.py`.

| Adapter | Source | Data Type | Coverage |
|---------|--------|-----------|----------|
| **NHANES** | US CDC survey cycles (1999-2023) | Demographics, labs (HbA1c, glucose, lipids, BP), BMI | ~10,000/cycle |
| **CDC PLACES** | Area-level health estimates | Diabetes, hypertension, obesity prevalence by county/tract | All US counties |
| **data.gov** | Federal open datasets (Socrata API) | Configurable per dataset | Varies |
| **Zenodo** | Open science repository | Research datasets (any format) | Record-based |
| **Glucose-ML** | Continuous glucose monitoring | CGM traces, meal/insulin events | Research cohorts |
| **T1 Granada** | Type 1 diabetes (Spain) | Clinical + CGM data | Spanish cohort |
| **UK Biobank** | Population health study (UK) | 500K participants, deep phenotyping | Locally downloaded |
| **BioLINCC** | NHLBI clinical trial data | Cardiovascular outcomes | Controlled access |

**Architecture:**
- **Harmonizer** (`_harmonizer.py`) — normalizes units (e.g., mg/dL → mmol/L), maps ICD-9 → ICD-10, creates stub persons from orphaned measurements
- **Cache** (`_cache.py`) — filesystem cache with SHA-256 integrity verification, avoids redundant downloads
- **Pipeline** (`_pipeline.py`) — orchestrates fetch → parse → harmonize → validate → export
- **CLI** (`medrisk-fetch`) — command-line interface with subcommands: `fetch`, `sources`, `list-datasets`, `export`

**Why this matters for underwriting:** Synthetic data (Chapter 2.1-2.4) demonstrates the mechanism; real external data validates it. The fetch pipeline is the bridge to Phase 2 validation against actual population health data.

> **Try it yourself:**
> 1. Run `python -m medrisk.fetch.cli sources` to list all registered adapters
> 2. Read `src/medrisk/fetch/_schema.py` — how does the `Measurement` model standardize values from different lab systems?

---

## Chapter 3: Medical Coding Systems

*~10 min | Beginner*

**Learning Objectives:**
- Understand ICD-10 code structure (chapter, block, category, code)
- Recognize LOINC codes for lab results and ATC codes for medications
- Know why coding granularity matters for risk assessment

### 3.1 ICD-10: The Language of Diagnoses

Every medical diagnosis is encoded as an ICD-10 code. The structure is hierarchical:

```
I21.0
│ ││
│ │└── Extension (0 = anterior wall)
│ └─── Category (21 = acute MI)
└───── Chapter (I = diseases of the circulatory system)
```

MedRisk-ADH registers 56 curated codes in `src/medrisk/data/icd10.py` (line 32), organized by clinical relevance:

**Cardiovascular (Chapter IX: I00-I99) — 21 codes:**
- I10 = Essential hypertension (the single most common underwriting code)
- I21.0 = Acute ST-elevation MI, anterior wall
- I21.4 = Acute NSTEMI (non-ST-elevation MI)
- I50.0 = Congestive heart failure
- I48.0/I48.1 = Atrial fibrillation (paroxysmal/persistent)
- I63.9 = Cerebral infarction (stroke)

**Diabetes & Metabolic (Chapter IV: E00-E90) — 16 codes:**
- E11.9 = Type 2 diabetes **without** complications (Charlson weight = 1)
- E11.2 = Type 2 diabetes **with** kidney complications (Charlson weight = 2)
- E11.21 = Type 2 diabetes with diabetic nephropathy
- E78.0/E78.2 = Hypercholesterolemia / Mixed hyperlipidemia

**Renal (Chapter XIV) — 6 codes:**
- N18.1 through N18.5 = CKD stages 1-5 (progressive severity)
- N18.6 = End-stage renal disease (ESRD)

The key underwriting insight: **the decimal extensions matter enormously.** E11.9 (diabetes, no complications) and E11.2 (diabetes, kidney complications) carry fundamentally different risk profiles — the Charlson index doubles from weight 1 to weight 2.

### 3.2 ICD-10-CM vs. ICD-10-GM

Germany uses ICD-10-GM (German Modification), which diverges from the US ICD-10-CM in several places. The most relevant for this project:

- **Alzheimer's dementia:** ICD-10-GM uses F00.0-F00.9 (Chapter V). These codes **do not exist** in ICD-10-CM, which uses G30.x + F02.8x instead.
- See `src/medrisk/data/icd10.py` lines 126-131 — these codes are annotated `[GM only]`

If you're building underwriting systems for the German market, you must handle both coding systems.

### 3.3 LOINC Codes for Lab Results

Lab results use LOINC codes (Logical Observation Identifiers Names and Codes). MedRisk-ADH defines 14 labs in `src/medrisk/data/synthetic.py` (line 143), each with normal and disease-state distributions:

| LOINC | Lab Test | Unit | Normal (mean ± SD) | Disease State (mean ± SD) | Condition |
|-------|----------|------|-------|---------|-----------|
| 4548-4 | HbA1c | % | 5.0 ± 0.3 | 8.0 ± 1.5 | Diabetes |
| 2160-0 | Creatinine | mg/dL | 0.9 ± 0.15 | 2.5 ± 1.0 | CKD |
| 48642-3 | eGFR | mL/min | 90 ± 15 | 35 ± 15 | CKD |
| 2093-3 | Total Cholesterol | mg/dL | 185 ± 25 | 260 ± 35 | Dyslipidemia |
| 2085-9 | HDL | mg/dL | 55 ± 10 | 35 ± 8 | Dyslipidemia |
| 13457-7 | LDL | mg/dL | 100 ± 20 | 170 ± 30 | Dyslipidemia |
| 2571-8 | Triglycerides | mg/dL | 110 ± 30 | 250 ± 60 | Dyslipidemia |
| 8480-6 | Systolic BP | mmHg | 118 ± 10 | 150 ± 15 | Hypertension |
| 8462-4 | Diastolic BP | mmHg | 75 ± 8 | 95 ± 10 | Hypertension |
| 33762-6 | NT-proBNP | pg/mL | 60 ± 30 | 1500 ± 800 | Heart failure |
| 72106-8 | MMSE | score | 28 ± 1.5 | 18 ± 5 | Alzheimer |
| 72172-0 | MoCA | score | 27 ± 2 | 16 ± 5 | Alzheimer |
| 33203-1 | CSF Amyloid-Beta42 | pg/mL | 900 ± 150 | 450 ± 120 | Alzheimer |
| 72260-3 | CSF p-tau181 | pg/mL | 15 ± 5 | 65 ± 20 | Alzheimer |

**What underwriters learn from labs:**
- HbA1c >= 6.5% is **diagnostic** for diabetes (even without an ICD code)
- eGFR < 30 means CKD stage 4-5 (severe kidney disease)
- NT-proBNP > 125 pg/mL suggests heart failure
- CSF amyloid-beta42 is **inverted** in Alzheimer's — it drops from 900 to 450 pg/mL

### 3.4 ATC Codes for Medications

Medications use the WHO ATC (Anatomical Therapeutic Chemical) classification. The code is 7 characters:

```
C09AA02
│ │ ││
│ │ │└── Chemical substance (02 = Enalapril)
│ │ └─── Chemical subgroup (AA = ACE inhibitors, plain)
│ └───── Pharmacological subgroup (09 = agents acting on the renin-angiotensin system)
└─────── Anatomical main group (C = cardiovascular system)
```

MedRisk-ADH maps conditions to medications in `src/medrisk/data/synthetic.py` (line 269):

| Condition | Drug | ATC | Probability |
|-----------|------|-----|-------------|
| Hypertension | Metoprolol | C07AB02 | 40% |
| Hypertension | Enalapril | C09AA02 | 35% |
| Hypertension | Losartan | C09CA01 | 30% |
| Dyslipidemia | Atorvastatin | C10AA05 | 45% |
| IHD | Aspirin (ASA) | B01AC06 | 70% |
| Diabetes | Metformin | A10BA02 | 65% |
| Atrial fib. | Rivaroxaban | B01AF01 | 50% |
| Alzheimer | Donepezil | N06DA02 | 50% |
| Alzheimer | Memantine | N06DX01 | 35% |

**Why medications matter for underwriting:** Medication records can **confirm or contradict** diagnoses. A patient with no hypertension code (I10) but on Metoprolol (C07AB02) likely has undiagnosed or undocumented hypertension.

### 3.5 Why Coding Granularity Drives Risk Assessment

Consider two patients, both labeled "diabetic":
- **Patient A:** E11.9 (T2D without complications) → Charlson weight = 1
- **Patient B:** E11.21 (T2D with diabetic nephropathy) → Charlson weight = 2

Patient B has double the comorbidity burden from one additional decimal digit. In Chapter 4, you'll see how the Charlson Index amplifies this distinction across all 17 disease categories.

> **Try it yourself:**
> 1. In a Python shell: `from medrisk.data.icd10 import get_codes_by_category; print(get_codes_by_category("diabetes"))` — count the diabetes codes
> 2. Look at the HbA1c lab definition. What would an underwriter conclude from HbA1c = 9.5%?
> 3. Find the ICD-10-GM-only codes in `icd10.py`. Why does this matter for a German insurer?

---

## Chapter 4: Comorbidity Assessment — The Charlson Index

*~8 min | Intermediate*

**Learning Objectives:**
- Understand what comorbidity means and why it multiplies risk
- Calculate the Charlson Comorbidity Index from ICD-10 codes
- Recognize hierarchy rules (complicated supersedes uncomplicated)

### 4.1 What Is Comorbidity?

Comorbidity is the presence of multiple conditions in the same patient. Crucially, the risk is **multiplicative, not additive.** A diabetic patient doesn't just have "diabetes risk + CKD risk" — diabetes increases CKD risk by 2.5x.

This is encoded in `COMORBIDITY_LINKS` in `src/medrisk/data/synthetic.py` (line 126):

| Primary Condition | Increases Risk Of | Multiplier |
|-------------------|-------------------|:---:|
| Diabetes | IHD | 2.0x |
| Diabetes | CKD | 2.5x |
| Diabetes | PVD | 1.8x |
| Diabetes | Stroke | 1.5x |
| Diabetes | Heart failure | 1.5x |
| Diabetes | Alzheimer | 1.5x |
| Hypertension | Stroke | 2.0x |
| Hypertension | IHD | 1.8x |
| Hypertension | CKD | 1.5x |
| Hypertension | Alzheimer | 1.4x |
| Obesity | Diabetes | 2.5x |
| Obesity | Hypertension | 1.8x |
| Obesity | Dyslipidemia | 2.0x |
| IHD | MI | 3.0x |
| IHD | Heart failure | 2.0x |

**Cascade example:** Obesity → 2.5x diabetes → 2.5x CKD. An obese patient has 6.25x the CKD risk of a lean patient — and that's before age effects.

### 4.2 The Charlson Comorbidity Index

The Charlson Comorbidity Index (CCI), implemented in `src/medrisk/data/charlson.py`, is the standard tool for aggregating comorbidity burden. It assigns **severity weights** (1, 2, 3, or 6) to 17 disease categories based on their impact on mortality.

| Weight | Category | Example ICD-10 Prefixes |
|:---:|----------|------------------------|
| **1** | Myocardial infarction | I21, I22, I25.2 |
| **1** | Congestive heart failure | I50, I42, I43 |
| **1** | Peripheral vascular disease | I70, I71, I73 |
| **1** | Cerebrovascular disease | I60-I68, G45, G46 |
| **1** | Dementia | F00-F03, G30, G31.1 |
| **1** | Chronic pulmonary disease | J40-J47, J60-J67 |
| **1** | Rheumatic disease | M05, M06, M32-M36 |
| **1** | Peptic ulcer disease | K25-K28 |
| **1** | Mild liver disease | B18, K70-K76 |
| **1** | Diabetes, uncomplicated | E10.0-E14.9 (excl. .2-.7) |
| **2** | Diabetes, complicated | E10.2-E14.7 |
| **2** | Hemiplegia/paraplegia | G81-G83 |
| **2** | Renal disease | N18, N19, I12.0 |
| **2** | Any malignancy | C00-C97 (excl. C77-C80) |
| **3** | Moderate/severe liver disease | I85, K70.4, K72, K76.5-K76.7 |
| **6** | Metastatic solid tumor | C77-C80 |
| **6** | AIDS/HIV | B20-B24 |

Source: Quan et al. (2005) adaptation of Charlson & Pompei (1987).

### 4.3 Hierarchy Rules

Three hierarchy rules prevent double-counting when a patient has both mild and severe forms of the same condition. From `src/medrisk/data/charlson.py` (lines 411-416):

1. **Complicated diabetes (weight 2) supersedes uncomplicated (weight 1)** — if a patient has both E11.9 and E11.21, only the weight-2 complicated form counts
2. **Severe liver disease (weight 3) supersedes mild (weight 1)** — decompensated cirrhosis replaces fatty liver
3. **Metastatic cancer (weight 6) supersedes any malignancy (weight 2)** — metastasis changes everything

### 4.4 From Codes to Score — Worked Example

**Patient:** 65-year-old male with codes I21.0, E11.4, N18.4, J44.9

| Code | Condition | Category | Weight |
|------|-----------|----------|:---:|
| I21.0 | Anterior wall MI | mi | 1 |
| E11.4 | T2D with neuro complications | diabetes_complicated | 2 |
| N18.4 | CKD stage 4 | renal | 2 |
| J44.9 | COPD | copd | 1 |

**Charlson Index = 1 + 2 + 2 + 1 = 6**

Note: Hypertension (I10) does **not** have a Charlson category. A patient with only hypertension and dyslipidemia has Charlson = 0 — even though they may still be high-risk for cardiovascular events. The Charlson Index captures comorbidity burden, not total risk.

You can verify this with `compute_charlson_index(["I21.0", "E11.4", "N18.4", "J44.9"])` from `src/medrisk/data/charlson.py`.

### 4.5 The Elixhauser Comorbidity Index

The Elixhauser Index (`src/medrisk/models/risk_scoring.py`) complements Charlson by covering **31 conditions** (vs. 17), including several that Charlson misses:

- **Hypertension** (uncomplicated and complicated) — the most common underwriting condition, invisible to Charlson
- **Obesity** — a major KTG risk factor
- **Depression** — strongly predicts sickness absence duration
- **Alcohol/drug abuse** — underwriting red flags
- **Fluid/electrolyte disorders**, **blood loss anemia**, **coagulopathy** — acute-care markers

The scoring uses additive weights from van Walraven et al. (2009), where each condition has a positive or negative weight reflecting its independent effect on in-hospital mortality.

**When to use which index:**
- **Charlson** — mortality prediction, long-term survival estimation (`S10 = 0.983^exp(CCI×0.9)`)
- **Elixhauser** — broader comorbidity burden, especially for sickness absence and morbidity models where conditions like hypertension, obesity, and depression are relevant

Both are implemented in `src/medrisk/models/risk_scoring.py` with a unified interface: `CharlsonIndex` and `ElixhauserIndex` classes.

> **Try it yourself:**
> 1. Compute the Charlson index for: I50.0 (CHF), E11.9 (T2D), J44.9 (COPD), N18.3 (CKD stage 3). Then verify using `compute_charlson_index()`.
> 2. What happens if a patient has both E11.9 (uncomplicated) and E11.4 (with neuro complications)? Run the function and explain.
> 3. Using `COMORBIDITY_LINKS`, trace the cascade: obesity → diabetes → CKD. What are the multipliers at each step?

---

## Chapter 5: Risk Classification Models

*~10 min | Intermediate*

**Learning Objectives:**
- Understand binary risk classification in underwriting
- Know what XGBoost predicts and how Platt calibration corrects confidence
- Read model metrics: AUC-ROC, Brier score, concordance index

### 5.1 What Risk Models Predict

The core underwriting question is binary: **will this patient experience a major adverse event within the follow-up period?**

Event types, defined in `src/medrisk/data/schemas.py` (line 97):
- death, MI, stroke, heart failure, CKD progression, institutionalization, cognitive decline

The model predicts `P(event_occurred = True)` — a probability between 0 and 1. Higher values mean higher risk.

### 5.2 Feature Engineering

The feature matrix is built from patient records in `src/medrisk/features/engineering.py`. The ~40 features break down as:

| Category | Count | Examples |
|----------|:---:|---------|
| Demographics | 5 | age, sex, bmi, smoking, market |
| Charlson indicators | 17 | has_mi, has_chf, has_diabetes_complicated, ... |
| Lab values | 10 | lab_hba1c, lab_egfr, lab_systolic_bp, ... |
| Medication flags | 8 | med_antihypertensive, med_statin, med_anticoagulant, ... |
| **Total** | **~40** | |

Critically, **no imputation is performed.** If a lab value is missing, it stays missing. This is a deliberate design decision — as you'll see in Section 5.5, different models handle different feature availability.

### 5.3 The XGBoost Classifier

The primary risk model is an XGBoost gradient boosted tree, configured in `src/medrisk/models/xgb_classifier.py`:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| n_estimators | 200 | Sufficient for ~40 features |
| max_depth | 6 | Balance expressiveness vs. overfitting |
| learning_rate | 0.05 | Conservative, benefits from more trees |
| early_stopping_rounds | 20 | Prevent overfitting on validation set |

Key methods:
- `predict_proba(X)` — raw, uncalibrated probabilities
- `predict_proba_calibrated(X)` — Platt-calibrated probabilities (see 5.4)
- `get_feature_importance()` — which features drive predictions

### 5.4 Platt Calibration

Raw XGBoost probabilities are **not well-calibrated.** A model that outputs 0.80 does not mean there's an 80% chance of an event — it means the model is relatively confident, but the actual probability may be 0.60 or 0.90.

Platt calibration (`calibrate()` method, sigmoid method) fits a logistic regression on validation predictions to map raw probabilities to calibrated ones. After calibration, a 0.80 output actually means ~80% event probability.

The mismatch between raw and calibrated probabilities is exactly what the **CCM (Calibration-Confidence Mismatch)** signal detects in Chapter 8. Large mismatches mean the model is overconfident in that region.

### 5.5 Model Metrics

On the synthetic cohort, MedRisk-ADH achieves:

| Metric | Value | Interpretation |
|--------|-------|---------------|
| AUC-ROC | 0.71 | Better than random (0.50), far from perfect (1.00) |
| Brier Score | 0.010 | Well-calibrated probability estimates |
| Concordance Index | 0.72 | Survival model discriminates well |

**What these mean for underwriting:**
- AUC 0.71 is modest but realistic for broad-population risk scoring. Clinical models rarely exceed 0.80 without genetics or imaging.
- Brier score near zero means the predicted probabilities are reliable — if the model says 30% risk, ~30% of such patients actually have events.
- These are **synthetic** metrics. Real-world validation (Phase 2) may differ.

### 5.6 The Model Router

Instead of training one model and imputing missing features, MedRisk-ADH trains **separate models per data profile** via the `ModelRouter` (`src/medrisk/models/model_router.py`):

| Profile | Features Available | Typical Market |
|---------|-------------------|----------------|
| FULL | All (demographics + diagnoses + labs + meds) | DE |
| NO_LABS | Demographics + diagnoses + meds | GKV claims |
| NO_MEDS | Demographics + diagnoses + labs | Research databases |
| MINIMAL | Demographics + diagnoses only | INT |
| INSUFFICIENT | Too little data for any model | → Mandatory human review |

**Why this matters:** A FULL model trained on German data will output high confidence even on sparse International data — because XGBoost fills the gap with training-set patterns, not patient evidence. The Model Router eliminates this failure mode by routing each patient to a model that only uses features actually present in their record.

This is the architectural foundation of PBW detection.

> **Try it yourself:**
> 1. Run Notebook 02 (`notebooks/02_risk_classification.ipynb`) end-to-end. What is the AUC on the test set?
> 2. In `model_router.py`, why does INSUFFICIENT profile trigger mandatory human review instead of running a model?
> 3. Compare `predict_proba()` vs. `predict_proba_calibrated()` on 10 patients. When do they diverge most?

---

## Chapter 6: Disease Progression Modeling

*~10 min | Intermediate*

**Learning Objectives:**
- Understand survival analysis (Cox PH) and its insurance application
- Understand Continuous-Time Markov Chains (CTMC) for disease progression
- Read state occupation probability charts

### 6.1 Why Time Matters

An underwriter doesn't just ask "will this patient get sick?" but "**when?**" and "**how fast will it progress?**" A 50-year-old with early-stage hypertension is a very different risk from a 50-year-old with hypertensive crisis.

Three time-aware models in MedRisk-ADH address this:

| Model | Question | Output |
|-------|----------|--------|
| Cox PH | How fast will the event occur? | Hazard ratios, survival curves S(t) |
| Kaplan-Meier | What's the population survival curve? | Non-parametric S(t) estimate |
| CTMC | What disease stage will the patient be in at time t? | State occupation probabilities |

### 6.2 Cox Proportional Hazards

The Cox PH model (`src/medrisk/models/cox_ph.py`) estimates how each covariate multiplies the baseline hazard:

```
h(t|X) = h₀(t) × exp(β₁X₁ + β₂X₂ + ... + βₚXₚ)
```

Key outputs:
- **Hazard ratio** `exp(βᵢ)` — e.g., if HR for diabetes = 2.1, a diabetic patient has 2.1x the hazard of a non-diabetic, all else equal
- **Survival function S(t)** — probability of being event-free at time t
- **Median survival** — the time at which S(t) = 0.50
- **Concordance index** — like AUC but for survival data. 0.72 in MedRisk-ADH.

**Insurance application:** Cox PH tells the underwriter how much extra risk a given condition adds (hazard ratio) and when the expected event occurs (median survival). This directly feeds pricing models.

### 6.3 CTMC Disease Progression

The Continuous-Time Markov Chain (`src/medrisk/models/multistate.py`) models disease as a sequence of states with transition rates between them.

**Key mathematical objects:**
- **Q matrix** — transition intensity matrix. Off-diagonal entries are rates; diagonal entries are negative row sums.
- **P(t) = expm(Q × t)** — transition probability matrix at time t, computed via matrix exponential
- **Mean sojourn time** = 1/(-Qᵢᵢ) — expected time in state i before transitioning

**Simulation:** Individual patient trajectories are generated via the **Gillespie algorithm** — at each state, sample a waiting time from Exponential(-Qᵢᵢ), then choose the next state proportional to transition rates.

### 6.4 Cardiovascular Disease — 5 States

Defined in `src/medrisk/models/disease_configs.py` (line 46):

```
Healthy (0) → Risk factors (1) → Chronic condition (2) → Complication (3) → Major event (4)
                  ↑                       │                                      ↑
                  └── lifestyle change ───┘                  (skip) ─────────────┘
```

| Transition | Intensity | Mean Sojourn |
|-----------|:---------:|:------------:|
| Healthy → Risk factors | 0.08 | 12.5 years |
| Risk factors → Chronic | 0.06 | 16.7 years |
| Risk factors → Healthy | 0.02 | (reverse) |
| Chronic → Complication | 0.04 | 25 years |
| Chronic → Major event | 0.01 | (skip) |
| Complication → Major event | 0.03 | 33 years |

### 6.5 Alzheimer's Disease — 7 States

Defined in `src/medrisk/models/disease_configs.py` (line 104). This demonstrates framework generalizability — adding a new disease requires only a config, no code changes:

```
Normal Cognition (0) → SCD (1) → MCI (2) → Mild AD (3) → Moderate AD (4) → Severe AD (5) → Death (6)
                                                  │                │
                                                  └── Death (6) ───┘   (competing risks)
```

| Transition | Intensity | Mean Sojourn | Source |
|-----------|:---------:|:------------:|--------|
| NC → SCD | 0.04 | 25 years | Subclinical pathology phase |
| SCD → MCI | 0.08 | 12.5 years | Increasing cognitive complaints |
| MCI → Mild AD | 0.15 | 6.7 years | **15% annual conversion** (Petersen et al., NEJM 2018) |
| Mild → Moderate AD | 0.25 | 4 years | Documented progression |
| Moderate → Severe AD | 0.33 | 3 years | Accelerated decline |
| Severe AD → Death | 0.50 | 2 years | Brookmeyer et al. |
| Mild AD → Death | 0.02 | — | Comorbid mortality |
| Moderate AD → Death | 0.05 | — | Comorbid mortality |

**What underwriters learn:** The transition from MCI to Mild AD is not instantaneous — it takes on average 6.7 years at 15% annual conversion. But once in Severe AD, survival is only ~2 years. This time structure determines when claims start and how long they last.

### 6.6 Mean Sojourn and Absorption

Two key quantities for insurance pricing:

- **Mean sojourn time in state i** = 1/(-Qᵢᵢ) — how long a patient stays in a state before moving
- **Mean time to absorption** — expected time from initial state to the absorbing state (death/major event), computed from the fundamental matrix

For the Alzheimer model starting from MCI (state 2):
- Mean time through Mild (4y) + Moderate (3y) + Severe (2y) = ~9 years to death
- But with competing risks (direct death from Mild/Moderate), actual mean is shorter

> **Try it yourself:**
> 1. Run Notebook 03 (`notebooks/03_disease_progression.ipynb`). At year 10, what is the probability of being in state 3 (Complication) starting from state 1 (Risk factors)?
> 2. In the Streamlit app (Page 4: Alzheimer Progression), change the initial state from "Normal Cognition" to "MCI" and observe how the curves shift.
> 3. Use the Alzheimer config intensities to compute mean sojourn time for each state. How long from MCI to death?

---

## Chapter 7: Data Quality — The DQS Framework

*~11 min | Intermediate*

**Learning Objectives:**
- Compute the Data Quality Score from its three components
- Understand consistency rules and why they matter
- Classify missingness types (structural, workflow, random)

### 7.1 Why Data Quality Comes Before Modeling

As you learned in Chapters 2 and 5, the model cannot distinguish "confident because data is good" from "confident because it filled gaps with training priors." The DQS is computed **per-patient, before any model inference,** to answer: how much should a downstream model trust its own input?

This is implemented in `src/medrisk/validation/data_quality.py`.

### 7.2 Completeness (weight 0.40)

Completeness measures the fraction of expected features that are actually present:

```
completeness = observed_features / TOTAL_EXPECTED_FEATURES
```

Where `TOTAL_EXPECTED_FEATURES = 40` (from `data_quality.py` line 36-38):
- 5 demographic features (always present)
- 17 Charlson diagnosis category indicators
- 10 lab values
- 8 medication flags

**Example:** A patient with 5 demographics + 3 diagnoses + 2 labs + 1 medication = 11/40 = **27.5% completeness.**

### 7.3 Consistency (weight 0.35)

Consistency checks whether diagnoses and lab values agree with each other. Five rules are implemented in `data_quality.py` (lines 67-141):

| Rule | Condition | Check | Clinical Logic |
|------|-----------|-------|----------------|
| `diabetes_hba1c` | E11.x diagnosed | HbA1c >= 5.7% | Diabetes without elevated glucose is suspicious |
| `ckd_egfr` | N18.4/N18.5/N18.6 | eGFR < 30 | Severe CKD must show in kidney function |
| `hf_bnp` | I50.x diagnosed | NT-proBNP > 125 | Heart failure elevates natriuretic peptides |
| `hypertension_bp` | I10.x diagnosed | SBP > 120 OR on antihypertensive | Controlled HTN is still consistent |
| `no_diabetes_hba1c` | No E11.x code | HbA1c < 6.5% | Elevated HbA1c without diabetes code = possible missed diagnosis |

**Scoring:** Consistency = (rules passed) / (rules applicable). A rule is only applicable if both the diagnosis and the relevant lab/med are present.

**What these rules catch:** A patient record that says "diabetes" but has HbA1c = 5.0% (normal) has either a wrong diagnosis, a stale lab, or perfect glycemic control. All three are important to flag.

### 7.4 Recency (weight 0.25)

Lab values decay in relevance over time. A blood pressure reading from 3 years ago tells less about today's risk than one from last month.

MedRisk-ADH uses exponential decay with a **half-life of 1.4 years** (from `data_quality.py` line 211):

```
weight(age) = exp(-ln(2) / 1.4 × age_in_years)
```

| Lab Age | Weight | Interpretation |
|---------|:------:|---------------|
| 0 months | 1.00 | Fresh, fully relevant |
| 6 months | 0.78 | Still reliable |
| 1 year | 0.61 | Moderately relevant |
| 1.4 years | 0.50 | Half-life: half as relevant |
| 3 years | 0.23 | Mostly stale |
| 5 years | 0.08 | Nearly irrelevant |

If a patient has no lab results at all, recency = 0.0.

### 7.5 The Composite DQS

The final score combines the three components:

```
DQS = 0.40 × completeness + 0.35 × consistency + 0.25 × recency
```

These weights (alpha, beta, gamma) reflect relative importance — completeness matters most (you can't assess what you can't see), consistency matters second (conflicting data is dangerous), recency matters third (stale data is better than no data).

### 7.6 DQS v2 Extensions

DQS v2 adds three capabilities on top of v1:

**Missingness classification** (`classify_missingness()`, line 282): Why is a feature missing?
- **Structural** — the healthcare system doesn't collect it (e.g., INT market with 50% lab completeness)
- **Workflow** — collected but not transmitted (e.g., lab ran at hospital but not linked to claims)
- **Random** — individual patient variation (e.g., patient didn't show up for blood draw)

This matters because structural missingness is **not the patient's fault** and should not be penalized the same way.

**Range checks** (`src/medrisk/validation/range_checks.py`): Are lab values physiologically possible? (e.g., HbA1c of 25% is a data entry error, not diabetes)

**Learned error probability**: Optional trained model that predicts P(model error) from quality features alone, before running the risk model.

### 7.7 Tier Classification and Cross-Market Distribution

| Tier | DQS Range | Expected Volume | Action |
|------|:---------:|:---------:|--------|
| Adequate | >= 0.80 | 60-70% | Auto-process |
| Caution | 0.60 - 0.80 | 20-30% | Review recommended |
| Insufficient | < 0.60 | 5-15% | Escalate to human |

**Typical DQS by market:**

| Market | Typical DQS | Typical Tier |
|--------|:-----------:|:---:|
| Germany (DE) | ~0.85 | Adequate |
| France (FR) | ~0.80 | Adequate/Caution |
| Spain (ES) | ~0.70 | Caution |
| International (INT) | ~0.45 | Insufficient |

> **Try it yourself:**
> 1. Manually compute DQS for: completeness=0.90, consistency=1.00, recency=0.70. What tier? (Answer: 0.40×0.90 + 0.35×1.00 + 0.25×0.70 = 0.885 → Adequate)
> 2. Run Notebook 04 (`notebooks/04_failure_modes.ipynb`) and find a patient where the consistency score is below 0.5. What rules were violated?
> 3. Think about a new consistency rule: "If COPD is coded, patient should be former or current smoker." Where in `data_quality.py` would you add it?

---

## Chapter 8: When to Trust a Model vs. Escalate to Human

*~11 min | Advanced*

**Learning Objectives:**
- Understand the three failure detection signals: CCM, EPU, PBW
- Explain why PBW is the most dangerous failure mode
- Understand cost-asymmetric decision-making

### 8.1 The Plausible-but-Wrong Problem

This is the core intellectual contribution of MedRisk-ADH, implemented in `src/medrisk/validation/failure_detection.py`.

**The problem:** A model trained on rich German data (95% completeness) will output a confident prediction (say 85% risk) even on sparse International data (50% completeness). The model doesn't know its input is degraded — it just pattern-matches against what it learned.

**Why it's dangerous:** The confidence must come from the **training distribution's prior**, not the **patient's data.** The model is saying "patients with these few features looked risky in my training set" — not "this specific patient's data supports a risk conclusion."

**The information-theoretic argument:** By the data processing inequality, a model cannot extract more information from a record than the record contains. If the record has DQS = 0.30, the maximum justifiable confidence is bounded by that data quality.

### 8.2 Signal 1: CCM (Calibration-Confidence Mismatch)

From `failure_detection.py` lines 89-94:

```python
ccm = abs(raw_proba - calibrated_proba)
if ccm > 0.20:  # 20 percentage points
    flags.append("ccm_high")
```

**What it detects:** The raw model probability and the calibrated probability diverge by more than 20 percentage points. This means the model is in a region where its confidence is unreliable.

**Example:** Raw = 0.85, calibrated = 0.60 → CCM = 0.25 → flagged.

As you learned in Chapter 5 about Platt calibration, calibration adjusts probabilities to be reliable. A large CCM means the model is overconfident in this region of feature space.

### 8.3 Signal 2: EPU (Epistemic Prediction Uncertainty)

From `failure_detection.py` lines 96-101:

```python
epu = max(model_risk_deciles) - min(model_risk_deciles)
if epu > 3:  # 3 deciles of disagreement
    flags.append("epu_high")
```

**What it detects:** Multiple risk models disagree about the same patient. If one model says "decile 3" (low risk) and another says "decile 8" (high risk), the patient's case is fundamentally ambiguous.

**Why deciles, not probabilities:** Decile disagreement is robust to calibration differences between models. A 3-decile spread means the models disagree on whether the patient is in the bottom third or top third of risk.

### 8.4 Signal 3: PBW (The Core Safety Flag)

From `failure_detection.py` lines 103-107:

```python
effective_confidence = max(raw_proba, 1.0 - raw_proba)
pbw_flag = (effective_confidence > 0.80) and (dqs < 0.60)
```

**What it detects:** High confidence + low data quality. The model is very sure (>80% either way), but the data is insufficient (DQS < 0.60) to justify that certainty.

**Why it's the hardest flag:** CCM and EPU are "yellow flags" that suggest review. PBW is a "red flag" that means the prediction should be rejected entirely. The model **literally cannot have enough information** to justify its confidence — the confidence is an artifact of training, not evidence.

### 8.5 Decision Logic

The three signals combine into a recommendation:

| Flags Triggered | Recommendation | Action |
|----------------|---------------|--------|
| None | `accept` | Auto-process the prediction |
| CCM and/or EPU (no PBW) | `review` | Human underwriter reviews |
| PBW (with or without others) | `reject_prediction` | Prediction discarded, human decides from scratch |

### 8.6 The Reliability Head (v2)

The v1 PBW detector uses fixed thresholds (confidence > 0.80, DQS < 0.60). The v2 **Reliability Head** (`src/medrisk/validation/reliability_head.py`) replaces these with a learned model:

**Training:** Logistic regression on validation data where the target = `(model prediction != ground truth)`. Uses 15 features:
- `predicted_score`, `effective_confidence`
- DQS components: `completeness`, `consistency`, `recency`, `range_score`
- Missingness counts: `n_structural_missing`, `n_workflow_missing`, `n_random_missing`
- Interaction terms: `conf_x_completeness`, `conf_x_range`
- Data profile one-hot: `profile_full`, `profile_no_labs`, `profile_no_meds`, `profile_minimal`

**Why logistic regression?** Interpretability. Regulators need to understand why a decision was flagged. Each coefficient directly shows the relationship between a quality feature and error probability.

### 8.7 Cost-Optimal Decisions

The Reliability Head makes decisions that **minimize expected cost**, not maximize accuracy:

```python
cost_accept = P(wrong) × cost_fn    # 5.0 — accept a bad risk
cost_reject = (1 - P(wrong)) × cost_fp  # 1.0 — reject a good applicant
cost_review = cost_review             # 0.5 — escalate to human
decision = argmin(cost_accept, cost_reject, cost_review)
```

**Default cost parameters** from `ReliabilityConfig` (line 29):
- `cost_fn = 5.0` — accepting a high-risk applicant is 5x more expensive than rejecting a healthy one
- `cost_fp = 1.0` — rejecting a healthy applicant (lost premium)
- `cost_review = 0.5` — human review is cheap relative to misclassification

**Decision examples:**

| P(wrong) | Cost Accept | Cost Reject | Cost Review | Decision |
|:--------:|:-----:|:-----:|:-----:|----------|
| 0.05 | 0.25 | 0.95 | 0.50 | **Accept** |
| 0.15 | 0.75 | 0.85 | 0.50 | **Review** |
| 0.50 | 2.50 | 0.50 | 0.50 | **Reject/Review** (tie) |
| 0.80 | 4.00 | 0.20 | 0.50 | **Reject** |

**The 5:1 asymmetry reflects insurance reality:**
- False positive (reject healthy): lost premium, maybe EUR 5,000-10,000 lifetime value
- False negative (accept high-risk): unexpected claims, maybe EUR 50,000+ plus reputational damage

You can tune the cost parameters to match business strategy:
- **Conservative insurer:** set `cost_fn = 10.0` → reject more, fewer claims
- **Growth-focused insurer:** set `cost_fn = 2.0` → accept more, larger portfolio

> **Try it yourself:**
> 1. A patient has raw_proba=0.85, calibrated_proba=0.60, DQS=0.55. Which flags fire? What is the recommendation?
> 2. Run Notebook 04 and find the PBW rate per market. Does INT have the highest rate?
> 3. Change `cost_fn` from 5.0 to 2.0. How does this change the accept/review/reject proportions?

---

## Chapter 9: Insurance Pricing Mechanics — The KTG Example

*~9 min | Advanced*

**Learning Objectives:**
- Understand the Krankentagegeld (daily sickness benefit) product
- Trace the full pricing path: disease staging → AU probability → expected cost → premium
- See how data quality uncertainty creates premium bands

### 9.1 What Is KTG?

Krankentagegeld (KTG) is a German private insurance product that pays a **daily rate** when the policyholder is unable to work (Arbeitsunfähigkeit, AU). It's common in the PKV market.

The underwriter must estimate three quantities:
1. **P(AU per year)** — how likely is work incapacity in a given year?
2. **E[duration | AU]** — if incapacitated, how many days?
3. **Daily rate** — contractual benefit (e.g., EUR 80/day)

The expected annual cost is: `P(AU) × E[duration] × daily_rate`

But AU probability depends on **disease stage** — and disease stage changes over time via the CTMC. This is where all the models connect.

### 9.2 Three Example Diseases

The KTG calculator (`app/pages/5_KTG_Kalkulation.py`) demonstrates pricing for three German-market diseases:

**Hypertonie (I10) — Prevalence 30% (RKI DEGS1 2012)**

| Stage | State | P(AU/year) | E[duration] |
|:---:|-------|:---:|:---:|
| 0 | Healthy | 1% | 7 days |
| 1 | Risk Factors | 3% | 14 days |
| 2 | Chronic condition | 12% | 28 days |
| 3 | Complication | 35% | 42 days |
| 4 | Major event | 80% | 120 days |

**Adipositas (E66.0) — Prevalence 24% (RKI DEGS1 2012)**

| Stage | State | P(AU/year) | E[duration] |
|:---:|-------|:---:|:---:|
| 0 | Normal weight | 1% | 5 days |
| 1 | Overweight | 2% | 10 days |
| 2 | Obesity | 8% | 21 days |
| 3 | Complication | 25% | 45 days |

**Rückenschmerzen (M54) — Prevalence 25% (RKI GEDA 2019)**

| Stage | State | P(AU/year) | E[duration] |
|:---:|-------|:---:|:---:|
| 0 | No symptoms | 1% | 3 days |
| 1 | Acute | 15% | 14 days |
| 2 | Chronic | 40% | 35 days |
| 3 | Invalidity | 75% | 90 days |

Notice: back pain is often more expensive for KTG than hypertension because the acute → chronic transition drives AU probability from 15% to 40%, and chronic episodes last 35 days.

### 9.3 The Pricing Formula

For a given time horizon (e.g., 10 years):

**Step 1:** Compute state occupation probabilities at year 10 using the CTMC:
```
P(state i at time t) = [expm(Q × t)]_{initial_state, i}
```

**Step 2:** Apply age adjustment:
```
age_multiplier = 0.7 + (age - 30) × 0.02
```
(0.7 at age 30, 1.0 at age 45, 1.4 at age 65)

**Step 3:** Compute expected annual KTG cost:
```
total = Σᵢ P(state i) × P(AU|state i) × age_mult × E[duration|state i] × daily_rate
```

**Step 4:** Add surcharges:
```
monthly_premium = total × 1.15 (safety) × 1.12 (admin) / 12
```

### 9.4 Worked Example: Hypertonie, Age 50, EUR 80/day, 10-year Horizon

Assume state occupation at year 10 (starting from Risk Factors):

| State | P(state) | P(AU) × age_mult | E[days] | Expected Cost |
|:---:|:---:|:---:|:---:|:---:|
| Healthy | 10% | 1% × 1.0 | 7 | EUR 0.70 |
| Risk Factors | 40% | 3% × 1.0 | 14 | EUR 13.44 |
| Chronic | 35% | 12% × 1.0 | 28 | EUR 94.08 |
| Complication | 12% | 35% × 1.0 | 42 | EUR 141.12 |
| Major Event | 3% | 80% × 1.0 | 120 | EUR 230.40 |
| **Total** | | | | **EUR 479.74** |

With surcharges: EUR 479.74 × 1.15 × 1.12 = **EUR 617.67/year → EUR 51.47/month**

(The exact numbers depend on CTMC intensities and starting state — this is illustrative.)

### 9.5 DQS Impact on Pricing Certainty

This is where Chapter 7 meets Chapter 9.

**Complete data (DQS 0.85):** Three antihypertensives documented, BP measured, HbA1c and lipid panel available. Stage clearly determined → **narrow premium band.**

**Sparse data (DQS 0.40):** Only diagnosis code I10, no meds, no BP readings, no labs. Stage could be anywhere from 1 (risk factors) to 4 (major event) → **premium range up to 3x.**

The same ICD code (I10) produces fundamentally different pricing confidence depending on data completeness. This is the business case for DQS.

### 9.6 Advanced Methods in the KTG Calculator

The Streamlit KTG page also demonstrates three advanced ML methods:

1. **Conformal prediction** (`src/medrisk/validation/conformal.py`) — guaranteed prediction intervals with selectable coverage (80-99%). Instead of a point estimate (EUR 480/year), you get a range (EUR 380-620/year at 90% coverage).

2. **Survival curves** — individual P(arbeitsfähig) over time with confidence bands from the Cox PH model.

3. **Causal ML via IPW** (`src/medrisk/evaluation/treatment_effect.py`) — estimates the treatment effect of medication compliance. Example: medication compliance reduces AU days by ~12 days/year (ATE with 95% CI).

> **Try it yourself:**
> 1. In the Streamlit app (Page 5), set Hypertonie, age 50, daily rate EUR 80, horizon 10 years. What monthly premium does it compute?
> 2. Switch to Rückenschmerzen. Why is back pain often more expensive for KTG?
> 3. Look at the "Datenqualität" section. Why does identical ICD code I10 produce up to 3x risk variance depending on data completeness?

---

## Chapter 10: The Underwriting Decision Engine

*~8 min | Advanced*

**Learning Objectives:**
- Understand how automated underwriting decisions are made from diagnosis codes
- Know the clinical consistency checks that validate applicant data
- Trace the most-restrictive-profile-wins decision logic

### 10.1 From Risk Score to Decision

Chapters 5-8 compute a risk score and flag potential errors. But the underwriter's final output is a **decision**: accept, accept with loading, accept with exclusion, postpone, or decline. The `UnderwritingEngine` (`src/medrisk/underwriting/decision_engine.py`) automates this.

**Decision hierarchy (most restrictive wins):**

| Decision | Meaning | Example |
|----------|---------|---------|
| **accept** | Standard terms | Controlled hypertension, no comorbidities |
| **accept_loading** | Premium surcharge (e.g., +50%) | Diabetes with good HbA1c control |
| **accept_exclusion** | Cover granted but specific condition excluded | History of back surgery |
| **postpone** | Defer decision, request more information | Recent psychiatric episode, need 2-year stability |
| **decline** | Reject application | Active cancer, severe multi-organ disease |

When multiple conditions apply, the engine takes the **most restrictive** outcome. A patient with well-controlled hypertension (accept) and recent depression (postpone) gets postponed.

### 10.2 Disease Profiles

Each underwriting-relevant condition is defined as a `DiseaseProfile` in `src/medrisk/underwriting/profiles.py`, loaded from YAML configuration (`configs/underwriting_profiles.yml`):

- **ICD code patterns** — which codes match this profile
- **Base decision** — default outcome for this condition
- **Prognostic factors** — modifiers based on age, lab values, medication compliance, episode count
- **Evidence tier** — what documentation level is needed (self-report, GP letter, specialist report)

### 10.3 Clinical Consistency Checks

Before making a decision, 6 independent checks validate the application data (`src/medrisk/underwriting/clinical_checks.py`):

| Check | What It Catches | Example |
|-------|-----------------|---------|
| **Drug-diagnosis consistency** | Medications without matching diagnoses | On metformin but no diabetes code |
| **Coding specificity** | Unspecific codes that prevent risk assessment | I48.9 (AF, unspecified) instead of I48.0 (paroxysmal) |
| **Comorbidity patterns** | Missing expected comorbidities | Diabetes without any renal or cardiovascular monitoring |
| **Temporal patterns** | Suspicious timing in medical history | 3+ psychiatric episodes, AU >8 weeks, recent surgery |
| **Missing data** | Critical information gaps | No lab values for a diabetic applicant |
| **Clinical red flags** | High-risk patterns requiring expert review | Chronic pain with opioid use, inpatient psychiatric admission |

Each check returns structured findings that feed into the decision and audit trail.

### 10.4 Temporal Risk Assessment

Not all diagnoses are equally relevant today. The temporal module (`src/medrisk/underwriting/temporal.py`) applies:

- **Time decay** — a psychiatric episode 5 years ago is less relevant than one 6 months ago
- **Lookback windows** — some conditions only count within specific timeframes (e.g., cancer within 5 years)
- **Remission assessment** — certain conditions can be considered resolved after sufficient stability periods
- **Red flag categories** — conditions that always require expert review regardless of age (e.g., multiple sclerosis, organ transplant)

### 10.5 The Underwriting Simulator

Page 6 of the Streamlit app (`app/pages/6_Underwriting_Simulator.py`) turns this into an interactive exercise: you see a case study with diagnosis codes, medications, and lab values, then make your underwriting decision before the engine reveals its answer. This is the same format used in PKV underwriting training.

Page 7 (`app/pages/7_KTG_Flashcards.py`) provides quick-reference flashcards covering clinical thresholds, ICD-10 codes, failure modes, comorbidity interactions, and regulatory knowledge — ideal for self-study and domain referencearation.

> **Try it yourself:**
> 1. Open Page 6 (Underwriting Simulator). Work through 3 case studies. How often did your decision match the engine's?
> 2. In `clinical_checks.py`, find the drug-diagnosis consistency check. What happens if a patient is on rivaroxaban (B01AF01) without an atrial fibrillation code?
> 3. Why does the engine use "most restrictive wins" instead of averaging across conditions?

---

## Chapter 11: Actuarial Reserving and Sickness Absence Modeling

*~8 min | Advanced*

**Learning Objectives:**
- Understand Chain-Ladder and Bornhuetter-Ferguson reserve estimation
- Know how sickness absence frequency and duration are modeled
- Connect actuarial reserves to underwriting decisions

### 11.1 Why Reserves Matter

An insurer collects premiums today to pay claims tomorrow. **Reserves** are the estimated future cost of claims already incurred but not yet fully reported (IBNR — Incurred But Not Reported). Getting reserves wrong means either:
- **Under-reserving** → solvency risk, regulatory intervention
- **Over-reserving** → capital inefficiency, competitive disadvantage

### 11.2 Chain-Ladder Method

The Chain-Ladder method (`src/medrisk/models/actuarial.py`) estimates ultimate claims from a **development triangle** — a matrix where rows are accident years and columns are development periods:

**Step 1:** Compute development factors from historical data:
```
f_k = Σ C[i, k+1] / Σ C[i, k]   (volume-weighted average)
```

**Step 2:** Project incomplete years by multiplying the latest observed value by remaining factors.

**Step 3:** Reserve = projected ultimate − already paid.

**Limitation:** Chain-Ladder assumes past development patterns will repeat. It performs poorly for recent accident years with little development history.

### 11.3 Bornhuetter-Ferguson Method

BF (`src/medrisk/models/actuarial.py`) addresses Chain-Ladder's instability by blending reported data with a prior estimate:

```
BF_ultimate = reported + prior × (1 − 1/CDF)
```

Where `prior` is an external estimate (e.g., from pricing) and `CDF` is the cumulative development factor. BF is more stable for recent years because it doesn't rely solely on sparse reported data.

### 11.4 Sickness Absence Models

The `sickness_absence.py` module models AU frequency and duration separately:

**Frequency** — Negative Binomial regression:
```
log(μ) = β₀ + β₁·age + β₂·male + β₃·MRS + β₄·log(occ_risk)
```
Where MRS is the MedRisk Score and occ_risk is the occupational risk class (1-4, with multipliers 1.0, 1.25, 1.60, 2.10).

**Duration** — Weibull Accelerated Failure Time model:
```
S(t) = exp(−(t/λ)^k)     E[T] = λ · Γ(1 + 1/k)
```
Models the probability of still being on sick leave at time t, and the expected total duration.

**GKV Reference Table** — Population-baseline sickness absence rates by age/sex from statutory health insurance data, used to benchmark individual predictions against population norms.

### 11.5 Aggregate Claims Distribution

For portfolio-level risk, Panjer recursion computes the compound distribution of total claims:
- **Frequency:** Negative Binomial (allows overdispersion vs. Poisson)
- **Severity:** Weibull (flexible shape for claim durations)
- **Aggregate:** Recursive convolution via (a,b,0) class

This feeds into Solvency II capital requirements and reinsurance pricing.

> **Try it yourself:**
> 1. In `actuarial.py`, trace the Chain-Ladder computation. What does a development factor of 1.15 mean in plain language?
> 2. Compare Chain-Ladder vs. BF reserves for the most recent accident year. Why does BF produce a more stable estimate?
> 3. Using `sickness_absence.py`, predict AU frequency for a 55-year-old male in occupational risk class 3 with MRS = 0.7.

---

## Chapter 12: The Full Pipeline and Validation

*~10 min | Advanced — Capstone*

**Learning Objectives:**
- Trace data through the full MedRisk-ADH v2 pipeline
- Understand the audit trail and governance requirements
- Know the validation roadmap from synthetic to real data

### 12.1 Pipeline Architecture

The `MedRiskPipeline` class (`src/medrisk/pipeline.py`) orchestrates the complete flow:

```
PatientRecord → DataFrame → Feature Matrix → Data Profiles → DQS v2
                                                                 ↓
Audit Log ← Reliability Head ← Router Predictions ← Model Router (trained)
```

### 12.2 Step-by-Step Walkthrough

| Step | Component | Source File | What Happens |
|:---:|-----------|-------------|-------------|
| 1 | Cohort generation | `data/synthetic.py` | Generate or accept patient records |
| 2 | DataFrame conversion | `data/synthetic.py` | PatientRecords → pandas DataFrame |
| 3 | Feature matrix | `features/engineering.py` | Extract ~40 features (no imputation) |
| 4 | Data profiling | `features/data_profile.py` | Classify each patient: FULL/NO_LABS/... |
| 5 | DQS v2 | `validation/data_quality.py` | Per-patient quality assessment |
| 6 | Model Router training | `models/model_router.py` | Train separate XGBoost per profile |
| 7 | Predictions | `models/model_router.py` | Route each patient to appropriate model |
| 8 | Reliability Head | `validation/reliability_head.py` | Compute P(wrong), cost-optimal decisions |
| 9 | Clinical checks | `underwriting/clinical_checks.py` | Drug-diagnosis consistency, red flags |
| 10 | Underwriting decision | `underwriting/decision_engine.py` | Most-restrictive-profile-wins logic |
| 11 | Audit logging | `governance/audit_log.py` | Write every decision to JSON Lines |

Each step builds on earlier chapters: Step 3 uses the coding knowledge from Chapter 3, Step 4 uses the market awareness from Chapter 2, Step 5 uses the DQS from Chapter 7, Step 6 avoids imputation as discussed in Chapter 5, Step 8 applies the cost-asymmetric logic from Chapter 8, and Steps 9-10 implement the underwriting decision engine from Chapter 10.

### 12.3 The Audit Trail

The `AuditLogger` (`src/medrisk/governance/audit_log.py`) writes one JSON object per patient per decision to an append-only JSON Lines file. Each `AuditEntry` contains:

| Field | Purpose |
|-------|---------|
| `timestamp`, `run_id` | When and which batch run |
| `patient_id`, `market` | Who and where |
| `data_profile`, `model_id` | Which model was used |
| `features_used`, `features_missing` | What the model saw (and didn't) |
| `dqs`, `dqs_tier`, `dqs_components` | Data quality assessment |
| `predicted_probability` | Model output |
| `reliability_decision`, `p_wrong` | Final decision and confidence |
| `explanation` | Human-readable reasoning |
| `human_override` | If/when a human overrode the model |

This directly supports **EU AI Act Art. 12** (record-keeping) — every automated decision has a complete, traceable audit trail.

### 12.4 Human Override

When a human underwriter disagrees with the model, the override is logged via `src/medrisk/governance/human_override.py`:

```python
HumanOverride(
    patient_id="...",
    original_decision="accept",
    override_decision="human_review",
    reason="Lab values inconsistent with diagnosis history",
    overrider_id="UW-12345",
)
```

This supports **EU AI Act Art. 14** (human oversight) and creates a feedback loop — override patterns can identify systematic model failures.

### 12.5 Distribution Shift Detection

Models degrade when the input population changes. `src/medrisk/validation/shift_detection.py` monitors for this using:

- **PSI (Population Stability Index)** — compares feature distributions between training and production. Threshold: 0.20 (major shift).
- **Jensen-Shannon divergence** — symmetric measure of distribution difference. Threshold: 0.10.

When shift is detected, the model should be recalibrated or retrained.

### 12.6 Validation Roadmap

| Phase | Status | Data | Goal |
|-------|:------:|------|------|
| **Phase 1** | Complete | Synthetic (4,000 patients) | Demonstrate mechanism works |
| **Phase 2** | Planned | Real (CPRD, InGef, PKV) | Validate thresholds against claims |
| **Phase 3** | Vision | Production (a major European insurer internal) | Deploy with monitoring |

**Phase 1 limitations (honest assessment):**
- Performance metrics are synthetic-only — AUC 0.71 may not hold on real data
- DQS thresholds (0.60/0.80) are heuristic, not empirically validated against claims outcomes
- Consistency rules are simplified — real clinical validation is much harder
- Comorbidity links are approximations from published meta-analyses, not derived from data

**What Phase 2 requires:**
- Minimum 50,000 patients with 5+ years follow-up and known outcomes
- Linked diagnoses + labs + medications + claims outcomes
- Legal basis: DSGVO Art. 89 (research exemption) + institutional ethics vote
- Timeline: 3-6 months from data access to validated thresholds

**The bottleneck is not engineering — it's data access and regulatory clearance.**

### 12.7 What You Have Built

MedRisk-ADH is a **regulatory-ready skeleton** that demonstrates:

- 442 passing tests across all components
- 4 European markets with realistic data quality variance
- 2 disease progression models (cardiovascular + Alzheimer)
- 5 Jupyter notebooks documenting the complete pipeline
- 7 Streamlit pages (Patient Assessment, PBW Comparison, Portfolio Dashboard, Alzheimer Progression, KTG Kalkulation, Underwriting Simulator, KTG Flashcards)
- 8 external data adapters for real-world cohort ingestion
- Automated underwriting decision engine with clinical consistency checks
- Chain-Ladder/BF actuarial reserving and sickness absence models
- Full explainability (SHAP) for every prediction
- Audit trail and human override logging

It answers the question: "Can we detect when an AI underwriting model is confidently wrong?" The answer is yes, on synthetic data. Phase 2 answers: "Does this detection work on real claims?"

> **Try it yourself:**
> 1. Run Notebook 05 (`notebooks/05_underwriting_report.ipynb`) end-to-end. How many patients are flagged for human review?
> 2. Look at the audit log output. Find a patient with decision="human_review". What was the DQS? What was P(wrong)?
> 3. If deploying to production, what is the first thing you'd need that synthetic data cannot provide? (Answer: validated thresholds calibrated against real claims outcomes.)

---

## Appendix A: Quick Reference Tables

### A.1 Charlson Comorbidity Index (17 Categories)

| # | Category | Weight | Key ICD-10 Prefixes |
|:-:|----------|:------:|---------------------|
| 1 | Myocardial infarction | 1 | I21, I22, I25.2 |
| 2 | Congestive heart failure | 1 | I50, I42, I43 |
| 3 | Peripheral vascular disease | 1 | I70, I71, I73 |
| 4 | Cerebrovascular disease | 1 | I60-I68, G45, G46 |
| 5 | Dementia | 1 | F00-F03, G30 |
| 6 | Chronic pulmonary disease | 1 | J40-J47, J60-J67 |
| 7 | Rheumatic disease | 1 | M05, M06, M32-M36 |
| 8 | Peptic ulcer disease | 1 | K25-K28 |
| 9 | Mild liver disease | 1 | B18, K70-K76 |
| 10 | Diabetes, uncomplicated | 1 | E10-E14 (excl. .2-.7) |
| 11 | Diabetes, complicated | 2 | E10.2-E14.7 |
| 12 | Hemiplegia/paraplegia | 2 | G81-G83 |
| 13 | Renal disease | 2 | N18, N19, I12.0 |
| 14 | Any malignancy | 2 | C00-C97 (excl. C77-C80) |
| 15 | Moderate/severe liver disease | 3 | I85, K70.4, K72 |
| 16 | Metastatic solid tumor | 6 | C77-C80 |
| 17 | AIDS/HIV | 6 | B20-B24 |

**Hierarchy rules:** #11 supersedes #10 | #15 supersedes #9 | #16 supersedes #14

### A.2 Lab Reference Ranges

| Lab | LOINC | Unit | Ref Low | Ref High |
|-----|-------|------|:-------:|:--------:|
| HbA1c | 4548-4 | % | 4.0 | 5.6 |
| Creatinine | 2160-0 | mg/dL | 0.6 | 1.2 |
| eGFR | 48642-3 | mL/min | 60 | 120 |
| Total Cholesterol | 2093-3 | mg/dL | 125 | 200 |
| HDL | 2085-9 | mg/dL | 40 | 60 |
| LDL | 13457-7 | mg/dL | 0 | 100 |
| Triglycerides | 2571-8 | mg/dL | 0 | 150 |
| Systolic BP | 8480-6 | mmHg | 90 | 120 |
| Diastolic BP | 8462-4 | mmHg | 60 | 80 |
| NT-proBNP | 33762-6 | pg/mL | 0 | 125 |
| MMSE | 72106-8 | score | 24 | 30 |
| MoCA | 72172-0 | score | 26 | 30 |
| CSF Ab42 | 33203-1 | pg/mL | 600 | 1500 |
| CSF p-tau181 | 72260-3 | pg/mL | 0 | 22 |

### A.3 Market Configuration Parameters

| Parameter | DE | ES | FR | INT |
|-----------|:---:|:---:|:---:|:---:|
| Coding completeness | 0.95 | 0.80 | 0.90 | 0.60 |
| Lab completeness | 0.92 | 0.75 | 0.88 | 0.50 |
| Lab noise sigma | 0.02 | 0.05 | 0.03 | 0.10 |
| Diagnosis lag (days) | 14 ± 7 | 30 ± 20 | 60 ± 30 | 90 ± 60 |
| Medication recording | 0.95 | 0.80 | 0.88 | 0.60 |
| Age (mean ± std) | 52 ± 14 | 56 ± 16 | 54 ± 15 | 50 ± 18 |

### A.4 Cost and Threshold Parameters

| Parameter | Value | Source |
|-----------|:-----:|--------|
| DQS weight: completeness (alpha) | 0.40 | `data_quality.py` |
| DQS weight: consistency (beta) | 0.35 | `data_quality.py` |
| DQS weight: recency (gamma) | 0.25 | `data_quality.py` |
| Recency half-life | 1.4 years | `data_quality.py` |
| DQS tier: adequate | >= 0.80 | `data_quality.py` |
| DQS tier: caution | >= 0.60 | `data_quality.py` |
| CCM threshold | 0.20 | `failure_detection.py` |
| EPU threshold | 3 deciles | `failure_detection.py` |
| PBW confidence threshold | 0.80 | `failure_detection.py` |
| PBW DQS threshold | 0.60 | `failure_detection.py` |
| Cost: false negative (cost_fn) | 5.0 | `reliability_head.py` |
| Cost: false positive (cost_fp) | 1.0 | `reliability_head.py` |
| Cost: human review | 0.5 | `reliability_head.py` |

---

## Appendix B: German-English Glossary

| German | English |
|--------|---------|
| Arbeitsunfähigkeit (AU) | Work incapacity |
| Beitrag | Premium |
| Datenschutz-Grundverordnung (DSGVO) | GDPR |
| Erkrankung | Disease / condition |
| Gesetzliche Krankenversicherung (GKV) | Statutory health insurance |
| Krankenkasse | Health insurance fund |
| Krankentagegeld (KTG) | Daily sickness benefit |
| Leistungsfall | Benefit event / claim |
| Nachversicherung | Supplementary insurance |
| Private Krankenversicherung (PKV) | Private health insurance |
| Risikoprüfung | Risk assessment / underwriting |
| Rückstellung | Reserve (actuarial) |
| Selbstbehalt | Deductible |
| Stadien | Stages (disease severity) |
| Tarifgestaltung | Tariff design / pricing |
| Übergangsrate | Transition rate |
| Versicherungsnehmer | Policyholder |
| Versicherungsvertrag | Insurance contract |
| Vorerkrankung | Pre-existing condition |
| Wartezeit | Waiting period |
| Deckungsrückstellung | Coverage reserve (life/health) |
| Schadenreserve | Claims reserve (P&C) |
| Berufsunfähigkeit (BU) | Occupational disability |
| Risikoklasse | Risk class / occupational risk category |
| Zuschlag | Premium loading / surcharge |

---

## Appendix C: Further Reading

| Reference | Relevance |
|-----------|-----------|
| Quan et al. (2005), "Coding algorithms for defining comorbidities in ICD-9-CM and ICD-10 administrative data", *Medical Care* | Charlson Index ICD-10 adaptation |
| Petersen et al. (2018), "Practice guideline update: MCI", *Neurology* | MCI → AD conversion rates |
| Brookmeyer et al. (2007), "Forecasting the global burden of Alzheimer's disease", *Alzheimer's & Dementia* | AD survival estimates |
| Hernan & Robins (2020), *Causal Inference: What If* | Causal ML foundations (IPW) |
| Vovk et al. (2005), *Algorithmic Learning in a Random World* | Conformal prediction theory |
| Angelopoulos & Bates (2023), "Conformal Prediction: A Gentle Introduction", *Foundations and Trends in ML* | Modern conformal methods |
| EU AI Act (2024), Regulation (EU) 2024/1689 | Regulatory framework for high-risk AI |
| Guo et al. (2017), "On Calibration of Modern Neural Networks", *ICML* | Calibration and confidence |
| Platt (1999), "Probabilistic Outputs for SVMs and Comparisons to Regularized Likelihood Methods" | Platt calibration |
| van Walraven et al. (2009), "A modification of the Elixhauser comorbidity measures", *Medical Care* | Elixhauser scoring weights |
| Mack (1993), "Distribution-free Calculation of the Standard Error of Chain Ladder Reserve Estimates", *ASTIN Bulletin* | Chain-Ladder theory and Mack standard errors |
| Bornhuetter & Ferguson (1972), "The Actuary and IBNR", *PCAS* | BF reserve estimation method |
| GBD 2019 Diseases and Injuries Collaborators, *The Lancet* | Global disease prevalence data |
