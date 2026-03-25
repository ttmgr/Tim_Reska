# Interview Talking Points — Medical Underwriting Expert Role

*Tim Reska | March 2026*
*Interview with Birgit Koenig, CEO Allianz Digital Health*
*Purpose: Demonstrate AI capabilities for medical underwriting through a working prototype built in ~48 hours with Claude*

---

## 1-Minute Elevator Pitch

> You said the expert needs to understand disease progressions — the rest can be done via LLMs. That's exactly my profile.
>
> My PhD was 4 years of modeling biological state transitions: how pathogens evolve through resistance stages over time. The math is Continuous-Time Markov Chains — the same framework I used here to model Alzheimer's progression through 7 clinical stages and cardiovascular disease through 5 states. I didn't learn this for the interview. I've been fitting transition matrices to real data throughout my PhD.
>
> To prove that the combination works — domain expertise plus AI — I built a complete underwriting system in 48 hours with Claude. Not a slide deck: a running application with 231 tests, four European markets, two disease models, every clinical number verified against PubMed. It detects "plausible-but-wrong" predictions — cases where the AI is confident but the data is too sparse to trust. On synthetic data across four markets, it flags a 2.4x difference in mispricing risk between German and international environments.
>
> I understand the disease progressions. Claude handles the engineering at scale. Imagine what I could do with real Allianz data and 90 days.

**Key framing:** Lead with the König quote. You match her exact description: disease progression expertise + LLM leverage. The 48-hour proof is the evidence, not the pitch.

**ADH mission alignment:** The JD says ADH strives for "rule-breaking approaches in health insurance." Building a complete AI underwriting system in 48 hours with an LLM co-pilot — instead of a 6-month team project — is exactly that. One person with domain expertise and AI tools, operating with startup agility inside Allianz's global infrastructure.

---

## My Background (Why I'm the Right Person)

### The PBW Origin Story
I published a peer-reviewed bioinformatics pipeline in ISME Communications (2024). That pipeline became the ground truth I used to evaluate 22 LLMs over 36 months (GPT-4o through GPT-5, Claude Sonnet 3.5 through Claude 4.6, Gemini 2.0 through 3 Pro). I tested whether they could reproduce my validated methodology.

The key observation: every LLM family produced code that is syntactically correct, executable, and passes surface review — but makes domain-specific choices that fail expert validation. I call this "plausible but wrong." It's the same failure mode in underwriting: a model produces a confident prediction that looks right but isn't supported by the data.

**MedRisk-ADH applies this observation to a new domain — using my experience spotting PBW in genomics to detect it in underwriting.**

### Why genomics is the perfect training ground for disease progression modeling

This is the key transition: my PhD was not just sequencing — it was **mathematical modeling of biological processes over time**.

- **Pathogen evolution is a Markov process.** In real-time genomics, you model how a pathogen mutates through states — susceptible → resistant → multi-drug resistant — with transition rates estimated from sequencing data. That's the same mathematical framework as disease progression: Normal Cognition → MCI → Mild AD → Moderate AD → Severe AD → Death. The math is identical. The states are different.
- **Data quality variance across countries is my lived experience.** I deployed 10 pipelines across 7 sites in Germany, France, and Spain. German labs delivered 95% complete sequencing data. Spanish field sites delivered 60%. I built quality-aware pipelines that adapted to what was available — not imputing what was missing. That's exactly what MedRisk-ADH does for underwriting data across DE/FR/ES/INT markets.
- **I know where AI works and where it fails.** 36 months evaluating 22 LLMs taught me that AI produces confident outputs even on domains it doesn't understand. In genomics, that means plausible but wrong bioinformatics code. In underwriting, that means confident risk scores on sparse patient data. The failure mode is the same — I just changed the domain.

**Bottom line for Frau König:** I understand disease progressions because I modeled biological processes for 4 years. The LLMs handle the engineering at scale. The domain expertise — knowing which transition rates are plausible, which biomarkers matter, when to trust the model and when not to — that's what I bring.

### What I Bring
- **Medical science foundation**: MSc Biochemistry (not CS — I come from the science side). Collaborated with **Rechts der Isar Hospital** (Munich) on clinical health surveillance. My PhD supervisor Prof. Lara Urban (now University of Zurich) describes me as having "interdisciplinary skill set ranging from laboratory, technical, to computational expertise."
- **Disease progression expertise**: 4 years modeling biological state transitions (pathogen evolution, drug resistance emergence) — the same CTMC mathematics that powers MedRisk-ADH's Alzheimer and cardiovascular models.
- **Regulatory compliance is second nature**: Served as **Occupational Safety Officer** for the entire Helmholtz AI lab — attended Safety & Compliance workshops, established SOPs, ensured regulatory compliance. The same mindset I applied to EU AI Act compliance in MedRisk-ADH.
- **I build platforms, not just projects**: Built the **computational framework for the entire research group** (HPC pipelines, data analysis infrastructure). My pipelines were adopted into the **University of Zurich "One Health" surveillance strategy** — that's production deployment, not a prototype.
- **Team builder and trainer**: First member of a new research group — helped build it from scratch. **Trained 6 researchers** in lab and computational methods. Created troubleshooting guides and SOPs. Led **2 independent research projects** out of 7 total. Prof. Urban calls me "a cohesive centre" of the group.
- **International network already in place**: Rechts der Isar Hospital (Munich), Global Health Institute (Barcelona), University of Zurich, School of Agriculture (Turin), Spanish Institute for Game and Wildlife Research — the same countries as ADH's European markets.
- **3 years evaluating Claude specifically**: From Sonnet 3.5 to Claude 4.6. I know where it works, where it fails, and how to get production value from it. Integrated Claude + MCP servers into live sequencing pipelines, reducing development time by 40%.
- **The 48-hour proof**: I built MedRisk-ADH — 231 tests, 2 disease models, 4 markets, fact-checked against PubMed, EU AI Act compliant — in about 48 hours with Claude. Prof. Urban's description of me: "does not shy away from unconventional problem-solving" and "gets things done efficiently." This demo is the evidence.

### The GitHub Trail
- github.com/ttmgr — portfolio with LLM evaluation framework, pipeline collection, publications
- github.com/ttmgr/Tim_Reska — "Against Plausibility" benchmark: 28 LLM evaluations, 196 scored results
- github.com/ttmgr/Air_Metagenomics — 7 stars, first-author pipeline (ISME Communications 2024)

---

## Confident AI predictions on bad data cost insurers 2,000+ mispriced policies per year

### What is PBW in plain English

A model scores a patient as "78% high risk" based on 3 coded diagnoses and no lab results. That score *looks* right — it matches population patterns. But for *this specific patient*, the model is just echoing its training data's average. It has no real information. The output is **plausible** — it passes every sanity check — but it is **wrong** for this individual. We call this Plausible-but-Wrong (PBW).

### Commercial impact

- At portfolio scale: 100,000 decisions/year, an illustrative 2% PBW rate = **2,000 mispriced policies annually**, invisible in standard model metrics (AUC, Brier score, C-index all look fine in aggregate).
- A single mispriced life insurance policy accepted at standard terms when it should have been rated can cost multiples of the annual premium in claims.
- PBW errors are *systematically invisible* — they do not show up until claims emerge years later, by which time the portfolio damage is locked in.

### Why current methods fail

- **Rules-based systems** reject cases with missing data but cannot detect cases where data is *present but insufficient*. They have no concept of per-case confidence.
- **Basic ML** does worse: it *imputes* missing data (fills gaps with population averages), which is exactly the mechanism that creates PBW. The model becomes confident precisely because it has manufactured the missing evidence.
- **Standard model validation** (AUC, calibration curves) measures aggregate performance. A model with AUC 0.85 can still be systematically wrong on the 5% of cases with poor input data — and aggregate metrics will not reveal it.

### EU AI Act regulatory pressure

The EU AI Act (Regulation 2024/1689) classifies insurance AI as **high-risk** under Article 6. This triggers mandatory requirements:

- **Art. 14 — Human oversight:** Systems must allow human intervention. MedRisk-ADH's tiered escalation (accept / review / reject) satisfies this directly.
- **Art. 15 — Accuracy and robustness:** Documented quality assurance for the AI's inputs and outputs. The DQS provides exactly this — a per-decision quality audit trail.
- **Art. 9 — Risk management:** Systematic identification and mitigation of risks. PBW detection is a textbook implementation.

Enforcement begins 2026. Insurers deploying AI without these safeguards face regulatory exposure.

---

## A reliability layer detects when AI predictions cannot be trusted

### The Pipeline

```
Patient Record --> Data Profile --> DQS --> Model Router --> Reliability Head --> Decision + Audit
```

Each step in plain English:

### 1. Data Quality Score (DQS) — "Should we trust this input?"

A per-patient score computed *before* any model runs. Three components:

| Component | Weight | What it measures | Example |
|-----------|--------|-----------------|---------|
| **Completeness** | 0.40 | Fraction of expected clinical features present (out of 50: 5 demographic + 17 Charlson comorbidity indicators + 10 lab values + 8 medication flags) | Patient has 35/50 features = 0.70 |
| **Consistency** | 0.35 | Do the data points agree with clinical domain rules? If diabetes is coded, is HbA1c elevated? If CKD stage 5, is eGFR below 30? | 4/5 rules pass = 0.80 |
| **Recency** | 0.25 | How fresh are the lab results? Exponential decay with a half-life of 1.4 years — a 3-year-old HbA1c carries half the weight of a fresh one | Mean lab age 1 year = 0.61 |

**DQS = 0.40 x Completeness + 0.35 x Consistency + 0.25 x Recency**

**Why these weights:** Completeness dominates because missing data is the primary driver of PBW. Consistency is next because contradictory data (diabetes coded but HbA1c normal) indicates coding errors or stale records. Recency matters but less — an old-but-present value is better than no value.

**Decision tiers:**

| Tier | Threshold | Action | Expected volume |
|------|-----------|--------|-----------------|
| Adequate | DQS >= 0.80 | Automate | ~60-70% |
| Caution | 0.60-0.80 | Human review | ~20-30% |
| Insufficient | < 0.60 | Reject prediction | ~5-15% |

### 2. Data Profile + Model Router — "Use the right model for this data"

Instead of imputing missing data (which creates PBW), the system classifies each patient into a **data profile**: FULL, NO_LABS, NO_MEDS, or MINIMAL. A separate XGBoost model is trained for each profile. A patient missing lab results gets scored by a model that was *trained* on patients without labs — it knows what it does not know, rather than pretending to know.

This is a critical architectural choice: **no imputation anywhere in the pipeline.** Imputation is the mechanism that converts missing data into false confidence.

### 3. Reliability Head — "How likely is this prediction to be wrong?"

The v2 system goes beyond fixed thresholds. A logistic regression model (chosen for interpretability — regulators need to see coefficients, not a black box) estimates **P(wrong)** — the probability that the main model's prediction disagrees with ground truth.

It then makes a **cost-optimal decision**:
- Expected cost of accepting = P(wrong) x cost of false negative (accepting a high-risk patient)
- Expected cost of rejecting = (1 - P(wrong)) x cost of false positive (denying a valid applicant)
- Cost of human review = fixed review cost
- **Choose the action that minimizes expected cost.**

Default cost ratio: false negative costs 5x a false positive (accepting a sick patient is far more expensive than losing a healthy applicant). These ratios are configurable to match Allianz's actual cost structure.

### 4. Audit Trail

Every decision produces a JSON Lines audit record: patient ID, DQS components, model prediction, P(wrong), cost calculation, final decision, human-readable explanation. This is the documentation package the EU AI Act requires.

---

## The Alzheimer extension proves the framework generalises to any disease

### Why we added it

The cardiovascular model alone could be dismissed as a one-disease prototype. The Alzheimer's extension proves the framework is **disease-agnostic** — new diseases are added as data configurations, not new code.

### 7-state CTMC explained simply

A Continuous-Time Markov Chain models disease progression as a patient moving through states:

```
Normal Cognition --> SCD --> MCI --> Mild AD --> Moderate AD --> Severe AD --> Death
```

Plus competing mortality risks from Mild and Moderate AD directly to Death (8 transitions total). Each arrow has a transition rate — a probability per unit time of moving to the next state.

### How disease models are "data configurations, not new code"

The `disease_configs.py` file contains two dataclass configurations: one for cardiovascular (5 states, 6 transitions) and one for Alzheimer's (7 states, 8 transitions). Adding a new disease (e.g., diabetes progression, cancer staging) requires adding a new configuration with state definitions and transition rates — no changes to the CTMC engine, the DQS framework, or the reliability scoring. The `build_model()` function instantiates any disease from its config.

### Fact-checked against published literature

All Alzheimer transition rates are calibrated to published sources:
- MCI to mild AD: ~15% annual conversion (Petersen et al., NEJM 2018)
- Mild to moderate AD: ~4-year mean sojourn (Brookmeyer et al.)
- Moderate to severe AD: ~3-year mean sojourn
- Severe AD to death: ~2-year mean survival
- AD prevalence for 65+: 9.6% in our model vs. 10.9% published (within range)
- Biomarkers: MMSE, MoCA, CSF amyloid-beta42, CSF p-tau181 (all LOINC-coded)
- Medications: Donepezil, Rivastigmine, Galantamine, Memantine (ATC-coded)
- ApoE4 genotype as graduated risk modifier

Every clinical number was verified against PubMed and WHO references.

---

## AI-driven underwriting solves 6 problems current methods cannot

### What AI adds that rules/actuarial/basic ML cannot

| Capability | Rules / Actuarial | Basic ML | MedRisk-ADH (AI) |
|-----------|-------------------|----------|-------------------|
| Per-case reliability | No | No | DQS + P(wrong) |
| Handles missing data | Reject case | Impute (creates PBW risk) | Route to right model |
| Individual risk drivers | No | Limited | SHAP per patient |
| Disease progression | Static tables | No | CTMC (any disease) |
| Confidence estimation | No | Uncalibrated | Cost-optimal decisions |
| EU AI Act compliance | Partial | Difficult | Built-in (Art. 14, 15) |

### Phase 3 LLM vision

Four concrete LLM applications, each already partially demonstrated in the PoC:

1. **Unstructured record extraction:** LLMs read doctor notes, discharge summaries, and lab reports in DE/FR/ES/EN, extracting structured data for the pipeline. This eliminates the manual coding bottleneck.
2. **Natural language explanations:** Instead of "SHAP: age +0.12", generate: "This patient's age (78) places them in the highest risk quartile, contributing 12% to the risk score." Underwriters get narratives, not numbers.
3. **Literature-calibrated parameters:** LLM agents query PubMed for systematic reviews and verify CTMC transition rates against published data — already demonstrated in this PoC for the Alzheimer extension.
4. **Continuous monitoring:** Flag when new publications change recommended clinical parameters, triggering automated model recalibration with full audit trail.

### Framing

This is **not replacing underwriters** — it is telling them where to look. The 60-70% of cases with high DQS get automated. Human expertise is concentrated on the 30-40% where it actually matters: ambiguous cases, data quality issues, edge cases. Underwriters become more effective, not redundant.

---

## Key numbers that prove the system works

| Metric | Value | Context |
|--------|-------|---------|
| Unit tests | **231 passing** | Full test coverage, lint clean |
| AUC-ROC | **0.71** | Binary risk classification (XGBoost) — deliberately conservative on synthetic data |
| Brier score | **0.010** | Calibration — very well calibrated (lower is better, 0 is perfect) |
| C-index | **0.72** | Concordance index for survival model (Cox PH) |
| Synthetic patients | **4,000** | 1,000 per market (DE/FR/ES/INT) |
| European markets | **4** | DE, FR, ES, INT — each with different data quality profiles |
| Disease models | **2** | Cardiovascular (5-state) + Alzheimer's (7-state) |
| PBW rate — DE | **0.9%** | Highest data quality market |
| PBW rate — FR | **1.0%** | Good data, slight diagnosis lag |
| PBW rate — ES | **1.3%** | Moderate completeness |
| PBW rate — INT | **2.1%** | Lowest data quality — 2.4x the DE rate |
| DQS weights | **0.40 / 0.35 / 0.25** | Completeness / Consistency / Recency |
| DQS thresholds | **0.80 / 0.60** | Adequate / Caution / Insufficient |
| Lab half-life | **1.4 years** | Informational half-life of a lab result |
| Expected features | **50** | 5 demographic + 17 Charlson + 10 lab + 8 medication |
| Consistency rules | **5** | Diabetes-HbA1c, CKD-eGFR, HF-BNP, HTN-BP, no-diabetes-HbA1c |
| AD prevalence (65+) | **9.6%** | Published: 10.9% — within acceptable range |
| Alzheimer CTMC states | **7** | NC, SCD, MCI, Mild AD, Moderate AD, Severe AD, Death |
| Alzheimer transitions | **8** | Including 2 competing mortality risks |
| Cost ratio (default) | **5:1** | False negative costs 5x false positive |
| Jupyter notebooks | **5** | Full pipeline documentation, all executable |

---

## Anticipated Questions & Answers

### 0. "You're a genomics PhD — why do you think you can model disease progression for insurance?"

Because disease progression modeling is what I've been doing for 4 years — just in a different domain. My PhD modeled how pathogens evolve through states over time: susceptible → resistant → multi-drug resistant. The math is a Continuous-Time Markov Chain — exactly the same framework I use in MedRisk-ADH for Alzheimer's (7 states) and cardiovascular disease (5 states). I didn't learn CTMC for this interview; I've been fitting transition matrices to real biological data throughout my PhD. The difference is the states: instead of resistance mutations, it's cognitive decline stages. Instead of sequencing quality, it's underwriting data quality. The mathematical framework, the calibration against published literature, the handling of incomplete observations across countries — that's all directly transferable. And to prove it: I built two disease progression models in 48 hours, with every transition rate verified against PubMed systematic reviews. That's not a weekend project from someone learning the domain — that's applied expertise.

### 1. "Why synthetic data? Can we trust these numbers?"

Synthetic data is by design, not by limitation. It gives us two things real data cannot: (a) ground truth — we know the "true" patient state, so we can measure exactly when the model is wrong, not just when it disagrees with a claim filed 5 years later; and (b) controlled experiments — we can systematically degrade data quality and observe the model's failure curve. The AUC of 0.71 is deliberately conservative; the point is not the model's performance but the *validation layer's* ability to detect when performance cannot be trusted. That said, we need real data to calibrate thresholds and validate that our synthetic distributions match reality — which is exactly why we are here.

### 2. "What's the AUC on real data?"

I don't have one yet, and I won't speculate. The synthetic AUC of 0.71 tells you the architecture works. What matters more is whether the DQS correctly predicts *when* the model fails on real data -- that requires a retrospective validation on claims data with linked outcomes. Give me 90 days with Allianz data and I'll have that number.

### 3. "How does this compare to what Swiss Re / Munich Re are doing?"

The reinsurers have built strong automated underwriting engines — rules-based triage, basic ML classifiers, even some NLP on medical reports. What none of them has published, to our knowledge, is a *pre-inference data quality gate* that estimates P(wrong) per case and makes cost-optimal routing decisions. They optimize the model. We optimize the decision of whether to trust the model. These are complementary: MedRisk-ADH's validation layer is model-agnostic and could sit in front of any existing scoring engine.

### 4. "What data do you need from us specifically?"

Minimum: 50,000+ pseudonymized patient records with 5+ years of follow-up and linked outcomes (death, MI, stroke, HF, CKD progression). Required fields: ICD-10-GM coded diagnoses with dates, lab results with values and dates (HbA1c, creatinine, eGFR, cholesterol panel, BP, NT-proBNP), ATC-coded medications, and demographics (age, sex, BMI, smoking). Ideally from at least 2 data sources with different quality characteristics to validate the cross-market design. Format: CSV or Parquet, one row per patient.

### 5. "What's the timeline and cost to validate this on real data?"

I'd structure it in 90-day sprints. Sprint 1: Allianz internal data, calibrate DQS, first real PBW prevalence numbers. Sprint 2: external validation with CPRD (UK, GBP 25-80K, only source with labs) and/or InGef (DE, EUR 30-80K). Sprint 3: production pilot on a subset of live underwriting. The cost of external data is modest compared to the cost of undetected PBW at portfolio scale.

### 6. "How do you handle GDPR/DSGVO?"

Three levels. The PoC uses 100% synthetic data — zero GDPR exposure. For Phase 2 with external databases: CPRD operates under UK GDPR + NHS Act 2006 Section 251; InGef under SGB X Section 75 + DSGVO Art. 89 (research exemption). For Allianz internal data: DSGVO Art. 6(1)(f) (legitimate interest) plus a DPIA under Art. 35 would be required. All data remains pseudonymized; the system never needs patient identifiers. The DPO clearance path is well-established for health insurance research in Germany.

### 7. "Why XGBoost and not deep learning?"

Three reasons. First, interpretability: XGBoost produces SHAP explanations that show exactly which features drive each prediction — regulators and underwriters need this. Deep learning is a black box by comparison. Second, sample efficiency: XGBoost works well on tabular data with thousands of records; deep learning needs orders of magnitude more. Third, auditability: the EU AI Act requires that we can explain *why* a decision was made. A gradient-boosted tree ensemble has a clear audit path. We use logistic regression for the Reliability Head for the same reason — the coefficients directly show the relationship between data quality and error probability.

### 8. "What if the data quality varies by region?"

That is exactly the scenario the system is designed for. The four-market design (DE/FR/ES/INT) simulates a gradient from high-quality (DE: 95% coding completeness, 92% lab completeness) to low-quality (INT: 60% coding, 50% lab). The DQS tracks this gradient faithfully, and the PBW detector fires 2.4x more often on INT than DE. In production, each Allianz market would get its own DQS calibration. The system also classifies *why* data is missing — structural (the market simply does not collect labs), workflow (labs exist but are not digitized), or random (individual patient gaps). This distinction matters because structural missingness requires a different model, while random missingness may just need escalation.

### 9. "How do you validate the CTMC transition rates?"

Every transition rate is calibrated to published literature with explicit citations. For example, the MCI-to-mild-AD rate of 0.15/year corresponds to the ~15% annual conversion rate from Petersen et al. (NEJM 2018). In the PoC, we used LLM agents to query PubMed and cross-reference our parameters against systematic reviews — this is documented and reproducible. For production, the validation protocol would include: (a) comparison against Allianz's own claims-based transition frequencies, (b) sensitivity analysis on all rates, and (c) annual recalibration against updated epidemiological data.

### 10. "What's the ROI? How many mispriced cases would this catch?"

A concrete example: at 100,000 underwriting decisions per year with a 2% PBW rate, that is 2,000 mispriced policies. If even 10% of those result in excess claims — and the average excess claim is EUR 50,000 — the annual cost of undetected PBW is EUR 10 million. The system's operating cost (data, compute, one FTE) is under EUR 500K annually. The ROI math works if the system catches even a fraction of those cases. The exact numbers need calibration against Allianz's portfolio, but the directional argument is strong: the cost of *not* detecting PBW at scale is orders of magnitude larger than the cost of the detection system.

### 11. "Can this work for other insurance lines (disability, long-term care)?"

Yes, by design. The DQS framework is domain-agnostic — it measures data completeness, consistency, and recency regardless of what the downstream model predicts. The CTMC engine accepts any disease configuration as a data file. For long-term care, you would define states like "independent / needs assistance / needs nursing care / institutional care" with transition rates from actuarial tables. For disability, states like "employed / short-term disability / long-term disability / return to work." The Alzheimer extension was specifically built to prove this point — it took adding one configuration file, no changes to the engine.

### 12. "What's the EU AI Act exposure for Allianz right now?"

Insurance AI is classified as high-risk under Art. 6 of the AI Act. Any AI system that influences underwriting decisions, pricing, or claims handling must comply with Art. 9 (risk management), Art. 14 (human oversight), and Art. 15 (accuracy and robustness). Enforcement begins in 2026. An insurer deploying ML models for underwriting without documented data quality assessment, without human escalation mechanisms, and without per-decision audit trails is non-compliant. MedRisk-ADH provides all three. This is not a theoretical concern — BaFin will enforce this, and the first enforcement actions will set precedents.

### 13. "Why should we build this in-house vs. buy from a vendor?"

Three reasons. First, the validation layer needs calibration against *your* data, *your* cost structure, and *your* regulatory environment -- a generic vendor product can't do that. Second, competitive advantage: if you buy a commodity tool, so can every other insurer. Building proprietary quality-aware underwriting AI creates a defensible edge. Third, the IP stays with Allianz. And with AI-augmented development, the build cost is a fraction of what it used to be -- I built this entire prototype in 48 hours. The bottleneck is no longer engineering capacity, it's domain expertise and data access.

### 14. "What happens when a prediction is wrong despite high DQS?"

Good question — this is the residual risk. High DQS means the *data supports* the prediction, but the model can still be wrong (irreducible error, rare disease presentations, novel drug interactions). The system addresses this through three mechanisms: (a) the Reliability Head estimates P(wrong) even for high-DQS cases — it uses model disagreement across the three-model ensemble (EPU) as an additional signal; (b) calibration-confidence mismatch (CCM) catches cases where the model's raw confidence diverges from its calibrated probability; and (c) the feedback loop in Phase 3 tracks whether "accepted" cases were later found to be mispriced, refining thresholds over time. No system eliminates all errors — but this one quantifies the residual risk and makes it visible.

### 15. "The JD says Medical Doctor — you're not an MD. Why should we hire you?"

First — I'm closer to medicine than a typical computer scientist. My Master's is in **Biochemistry**, not CS. I collaborated with **Rechts der Isar Hospital** on clinical health surveillance. I served as **Safety & Compliance Officer** for the Helmholtz AI lab — SOPs, regulatory compliance, safety workshops. I understand the clinical world from the inside.

But more importantly: the job says "clinical architect driving the evolution of digital health tools." An MD brings diagnostic intuition for individual patients. I bring **mathematical modeling of disease populations**, which is what underwriting actually requires. You don't need someone who diagnoses Alzheimer's at the bedside — you need someone who models its 7-stage progression through a population and tells you when the model's predictions can't be trusted. My PhD is 4 years of exactly that.

Plus: I write production Python, I understand ICD-10-GM/LOINC/ATC coding, and I built a complete AI underwriting system in 48 hours. The JD says "experience with Python is a significant advantage" — that's my core profile, not an advantage. And Frau König already told me: the expert understands disease progressions, the rest goes via LLMs. That's me. Find me an MD who also builds computational frameworks, trains researchers, and ships production systems across 7 international sites.

### 16. "How would you work with our Product Owner and Data Team?"

I've spent my entire PhD in cross-functional teams — bioinformaticians, clinicians, lab technicians, IT administrators across 7 international sites. In GenomicsForOneHealth, I was the bridge between the sequencing lab (which speaks FASTQ files and quality scores) and the clinical team (which speaks diagnoses and treatment decisions). That's the same translation role between a Data Team and a Product Owner. Concretely: I translate clinical requirements into structured logic (ICD-10 rules, transition rates, biomarker thresholds), I validate the Data Team's outputs against medical literature, and I help the PO prioritize which medical enhancements have the highest actuarial impact. The 90-day plan I presented is how I'd structure that collaboration — Month 1 is joint audit with existing underwriters, Month 2 is calibration with the Data Team, Month 3 is production delivery with the PO.

### 17. "How do you handle edge cases the model hasn't seen?"

The system has two defenses against out-of-distribution cases. First, the distribution shift detector (PSI/Jensen-Shannon divergence) monitors whether incoming patient profiles differ from the training distribution. If a patient's feature vector is significantly different from what the model was trained on, the system flags it before producing a score. Second, the ensemble disagreement signal (EPU): when XGBoost, Cox PH, and the CTMC model disagree substantially (more than 3 risk deciles apart), the case is flagged for human review regardless of DQS. A truly novel case will produce disagreement across models trained on different assumptions — that disagreement is the signal.

---

## In 90 days I'd deliver calibrated PBW detection on real Allianz data

| Month | What I'd deliver | What I need |
|-------|-----------------|-------------|
| **Month 1** | Audit current underwriting pipeline for PBW risk. Map data quality across Allianz markets. Identify the 3 highest-impact failure modes. | Access to anonymised claims sample + 2 hours with a senior medical underwriter |
| **Month 2** | Calibrate DQS thresholds against real Allianz data. Retrain model router on actual data profiles. First real-data PBW prevalence estimate. | DPO clearance for research use (DSGVO Art. 6(1)(f) + Art. 35 DPIA) |
| **Month 3** | Production prototype: REST API for per-case quality scoring. Validated PBW detection rates by market. EU AI Act compliance documentation. | Integration with existing underwriting workflow for pilot |

### How I match the role (mapped to job description)

| JD Requirement | What I bring | Evidence |
|----------------|-------------|----------|
| **Refine underwriting algorithms** | Built a complete underwriting pipeline from scratch — DQS, model router, reliability scoring, PBW detection | MedRisk-ADH: 21,000 lines, 231 tests |
| **Product Roadmap with PO** | First member of a new research group — helped build it from zero. Translated clinical requirements into technical specs. 10 pipelines = 10 product deliveries with stakeholders across 7 sites | GenomicsForOneHealth: coordinated with site leads, lab directors, IT across DE/FR/ES. Trained 6 researchers. Led 2 independent projects. |
| **Scale for international markets** | Built quality-aware systems for 4 European markets with different data completeness (95% DE → 60% INT) | MedRisk-ADH market profiles + my real deployment experience in same countries |
| **Collaborative analysis with Data Team** | Collaborated with Rechts der Isar Hospital (Munich), Global Health Institute (Barcelona), University of Zurich, Turin, Spanish wildlife research. Built computational frameworks for the entire group. Co-authored 8 papers. | Nature Communications co-authorship, pipelines adopted into UZH "One Health" strategy |
| **Complex conditions → underwriting risk** | Modeled Alzheimer (7 states), cardiovascular (5 states), all transition rates literature-calibrated. Framework extends to any disease via config | `disease_configs.py`: add a dataclass, get a new disease model |
| **Internal medical consultant** | MSc Biochemistry + collaborated with Rechts der Isar Hospital. Not an MD, but I read primary literature (PubMed systematic reviews), understand ICD-10-GM/LOINC/ATC coding, served as Safety & Compliance Officer. I translate between clinical evidence and technical implementation | 3 parallel fact-checking agents verified every clinical number. SOPs, compliance workshops, regulatory safety |
| **QA & clinical integrity** | Occupational Safety Officer at Helmholtz AI — established SOPs, attended compliance workshops, ensured regulatory safety for years. Same mindset in code: 231 automated tests, severity-rated fact-checks, range checks, evidence grading (5 levels) | `tests/`, `validation/range_checks.py`, literature verification agents, lab SOPs |
| **E-health trends** | EU AI Act compliance built in from day 1. LLM-powered unstructured record extraction (Phase 3). Monitoring international AI-in-insurance developments | Art. 14/15 compliance, Phase 3 LLM vision |
| **Python / data analysis** | Python is my primary language. Built the full stack: data generation, ML models (XGBoost, Cox PH, CTMC), validation, Streamlit app, PDF/PPTX generation | 21,000 lines Python, Streamlit app, automated reports |
| **Speaks medicine AND product** | PhD trained me in medical/biological reasoning. Pipeline deployments trained me in product delivery. I present to both audiences (ETH Zurich, Cambridge = science; this interview = business) | Invited talks at top universities + this MBB-quality pitch |
| **Owner personality, startup agility** | First member of Prof. Urban's new research group — built it from zero. Took over entire lab management voluntarily. Built MedRisk-ADH alone in 48 hours. Prof. Urban: "remarkably independent," "does not shy away from unconventional problem-solving," "gets things done efficiently" | Reference letter + the 48-hour proof |
| **German + English** | Native German. Academic and professional English (8 publications, international conference speaker, multinational team coordination) | Publications in English, PhD at German institution, campaigns across DE/FR/ES |

### What Allianz gets from hiring me

- **The clinical architect they described** — not an MD, but someone who models disease progressions mathematically and validates every number against published evidence. Frau König said it herself: the expert understands disease progressions, the rest goes via LLMs.
- A validated, EU AI Act-compliant underwriting quality layer — built in-house, not bought from a vendor
- The AI-augmented workflow itself: I + Claude = output that would normally take a team of 3-5 developers months
- Someone who has already deployed data pipelines across the same 3 countries (DE/FR/ES) ADH operates in
- A framework extensible to any disease or insurance line (life, disability, long-term care)

---

## Demo Flow (Recommended Order)

Walk through the Streamlit app in this sequence. Total time: 12-15 minutes.

### Step 1: Landing Page (1 min)
Open the app. Point to the pipeline architecture diagram:
> "Patient Record goes through Data Profile, DQS, Model Router, Reliability Head, and out comes a decision with a full audit trail. Every step is documented and explainable."

Mention the KPI bar: 4,000 patients, 4 markets, 231 tests.

### Step 2: Patient Assessment — Clean DE patient (2 min)
Navigate to Page 1. Select a DE-market patient with high DQS.
> "This is what a good case looks like. DQS 0.85, all consistency rules pass, recent labs. The model says 'accept' and the Reliability Head agrees — P(wrong) is low. This case can be automated with confidence."

Show the SHAP explanation: "Here is exactly *why* the model scored this patient — age contributed +12%, hypertension +8%, Charlson index +6%."

### Step 3: Patient Assessment — Flagged INT patient (3 min)
Select an INT-market patient with low DQS.
> "Same model, same architecture. But DQS is 0.42 — most labs are missing, no medication records. The model still produces a confident score, but the Reliability Head says P(wrong) is high. Decision: escalate to human review."

This is the key moment: **"The model is confident. The data does not support that confidence. Without our quality gate, this case would have been automated — and potentially mispriced."**

### Step 4: PBW Comparison (2 min)
Navigate to Page 2.
> "Side by side: same risk profile, different data quality. The model produces similar confidence scores for both. Only the DQS distinguishes them. This is the failure mode — and this is what we detect."

### Step 5: Portfolio Dashboard (2 min)
Navigate to Page 3.
> "Zooming out to portfolio level. You can see the PBW flag rate by market — DE at 0.9%, INT at 2.1%. The market with the worst data infrastructure produces 2.4 times the mispricing risk. This is invisible in standard model metrics."

Point to the DQS distribution and the tier breakdown.

### Step 6: Alzheimer Progression (2 min)
Navigate to Page 4.
> "To prove this is not a cardiovascular-only tool: here is Alzheimer's disease. Seven states from normal cognition to death, all transition rates from published literature. We added this as a configuration file — no changes to the engine. Any disease with a progression model works."

Show the state probability curves over time.

### Step 7: "Why AI?" — Close with strategic argument (2 min)
Scroll to the comparison table on the landing page.
> "Rules-based systems reject missing data. Basic ML imputes it — which is how PBW happens. We route to the right model and tell you whether to trust the output. That is the difference."

Point to the LLM Phase 3 cards:
> "Phase 3 adds unstructured record extraction — doctor notes, discharge summaries — and natural language explanations. The foundation we have built today is what makes that possible."

Close:
> "I built this in about 48 hours with Claude -- the architecture, the validation framework, the Alzheimer extension, 231 tests, all clinical numbers verified against PubMed. This is what I do: I take complex medical problems, combine them with AI tools, and produce production-quality systems fast. With real Allianz data, I could have calibrated results in 90 days."

---

## The interview itself is the proof: 48 hours, one person, production-grade output

This is the most important talking point. The demo is not just a prototype -- it's evidence of the workflow:

- **48 hours, one person, AI-assisted** -- not a team of 5 working for 6 months
- **231 tests, lint clean, fact-checked** -- not a hack, but production-grade engineering
- **2 disease models** -- proving generalizability, not just a one-off
- **Literature-verified** -- every clinical number cross-referenced against PubMed systematic reviews
- **EU AI Act ready** -- audit trail, human oversight, explainability built in from day 1

The question is not "is this system perfect?" (it's synthetic data, of course not). The question is: **"Do you want the person who built this working on your underwriting pipeline?"**

---

*Read this 30 minutes before. Know the Key Numbers cold. Practice the elevator pitch aloud once. Step 3 of the demo (the flagged INT patient) is the emotional peak -- land that moment and the rest follows. Close with the meta-argument: the interview itself is the proof of concept.*
