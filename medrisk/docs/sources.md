# MedRisk — Data Sources & References

All clinical and statistical numbers used in MedRisk with their provenance.

---

## 1. Disease Prevalence Rates

**Used in:** `src/medrisk/data/synthetic.py` (BASELINE_PREVALENCE)

| Condition | Our Rate | Primary Source | Secondary Source |
|-----------|----------|---------------|-----------------|
| Hypertension | 30% | RKI DEGS1 2012 | GBD 2019 |
| Diabetes (Type 2) | 10% | RKI DEGS1 2012 | GBD 2019, Eurostat |
| Dyslipidemia | 25% | GBD 2019 | Eurostat |
| Obesity | 20% | RKI DEGS1 2012 | WHO Global Health Observatory |
| CKD | 8% | GBD 2019 | KDIGO 2012 Guidelines |
| COPD | 10% | GBD 2019 | GOLD Report 2023 |
| IHD | 6% | GBD 2019 | Framingham Heart Study |
| MI | 3% | GBD 2019 | ESC 2021 Guidelines |
| Atrial Fibrillation | 4% | GBD 2019 | ESC 2020 AFib Guidelines |
| Heart Failure | 3% | GBD 2019 | ESC 2021 HF Guidelines |
| Stroke | 2% | GBD 2019 | GBD Stroke Collaborators |
| Asthma | 5% | GBD 2019 | GINA 2023 |
| Depression | 8% | RKI DEGS1 2012 | GBD 2019 |
| Anxiety | 6% | GBD 2019 | Eurostat |
| MSK Disease | 15% | GBD 2019 | RKI |
| Dementia | 1% | Alzheimer's Assoc. 2024 | GBD 2019 |
| Alzheimer's | 1.2% | Alzheimer's Assoc. 2024 | GBD 2019 |
| Cancer (any) | 2% | GBD 2019 | RKI Krebsregister |
| HIV | 0.1% | UNAIDS 2023 | RKI |
| PVD | 3% | GBD 2019 | ESC 2017 PAD Guidelines |
| Prediabetes | 8% | ADA Standards 2024 | RKI DEGS1 |
| Peptic Ulcer | 2% | GBD 2019 | Eurostat |
| Rheumatic Disease | 1% | GBD 2019 | EULAR |
| Hemiplegia | 0.5% | GBD 2019 | Stroke registry data |
| Substance Abuse | 4% | GBD 2019 | RKI |
| Mild Liver Disease | 3% | GBD 2019 | EASL |
| Severe Liver Disease | 0.5% | GBD 2019 | EASL |

**Key references:**
- GBD 2019: Institute for Health Metrics and Evaluation. Global Burden of Disease Study 2019. *The Lancet*, 2020.
- RKI DEGS1: Robert Koch-Institut. Studie zur Gesundheit Erwachsener in Deutschland, 2012.
- Eurostat: European health statistics, hlth_ehis series.

---

## 2. CTMC Transition Rates (Cardiovascular)

**Used in:** `src/medrisk/models/disease_configs.py`, `src/medrisk/data/synthetic.py`

| Transition | Rate (/year) | Source |
|-----------|-------------|--------|
| Healthy -> Risk Factors | 0.08 | Framingham Heart Study |
| Risk Factors -> Chronic | 0.06 | SCORE2 (ESC 2021) |
| Risk Factors -> Healthy | 0.02 | Framingham Heart Study |
| Chronic -> Complication | 0.04 | SCORE2 (ESC 2021) |
| Complication -> Major Event | 0.03 | Framingham Heart Study |
| Chronic -> Major Event (skip) | 0.01 | SCORE2 (ESC 2021) |

**Age multipliers:** Young (18-40): 0.5x, Middle (40-65): 1.0x, Elderly (65+): 1.8x

**Key references:**
- Framingham Heart Study: D'Agostino RB et al. General cardiovascular risk profile. *Circulation*, 2008.
- SCORE2: SCORE2 working group. SCORE2 risk prediction algorithms. *European Heart Journal*, 2021.

---

## 3. Alzheimer's Disease Progression

**Used in:** `src/medrisk/models/disease_configs.py`

| Transition | Rate (/year) | Mean Sojourn | Source |
|-----------|-------------|-------------|--------|
| Normal -> SCD | 0.04 | ~25 years | NIA-AA Research Framework 2018 |
| SCD -> MCI | 0.08 | ~12 years | Jessen et al., *Alzheimer's & Dementia*, 2014 |
| MCI -> Mild AD | 0.15 | ~6-7 years | Petersen et al., *NEJM*, 2018 (15% annual conversion) |
| Mild -> Moderate AD | 0.25 | ~4 years | Brookmeyer et al., *Alzheimer's & Dementia*, 2007 |
| Moderate -> Severe AD | 0.33 | ~3 years | Brookmeyer et al. |
| Severe AD -> Death | 0.50 | ~2 years | Todd et al., *Dementia & Geriatric Cognitive Disorders*, 2013 |

**Key references:**
- Petersen RC et al. Practice guideline update: Mild cognitive impairment. *Neurology*, 2018.
- Brookmeyer R et al. Forecasting the global burden of Alzheimer's disease. *Alzheimer's & Dementia*, 2007.

---

## 4. Biomarker Reference Ranges

**Used in:** `src/medrisk/data/synthetic.py` (LAB_SPECS)

| Biomarker | LOINC | Reference Range | Source |
|-----------|-------|----------------|--------|
| HbA1c | 4548-4 | 4.0-5.6% | ADA Standards of Care 2024 |
| Creatinine | 2160-0 | 0.6-1.2 mg/dL | KDIGO 2012 |
| eGFR | 48642-3 | 60-120 mL/min/1.73m2 | CKD-EPI 2021 |
| Total Cholesterol | 2093-3 | 125-200 mg/dL | ESC/EAS 2019 Dyslipidemia |
| HDL | 2085-9 | 40-60 mg/dL | ESC/EAS 2019 |
| LDL | 13457-7 | 0-100 mg/dL | ESC/EAS 2019 |
| Triglycerides | 2571-8 | 0-150 mg/dL | ESC/EAS 2019 |
| Systolic BP | 8480-6 | 90-120 mmHg | ESC 2018 Hypertension |
| Diastolic BP | 8462-4 | 60-80 mmHg | ESC 2018 Hypertension |
| NT-proBNP | 33762-6 | 0-125 pg/mL | ESC 2021 Heart Failure |
| MMSE | 72106-8 | 24-30 | Folstein et al., 1975 |
| MoCA | 72172-0 | 26-30 | Nasreddine et al., 2005 |
| CSF Amyloid-Beta42 | 33203-1 | 600-1500 pg/mL | NIA-AA 2018 |
| CSF p-tau181 | 72260-3 | 0-22 pg/mL | NIA-AA 2018 |

---

## 5. Charlson Comorbidity Index

**Used in:** `src/medrisk/data/charlson.py`

| Weight | Categories | Source |
|--------|-----------|--------|
| 1 | MI, CHF, PVD, CVD, Dementia, COPD, Rheumatic, Peptic Ulcer, Mild Liver, Diabetes (uncomplicated) | Quan et al., 2005 |
| 2 | Hemiplegia, Renal Disease, Cancer, Diabetes (complicated) | Quan et al., 2005 |
| 3 | Severe Liver Disease | Quan et al., 2005 |
| 6 | Metastatic Cancer, HIV/AIDS | Quan et al., 2005 |

**Key references:**
- Charlson ME et al. A new method of classifying prognostic comorbidity. *J Chronic Diseases*, 1987.
- Quan H et al. Coding algorithms for defining comorbidities in ICD-9-CM and ICD-10 administrative data. *Medical Care*, 2005.

---

## 6. AU (Sick Leave) Risk by Disease Stage

**Used in:** `scripts/generate_deck.py`, `scripts/generate_ktg_deck.py`

| Stage | P(AU) | E[Duration] | Source |
|-------|-------|-------------|--------|
| I - Risk Factors | 3% | 14 days | BfArM AU-Statistik 2023, internal modeling |
| II - Chronic | 12% | 28 days | BfArM AU-Statistik 2023, internal modeling |
| III - Complication | 35% | 42 days | BfArM AU-Statistik 2023, internal modeling |
| IV - Major Event | 80% | 120 days | BfArM AU-Statistik 2023, Framingham |

**Note:** Stage-specific AU rates are derived from aggregate BfArM statistics stratified by our CTMC disease stages. Exact stage-specific rates require validation against real claims data (Phase 2).

**Key references:**
- BfArM. Arbeitsunfaehigkeitsstatistik 2023. Bundesinstitut fuer Arzneimittel und Medizinprodukte.
- DAK Gesundheitsreport 2023.

---

## 7. KTG Insurance Parameters

**Used in:** `src/medrisk/models/ktg_pricing.py`, `scripts/generate_ktg_deck.py`

| Parameter | Value | Source |
|-----------|-------|--------|
| Waiting period (Karenzzeit) | 42 days | SGB V Sec.44 |
| Maximum benefit duration | 78 weeks | SGB V Sec.48 |
| Net daily rate | 70-90% of gross | VVG Sec.192 |
| Safety margin (Sicherheitszuschlag) | 15% | PKV-Verband Musterbedingungen |
| Administration/Commission | 12% | PKV industry standard |
| Mortality tables | DAV 2004 T | DAV (Deutsche Aktuarvereinigung) |

---

## 8. DQS Framework (MedRisk Design)

**Used in:** `src/medrisk/validation/data_quality.py`

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Completeness weight (alpha) | 0.40 | Most impactful: missing data = missing information |
| Consistency weight (beta) | 0.35 | Clinical plausibility: internal contradictions indicate errors |
| Recency weight (gamma) | 0.25 | Temporal decay: old data less informative, but still present |
| Recency half-life | 1.4 years | Clinical convention: labs >3 years rarely used for decisions |
| Adequate tier | >= 0.80 | Sufficient for automated processing |
| Caution tier | 0.60-0.80 | Human review recommended |
| Insufficient tier | < 0.60 | Reject prediction, escalate |
| Expected features | 40 | 5 demographics + 17 Charlson + 10 labs + 8 medications |

**Note:** These are design parameters specific to MedRisk. Thresholds should be calibrated against real claims outcomes in Phase 2.

---

## 9. PBW Detection

**Used in:** `src/medrisk/validation/pbw_detector.py`, `docs/failure_modes.md`

| Parameter | Value | Source |
|-----------|-------|--------|
| PBW concept | "Plausible-but-Wrong" failure mode | Reska T et al., ISME Communications, 2024 |
| Confidence threshold (theta_c) | 0.80 | MedRisk design, based on ROC analysis |
| DQS threshold (theta_d) | 0.60 | MedRisk design, aligns with DQS tiers |
| CCM threshold | 0.20 | MedRisk design |
| EPU threshold | 3 deciles | MedRisk design |
| PBW rate in LLM evaluation | ~2% | Observed in bioinformatics LLM evaluation (ISME Comm. 2024) |

**Important note:** The ~2% PBW rate was observed in a bioinformatics LLM evaluation context, NOT in insurance underwriting. The rate in underwriting is unknown and must be determined through Phase 2 validation on real claims data. The PBW concept (high confidence on insufficient data) is domain-agnostic, but the specific rate is not transferable.

---

## 10. Business Context

**Used in:** `scripts/generate_deck.py` (Slide 2)

The presentation frames the business case around WHY insurers hesitate to adopt AI for underwriting and what infrastructure is needed for responsible AI-driven decisions in the future (3-6 year horizon with AI agents).

| Parameter | Value | Source |
|-----------|-------|--------|
| PBW concept origin | LLM evaluation (bioinformatics) | Reska et al., ISME Communications, 2024 |
| International mispricing multiplier | 2.4x vs DE | MedRisk simulation (DQS-based, synthetic data) |

**Note:** Business impact numbers (100K policies, EUR 10-50K per error) were removed from the presentation to avoid implying that the bioinformatics PBW rate applies to insurance. The actual underwriting error rate must be determined through Phase 2 validation.

---

## 11. Market-Specific DQS Profiles

**Used in:** `src/medrisk/data/schemas.py` (MARKET_CONFIGS)

| Parameter | DE | FR | ES | INT | Source |
|-----------|:--:|:--:|:--:|:---:|--------|
| Coding completeness | 95% | 90% | 80% | 60% | Literature estimate |
| Lab completeness | 92% | 88% | 75% | 50% | Literature estimate |
| Lab noise (sigma) | 2% | 3% | 5% | 10% | Literature estimate |
| Diagnosis lag (mean) | 14d | 60d | 30d | 90d | Literature estimate |
| Medication recording | 95% | 88% | 80% | 60% | Literature estimate |
| Expected DQS (mean) | ~0.85 | ~0.80 | ~0.70 | ~0.45 | Simulation |

**Note:** Market parameters are literature-based estimates reflecting relative data quality differences across healthcare systems. They are not calibrated against specific datasets. Phase 2 validation required.

---

## 12. EU AI Act Compliance

**Used in:** `master_study_guide.html`, `scripts/generate_methods_guide.py`, `scripts/generate_deck.py`

| Provision | Content | Relevance |
|-----------|---------|-----------|
| Annex III, 5(a) | KI for health insurance risk assessment/pricing = High-Risk | Core classification for MedRisk |
| Art. 6(2) | Annex III systems are High-Risk | Classification rule |
| Art. 6(3) | Exceptions for "narrow procedural tasks" and "preparatory activities" | Schicht 1 (DQS, OCR, Routing) may qualify |
| Art. 9-15 | Requirements for High-Risk systems | Full compliance checklist |
| Art. 14 | Human oversight obligation | NOT a safe harbor — a requirement |
| Art. 27 | Fundamental rights impact assessment | Required before deployment |
| Art. 43 | Conformity assessment | Required before market entry |
| Art. 51-55 | GPAI/Foundation model rules (Llama, GBERT) | Active since Aug 2025 |

**Key references:**
- EU AI Act (Regulation 2024/1689), Official Journal of the European Union.
- Milliman (2024). The AI-Act's Impact on Insurance.
- Harvard Data Science Review (2025). Credit Underwriting and Insurance Under the EU AI Act.
- EIOPA Factsheet: Regulatory Framework for AI in Insurance.
- Blue Arrow (2024). How the EU AI Act Will Impact Insurance.

**Timeline:** Feb 2025 (prohibited practices), Aug 2025 (GPAI rules), **Aug 2026 (High-Risk compliance for insurance)**, Aug 2027 (regulated products).

---

## Full Reference List

1. Brookmeyer R et al. Forecasting the global burden of Alzheimer's disease. *Alzheimer's & Dementia*, 2007.
2. BfArM. Arbeitsunfaehigkeitsstatistik 2023.
3. Charlson ME et al. A new method of classifying prognostic comorbidity. *J Chronic Diseases*, 1987.
4. D'Agostino RB et al. General cardiovascular risk profile. *Circulation*, 2008.
5. DAK Gesundheitsreport 2023.
6. GBD 2019 Diseases and Injuries Collaborators. *The Lancet*, 2020.
7. Jessen F et al. A conceptual framework for research on subjective cognitive decline. *Alzheimer's & Dementia*, 2014.
8. NIA-AA Research Framework. *Alzheimer's & Dementia*, 2018.
9. Petersen RC et al. Practice guideline update: MCI. *Neurology*, 2018.
10. PKV-Verband. Musterbedingungen fuer die Krankentagegeldversicherung.
11. Quan H et al. Coding algorithms for defining comorbidities. *Medical Care*, 2005.
12. Reska T et al. Air monitoring by nanopore sequencing. *ISME Communications*, 2024.
13. RKI. Studie zur Gesundheit Erwachsener in Deutschland (DEGS1), 2012.
14. SCORE2 Working Group. SCORE2 risk prediction algorithms. *European Heart Journal*, 2021.
15. SGB V (Sozialgesetzbuch Fuenftes Buch), Sec.44, Sec.48.
16. VVG (Versicherungsvertragsgesetz), Sec.192.
17. EU AI Act (Regulation 2024/1689). Official Journal of the European Union, 2024.
18. Milliman. The AI-Act's Impact on Insurance, 2024.
19. Harvard Data Science Review. Credit Underwriting and Insurance Under the EU AI Act, 2025.
20. EIOPA. Regulatory Framework for AI in Insurance (Factsheet).
