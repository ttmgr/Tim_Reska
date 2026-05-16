# Medical Underwriting Manual
## Krankentagegeld (KTG) — Private Krankenversicherung

**Practitioner Reference: Clinical Risk Assessment, Underwriting Logic & Algorithm QA**

*Version 1.0 | For Internal Use Only*

---

## Scope and Purpose

This manual is a daily-use practitioner reference for medical underwriting of Krankentagegeld (KTG) products in German private health insurance (PKV). It is addressed to the Medical Underwriting Expert role: the clinical-algorithmic bridge who reviews algorithm outputs for medical plausibility, validates underwriting rules against evidence, and produces audit-ready documentation.

The reader has deep expertise in ML pipeline validation and systematic AI output quality assurance, but is building clinical and actuarial domain knowledge. This manual prioritises operational clarity and clinical concreteness over theory.

**What this manual covers:**

- Part 1: Clinical disease profiles for KTG-relevant diagnoses (psychiatric, musculoskeletal, cardiovascular, metabolic, neurological)
- Part 2: Comorbidity interaction matrix
- Part 3: Temporal risk framework (look-back windows, remission, red flags)
- Part 4: Documentation standards and data minimisation
- Part 5: 10 worked case studies (cancer replaced)
- Part 6: QA and red-team framework for underwriting algorithms

> **Evidence labelling convention used throughout:**
> - **[T1]** = guideline-level or strong observational evidence
> - **[T2]** = observational evidence, moderate quality
> - **[T3]** = expert judgment / market practice inference

---

# Part 1: Clinical Foundation for KTG Underwriting

This part provides structured underwriting profiles for each major disease category. Each profile follows a fixed schema: definition, AU statistics, prognostic factors, underwriting response options, algorithmic failure modes, and evidence tiers. Where thresholds are evidence-based this is marked [T1] or [T2]; where they rely on expert judgment or market convention they are marked [T3].

---

## 1.1 Psychiatric Conditions (F/Z Chapter — Symptom Cluster Approach)

Psychiatric conditions are the single largest driver of long-term AU in the PKV population. For KTG underwriting, individual ICD codes are less important than the functional syndrome cluster and recurrence pattern. The profiles below are organised by cluster; relevant ICD-10-GM codes are noted for reference but the clinical rules apply to the cluster as a whole.

---

### Cluster 1: Mood Disorders (Depressive & Bipolar Spectrum)

**ICD-10-GM:** F32 (depressive Episode), F33 (rezidivierende depressive Störung), F34 (anhaltende affektive Störungen), F31 (Bipolare Störung)

A spectrum of conditions characterised by persistent low mood, anhedonia, cognitive slowing, and somatic symptoms. Severity ranges from mild single episodes to severe recurrent or treatment-resistant depression and bipolar disorder. For KTG risk the critical dimension is episode recurrence and functional impairment, not diagnosis label alone.

#### AU Duration & Recurrence

- Single mild/moderate episode (F32.0/F32.1): median AU 6–12 weeks; ~30% recurrence within 5 years [T2, DGPPN S3 Leitlinie Depression]
- Single severe episode (F32.2/F32.3): median AU 3–6 months; ~50% recurrence within 2 years [T2]
- Recurrent disorder (F33): each subsequent episode is more severe and longer; after 3 episodes lifetime recurrence risk >90% [T1]
- Bipolar disorder (F31): highest KTG risk in the mood cluster; cycling unpredictable; mean 5–10 episodes per decade without optimal medication [T1]
- Treatment-resistant depression: AU duration often exceeds 12 months; significant risk of permanent disability [T3]

#### Key Prognostic Factors

- **Remission status:** full functional remission (return to prior occupational level) vs partial remission (residual symptoms) — most critical factor
- **Episode count:** first episode vs recurrent. Two prior episodes = high-risk category regardless of current remission [T1]
- **Time since last episode:** <12 months = high risk; 12–24 months = moderate; >24 months in full remission with stable medication = lower risk [T2]
- **Medication:** ongoing antidepressant = not necessarily negative if for relapse prevention; absence of medication after recurrent episodes may indicate poor adherence or treatment gap [T3]
- **Inpatient psychiatric treatment:** strong negative prognostic marker — indicates severity sufficient to require hospitalisation [T1]
- **Comorbid anxiety disorder:** doubles long-term AU duration [T2]
- **Comorbid substance use (F10–F19):** major risk amplifier — see comorbidity matrix
- **Occupational stress exposure:** high-demand professions (physicians, managers, lawyers) have higher recurrence risk in KTG context [T3]
- **Bipolar vs unipolar:** bipolar is categorically higher risk for KTG — long-term medication required, manic episodes can cause acute non-AU risk events [T1]

#### Standard Underwriting Response Options

- **Accept:** first episode, full remission >24 months, no psychotropic medication, no hospitalisation, no recurrence risk markers [T2]
- **Accept with loading (10–50%):** first episode, remission 12–24 months, stable on antidepressant for relapse prevention, good occupational function [T3]
- **Accept with exclusion (psychiatric AU excluded):** recurrent episodes (≥2), currently stable but history of multiple AU episodes; exclusion for psychiatric-coded AU only [T3]
- **Temporary postponement (12–24 months):** active episode ongoing, recently initiated treatment, <6 months remission [T3]
- **Decline:** recurrent severe disorder with ≥3 inpatient admissions; treatment-resistant depression; bipolar disorder with recent cycling; any active episode at time of application [T3]

#### Common Algorithmic Failure Modes

- **Overreaction:** treating a single ICD F32 code from 5 years ago as equivalent to current recurrent depression — ignores time decay and episode count
- **Underestimation:** accepting F33 applicant because most recent AU episode was coded F43 (adjustment disorder) — missed pattern recognition across episodes
- **Coding ambiguity:** F32/F43 differential is clinically significant but coding varies by treating physician; algorithms cannot distinguish without severity markers in physician report
- **Missed bipolar:** F31 is sometimes initially coded F32 or F33 until pattern is recognised — first bipolar manic episode may appear as F30 without prior depressive history in the record

#### Evidence Tiers

- [T1] DGPPN S3 Leitlinie Unipolare Depression: recurrence rates, episode severity classification
- [T2] BARMER/AOK Gesundheitsreport data on depression-related AU duration
- [T3] Market practice thresholds for accept/loading/decline boundaries in German PKV

---

### Cluster 2: Anxiety and Stress-Related Disorders

**ICD-10-GM:** F40 (phobische Störungen), F41 (andere Angststörungen), F43 (Reaktionen auf schwere Belastungen, Anpassungsstörungen), Z73 (Burnout/Probleme bei der Lebensbewältigung)

A functionally heterogeneous cluster ranging from isolated phobias with minimal AU impact to severe generalised anxiety disorder or post-traumatic stress disorder (PTSD) with substantial functional impairment. F43 adjustment disorder and Z73 burnout are frequently over-coded and deserve careful differentiation from severe anxiety.

#### AU Duration & Recurrence

- Simple phobia (F40.2): minimal AU impact if occupationally non-disabling; often <2 weeks per episode [T2]
- Panic disorder (F41.0): acute episodes; moderate AU risk; median annual AU 3–8 weeks in untreated cases [T2]
- Generalised anxiety disorder / GAD (F41.1): chronic course; significant AU; mean 4–6 weeks per year in treated patients [T2]
- Adjustment disorder (F43.2): time-limited by definition (resolves within 6 months of stressor removal); single AU episode typical [T1]
- PTSD (F43.1): highly variable; chronic PTSD has AU profile closer to severe depression [T2]
- Burnout (Z73): Z73 is not a psychiatric diagnosis — it is a condition code. AU duration varies enormously; often reflects employer certificate practice. Cannot be underwritten equivalently to F-diagnoses [T3]

#### Key Prognostic Factors

- **Chronicity:** isolated adjustment reaction vs chronic anxiety disorder — clinically distinct and must be separated
- **Stressor resolution:** for F43, has the precipitating stressor resolved? If ongoing (e.g., divorce, severe illness in family), prognosis worse [T2]
- **Comorbid mood disorder:** GAD + depression combination has worst AU prognosis in the anxiety cluster [T1]
- **Treatment status:** CBT completion for phobia/panic = favourable marker; untreated GAD = higher risk [T2]
- **Z73/Burnout:** seek underlying F-code; if no F-code present, risk is closer to general population [T3]
- **PTSD trauma type:** single-incident vs complex/childhood trauma — complex PTSD has worse prognosis [T2]

#### Standard Underwriting Response Options

- **Accept:** isolated phobia (non-occupationally-disabling), single F43 episode fully resolved >12 months, Z73 without underlying F-code [T3]
- **Accept with loading (10–25%):** GAD in remission >12 months on stable medication; resolved panic disorder with CBT [T3]
- **Accept with exclusion:** chronic GAD with ≥2 AU episodes; ongoing medication for anxiety [T3]
- **Postpone (12 months):** active F43 or F41 episode; <6 months since last AU for psychiatric cause [T3]
- **Decline:** PTSD with severe functional impairment; treatment-resistant anxiety disorder; chronic anxiety + comorbid depression [T3]

#### Common Algorithmic Failure Modes

- **Overreaction:** treating Z73 as equivalent to F41 — Z73 is a contact reason code, not a psychiatric diagnosis
- **Underestimation:** accepting F43 without checking whether F32/F33 codes exist earlier in the history — adjustment disorder is sometimes used to 'soften' a depression diagnosis
- **Missed PTSD:** F43.1 may appear as only one ICD entry but represent a chronic severely impairing condition; algorithm may not weight it differently from adjustment disorder
- **Coding heterogeneity:** GAD, panic, and mixed anxiety-depression (F41.2) are clinically distinct but may be coded interchangeably by GPs

#### Evidence Tiers

- [T1] AWMF S3 Leitlinie Angststörungen: course, treatment, prognosis
- [T2] Robert Koch Institut: psychische Gesundheit in Deutschland; anxiety disorder AU data
- [T3] Market convention: Z73 treatment, phobia vs GAD underwriting thresholds

---

### Cluster 3: Personality Disorders

**ICD-10-GM:** F60 (spezifische Persönlichkeitsstörungen: F60.0 paranoid, F60.2 dissozial, F60.3 emotional instabil/Borderline, F60.4 histrionisch, F60.5 anankastisch, F60.6 ängstlich-vermeidend, F60.7 abhängig), F61 (kombinierte Persönlichkeitsstörungen)

Persistent, inflexible, maladaptive patterns of inner experience and behaviour that deviate markedly from cultural expectations, cause distress, and impair functioning. For KTG underwriting, borderline (F60.3), anxious-avoidant (F60.6), and dependent (F60.7) personality disorders carry the highest AU risk. Anankastic (F60.5) may paradoxically reduce AU in some occupational settings. Personality disorders are chronic by definition.

#### AU Duration & Recurrence

- Borderline (F60.3): highest AU risk in this cluster; crisis episodes cause recurrent short AU periods; inpatient admissions common; annual AU often exceeds 6 weeks [T2]
- Anxious-avoidant (F60.6): chronic low-grade impairment; moderate annual AU; risk amplified by high-demand occupations [T2]
- Dependent (F60.7): AU often triggered by relationship crises; unpredictable pattern [T3]
- Anankastic/obsessive-compulsive (F60.5): may actually reduce AU in structured occupations; monitor for comorbid OCD [T3]
- Antisocial (F60.2): low direct AU risk but underwriting integrity concerns [T3]

#### Key Prognostic Factors

- Personality disorders are by definition chronic — remission in the traditional sense does not apply; assess current functional level and treatment engagement
- **DBT (Dialectical Behaviour Therapy) completion for borderline:** significantly improves prognosis and reduces crisis episodes [T1]
- **Inpatient psychiatric admissions:** each admission significantly increases expected future AU [T2]
- **Comorbid substance use disorder:** major risk amplifier
- **Occupational stability:** sustained employment in same role >2 years is a favourable functional marker [T3]
- **Age:** borderline symptoms often attenuate somewhat after age 35–40 [T2]

#### Standard Underwriting Response Options

- **Accept:** anankastic personality disorder, stable occupational function, no hospitalisation, no AU in past 3 years [T3]
- **Accept with exclusion (psychiatric AU):** most other personality disorders with good functional stability, no recent crisis [T3]
- **Postpone or decline:** borderline with ≥1 inpatient admission in past 3 years; any personality disorder with active crisis pattern; combination with substance use disorder
- **Decline:** borderline with multiple inpatient admissions; antisocial with legal history; any personality disorder causing >8 weeks AU in past 12 months [T3]

#### Common Algorithmic Failure Modes

- **Over-penalising anankastic PD:** F60.5 may have zero or negative KTG impact in structured professions
- **Missing severity distinction:** algorithm treating F60.3 borderline identically to F60.5 anankastic is a major error
- **Coding rarity:** personality disorder diagnoses are under-coded in German primary care — the absence of F60 does not mean absence of PD; look for repeated crisis-coded contacts
- **Missing DBT marker:** completed DBT is a clinically meaningful positive prognostic factor that no algorithm currently extracts from free text

#### Evidence Tiers

- [T1] AWMF S3 Leitlinie Borderline (BPS): treatment efficacy, hospitalisation rates
- [T2] Long-term follow-up studies (Zanarini et al.): course of BPD
- [T3] Market convention for PD underwriting decisions; no formal actuarial tables exist

---

## 1.2 Musculoskeletal Conditions

---

### Intervertebral Disc Conditions

**ICD-10-GM:** M50 (Zervikaler Bandscheibenschaden), M51 (Sonstiger Bandscheibenschaden — lumbar/thoracic), M51.1 (Bandscheibenprolaps mit Radikulopathie)

Disc herniation (prolapse) occurs when nucleus pulposus material displaces beyond the annular boundary, potentially compressing nerve roots (radiculopathy) or the spinal cord. M51 without neurological involvement = disc degeneration/bulge. M51.1 with radiculopathy = significantly higher severity.

#### AU Duration & Recurrence

- Uncomplicated M51 (disc degeneration without radiculopathy): acute exacerbation AU 2–6 weeks; recurrence rate 40–60% within 5 years [T2]
- M51.1 with radiculopathy, conservative management: AU 6–12 weeks per episode; ~30% require eventual surgery [T2]
- Post-surgical (discectomy): return to work typically 6–12 weeks; re-herniation rate 5–15% within 5 years [T1, AWMF S2k Leitlinie Bandscheibenprolaps]
- Multiple level disease or chronic radiculopathy: AU pattern shifts to recurrent; expect 4–8 weeks AU annually long-term [T2]

#### Key Prognostic Factors

- **Radiological severity:** multilevel vs single level; spinal stenosis as comorbidity
- **Neurological deficit:** motor weakness or bladder/bowel involvement = severe, usually surgical indication
- **Surgery history:** type of surgery (microdiscectomy vs fusion); outcome; time since surgery
- **Occupation:** heavy manual labour significantly worsens prognosis [T1]; sedentary work with ergonomic modification = better
- **BMI/obesity:** strong prognostic factor for recurrence [T2]
- **Pain chronification:** pain >12 weeks = risk of central sensitisation, which dramatically worsens prognosis [T1]
- **Psychosocial yellow flags (STarT Back tool):** catastrophising, depression, job dissatisfaction — predict chronification [T1]

#### Standard Underwriting Response Options

- **Accept:** M51 without radiculopathy, single episode >24 months ago, full recovery, sedentary occupation [T2]
- **Accept with loading (15–30%):** M51 with past radiculopathy, conservatively treated, remission >12 months, no surgery, non-manual occupation [T3]
- **Accept with loading + musculoskeletal exclusion:** post-surgery discectomy with good outcome >12 months, white-collar occupation [T3]
- **Decline:** chronic radiculopathy with ongoing medication; multilevel disease with surgery history + heavy occupation; failed back surgery syndrome [T3]

#### Common Algorithmic Failure Modes

- Not distinguishing M51 (degeneration) from M51.1 (radiculopathy) — categorically different risk
- Missing occupation data: identical ICD history carries very different risk in a physiotherapist vs a software developer
- Post-surgery underestimation: successful microdiscectomy outcome is not always captured — algorithm may permanently flag surgical history without noting good recovery
- Ignoring psychosocial yellow flags: never present in ICD codes; require physician report interpretation

#### Evidence Tiers

- [T1] AWMF S2k Leitlinie Bandscheibenprolaps mit Radikulopathie; STarT Back research programme
- [T2] German GKV AU data on back disorders (BKK Gesundheitsreport)
- [T3] PKV market practice thresholds

---

### Non-specific Back Pain

**ICD-10-GM:** M54 (Rückenschmerzen): M54.4 (Ischialgie), M54.5 (Kreuzschmerz/LBP), M54.6 (Schmerzen im BWS-Bereich)

M54 covers non-specific back pain without identified structural disc pathology. It is the highest-volume AU diagnosis in Germany. The key clinical distinction is acute/subacute (<12 weeks) vs chronic (>12 weeks) and primary vs secondary (symptom-attributed to structural cause). Non-specific LBP in 90% of cases has no identifiable structural cause.

#### AU Duration & Recurrence

- Acute non-specific LBP: 90% resolve within 6 weeks; expected AU 1–4 weeks [T1, NVL Kreuzschmerz]
- Recurrent LBP: defined as ≥3 episodes within 12 months; annual AU burden 6–12 weeks [T2]
- Chronic LBP (>12 weeks): significantly elevated AU; mean 8–14 weeks per year; major driver of long-term disability [T1]
- Ischialgia (M54.4): acute 4–8 weeks; distinguish from true radiculopathy (M51.1)

#### Key Prognostic Factors

- **Episode count and chronicity:** most important factors; isolated acute episode = very different risk from recurrent/chronic
- **Medication:** opioid use for back pain = serious red flag indicating chronification and severity [T1]
- **Occupation (physical load):** strong evidence for causal and prognostic relationship [T1]
- **Psychosocial factors:** same yellow flags as disc pathology
- **Imaging:** absence of structural finding on MRI is actually favourable — rules out serious pathology and points to functional or muscular cause

#### Standard Underwriting Response Options

- **Accept:** isolated M54 AU <2 weeks, >18 months ago, no recurrence, no chronic pattern [T2]
- **Accept with loading (10–20%):** 2–3 episodes within 3 years, total AU <8 weeks, no chronification markers [T3]
- **Accept with musculoskeletal exclusion:** recurrent pattern (≥3 episodes), chronic LBP diagnosis, opioid use [T3]
- **Decline:** chronic LBP with permanent disability markers; ongoing opioid therapy; heavy manual occupation with multilevel changes [T3]

#### Common Algorithmic Failure Modes

- Single M54 episode from 4 years ago triggering loading — textbook overreaction
- Not distinguishing M54 (non-specific) from M51 (structural) — systematically different risk
- Missing recurrence pattern: three separate M54 AU episodes coded identically; algorithm may treat as one condition without counting episodes across years
- Opioid marker absent: opioid prescriptions for back pain may appear in medication section, not in ICD codes — integration gap

#### Evidence Tiers

- [T1] NVL Nicht-spezifischer Kreuzschmerz (German National Guideline): prognosis, chronification risk
- [T2] BKK Gesundheitsreport back pain AU data
- [T3] Market practice thresholds for recurrent LBP

---

### Soft Tissue Disorders

**ICD-10-GM:** M79.0 (Rheumatismus), M79.1 (Myalgie), M79.2 (Neuralgie/Neuritis), M79.3 (Panniculitis), M79.7 (Fibromyalgie-Syndrom)

M79 is a heterogeneous group. For KTG underwriting, the most clinically significant subtype is M79.7 Fibromyalgie-Syndrom (FMS). Other M79 codes (myalgia, unspecified soft tissue pain) are often self-limiting and carry lower risk. FMS is a centralised pain disorder characterised by widespread musculoskeletal pain, fatigue, sleep disturbance, and cognitive symptoms.

#### AU Duration & Recurrence

- General M79 (non-FMS): typically acute; AU 1–3 weeks; high recurrence but usually short individual episodes [T2]
- M79.7 Fibromyalgia: chronic condition; mean annual AU 6–10 weeks; 10–20% are on long-term sick leave at any point [T2]
- Fibromyalgia with comorbid psychiatric disorder: AU burden may exceed 12 weeks annually [T2]

#### Key Prognostic Factors

- **Specific FMS diagnosis vs non-specific M79:** must be separated — very different risk profiles
- **Comorbid mood disorder in FMS:** near-universal; the comorbid depression often drives AU more than the pain itself
- **Medication:** central sensitisation medications (duloxetine, pregabalin, amitriptyline) suggest confirmed FMS diagnosis
- **Functional status:** ability to maintain full-time employment = favourable marker in FMS
- Tender point count and symptom severity: not available in application data; require physician report

#### Standard Underwriting Response Options

- **Accept:** non-specific M79 (non-FMS), single episode, resolved [T3]
- **Accept with loading:** M79.7 FMS with stable full-time employment, no psychiatric comorbidity, minimal medication [T3]
- **Accept with musculoskeletal exclusion:** FMS with moderate impact, controlled comorbidities [T3]
- **Decline:** FMS with severe functional impairment, psychiatric comorbidity, opioid or high-dose gabapentinoid use, prior long-term sick leave [T3]

#### Common Algorithmic Failure Modes

- Treating all M79 codes uniformly — M79.1 myalgia and M79.7 FMS are categorically different risks
- Missing FMS via medication: duloxetine prescribed for FMS may not be linked to M79.7 in code data
- FMS comorbidity blindness: psychiatric and FMS codes often coded separately; algorithm summing both naïvely may not capture the synergistic AU risk

#### Evidence Tiers

- [T2] German fibromyalgia patient survey data; AWMF S3 Leitlinie Fibromyalgiesyndrom
- [T3] Market practice for FMS underwriting; no tier-1 actuarial studies available

---

### Rheumatoid Arthritis

**ICD-10-GM:** M05 (seropositive RA), M06 (sonstige RA inkl. seronegative)

Chronic systemic autoimmune disease with symmetrical inflammatory polyarthropathy. RA is a potentially severe, progressive condition requiring long-term specialist management and DMARDs/biologics. Disease activity fluctuates; sustained remission is achievable with modern treatment but relapse occurs in a significant proportion.

#### AU Duration & Recurrence

- Active RA without optimal treatment: AU 8–20 weeks per flare; multiple flares per year possible [T2]
- RA in remission on DMARDs: annual AU 2–4 weeks in well-controlled patients [T2, ACR/EULAR treat-to-target data]
- RA on biologics (anti-TNF etc.): remission rates ~40–60%; functional outcomes significantly improved [T1]
- RA with joint erosions/deformities: permanent functional limitation; elevated long-term AU [T1]

#### Key Prognostic Factors

- **Disease activity score (DAS28):** clinical remission criterion — not available in application data but can be requested in physician report
- **Seropositivity (RF, anti-CCP):** seropositive RA has more erosive course [T1]; M05 vs M06 is a meaningful prognostic distinction
- **Medication level:** hydroxychloroquine/methotrexate alone vs combination csDMARDs vs biologics/JAK inhibitors — escalation reflects disease severity
- **Joint erosions or deformities:** radiological finding indicating irreversible damage — very negative prognostic marker
- **Extra-articular manifestations (Felty syndrome, pulmonary RA):** indicate systemic severe disease
- **Comorbid cardiovascular disease:** RA independently elevates CV risk by 50% [T1]

#### Standard Underwriting Response Options

- **Accept with loading (20–40%):** RA in clinical remission >12 months, DAS28 <2.6, stable DMARD, no erosions, white-collar occupation [T3]
- **Accept with loading + musculoskeletal exclusion:** active disease, moderate severity, responsive to treatment [T3]
- **Postpone:** newly diagnosed RA awaiting treatment response assessment [T3]
- **Decline:** severe erosive RA, biologic escalation with incomplete response, significant functional limitation, manual occupation [T3]

#### Common Algorithmic Failure Modes

- Not distinguishing M05 (seropositive, more severe) from M06 (seronegative, heterogeneous) — coding difference carries clinical weight
- Missing medication escalation signal: biologic prescription should be a strong risk escalation trigger that ICD codes alone do not capture
- Underestimating CV comorbidity risk in RA — RA itself is a CV risk multiplier

#### Evidence Tiers

- [T1] ACR/EULAR RA treatment guidelines; treat-to-target studies; CV risk in RA meta-analyses
- [T2] German rheumatology registry (RABBIT) data on work disability
- [T3] PKV market practice for RA underwriting

---

## 1.3 Cardiovascular Conditions

---

### Hypertension

**ICD-10-GM:** I10 (essentielle Hypertonie), I11 (hypertensive Herzkrankheit), I12 (hypertensive Nierenkrankheit), I13 (hypertensive Herz- und Nierenkrankheit)

Persistent elevation of systolic blood pressure ≥140 mmHg or diastolic ≥90 mmHg (ESC 2023 guidelines). I10 alone (essential, isolated) is common and usually well-controlled. Risk escalates with target organ damage (I11–I13) and comorbidities.

#### AU Duration & Recurrence

- Controlled I10 without organ damage: minimal direct AU impact; most AU arises from comorbidities or treatment side-effects [T2]
- Hypertensive crisis or emergency: acute AU 1–4 weeks; rare in well-managed patients [T2]
- I11/I12/I13 (organ involvement): AU driven by cardiac or renal complications rather than hypertension per se [T1]

#### Key Prognostic Factors

- **Blood pressure control:** last documented BP reading; number of antihypertensive agents required
- **Target organ damage:** LVH on ECG/echo, microalbuminuria, retinopathy, CKD stage
- **Number of antihypertensive agents:** 1 drug = mild; 2–3 drugs = moderate; ≥4 drugs or resistant hypertension = high risk [T2]
- **Metabolic comorbidities:** diabetes + hypertension = major risk multiplier for KTG (see comorbidity matrix)
- **Age at diagnosis:** early-onset hypertension (<40 years) implies longer exposure and higher lifetime complication risk

#### Standard Underwriting Response Options

- **Accept:** isolated I10, well-controlled on 1–2 agents, no organ damage, no metabolic comorbidity [T2]
- **Accept with loading (15–30%):** 2–3 antihypertensive agents, or mild microalbuminuria, or hypertension + one metabolic factor [T3]
- **Accept with higher loading or exclusion:** hypertensive heart disease (I11), moderate CKD, resistant hypertension [T3]
- **Decline:** malignant hypertension, I11/I12/I13 with significant organ damage, multiple high-risk comorbidities [T3]

#### Common Algorithmic Failure Modes

- Treating all I10 codes as equal risk — controlled single-agent hypertension is near-normal KTG risk
- Ignoring medication data: number of antihypertensives required is the most powerful proxy for severity available in application data
- Missing I11/I12/I13 distinction: hypertension-with-organ-damage codes carry materially higher risk than pure I10

#### Evidence Tiers

- [T1] ESC/ESH Hypertension Guidelines 2023: staging, organ damage classification
- [T2] PKV actuarial data (partial, proprietary); GKV mortality data for hypertension subgroups
- [T3] Market practice thresholds for antihypertensive drug count proxies

---

### Chronic Ischaemic Heart Disease / Coronary Artery Disease

**ICD-10-GM:** I25 (chronische ischämische Herzkrankheit): I25.0 (atherosklerotische Herzkrankheit), I25.1 (atherosklerotische Herzkrankheit mit Angina pectoris), I25.5 (ischämische Kardiomyopathie). Related: I21/I22 (Z.n. Myokardinfarkt)

Obstructive coronary artery disease causing chronic myocardial ischaemia. For KTG underwriting, key questions are: has the patient had an MI? What is current cardiac function (EF)? Are symptoms controlled? Has revascularisation been performed?

#### AU Duration & Recurrence

- Stable CAD without prior MI, medically managed: AU primarily from acute events; baseline 2–4 weeks/year [T2]
- Post-MI, EF preserved: return to work 4–12 weeks; long-term AU increases with recurrent events [T2]
- Post-MI, reduced EF (<40%): significantly elevated long-term AU; heart failure trajectory [T1]
- Post-CABG: return to work 8–16 weeks; long-term AU depends on residual disease and EF [T2]
- Post-PCI (stent): return to work 2–6 weeks if uncomplicated; recurrent events risk depends on residual disease [T2]

#### Key Prognostic Factors

- **Left ventricular ejection fraction (LVEF):** most important single prognostic parameter; EF >50% = preserved; <40% = significantly impaired
- **Number of vessels affected:** single-vessel vs multi-vessel disease
- **Revascularisation status:** complete vs incomplete revascularisation
- **Post-event medication adherence:** dual antiplatelet, statin, ACE inhibitor — full regimen is favourable marker
- **Residual angina symptoms:** any CCS class ≥2 angina = elevated risk
- **Comorbidities:** diabetes, renal failure, hypertension — multiplicative risk

#### Standard Underwriting Response Options

- **Accept with loading (25–50%):** stable CAD, no MI, EF >55%, fully revascularised PCI, sedentary occupation, optimal medication, >12 months stable [T3]
- **Accept with higher loading or cardiac exclusion:** post-MI with preserved EF, >24 months stable, full revascularisation [T3]
- **Postpone (24 months):** recent MI or CABG <24 months [T3]
- **Decline:** reduced EF (<40%), multi-vessel unrevascularised disease, CCS ≥2 angina, ischaemic cardiomyopathy [T3]

#### Common Algorithmic Failure Modes

- Treating I25 as a homogeneous block — I25.0 (atherosclerosis, no symptoms) is very different from I25.5 (ischaemic cardiomyopathy)
- No LVEF data: algorithms rarely receive echocardiographic data; major gap between ICD-coded risk and functional reality
- Post-PCI underestimation: algorithm may not distinguish complete revascularisation from incomplete; the residual disease burden is the key variable

#### Evidence Tiers

- [T1] ESC Chronic Coronary Syndromes Guidelines 2019/2024: prognosis, revascularisation outcomes
- [T2] Post-MI work return data; GKV disability data
- [T3] Market convention for post-cardiac-event KTG

---

### Atrial Fibrillation

**ICD-10-GM:** I48 (Vorhofflimmern und Vorhofflattern): I48.0 (paroxysmal), I48.1 (persistent), I48.2 (chronisch/permanent), I48.9 (nicht näher bezeichnet)

Supraventricular tachyarrhythmia with disorganised atrial electrical activity. For KTG, AF itself rarely causes direct AU. The primary underwriting concern is the underlying cardiac pathology, stroke risk (CHA₂DS₂-VASc), and anticoagulation status.

#### AU Duration & Recurrence

- Lone paroxysmal AF in young patient, structurally normal heart: minimal AU (1–2 weeks/year for cardioversion or monitoring) [T2]
- AF with comorbid cardiac disease (heart failure, valvular): AU driven by underlying condition [T1]
- AF with stroke event: AU 4–24 weeks for acute stroke; ongoing disability possible [T2]

#### Key Prognostic Factors

- **AF subtype:** paroxysmal (I48.0) vs permanent (I48.2) — permanent AF implies less cardiovascular reserve
- **CHA₂DS₂-VASc score:** stroke risk stratification — each additional point = elevated risk; can be calculated from comorbidity data
- **Anticoagulation:** OAC (DOAC/warfarin) on board = stroke prevention — favourable marker for stroke risk management
- **Underlying cardiac disease:** structural heart disease (reduced EF, valvular, hypertrophic) = much higher risk than lone AF
- **Ablation:** successful catheter ablation with maintained sinus rhythm = favourable [T2]
- **Thyroid function:** hyperthyroid-induced AF resolves with treatment — unique self-limiting subgroup

#### Standard Underwriting Response Options

- **Accept:** lone paroxysmal AF, structurally normal heart, low CHA₂DS₂-VASc, rate-controlled, anticoagulated if indicated [T3]
- **Accept with loading (20–35%):** persistent/permanent AF, CHA₂DS₂-VASc 1–2, no significant comorbidity [T3]
- **Accept with loading or cardiovascular exclusion:** AF + 1–2 comorbidities (hypertension, diabetes, mild heart failure) [T3]
- **Decline:** AF with prior stroke/TIA, AF with severe structural heart disease, uncontrolled heart rate [T3]

#### Common Algorithmic Failure Modes

- Treating I48.9 (unspecified) the same as I48.2 (chronic) — subtype coding matters significantly
- Missing comorbidity context: AF risk is almost entirely determined by comorbidities; AF ICD code alone cannot generate a meaningful underwriting decision
- Anticoagulation blind spot: DOAC prescription for AF is a clinically important marker that algorithms without medication integration miss

#### Evidence Tiers

- [T1] ESC AF Guidelines 2023: CHA₂DS₂-VASc, ablation outcomes
- [T2] Long-term follow-up data on lone AF; stroke incidence by CHA₂DS₂-VASc
- [T3] Market convention for AF underwriting

---

## 1.4 Metabolic Conditions

---

### Type 2 Diabetes Mellitus

**ICD-10-GM:** E11 (Diabetes mellitus Typ 2): E11.0–E11.9 (with/without complications). E11.7 (multiple Komplikationen), E11.9 (ohne Komplikationen)

Chronic metabolic disorder of insulin resistance and progressive beta-cell failure. For KTG underwriting, the critical axis is glycaemic control (HbA1c) and complication status. Uncomplicated, well-controlled T2DM has moderate KTG impact; complicated T2DM is a major long-term risk.

#### AU Duration & Recurrence

- E11.9 (no complications), HbA1c <7.5%, diet/metformin: minimal direct AU; risk arises from future complications [T2]
- E11 with mild complications (retinopathy, microalbuminuria): moderate AU elevation; 4–8 weeks/year [T2]
- E11 with macrovascular complications (CAD, PAD, stroke): AU profile dominated by cardiovascular events [T1]
- E11 with severe neuropathy or foot complications: significant AU; amputation risk is long-term tail risk [T1]
- E11 with renal failure (diabetic nephropathy, CKD ≥3): major long-term AU risk; dialysis = decline territory [T1]

#### Key Prognostic Factors

- **HbA1c:** most important glycaemic control marker; <7.0% = well controlled; 7.0–8.0% = acceptable; >8.0% = poor; >9.0% = very poor [T1]
- **Complications:** presence of microvascular (retinopathy, nephropathy, neuropathy) or macrovascular complications [T1]
- **Medication escalation:** diet only → metformin → dual oral → insulin = proxy for disease progression
- **Insulin use:** any insulin = more advanced disease; insulin pump = most intensive management, also most advanced
- **Duration of diabetes:** >10 years = higher cumulative complication risk even if currently controlled
- **Comorbid hypertension:** near-universal in T2DM; the combination is greater than additive for KTG (see comorbidity matrix)
- **Obesity:** exacerbates insulin resistance; weight loss is only modifiable factor that can reverse early T2DM [T1]

#### Standard Underwriting Response Options

- **Accept with loading (15–25%):** E11.9, HbA1c <7.5%, diet or metformin only, no complications, <5 years duration, BMI <30 [T2/T3]
- **Accept with higher loading (25–50%):** E11.9, HbA1c 7.5–8.0%, 2 oral agents, mild microalbuminuria, <10 years duration [T3]
- **Accept with metabolic exclusion or high loading:** insulin therapy, HbA1c 8–9%, moderate complications [T3]
- **Decline:** HbA1c >9.0%, macrovascular complications, CKD ≥3, insulin + complication cluster, heavy manual occupation [T3]

#### Common Algorithmic Failure Modes

- Treating all E11 as uniform risk — E11.9 uncomplicated on metformin vs E11.7 multiple complications are not comparable
- Not using HbA1c data: HbA1c is routinely available in health questionnaires and physician reports but algorithms often treat it as free text, failing to extract it
- Missing medication escalation signal: oral hypoglycaemic drug count is a powerful proxy for disease progression
- Underestimating T2DM + hypertension interaction: algorithms treating these as additive underestimate synergistic KTG risk

#### Evidence Tiers

- [T1] ADA/EASD T2DM management guidelines; UKPDS long-term complication data
- [T2] German DMP Diabetes data; GKV AU statistics for diabetic patients
- [T3] Market convention for HbA1c thresholds and loading levels

---

### Obesity

**ICD-10-GM:** E66 (Adipositas): E66.0 (ernährungsbedingt), E66.1 (medikamentös), E66.8/E66.9. Also relevant: E66 + metabolic syndrome components.

BMI ≥30 kg/m². Classified as Class I (30–34.9), Class II (35–39.9), Class III (≥40). For KTG underwriting, obesity is primarily a comorbidity amplifier and metabolic/musculoskeletal risk multiplier rather than a direct AU driver in isolation.

#### AU Duration & Recurrence

- Class I obesity without comorbidities: modest AU elevation (2–4 weeks/year above baseline) [T2]
- Class II–III obesity: AU risk escalates rapidly; 4–8 weeks/year directly attributable to obesity-related conditions [T2]
- Obesity + metabolic syndrome (E66 + hypertension + dyslipidaemia + impaired glucose): major AU driver [T1]
- Obesity + musculoskeletal: back and joint pain AU risk multiplied [T2]

#### Key Prognostic Factors

- **BMI class:** Class III (≥40) = dramatically elevated risk; Class I = modest elevation
- **Metabolic syndrome components:** number and severity of associated metabolic risk factors
- **Weight trajectory:** actively losing weight with intervention vs gaining = very different outlook [T2]
- **Bariatric surgery history:** successful bariatric surgery with sustained weight loss = favourable prognostic reversal [T1]
- **Sleep apnoea (G47.3):** near-universal in class II–III obesity; CPAP adherence is a positive marker; untreated OSA is highly impairing

#### Standard Underwriting Response Options

- **Accept with loading:** E66 Class I, no metabolic comorbidities [T3]
- **Accept with moderate loading (20–35%):** E66 Class II, 1 metabolic comorbidity, no severe complications [T3]
- **Accept with high loading or exclusion:** E66 Class III without bariatric surgery, multiple comorbidities [T3]
- **Decline:** Class III + diabetes + hypertension + CAD combination; OSA non-adherent to treatment; BMI >45 + manual occupation [T3]

#### Common Algorithmic Failure Modes

- BMI data quality: BMI from health questionnaire self-report; significant underreporting bias
- Not combining E66 with comorbidity codes: an E66 code alone gives little information; risk is in the comorbidity cluster
- Missing bariatric surgery: L-code for bariatric surgery may be in medication/surgical history but not linked to current metabolic status in algorithm

#### Evidence Tiers

- [T1] NICE/DGEM obesity guidelines; bariatric surgery outcomes literature
- [T2] BMI-stratified AU data from GKV reports
- [T3] Market practice for BMI-based loading decisions

---

## 1.5 Neurological Conditions

---

### Multiple Sclerosis

**ICD-10-GM:** G35 (Multiple Sklerose)

Chronic autoimmune demyelinating disease of the CNS. Clinical course varies: relapsing-remitting (RRMS, ~85% at onset), secondary progressive (SPMS), primary progressive (PPMS). For KTG underwriting, MS is one of the highest long-term AU risks in the neurological category.

#### AU Duration & Recurrence

- RRMS, low disease activity, no disability: relapse AU 2–8 weeks per event; relapses occur mean 1–2/year untreated, 0.3–0.5/year on effective DMT [T1]
- RRMS on high-efficacy DMT (natalizumab, ocrelizumab): AU substantially reduced; approach near-normal in best-case [T1]
- SPMS/PPMS: progressive disability accumulation; long-term AU risk very high; permanent disability common [T1]
- EDSS 0–2.5 (minimal disability): near-normal work function; lower short-term AU [T2]
- EDSS ≥3.0: meaningful functional impairment; AU risk escalates with each EDSS step [T1]

#### Key Prognostic Factors

- **EDSS score:** Expanded Disability Status Scale 0–10; most important single functional marker
- **Disease course:** RRMS vs SPMS vs PPMS
- **DMT level:** no treatment vs platform therapy (interferons, glatiramer) vs high-efficacy (natalizumab, alemtuzumab, ocrelizumab)
- **Relapse rate** over past 2 years on current therapy
- **MRI activity:** gadolinium-enhancing lesions indicate active inflammation
- **Time since last relapse**
- **Age at onset:** younger onset = longer exposure but sometimes more benign RRMS course
- **Sphincter/cognitive involvement:** very poor prognostic markers for occupational function

#### Standard Underwriting Response Options

- **Postpone (3–5 years):** newly diagnosed MS, treatment just initiated — insufficient data on disease activity [T3]
- **Accept with high loading + neurological exclusion:** RRMS, EDSS 0–1.5, on effective DMT, 0 relapses in past 2 years, >3 years stable [T3]
- **Accept with neurological exclusion only:** RRMS, EDSS ≤2.5, low disease activity [T3]
- **Decline:** EDSS ≥3.0; SPMS/PPMS; active relapses; high MRI burden; cognitive or sphincter involvement [T3]

#### Common Algorithmic Failure Modes

- Treating all G35 as equal — newly diagnosed RRMS with one relapse and EDSS 0 vs SPMS with EDSS 4 are not comparable
- No EDSS access: the most important clinical variable is almost never present in administrative data
- DMT level proxy: high-efficacy DMT prescription (natalizumab = hospital prescription) vs platform therapy can sometimes be inferred from prescription data — underutilised signal

#### Evidence Tiers

- [T1] ECTRIMS/EAN MS Treatment Guidelines; EDSS natural history studies
- [T2] MS registry data (e.g. German MS Society DMSG); vocational outcomes research
- [T3] Market convention for MS underwriting

---

### Migraine

**ICD-10-GM:** G43 (Migräne): G43.0 (ohne Aura), G43.1 (mit Aura), G43.3 (komplizierte Migräne), G43.8/G43.9. Also: G44.2 (Spannungskopfschmerz — lower risk)

Recurrent episodic headache disorder with significant functional impairment during attacks. Frequency and disability distinguish episodic (<15 days/month) from chronic migraine (≥15 days/month, ≥8 with migraine features). For KTG, the key dimension is attack frequency and functional impact, not simply the diagnosis.

#### AU Duration & Recurrence

- Episodic migraine, 1–4 attacks/month, good triptan response: AU 5–15 days/year [T2]
- High-frequency episodic migraine (8–14 days/month): AU 20–40 days/year [T2]
- Chronic migraine (≥15 days/month): major AU driver; up to 60–80 days/year [T2]
- Migraine with aura: higher stroke risk especially in women on OCP — relevant for comorbidity assessment [T1]

#### Key Prognostic Factors

- **Attack frequency:** most important KTG factor; attacks per month must be established
- **Triptan/acute medication responsiveness:** good triptan response = manageable AU; medication overuse headache (MOH) = chronic pattern = major red flag
- **Preventive therapy:** use of beta-blocker, topiramate, CGRP antagonists suggests significant disease burden
- **Medication overuse headache (G44.4):** paradoxically worsens migraine; indicator of chronification and poor management
- **Comorbid depression/anxiety:** extremely common with chronic migraine; amplifies AU

#### Standard Underwriting Response Options

- **Accept:** episodic migraine, ≤4 days/month, good acute medication response, no preventive medication required [T2]
- **Accept with loading (10–20%):** episodic migraine 5–8 days/month, on preventive therapy, no MOH [T3]
- **Accept with loading + neurological exclusion:** high-frequency episodic migraine, 8–14 days/month, no chronic conversion [T3]
- **Decline or exclusion only:** chronic migraine ≥15 days/month; MOH; occupations where sudden incapacity is dangerous [T3]

#### Common Algorithmic Failure Modes

- G43 coding frequency not captured: all G43 patients appear identical regardless of 2 vs 20 attacks/month — the most critical variable is not in the code
- Missing MOH: medication overuse headache may be coded G44.4 or not at all — algorithms miss it
- Overreaction to single G43 code: patients with 1–2 migraines per year are normal-risk for KTG; algorithm flagging all G43 is a major overreaction failure mode

#### Evidence Tiers

- [T1] ICHD-3 migraine classification; migraine + OCP stroke data
- [T2] German headache society (DMKG) data; GKV AU days for headache disorders
- [T3] Market convention for migraine loading thresholds

---

### Epilepsy

**ICD-10-GM:** G40 (Epilepsie): G40.0–G40.9 by syndrome. Related: G41 (Status epilepticus)

Neurological disorder characterised by recurrent unprovoked seizures. For KTG underwriting, the primary concern is occupational restriction due to seizure risk (driving, working at heights, machinery), and the AU burden from seizure events and titration periods. Well-controlled epilepsy on monotherapy has a very different risk profile from refractory epilepsy.

#### AU Duration & Recurrence

- Seizure-free ≥24 months on monotherapy: minimal direct AU; primary risk is occupational restriction [T2]
- Active seizures (≥1/year): AU per seizure event 1–4 weeks; risk of status epilepticus adds tail risk [T2]
- Refractory epilepsy (≥2 adequate drugs failed): significant AU; surgery consideration [T1]

#### Key Prognostic Factors

- **Seizure-free duration:** most important marker; ≥24 months = meaningful threshold [T1]
- **Number of AEDs:** monotherapy vs polytherapy is a strong proxy for disease control
- **Driving licence status:** revoked licence = objective marker of insufficient seizure control
- **Seizure type:** focal vs generalised tonic-clonic; the latter carries more injury risk
- **Epilepsy syndrome:** idiopathic generalised epilepsies have better prognosis than focal symptomatic [T1]
- **Occupation:** work at heights, driving, machinery = major occupational restriction implications

#### Standard Underwriting Response Options

- **Accept with loading:** seizure-free ≥24 months, monotherapy, driving licence intact, no occupational restriction required [T3]
- **Accept with neurological exclusion:** seizure-free ≥12 months, well-tolerated medication, non-safety-critical occupation [T3]
- **Postpone (12 months):** newly initiated AED, seizure frequency not yet established [T3]
- **Decline:** refractory epilepsy, frequent seizures, safety-critical occupation, status epilepticus history [T3]

#### Common Algorithmic Failure Modes

- Not capturing AED count: polypharmacy is a strong severity proxy; algorithms without medication integration miss this entirely
- Missing driving status: licence revocation is an objective external severity marker, available only from questionnaire free text
- Overreacting to childhood epilepsy codes: juvenile absence epilepsy with adult remission is fundamentally different from adult-onset focal epilepsy

#### Evidence Tiers

- [T1] ILAE epilepsy classification and prognosis literature; Kwan & Brodie AED response data
- [T2] German epilepsy registry; GKV AU data for epilepsy
- [T3] Market convention; occupational restriction standards (§23 FeV driving licence)

---

# Part 2: Comorbidity Interaction Matrix

Underwriting algorithms typically add comorbidity risks linearly. In clinical reality, many disease combinations interact non-linearly — sometimes dramatically amplifying AU risk, sometimes being over-penalised because one condition is actually managed under another. This part provides a structured analysis of the most important interactions for KTG underwriting.

| Combination | Interaction Type | KTG Impact | Algorithm Failure Mode |
|---|---|---|---|
| Depression + chronic pain (back/fibromyalgia) | Synergistic amplification | Very high — pain catastrophisation, reduced rehabilitation engagement | Linear addition underestimates; expect 1.5–2× AU of individual conditions |
| T2DM + Hypertension | Multiplicative CV risk | High long-term; acute AU modest; tail risk cardiovascular events | Naïve linear addition; CV event risk is multiplicative not additive |
| GAD + chronic migraine | Bidirectional worsening | Moderate-high; anxiety lowers pain threshold, migraine worsens anxiety | Often separately coded; interaction invisible to algorithm |
| RRMS + depression | Neurological comorbidity | Very high; depression in MS often treatment-resistant; disability + mood | MS already flagged; depression may be under-coded; interaction missed |
| RA + CVD | Shared inflammatory pathway | High; RA independently elevates CV risk 50%; also shared AU drivers | RA loading + CV loading stacked naïvely; may over-penalise |
| Obesity (Class III) + OSA + T2DM | Metabolic-respiratory cluster | Very high; OSA impairs glucose control, fatigue drives AU | Three codes may each be loaded; combined effect is non-linear |
| Epilepsy + depression (AED-induced) | Iatrogenic comorbidity | Moderate; some AEDs (levetiracetam, topiramate) cause mood disorders | Depression coded separately; AED causality not recognised |
| Borderline PD + substance use disorder | Synergistic psychiatric | Very high; impulsivity + substance use = crisis spiral; worst AU pattern | May both be coded but interaction effect not captured; should always be expert review |

---

## Detailed Comorbidity Cases

### Case A: F33 (recurrent depression) + M79.7 (fibromyalgia)

**Clinical interaction:** Fibromyalgia syndrome and recurrent depression share neural pathways — central sensitisation and serotonergic dysregulation. Patients with both conditions experience higher pain severity, lower treatment response, and dramatically longer AU per episode. The combination is one of the most AU-intensive pairings seen in PKV.

**AU impact:** Expected AU 12–20 weeks/year; far exceeding either condition alone (depression ~8 weeks, FMS ~8 weeks separately).

**Underwriting recommendation:** Decline or very high loading with dual exclusion (musculoskeletal + psychiatric AU). Mandatory expert review.

**Expert review required:** Yes — mandatory

---

### Case B: E11 (T2DM, HbA1c 7.8%) + I10 (hypertension, 3 agents) + E66 (obesity Class II)

**Clinical interaction:** The metabolic syndrome triad. Each component amplifies the others: obesity worsens insulin resistance and blood pressure; hypertension accelerates diabetic kidney disease. The 10-year cardiovascular event risk in this combination significantly exceeds any single-component estimate. KTG risk arises from both acute events and chronic complications.

**AU impact:** Moderate current AU; high future tail risk from cardiac/renal events. Current AU ~4–8 weeks/year; 10-year disability risk substantial.

**Underwriting recommendation:** High loading (40–60%) or decline depending on HbA1c control and organ damage status. Do not apply three separate loadings naïvely.

**Expert review required:** Yes — multiplicative risk assessment required

---

### Case C: G35 (RRMS) + F33 (depression)

**Clinical interaction:** Depression occurs in ~50% of MS patients and is frequently under-treated. In MS, depression is not merely a psychological reaction but has neurobiological underpinnings (demyelination in limbic pathways). The combination produces a disability burden substantially higher than either alone. Standard antidepressant treatments are less effective in MS-related depression.

**AU impact:** RRMS alone: 8–15 weeks/year. RRMS + depression: 16–24 weeks/year or more.

**Underwriting recommendation:** Decline for standard KTG. Possible acceptance with very high loading and dual exclusion only. Expert review mandatory.

**Expert review required:** Yes — mandatory

---

### Case D: I48 (AF, paroxysmal) + I10 (hypertension, 2 agents) — over-penalised example

**Clinical interaction:** Paroxysmal AF in a 54-year-old with controlled hypertension on 2 agents and CHA₂DS₂-VASc = 2 (on DOAC). Many algorithms will flag both I48 and I10 with separate loadings and produce a combined loading that is clinically disproportionate. The actual AU risk here is moderate, primarily driven by hypertension; the AF per se adds stroke risk managed by DOAC.

**AU impact:** Expected AU 2–4 weeks/year. Manageable. AF episodes usually brief; cardioversions occasional.

**Underwriting recommendation:** Accept with single moderate loading (25–30%). Do NOT stack cardiovascular loadings naïvely. AF + controlled hypertension on DOAC is not equivalent to structural heart disease.

**Expert review required:** No — but algorithm output should be verified by human underwriter

---

### Case E: F60.3 (borderline PD) + F1x.2 (substance dependence)

**Clinical interaction:** The combination of borderline personality disorder and substance dependence produces the most unstable psychiatric profile in the KTG context. Impulsivity drives substance use; substance intoxication precipitates self-harm and crisis; crises lead to acute inpatient admissions; discharge leads to relapse. AU pattern is recurrent and unpredictable with sustained high frequency.

**AU impact:** AU highly erratic; 8–24 weeks/year in active phase; multi-month inpatient episodes possible.

**Underwriting recommendation:** Decline for KTG. No loading or exclusion option is actuarially adequate. Expert review mandatory.

**Expert review required:** Yes — mandatory decline

---

### Case F: M51.1 (disc prolapse post-microdiscectomy 18 months) + M54.5 (chronic LBP)

**Clinical interaction:** Persistent chronic LBP following disc surgery is common (15–30% of cases). The combination of a surgical history with ongoing M54.5 coding suggests incomplete recovery. The critical question is whether the chronic pain is mechanical (residual disc degeneration) or neuropathic/central (failed back surgery syndrome). Algorithms typically load both codes without assessing recovery quality.

**AU impact:** If genuine chronic pain post-surgery: 6–12 weeks AU/year. If good recovery with residual background pain: 2–4 weeks/year.

**Underwriting recommendation:** Request post-surgical functional assessment. Accept with musculoskeletal exclusion if surgeon's report indicates good outcome; higher loading or decline if failed back surgery pattern.

**Expert review required:** Yes — physician report required to distinguish outcomes

---

### Case G: G43 (migraine, episodic, 3 attacks/month) + F41.1 (GAD)

**Clinical interaction:** GAD and chronic migraine have a well-established bidirectional comorbidity. Anxiety lowers pain threshold and reduces triptan efficacy; migraine triggers anxiety about attacks (anticipatory anxiety). The interaction creates a self-reinforcing cycle. However, the combined AU is usually predictable and manageable if both conditions are well-treated.

**AU impact:** Expected AU 4–8 weeks/year combined; not dramatically above isolated conditions but consistently elevated.

**Underwriting recommendation:** Accept with moderate loading (20–30%). Both conditions well-documented; combined exclusion may be preferable to loading if sum insured is high. Not typically a mandatory expert review case.

**Expert review required:** No — algorithmic with human verification of treatment status

---

### Case H: E66 (obesity Class III, BMI 43) + post-bariatric surgery (3 years ago, BMI now 29)

**Clinical interaction:** This case is the reverse of typical obesity risk assessment. The current metabolic status post-bariatric surgery may be near-normal despite the historical E66 code. Algorithms flag E66 as high risk without recognising that successful bariatric surgery with sustained weight loss is a major favourable risk reversal. Current metabolic parameters (HbA1c, BP, lipids) are the appropriate basis for underwriting, not the historical BMI code.

**AU impact:** If post-bariatric remission of T2DM and hypertension: modest AU, closer to normal population.

**Underwriting recommendation:** Do not underwrite on historical E66 code alone. Request current BMI, HbA1c, blood pressure, medication list. If metabolic remission confirmed: accept with modest loading reflecting residual obesity-related musculoskeletal risk.

**Expert review required:** Yes — code-driven algorithm will produce wrong answer; human review required

---

# Part 3: Temporal Risk Assessment Framework

Time is the most underutilised dimension in algorithmic underwriting. A condition coded in the past is not the same risk as the same condition coded last week. This part builds a practical framework for time-sensitive KTG risk assessment.

---

## 3.1 Look-Back Windows by Condition Category

| Condition Category | Standard Look-Back | Extended Look-Back | Rationale |
|---|---|---|---|
| Single episode mood disorder (F32), full remission | 3 years | 5 years if severe/hospitalised | Recurrence risk falls to near-baseline after 3–5 years [T2] |
| Recurrent mood disorder (F33) | 10 years | Lifetime | Each prior episode is prognostically relevant; no meaningful decay [T1] |
| Anxiety/adjustment disorders (F40–F43) | 3 years | 5 years if chronic/hospitalised | Time-limited conditions; single episodes decay quickly [T2] |
| Personality disorders (F60–F61) | Lifetime | Lifetime | Chronic by definition; no time decay [T1] |
| Musculoskeletal (M54 non-specific) | 3 years | 5 years if chronic | Acute episodes lose relevance after 3 years without recurrence [T2] |
| Musculoskeletal (M51 structural + surgery) | 5 years | 10 years if multilevel/failed surgery | Structural changes and surgical history carry long-term relevance [T2] |
| RA (M05/M06) | 5 years | Lifetime if active | Progressive systemic disease; remission periods relevant but history matters [T1] |
| Hypertension (I10, controlled) | 3 years | 5 years if organ damage | Well-controlled I10 decays in relevance quickly; organ damage does not [T2] |
| CAD/post-MI (I25, I21) | 5 years | Lifetime | Cardiovascular events are landmark events; never fully decay [T1] |
| AF (I48) | 5 years | Lifetime if permanent | Paroxysmal AF can resolve; permanent AF does not [T2] |
| T2DM (E11) | 5 years | Lifetime if complications | Controlled T2DM on diet may remit; established complications do not [T1] |
| Obesity (E66) | 3 years (current BMI matters most) | 5 years for Class III | Current metabolic status more important than historical code [T3] |
| MS (G35) | Lifetime | Lifetime | Chronic progressive; no time decay [T1] |
| Migraine (G43) | 3 years | 5 years if chronic pattern | Episodic migraine may remit; chronic pattern history more durable [T2] |
| Epilepsy (G40) | 5 years | Lifetime if refractory | Seizure-free period is the key variable; history sets context [T1] |

---

## 3.2 Remission: Clinical Definition vs Underwriting Verification

> **Key principle:** Clinical remission requires active clinical assessment. Underwriting operates from application data and physician reports only. There is always a gap between what remission means clinically and what can be verified from documentary evidence. Never assume remission from absence of recent AU alone.

### What counts as remission clinically

- **Mood disorders:** absence of DSM/ICD criteria for ≥8 weeks; normal GAF score; functional return to prior occupational level [T1]
- **Anxiety disorders:** no diagnosable anxiety disorder criteria met; anxiety sensitivity normalised; no avoidance behaviour [T1]
- **RA:** DAS28 <2.6 for ≥6 months; no active synovitis; stable or improving imaging [T1]
- **T2DM:** HbA1c <6.5% off glucose-lowering medication = remission (ADA criteria, T2DM specific); very rare [T1]
- **Epilepsy:** no seizures for ≥24 months on stable AED regimen [T1]

### What underwriting can realistically verify

- Absence of AU episodes attributable to the condition in the look-back window
- Absence of active medication for the condition (or stable prophylactic dose)
- GP or specialist letter confirming remission status — most valuable but subject to availability
- No inpatient admissions for the condition in the look-back window
- Absence of relevant specialist follow-up (rheumatologist, neurologist, psychiatrist visits in the recent period)

> ⚠ **Warning:** Absence of evidence is not evidence of absence. An applicant who has not seen a GP for 2 years and has no coded diagnoses is not necessarily in remission — they may be untreated or seeking no care. Always assess the plausibility of claimed remission against the clinical trajectory of the condition.

---

## 3.3 Red Flags That Override Time Decay

The following red flags suspend normal time-decay rules and require manual expert review regardless of how much time has passed:

| Red Flag | Why it overrides time decay |
|---|---|
| Multiple episodes of the same condition | Pattern of recurrence is itself a permanent risk marker; no time decay applies to the count |
| Inpatient psychiatric admission | Indicates severity sufficient to require hospitalisation; permanently modifies risk class |
| Repeated AU >8 weeks for same condition in any 12-month period | Suggests chronification or inadequate treatment; persistent elevated risk |
| Ongoing specialist follow-up (psychiatrist, neurologist, rheumatologist) | Active specialist care = condition not in true remission regardless of AU gap |
| Ongoing disease-specific medication | Prophylactic antidepressants, DMARDs, DMTs, AEDs = active management, not remission |
| Residual symptoms documented in physician report | Even if sub-threshold for diagnosis, residual symptoms predict future episodes |
| Surgery history for the condition | Structural changes are permanent; surgical history for disc, cardiac, joint never fully decays |
| Chronic pain patterns with opioid or gabapentinoid use | Central sensitisation marker; opioid use in non-malignant pain = very high long-term AU predictor |
| Prior disability pension application or decision | Objective external severity marker; indicates impairment sufficient to approach social insurance system |

---

# Part 4: Practical Documentation and Datenschutz

---

## 4.1 Data Minimisation Principles

> **Legal basis:** Art. 9 GDPR (sensitive health data) and §213 VVG (Auskunftspflichten) apply. Health data collected in underwriting must be adequate, relevant, and limited to what is necessary for the specific risk assessment purpose. This section provides operational guidance only — it does not replace legal or DPO review.

**Collect only what the risk decision requires.** If the underwriting decision can be made on diagnosis + AU duration + remission status, do not collect the full medical record.

**Purpose limitation.** Data collected for KTG underwriting cannot be used for other insurance products or marketing without separate consent. Note this in the case file.

**Do not copy raw physician reports verbatim.** Summarise the clinically relevant findings. Do not reproduce sensitive social or psychological history that is not directly relevant to the AU risk.

**Retain only what is needed for the audit period.** The underwriting decision and its documented basis must be retained. Supporting raw data should be deleted or pseudonymised after the retention period.

**Separate input, algorithm output, and human judgment.** These three components of the decision must be clearly distinguishable in the documentation.

---

## 4.2 Documentation Template for a Single Underwriting Decision

| Field | Content | Data Source |
|---|---|---|
| Case ID | Internal identifier (pseudonym — no full name in working document) | System |
| Underwriting date | Date of decision | System |
| Product / KTG sum insured | KTG daily rate applied for (€/day) | Application |
| Applicant profile | Age, occupation category, employment status only | Application (minimised) |
| ICD codes documented | ICD-10-GM codes as declared and/or extracted from health questionnaire | Application + physician report |
| Relevant AU history | Date ranges and durations only; no diagnosis narrative beyond code | Physician report (extracted) |
| Algorithm output | Decision flag (accept/review/decline); loading percentage; stated rule triggers | Algorithm |
| Clinical review summary | 2–5 sentences: what findings are relevant, why they matter for KTG AU risk | Medical underwriter |
| Prognostic factors assessed | Checklist: remission Y/N; medication Y/N (type abstracted); hospitalisation Y/N; episode count; time since last episode | Physician report + application |
| Evidence tier | T1/T2/T3 for the primary decision rule applied | Medical underwriter |
| Human decision | Accept / Accept with loading (%) / Accept with exclusion / Postpone / Decline | Medical underwriter |
| Deviation from algorithm | Yes/No. If yes: brief rationale for override | Medical underwriter |
| Data minimisation note | Confirm that no unnecessary health data has been retained in working file | Medical underwriter |
| Reviewer sign-off | Initials of reviewing underwriter if double-check applied | QA process |

---

## 4.3 How to Write a Clinical Rationale Without Over-Documenting

Good clinical rationale is concise, factual, and tied directly to the AU risk. It does not reproduce social history, family dynamics, or psychological context unless these are directly prognostically relevant.

> **WRONG:** "Applicant disclosed history of depression following divorce in 2019, relationship breakdown led to significant distress, started antidepressant therapy, disclosed feeling hopeless, seen by psychiatrist Dr. XY, hospitalised for 3 weeks at Klinikum XY."
>
> **RIGHT:** "Single episode F32.2 (severe depression), 2019; inpatient treatment 3 weeks; remission confirmed by GP letter 2021; antidepressant discontinued 2022. No recurrence since. AU: 8 weeks in 2019, none thereafter. Decision basis: single severe episode, full remission >36 months, no recurrence markers. [T2]"

---

# Part 5: Worked Case Studies

These 10 cases cover the primary underwriting scenarios in KTG. Cancer cases have been replaced with high-frequency PKV scenarios. Each case is structured to train the clinical-algorithmic bridge role: identifying what the algorithm did correctly, where it failed, and how human judgment corrects it.

---

## Case 1: Single Psychiatric Episode — Algorithm Overreaction

**Applicant:** Age 38 | Marketing Manager (Angestellter) | KTG €150/day

**ICD History:**
- F32.1 (moderately severe depressive episode): Q2 2021, AU 7 weeks, treated with escitalopram 10mg
- GP certificate of remission: December 2021. Medication discontinued: March 2022
- No further psychiatric contacts, no AU for psychiatric cause since 2021

**Algorithm Flag:** F32.1 coded — psychiatric condition detected. Automated output: Decline (psychiatric AU risk). Rule triggered: F32.x = automatic decline for KTG.

**Clinical Analysis:**

*What the algorithm got right:* The algorithm correctly identified the psychiatric diagnosis and flagged it for review.

*What it got wrong:* Applying a blanket decline rule to F32 regardless of episode count, severity, time since episode, or remission status. A single moderate episode now 3+ years in full remission is not equivalent to recurrent severe depression. This is a textbook algorithmic overreaction failure mode.

*Additional evidence needed:* GP letter confirming remission (already present). Confirm absence of antidepressant on current medication list. Confirm no further AU episodes. No specialist follow-up.

**Underwriting Recommendation:** Accept with modest loading (10–15%) for 2 years, then standard terms. No psychiatric exclusion required for single episode in stable long-term remission. Evidence basis: T2 (observational data on single-episode recurrence decay).

**Documentation Summary:** F32.1, single episode 2021 (7 weeks AU), full remission >36 months, medication discontinued >24 months, no recurrence markers. Algorithm decline overridden. Human decision: accept with 10% loading. [T2]

> ⚠ **Key Learning — Algorithmic failure mode: overreaction.** F32 blanket decline ignores temporal risk decay and episode count. Single episode in full remission is not a decline diagnosis.

---

## Case 2: Recurrent Depression — Algorithm Underestimation

**Applicant:** Age 44 | Lehrerin (Beamtin) | KTG €100/day

**ICD History:**
- F33.1 (recurrent depressive disorder, moderate): episodes in 2018 (5 weeks AU), 2020 (9 weeks AU), 2022 (11 weeks AU)
- Currently on sertraline 100mg — described in health questionnaire as "for prevention"
- Last episode remitted: Q4 2022. No psychiatric hospitalisation. Regular GP follow-up.

**Algorithm Flag:** F33 coded. Automated output: Accept with 25% loading. Rule triggered: F33 = loading tier 2. Algorithm interpreted most recent AU as >12 months ago → applied time decay.

**Clinical Analysis:**

*What the algorithm got right:* Correctly identified F33 as elevated risk relative to F32.

*What it got wrong:* Applied time decay to recurrent depression as if it were a single episode. F33 with three documented episodes and ongoing medication has no meaningful time decay. The loading of 25% is grossly insufficient for this profile. Algorithm failure mode: underestimation of recurrence risk in F33.

*Additional evidence needed:* Confirm current medication (sertraline = active management, not remission). Establish episode count and AU duration trend. Note: AU is escalating (5, 9, 11 weeks) — this is the opposite of improving.

**Underwriting Recommendation:** Decline for standard KTG, or accept with psychiatric AU exclusion only (if acceptable to applicant). This is not a loading case — three escalating episodes with ongoing medication is a decline or exclusion-only profile. [T3 market practice, T2 recurrence data]

**Documentation Summary:** F33.1, 3 episodes 2018–2022, escalating AU (5/9/11 weeks), ongoing antidepressant. Algorithm output (25% loading) overridden — insufficient for demonstrated recurrence pattern. Human decision: decline or psychiatric exclusion only. [T2/T3]

> ⚠ **Key Learning — Algorithmic failure mode: underestimation.** Time decay logic must not be applied to recurrent conditions. Episode count and AU trend are more informative than time since last episode.

---

## Case 3: Adjustment Disorder — Correct Acceptance (Algorithm Broadly Right)

**Applicant:** Age 29 | Software Engineer | KTG €120/day

**ICD History:**
- F43.2 (adjustment disorder with depressed mood): 2022, following job redundancy, AU 4 weeks
- Treated with 6 sessions CBT; no medication
- Fully returned to work; new employment secured within 3 months; no further contacts

**Algorithm Flag:** F43 coded — psychiatric history. Automated output: Accept with 15% loading. Review recommended.

**Clinical Analysis:**

*What the algorithm got right:* The algorithm correctly identified the psychiatric code and did not decline. The 15% loading is in the right zone for a recent event.

*What it got wrong:* Loading may be slightly high for a true adjustment disorder with complete resolution and no recurrence. The stressor (redundancy) was time-limited and resolved. CBT without medication = good prognostic sign.

*Additional evidence needed:* Confirm stressor has resolved (new employment = objective marker). Confirm no further psychiatric contacts. No medication history. 2-year follow-up period clean.

**Underwriting Recommendation:** Accept at standard terms, or at most 10% loading for 1 year. This is a case where the algorithm got broadly right but slightly over-loaded. F43 with complete stressor resolution and no recurrence is near-standard-risk after 18 months. [T2]

**Documentation Summary:** F43.2, single episode 2022, stressor resolved, CBT only, no recurrence >24 months. Algorithm 15% loading reviewed and reduced to 0% (standard terms). [T2]

> ⚠ **Key Learning — Algorithmic failure mode: minor overreaction.** Z73 and F43 with stressor resolution are not equivalent to F32/F33. Validate stressor resolution before loading.

---

## Case 4: Musculoskeletal Without Surgery — Missing Occupation Data

**Applicant:** Age 51 | Physiotherapist (self-employed) | KTG €200/day

**ICD History:**
- M51.1 (lumbar disc prolapse with radiculopathy, L4/L5): diagnosed 2021, AU 9 weeks
- Conservative management: physiotherapy, NSAIDs, epidural steroid injection ×2
- MRI 2022: persistent disc bulge L4/L5 without current radiculopathy
- M54.5 coded: 2023, AU 2 weeks, described as "flare of pre-existing back condition"

**Algorithm Flag:** M51.1 + M54.5 — musculoskeletal history. Algorithm output: Accept with musculoskeletal exclusion + 30% loading. Rule: M51 with recurrence = exclusion + loading.

**Clinical Analysis:**

*What the algorithm got right:* Identifying the structural disc pathology and applying an exclusion is clinically appropriate. This is a recurrent condition.

*What it got wrong:* The 30% loading on top of the exclusion is likely excessive. If the musculoskeletal exclusion covers the primary risk, the loading should reflect residual non-musculoskeletal risk only. The critical missed factor here is occupation — physiotherapy is high-demand physical work. The occupation multiplier should trigger automatic expert review, not just loading.

*Additional evidence needed:* Confirm occupation involves significant manual patient handling. Request most recent functional assessment — can the applicant maintain full case load? Any surgical referral pending? Current medication (opioids or not)?

**Underwriting Recommendation:** Accept with musculoskeletal exclusion. Remove loading given exclusion covers the primary risk. However: flag for expert review due to occupation-diagnosis interaction (physiotherapist + M51.1 = materially different risk than same diagnosis in a software developer). Consider whether KTG sum insured justifies a higher-level physical demand assessment. [T2/T3]

**Documentation Summary:** M51.1 + M54.5, physiotherapist occupation, recurrent mechanical back condition. Musculoskeletal exclusion applied. Loading removed — exclusion adequately captures risk. Occupation flagged for expert review. [T2/T3]

> ⚠ **Key Learning — Algorithmic failure mode: missing occupation data.** Identical diagnoses carry categorically different risk in physical vs sedentary occupations. Occupation must be integrated into musculoskeletal risk assessment.

---

## Case 5: Musculoskeletal With Surgery — Incomplete Recovery Assessment

**Applicant:** Age 47 | Logistics Manager (warehouse supervision) | KTG €130/day

**ICD History:**
- M51.1 (L5/S1 disc prolapse with radiculopathy): 2020, AU 14 weeks
- L5/S1 microdiscectomy: Q3 2020
- Post-surgical: physiotherapy completed 2021. AU for M54.5: 2021 (3 weeks), 2022 (5 weeks)
- Current: no documented specialist follow-up. NSAIDs PRN. Works full-time.

**Algorithm Flag:** M51.1 (surgery history) + M54.5 (recurrent). Algorithm output: Decline. Rule: post-disc-surgery + recurrent AU = decline.

**Clinical Analysis:**

*What the algorithm got right:* The post-surgical + recurrent AU pattern is a legitimate concern. The algorithm is not wrong to flag this as high risk.

*What it got wrong:* Decline without requesting a post-surgical assessment is premature. The recurrent M54.5 episodes (3 and 5 weeks) may represent normal post-surgical rehabilitation variability, or may indicate ongoing structural instability. The outcome quality of the surgery is unknown. Occupation is relevant — warehouse supervision is semi-physical.

*Additional evidence needed:* Request surgeon's follow-up report or GP report on post-surgical outcome. Key questions: is there residual neurological deficit? Is the AU trend improving or worsening? Are there signs of re-herniation? Is the patient progressing toward full recovery or chronic pain syndrome?

**Underwriting Recommendation:** Postpone decision pending post-surgical assessment report. If surgeon confirms good anatomical result and functional recovery: accept with musculoskeletal exclusion. If report confirms chronic pain / failed back surgery syndrome markers: decline. Do not decline based on ICD codes alone without functional outcome data. [T2/T3]

**Documentation Summary:** M51.1, microdiscectomy 2020, recurrent M54.5 post-op. Algorithm decline deferred. Physician report requested. Decision conditional on recovery assessment. [T2/T3]

> ⚠ **Key Learning — Algorithmic failure mode: premature decline.** Post-surgical ICD history must be evaluated against functional outcome, not just code presence. Physician report is mandatory in this scenario.

---

## Case 6: Controlled T2DM Plus Cardiovascular Comorbidity

**Applicant:** Age 57 | Accountant (Steuerberater) | KTG €180/day

**ICD History:**
- E11.9 (T2DM, no complications): diagnosed 2017. HbA1c 7.1% on metformin 1g BD
- I10 (essential hypertension): 2015, on ramipril 5mg + amlodipine 5mg
- E78.5 (hyperlipidaemia): atorvastatin 20mg. No AU attributable to metabolic conditions.
- BMI 27 (self-reported)

**Algorithm Flag:** E11 + I10 + E78 — metabolic triad. Algorithm output: 45% loading + metabolic exclusion. Rules stacked: E11 = 20%, I10 = 15%, E78 = 10% additive.

**Clinical Analysis:**

*What the algorithm got right:* Correctly identifying the metabolic triad as elevated risk. The comorbidity cluster is the right focus.

*What it got wrong:* Naïve linear stacking of loadings. The actual current AU risk from this well-controlled accountant is low (sedentary occupation, HbA1c 7.1%, BP presumably controlled on 2 agents). The correct underwriting question is: what is the long-term tail risk from cardiovascular events, and how does the current control status modify it? The 45% loading overestimates current risk.

*Additional evidence needed:* Confirm current HbA1c (available in health questionnaire). Confirm BP reading. Check for any early complication markers (microalbuminuria? CKD stage?). Occupation is clearly sedentary — occupation modifier is favourable.

**Underwriting Recommendation:** Accept with single integrated metabolic loading of 25–30%, reflecting: well-controlled T2DM (HbA1c 7.1%), controlled hypertension on 2 agents, sedentary occupation, no complications. Add metabolic exclusion for T2DM-direct complications. Do not stack three separate loadings naïvely. [T3; T2 — metabolic control evidence]

**Documentation Summary:** E11.9 (HbA1c 7.1%, metformin), I10 (controlled, 2 agents), E78.5. Sedentary occupation. Algorithm stacked loading (45%) overridden. Integrated assessment: 28% loading + metabolic exclusion. [T2/T3]

> ⚠ **Key Learning — Algorithmic failure mode: naïve linear stacking.** Metabolic comorbidities require integrated assessment, not additive loading. Control status and occupation must modify the output.

---

## Case 7: Mixed Psychiatric and Physical Morbidity

**Applicant:** Age 42 | Kindergarten teacher (Erzieherin) | KTG €90/day

**ICD History:**
- F32.0 (mild depressive episode): 2020, AU 4 weeks. Resolved without medication.
- M79.7 (fibromyalgia syndrome): diagnosed 2021 by rheumatologist. Duloxetine 60mg (dual-use: pain + mood).
- AU 2022: 6 weeks coded M79.7. AU 2023: 8 weeks coded F32.0 (GP recoded same episode).
- Ongoing rheumatology follow-up. Part-time work (60%) since 2022.

**Algorithm Flag:** F32 + M79.7 — dual comorbidity. Algorithm output: Accept with 35% loading. Rules: F32 = 15%, M79 = 20% additive.

**Clinical Analysis:**

*What the algorithm got right:* Correctly identifying dual comorbidity as elevated risk.

*What it got wrong:* Multiple problems: (1) the coding inconsistency (same episode coded differently in 2022 vs 2023) is missed; (2) the depression and FMS are not independent conditions — duloxetine treats both, and they share pathophysiology; (3) the most important signal — part-time work since 2022 — is not captured in ICD coding at all; (4) AU trend is worsening. This is a significantly under-assessed risk.

*Additional evidence needed:* Part-time employment (60%) is an objective marker of significant ongoing functional impairment. Request rheumatology report: FMS severity scale, current functional capacity. Clarify duloxetine dose and indication. Assess whether full-time return to work is realistic given occupation (physical, emotional demands of Erzieherin are high).

**Underwriting Recommendation:** This profile requires mandatory expert review. The part-time employment marker alone changes the risk category. If full occupational capacity cannot be confirmed: decline or very high loading with dual exclusion. If rheumatology report confirms stabilisation with realistic return to full-time: accept with dual exclusion (psychiatric + musculoskeletal) and moderate loading. [T2/T3]

**Documentation Summary:** F32 + M79.7 (FMS), duloxetine dual-use, part-time work since 2022 (objective impairment marker), worsening AU trend. Algorithm 35% loading is insufficient. Expert review flagged. Decision deferred to physician report. [T2/T3]

> ⚠ **Key Learning — Algorithmic failure mode: missing functional status data.** ICD codes do not capture employment capacity. Part-time work is one of the most powerful AU risk markers and is invisible to code-based algorithms.

---

## Case 8: High-Income Self-Employed Edge Case

**Applicant:** Age 49 | Consultant / Managing Partner (self-employed) | KTG €300/day

**ICD History:**
- I48.0 (paroxysmal AF): diagnosed 2022, one cardioversion performed, now rate-controlled on bisoprolol + rivaroxaban
- I10 (hypertension): 2018, on olmesartan 20mg, well-controlled
- G43.0 (migraine without aura): since 2015, 2–3 attacks/month, sumatriptan responsive
- No AU history documented (self-employed — no AU certificates issued)

**Algorithm Flag:** I48 + I10 + G43 — multiple flags. Algorithm output: Refer to manual underwriting. Rule: I48 = automatic manual review; sum insured exceeds auto-approval limit.

**Clinical Analysis:**

*What the algorithm got right:* Correctly escalating due to high sum insured and AF diagnosis. I48 as an automatic manual review trigger is appropriate.

*What it got wrong:* Nothing obviously wrong — escalation is correct. The challenge here is clinical: the applicant's low AU history reflects self-employed status, not health. Self-employed applicants manage AU differently (often working through illness). This creates both under-reporting and a genuine AU risk that only materialises if a significant acute event occurs.

*Additional evidence needed:* (1) Financial underwriting — confirm income to validate €300/day sum; (2) AF: request echocardiography result (confirm no structural abnormality, confirm LVEF); (3) CHA₂DS₂-VASc calculation (already on anticoagulant — favourable); (4) Migraine: confirm frequency and triptan efficacy from GP letter.

**Underwriting Recommendation:** Accept with cardiovascular loading (25%) reflecting AF + controlled hypertension. Migraine: accept at standard terms (episodic, triptan-responsive, low AU impact). No psychiatric or musculoskeletal risk. Financial underwriting confirmation required for €300/day sum. Self-employed status noted in file. [T2/T3]

**Documentation Summary:** I48.0 (cardioverted, anticoagulated), I10 (controlled), G43.0 (episodic, low impact). Self-employed — no AU history; financial income verified. 25% cardiovascular loading applied. AF management confirmed adequate. [T2/T3]

> ⚠ **Key Learning — Algorithmic failure mode: AU history gap for self-employed.** Absence of AU records in self-employed applicants is not equivalent to health — it reflects payment structure. Risk assessment must rely more heavily on clinical data and less on AU history in this group.

---

## Case 9: Migraine Plus GAD — Improving Trend Ignored

**Applicant:** Age 34 | Journalist (angestellt) | KTG €110/day

**ICD History:**
- G43.0 (migraine without aura): since 2018, average 4–6 attacks/month, on propranolol 40mg BD as prophylaxis
- F41.1 (generalised anxiety disorder): diagnosed 2020, on sertraline 50mg, 12 sessions CBT completed 2021
- AU: 2019 (3 weeks, migraine), 2020 (5 weeks, mixed migraine/anxiety), 2021 (2 weeks, migraine), 2022 (1 week, migraine)
- No hospitalisation. Stable employment.

**Algorithm Flag:** G43 + F41 — dual flag. Algorithm output: 40% loading. Rules: G43 = 20%, F41 = 20% additive.

**Clinical Analysis:**

*What the algorithm got right:* Identifying both conditions as elevated risk for KTG is correct. The 4–6 migraine days/month is significant.

*What it got wrong:* Linear stacking misses interaction and ignores trend. The GAD is well-managed (CBT completed, stable sertraline), and the AU trend is improving (5 weeks in 2020 → 1 week in 2022). The algorithm applies the same loading regardless of trajectory.

*Additional evidence needed:* Confirm current migraine attack frequency from GP or neurologist. Confirm GAD remains in stable remission. Confirm propranolol efficacy — has attack frequency reduced since initiating prophylaxis?

**Underwriting Recommendation:** Accept with single integrated neuropsychiatric loading of 20–25%, reflecting: improving AU trend, GAD in stable remission, migraine partially controlled on prophylaxis. Consider neurological exclusion rather than high loading for the migraine component. [T2/T3]

**Documentation Summary:** G43 (4–6 attacks/month, on propranolol) + F41.1 (GAD in stable remission on sertraline). AU trend improving. Algorithm 40% stacked loading overridden. Integrated loading 22% + neurological exclusion. [T2/T3]

> ⚠ **Key Learning — Algorithmic failure mode: ignoring trend data.** An improving AU trajectory materially changes the risk assessment but is invisible to code-based algorithms that treat conditions statically.

---

## Case 10: Algorithm Was Correct — Validating the Output

**Applicant:** Age 53 | Construction site supervisor (manual oversight + physical presence) | KTG €160/day

**ICD History:**
- F33.2 (recurrent depression, severe without psychotic features): episodes 2015, 2018, 2021 — each with AU 10–14 weeks
- M51.1 (lumbar disc prolapse with radiculopathy, L3/L4): 2019, AU 12 weeks, surgery (microdiscectomy) 2019
- M54.5: recurrent post-surgery, AU 2021 (6 weeks), 2022 (8 weeks)
- E11.9 (T2DM, HbA1c 8.2%): 2020, on metformin + sitagliptin. No complications documented yet.
- Current: duloxetine 120mg, still seeing psychiatrist quarterly

**Algorithm Flag:** F33 + M51 (post-surgery) + M54 (recurrent) + E11 — multiple flags. Algorithm output: Decline. Rules: F33 with ≥3 episodes = decline; post-surgical M51 with recurrent AU = decline; E11 HbA1c >8% = decline.

**Clinical Analysis:**

*What the algorithm got right:* This time, the algorithm is correct. Three recurrent severe depressive episodes with ongoing psychiatric follow-up and duloxetine, post-surgical disc pathology with worsening AU trend, poor glycaemic control, and semi-physical occupation — the combination is uninsurable for standard KTG without major restrictions.

*What it got wrong:* The algorithm may not have assessed whether any element of the risk could be ring-fenced. However, in this case the three independent high-risk conditions with no favourable prognostic markers means the output is substantively correct.

*Additional evidence needed:* No additional evidence would change the decision. Even with a physician report showing partial improvement on one dimension, the combined load is too high. T2DM HbA1c 8.2% indicates poor control — confirm but outcome unlikely to change decision.

**Underwriting Recommendation:** Decline for standard KTG. If applicant insists, discuss limited KTG product with 6-month waiting period, psychiatric + musculoskeletal + metabolic exclusion, and low daily sum — but this is marginal product territory. The algorithm's decline is validated. [T2/T3]

**Documentation Summary:** F33.2 (3 episodes, ongoing medication), M51.1 (post-surgery, worsening recurrence), E11.9 (HbA1c 8.2%). Algorithm decline validated by human review. No overriding factors identified. Decline confirmed. [T2/T3]

> ⚠ **Key Learning: Validation is as important as override.** Human expert must be able to confirm when the algorithm is right, not just when it is wrong. Document the validation explicitly.

---

# Part 6: Quality Assurance and Red-Team Framework

---

## 6.1 What is a Regression Test Suite for Underwriting?

A regression test suite in the underwriting context is a curated library of cases with known correct answers, which is re-run against the algorithm after any model update to verify that prior correct decisions are preserved and new decisions are consistent. It serves the same function as software regression testing: detecting unintended behavioural changes.

### How to Build the Test Suite

- **Seed with validated historical cases:** Cases where human expert review produced a documented, justified final decision. These become the ground-truth corpus.
- **Label each case with:** algorithm output, human override (if any), evidence tier of the final decision, and the category of algorithmic failure mode (if applicable).
- **Tier the suite by sensitivity:** Tier A = clear-cut cases (both algorithm and human agree); Tier B = borderline cases; Tier C = known algorithm failure mode cases.
- **Minimum suite size:** aim for ≥200 cases before first model update; ≥500 for ongoing production. Tier C (failure modes) should constitute ≥30% of the suite.
- **Version-control the suite:** track which model version produced which output on each case.

---

## 6.2 Building a Borderline Case Library

| Case Category | Selection Criteria | Minimum Count |
|---|---|---|
| Edge cases | Any diagnosis where the accept/decline boundary is within ±1 prognostic factor | 30 |
| Comorbidity cases | Two or more ICD codes from the comorbidity matrix; interaction effect relevant | 40 |
| Time-decay cases | Same diagnosis, varied time-since-episode (6 months, 12 months, 24 months, 5 years, 10 years) | 25 per major condition |
| High-value applicants | KTG sum ≥€200/day; self-employed; financial underwriting implications | 20 |
| Coding ambiguity cases | ICD code differentials: F32 vs F43; M51 vs M54; I48.0 vs I48.2; E11.9 vs E11.7 | 30 |
| Occupation-diagnosis interaction | Same ICD history, different occupation categories (manual vs sedentary) | 20 |
| Post-treatment states | Post-bariatric surgery; post-cardiac intervention; post-surgical disc; completed CBT | 20 |

---

## 6.3 Detecting Concept Drift in Underwriting Models

Concept drift occurs when the statistical relationship between input features and correct underwriting decisions changes over time — for example, because disease management has improved (making a historically high-risk diagnosis now lower-risk) or because coding practices have changed. For underwriting algorithms, concept drift is slow but consequential.

### Drift Detection Methods

**Override rate tracking.** If the rate of human expert overrides is increasing, the model is likely drifting from correct decisions. Track monthly override rate by decision type (accept overridden to decline, decline overridden to accept, loading changed). A sustained upward trend in override rate is the primary drift signal.

**Input feature distribution monitoring.** Track the distribution of incoming ICD code combinations, applicant ages, and comorbidity profiles month-on-month. Significant distributional shift in inputs may require retraining even if override rate is stable.

**Periodic regression suite re-runs.** Re-run the full regression suite at least quarterly. Flag any case where the new model produces a different output from the previously validated answer.

**Claims experience feedback loop.** Link underwriting decisions to subsequent claims (where legally permissible). If accept decisions are generating materially higher AU claims than expected by the underwriting model, this is evidence of systematic model under-estimation.

---

## 6.4 Structuring Periodic Independent Model Review

Independent review of the underwriting model should occur at a minimum annually, and following: any significant AU epidemic (pandemic, sudden-onset population-level disease change), any major clinical guideline update affecting underwritten conditions, any change in the algorithm rules exceeding 10% of decision rules.

| Review Component | Frequency | Responsible Party |
|---|---|---|
| Full regression suite re-run | Quarterly | Algorithm QA team + medical underwriter |
| Override pattern analysis (aggregate) | Monthly | Medical underwriting manager |
| External clinical evidence scan (guideline updates) | Semi-annual | Medical underwriter |
| Claims-to-underwriting feedback analysis | Annual | Actuarial + medical underwriting |
| Independent external audit of model rules | Annual | External clinical expert panel |
| Bias and fairness review (age, occupation, gender proxies) | Annual | QA team + DPO |

---

## 6.5 Algorithm-to-Human Interface: Override Protocol

> **Design principle:** The algorithm should produce a provisional decision and a structured reasoning trace (which rules fired, which features triggered them). The human expert's job is not to re-underwrite from scratch but to validate the reasoning trace — checking that the right rules fired, that no relevant clinical features were missed, and that the evidence tier is appropriate.

### Override Categories

**Category 1 — Factual error.** Algorithm used wrong ICD interpretation, failed to apply time decay, counted episodes incorrectly. Override is mandatory; document the specific error.

**Category 2 — Missing clinical context.** Algorithm lacks occupation data, medication data, functional status data. Human expert integrates this; document what was added.

**Category 3 — Interaction failure.** Algorithm applied linear risk addition to synergistic comorbidities. Human expert applies integrated assessment. Document the interaction rationale.

**Category 4 — Threshold judgment.** Algorithm's decision is within the acceptable range but at a boundary; human expert has discretion. Document why the boundary was crossed.

**Category 5 — Algorithm validated.** Human review confirms algorithm output is correct. Document the validation explicitly — this is as important as overrides for model QA.

---

## 6.6 Using Override Patterns as Model Weakness Signals

Every override is a data point about model weakness. Aggregate override analysis is the most powerful tool for identifying systematic model failures.

| Override Pattern | Model Weakness Indicated | Action |
|---|---|---|
| High override rate for F32/F43 → accept override | Blanket psychiatric decline or over-loading rules | Revise psychiatric time-decay and episode-count rules |
| High override rate for metabolic triad → loading reduced | Naïve linear stacking of metabolic codes | Implement integrated metabolic risk calculator |
| High override rate for self-employed → data insufficient | AU history gap for self-employed not handled | Add self-employed flag; change evidence requirement |
| High override rate for post-surgical cases | Surgery outcome not distinguished from surgery history | Add post-surgical outcome state as explicit model feature |
| Sustained increase in Category 5 (validation) overrides | Model broadly correct; human review effort wasted | Consider raising auto-approval threshold for validated case types |
| Increasing mismatch between loading and subsequent claims | Systematic calibration error in loading levels | Actuarial recalibration of loading tables; external expert review |

> **Minimum data requirement for override tracking:** Case ID | Algorithm output | Override category (1–5) | Human decision | ICD codes involved | Deviation direction (more restrictive / less restrictive) | Reviewer ID | Date. Monthly aggregate reports should be reviewed by the medical underwriting manager and fed into the model development backlog.

---

# Appendix: Evidence Tier Reference

| Tier | Description | Examples |
|---|---|---|
| **T1** | Guideline-level evidence or strong, consistent observational data. Conclusions supported by national/international clinical guidelines or large cohort studies with directly applicable outcomes. | DGPPN S3 depression guideline recurrence rates; ESC hypertension staging; EDSS natural history in MS; NVL Kreuzschmerz acute LBP prognosis |
| **T2** | Moderate-quality observational evidence. Register data, health insurance (GKV/PKV) actuarial data, or cohort studies with relevant but imperfectly applicable outcomes. | BKK Gesundheitsreport AU data; GKV disability statistics by diagnosis; German MS registry; fibromyalgia patient survey data |
| **T3** | Expert judgment and market practice. No direct actuarial or clinical evidence base; rules derived from industry convention, internal expert review, or analogical reasoning. | Loading percentages for specific underwriting decisions; decline thresholds for personality disorders; self-employed AU handling; most specific KTG loading figures |

> When T3 rules are applied, this should always be documented. T3 rules are the primary target for evidence upgrading: where market practice and clinical evidence diverge, the rule should be reviewed against any available literature and flagged for periodic re-evaluation.
