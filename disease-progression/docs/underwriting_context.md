# Underwriting Context: Disease Progression Models for DACH Insurance

## Overview

This document provides context on the DACH insurance landscape and explains where disease progression models fit within the underwriting process. It covers the structure of health and life insurance in Germany, Austria, and Switzerland, identifies the insurance lines where medical underwriting applies, describes key endpoints for insurers, and provides cost structure references.

---

## 1. DACH Insurance Landscape

### Germany

Germany operates a dual health insurance system:

**Gesetzliche Krankenversicherung (GKV) -- Statutory Health Insurance:**
- Covers approximately 87% of the population.
- Community-rated: premiums are a percentage of income, not risk-adjusted.
- No medical underwriting at enrolment.
- Risk equalisation scheme (Morbi-RSA) transfers funds between insurers based on morbidity.
- Disease progression models are relevant for Morbi-RSA risk adjustment and disease management programme (DMP) targeting, but not for individual pricing.

**Private Krankenversicherung (PKV) -- Private Health Insurance:**
- Covers approximately 11% of the population (self-employed, civil servants, high earners above the Versicherungspflichtgrenze).
- Risk-rated at entry with full medical underwriting.
- Lifelong contracts with ageing reserves (Alterungsrueckstellungen).
- Medical underwriting uses health questionnaires covering the past 3-10 years of medical history.
- Disease progression models are directly relevant for initial risk assessment and surcharge calculation.

**Lebensversicherung -- Life Insurance:**
- Full medical underwriting for sums above simplified issue thresholds (typically EUR 150,000-300,000).
- Underwriting considers mortality risk, including cardiovascular and metabolic disease progression.
- Reinsurers provide underwriting manuals with excess mortality ratings by condition and severity.

**Berufsunfahigkeitsversicherung (BU) -- Disability Insurance:**
- Considered one of the most important personal insurance lines in Germany.
- Extensive medical underwriting with detailed health questionnaires.
- Key endpoint: inability to work in the insured's own occupation.
- Disease progression models are highly relevant, as chronic conditions (CVD, diabetes, mental health) are leading causes of disability claims.

### Austria

Austria's health insurance system is structured similarly to Germany's statutory model:

**Sozialversicherung -- Social Insurance:**
- Mandatory health insurance through occupational health insurance funds (e.g., OeGK -- Oesterreichische Gesundheitskasse).
- Community-rated; no medical underwriting.
- Covers approximately 99% of the population.

**Private Insurance:**
- Supplementary health insurance (Zusatzversicherung) provides private hospital rooms, choice of physician, and dental coverage.
- Medical underwriting applies, though typically less extensive than German PKV.
- Life and disability insurance follow similar underwriting principles as in Germany.

### Switzerland

Switzerland has a unique hybrid system:

**Obligatorische Krankenpflegeversicherung (OKP) -- Mandatory Health Insurance:**
- Universal coverage under the KVG/LAMal.
- Community-rated within each canton, with age bands (children, young adults, adults) and franchise (deductible) choices.
- No medical underwriting. Insurers must accept all applicants.
- Disease progression models are not applicable for OKP pricing but may inform reserving.

**Zusatzversicherung -- Supplementary Health Insurance:**
- Governed by the VVG (Insurance Contract Act), not the KVG.
- Full medical underwriting applies. Insurers may reject applicants or apply exclusions.
- Covers hospital upgrades (private/semi-private rooms), alternative medicine, dental, and international coverage.
- Disease progression models are relevant for risk assessment in supplementary lines.

**Life and Disability Insurance:**
- Medical underwriting applies for individual policies above simplified issue thresholds.
- The Swiss disability insurance system (IV -- Invalidenversicherung) provides a first-pillar safety net, with BVG (occupational pension) providing the second pillar. Private disability insurance is the third pillar.

---

## 2. Where Medical Underwriting Applies

| Insurance Line | DE | AT | CH | Underwriting Depth |
|---|---|---|---|---|
| Statutory health (GKV/OKP) | No UW | No UW | No UW | None |
| Private health (PKV) | Full UW | Moderate UW | Full UW (supplementary) | Health questionnaire, 3-10 year history |
| Life insurance | Full UW above threshold | Full UW above threshold | Full UW above threshold | Questionnaire + medical exams for high sums |
| Disability (BU/IV supplement) | Full UW | Full UW | Full UW | Most detailed; includes mental health history |
| Long-term care | Limited UW | Limited UW | Limited UW | Simplified underwriting |
| Critical illness | Full UW | Full UW | Full UW | Condition-specific exclusions |

Disease progression models are most relevant for PKV, life, disability, and critical illness insurance, where individual risk assessment directly affects pricing and acceptance decisions.

---

## 3. Key Endpoints for Insurers

Insurance underwriting evaluates the probability and cost of specific adverse outcomes. Disease progression models should predict endpoints that map directly to insurable events:

### Mortality (Life Insurance)
- **All-cause mortality**: The primary endpoint for life insurance pricing.
- **Cause-specific mortality**: CVD death vs non-CVD death allows competing risk analysis.
- **Excess mortality**: Expressed as a percentage above standard population mortality (e.g., "+150%" means 2.5x standard mortality).

### Disability (BU Insurance)
- **Occupational disability**: Inability to perform the insured's own occupation at >50% capacity.
- **CVD-related disability**: Post-MI cardiac rehabilitation failure, heart failure NYHA III-IV, post-stroke functional impairment.
- **Diabetes-related disability**: Severe hypoglycaemia, diabetic foot, dialysis, visual impairment from retinopathy.
- **Duration of disability**: Temporary vs permanent. Many BU claims are for limited periods.

### Morbidity (Health Insurance)
- **Hospitalisation**: Inpatient admission probability and length of stay.
- **Chronic care utilisation**: Ongoing outpatient visits, specialist referrals, lab monitoring.
- **Pharmaceutical costs**: Escalation from generic oral medications to biologics or device-based therapies.

### Competing Risks
In practice, insured individuals face multiple potential endpoints simultaneously:
- Death vs disability vs lapse (policy termination).
- CVD event vs diabetes complication vs other cause of death.
- Multistate models naturally handle these competing risks, making them well-suited for insurance applications.

### Lapse
Policy lapse (voluntary termination) is a competing risk that affects the insurer's exposure. Sicker policyholders may be less likely to lapse (anti-selection), which means that naive survival models ignoring lapse may underestimate risk in the remaining portfolio.

---

## 4. Cost Structure Overview

### German Reference Figures

**Inpatient Costs (InEK DRG-based):**

| Condition | DRG | Mean Cost (EUR) | Mean LOS (days) |
|---|---|---|---|
| Acute MI with PCI | F49A | 8,200 | 5.2 |
| Acute MI without PCI | F49B | 3,800 | 2.8 |
| Heart failure (complex) | F62A | 5,600 | 8.1 |
| Heart failure (standard) | F62B | 3,200 | 5.5 |
| Stroke with thrombolysis | B70A | 9,500 | 12.3 |
| Stroke without thrombolysis | B70B | 5,200 | 9.1 |
| Dialysis (complex) | L71A | 12,500 | 9.5 |
| Dialysis (standard) | L71B | 7,800 | 6.3 |

**Outpatient Costs (EBM-based, quarterly):**

| Category | Quarterly Cost (EUR) |
|---|---|
| General practitioner management | 40-60 |
| Cardiology specialist | 80-150 |
| Diabetology specialist | 60-120 |
| Nephrology (pre-dialysis) | 100-200 |
| DMP T2D quarterly visit | 30-50 |

**Pharmaceutical Costs (annual estimates):**

| Medication Class | Annual Cost (EUR) |
|---|---|
| Statins (generic) | 50-100 |
| ACE inhibitors (generic) | 40-80 |
| Metformin (generic) | 30-60 |
| SGLT2 inhibitors | 500-700 |
| GLP-1 receptor agonists | 1,200-2,500 |
| Insulin (basal) | 400-800 |
| PCSK9 inhibitors | 5,000-7,000 |
| Dialysis (total annual) | 40,000-55,000 |

**Rehabilitation Costs:**

| Type | Cost (EUR) | Duration |
|---|---|---|
| Cardiac rehabilitation (inpatient) | 4,000-6,000 | 3 weeks |
| Cardiac rehabilitation (outpatient) | 2,000-3,000 | 6-12 weeks |
| Diabetes rehabilitation | 3,500-5,000 | 3 weeks |
| Neurological rehabilitation (stroke) | 15,000-25,000 | 4-8 weeks |

**Long-Term Care (Pflegeversicherung):**

| Pflegegrad | Monthly Benefit (EUR) | Typical Conditions |
|---|---|---|
| Pflegegrad 1 | 125 (care support) | Mild limitations |
| Pflegegrad 2 | 316 (home) / 770 (facility) | Moderate limitations; early HF |
| Pflegegrad 3 | 545 (home) / 1,262 (facility) | Severe limitations; post-stroke |
| Pflegegrad 4 | 728 (home) / 1,775 (facility) | Very severe; advanced HF, ESRD |
| Pflegegrad 5 | 901 (home) / 2,005 (facility) | Complete dependency |

### Swiss Reference Figures

**Inpatient (SwissDRG):**

| Condition | Mean Cost (CHF) |
|---|---|
| Acute MI (primary PCI) | 25,000-32,000 |
| Stroke (comprehensive stroke centre) | 18,000-28,000 |
| Heart failure hospitalisation | 10,000-15,000 |
| Dialysis session | 500-650 |

**Outpatient (TARMED):**

Swiss outpatient costs are generally 1.5-2x German levels due to higher fee schedules and practice costs.

### Austrian Reference Figures

**Inpatient (LKF system):**

| LKF Group | Description | Mean Cost (EUR) |
|---|---|---|
| HDG05.01 | Acute coronary syndrome | 12,000-18,000 |
| HDG05.03 | Heart failure (inpatient) | 5,000-8,000 |
| HDG01.03 | Stroke (acute) | 8,000-15,000 |
| HDG11.02 | Renal replacement therapy | 40,000-50,000 (annual) |

Austrian inpatient costs are broadly comparable to German levels, with some variation by Bundesland.

---

## 5. Translating Model Outputs to Underwriting Decisions

### From Survival Probabilities to Risk Classification

Disease progression models produce survival probabilities or cumulative incidence functions. These must be translated into underwriting actions:

1. **Calculate excess mortality**: Compare model-predicted mortality to standard population mortality tables (e.g., DAV 2008T for Germany, VZ 2020 for Switzerland).

2. **Express as percentage extra mortality**: Standard actuarial practice expresses elevated risk as a percentage surcharge. For example, a predicted 5-year mortality of 8% against a standard of 4% represents +100% extra mortality.

3. **Map to risk class**: Insurers typically use discrete risk classes:
   - **Standard**: No additional loading (extra mortality <25%)
   - **Substandard**: Graded premium surcharges (+25% to +200%)
   - **Postpone**: Review after specified interval (e.g., 2 years post-MI)
   - **Decline**: Risk too high for standard products (extra mortality >300-500%)

### Expected Claim Cost Calculation

For health insurance (PKV) and critical illness products, the model output should be translated into expected claim costs:

```
Expected annual cost = Sum over states [P(being in state) x Annual cost of state]
```

The multistate model provides state occupation probabilities, which are multiplied by the state-specific cost estimates from the tables above.

### Practical Workflow

1. **Application received**: Applicant completes health questionnaire.
2. **Data extraction**: Relevant diagnoses, labs, and medications are coded.
3. **Model scoring**: Disease progression model predicts state occupation probabilities and survival.
4. **Risk translation**: Actuarial team converts model outputs to excess mortality / expected cost.
5. **Underwriting decision**: Underwriter reviews model recommendation alongside full application.
6. **Override logging**: Any deviation from model recommendation is documented.
7. **Portfolio monitoring**: Aggregate model performance is tracked against actual claims experience.
