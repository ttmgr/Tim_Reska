# DACH Regulatory Context for Health Data and AI in Insurance

## Overview

This document outlines the regulatory landscape relevant to deploying disease progression models for insurance underwriting in the DACH region (Germany, Austria, Switzerland). It covers data protection, anti-discrimination law, sector-specific insurance regulation, and AI governance frameworks.

---

## 1. GDPR and Health Data Processing

### Article 9: Special Categories of Personal Data

Health data is classified as a special category of personal data under GDPR Article 9(1), meaning its processing is prohibited by default. Processing is only permitted under one of the specific exceptions in Article 9(2):

- **Explicit consent** (Art. 9(2)(a)): The data subject has given explicit, informed consent. In insurance contexts, this is typically obtained during the application process. However, consent must be freely given, and refusal to consent cannot automatically result in coverage denial in certain insurance lines.

- **Insurance contract necessity** (Art. 9(2)(b)): Processing may be necessary for the performance of obligations under employment, social security, or social protection law. This applies primarily to statutory health insurance (GKV in Germany) rather than private insurance (PKV).

- **Substantial public interest** (Art. 9(2)(g)): Member states may provide for processing on grounds of substantial public interest, with appropriate safeguards. Germany has implemented this through sector-specific laws.

- **Scientific research** (Art. 9(2)(j)): Processing for scientific research purposes is permitted with appropriate safeguards, including pseudonymisation where feasible.

### Data Protection Impact Assessment (DPIA)

Under GDPR Article 35, a DPIA is mandatory when processing is likely to result in a high risk to the rights and freedoms of individuals. Health data processing for automated risk assessment clearly meets this threshold. The DPIA must include:

- A systematic description of the processing operations and purposes
- An assessment of necessity and proportionality
- An assessment of risks to data subjects
- Measures to address those risks, including safeguards and security

---

## 2. Germany-Specific Regulation

### Bundesdatenschutzgesetz (BDSG)

The BDSG supplements the GDPR with Germany-specific provisions. Section 22 BDSG provides additional conditions for processing special categories of data, including requirements for appropriate and specific safeguards such as pseudonymisation, encryption, and appointment of a data protection officer.

### Versicherungsvertragsgesetz (VVG)

The Insurance Contract Act governs the pre-contractual duty of disclosure. Under VVG Section 19, applicants must truthfully answer questions about risk-relevant circumstances, including health conditions. The insurer's right to ask health-related questions is well established, but the scope of automated decision-making based on health data is subject to additional scrutiny.

### Gendiagnostikgesetz (GenDG)

The Genetic Diagnostics Act is particularly relevant if any genetic or genomic data is considered. Key provisions:

- **Section 18 GenDG**: Insurers may not require genetic tests or use results of genetic tests previously performed. This prohibition is absolute for health, life, and disability insurance below certain thresholds.
- **Exception**: For life insurance, disability insurance, and occupational disability insurance with coverage exceeding EUR 300,000 or annuity exceeding EUR 30,000 per year, insurers may request existing genetic test results.
- **Practical implication**: Disease progression models must not incorporate genetic risk scores or polygenic risk scores unless the GenDG exception applies and the applicant has voluntarily disclosed results.

### Allgemeines Gleichbehandlungsgesetz (AGG)

The General Equal Treatment Act prohibits discrimination on grounds of race, ethnic origin, gender, religion, disability, age, or sexual orientation. In insurance:

- **Section 20(2) AGG**: Differential treatment in insurance is permissible if based on recognised principles of risk-adequate calculation, supported by actuarial data. This allows age-based and, in some cases, health-based risk differentiation.
- **Test-Achats ruling** (CJEU C-236/09): Since December 2012, gender may not be used as a risk factor in insurance pricing within the EU. This applies to all DACH countries within the EU (Germany and Austria). Models must not use sex as a direct pricing factor, though it may be used for calibration and fairness monitoring.

---

## 3. Austria-Specific Regulation

### Datenschutzgesetz (DSG)

Austria's data protection law largely follows the GDPR framework. Section 1 DSG establishes a constitutional right to data protection. For health data processing in insurance:

- Processing requires explicit consent or a legal basis under Austrian law.
- The Austrian Data Protection Authority (Datenschutzbehoerde) has issued guidance on automated decision-making in insurance.

### Gleichbehandlungsgesetz (GlBG)

Austria's equal treatment legislation mirrors EU anti-discrimination directives. Risk-based differentiation in insurance is permitted when actuarially justified, with the same Test-Achats gender-neutrality requirement as in Germany.

### Versicherungsvertragsgesetz (Austrian VersVG)

The Austrian Insurance Contract Act contains pre-contractual disclosure obligations similar to the German VVG. Automated underwriting decisions must comply with GDPR Article 22 (right not to be subject to solely automated decision-making with legal effects).

---

## 4. Switzerland-Specific Regulation

### Datenschutzgesetz (DSG / revDSG)

Switzerland's revised Data Protection Act (revDSG), effective since September 2023, aligns more closely with the GDPR while maintaining Swiss specificities:

- Health data is classified as "particularly sensitive personal data" (Art. 5(c) revDSG).
- Processing requires explicit consent or a legal basis (Art. 31 revDSG).
- Automated individual decision-making must be disclosed, and data subjects have the right to request human review (Art. 21 revDSG).
- The FDPIC (Federal Data Protection and Information Commissioner) oversees enforcement.

### Krankenversicherungsgesetz (KVG) / Obligatorische Krankenpflegeversicherung (OKP)

Swiss mandatory health insurance (OKP/LAMal) operates under community rating: premiums may not be differentiated based on health status. This means disease progression models are not applicable to OKP pricing. However, they are relevant for:

- Supplementary hospital insurance (VVG-governed)
- Life insurance
- Disability insurance (IV/BVG supplementary)

### Swiss Solvency Test (SST)

The SST requires insurers to hold capital commensurate with their risk profile. Disease progression models could inform reserving and capital adequacy calculations, subject to FINMA approval.

---

## 5. EU AI Act: High-Risk Classification

The EU AI Act (Regulation 2024/1689) establishes a risk-based framework for AI systems. Disease progression models used in insurance underwriting are likely classified as **high-risk** AI systems under Annex III, point 5(b): "AI systems intended to be used to evaluate the creditworthiness of natural persons or to establish their credit score, with the exception of AI systems used for the purpose of detecting financial fraud" -- and by extension, insurance risk assessment systems that affect access to essential services.

### Requirements for High-Risk AI Systems

- **Risk management system** (Art. 9): Identification and mitigation of known and foreseeable risks.
- **Data governance** (Art. 10): Training data must be relevant, representative, free of errors, and complete. Bias examination is required.
- **Technical documentation** (Art. 11): Comprehensive documentation of the AI system, including model cards and data sheets.
- **Record-keeping** (Art. 12): Automatic logging of events during system operation.
- **Transparency** (Art. 13): Users must be able to interpret system output and use it appropriately.
- **Human oversight** (Art. 14): AI systems must allow effective human oversight, including the ability to override or reverse automated decisions.
- **Accuracy, robustness, cybersecurity** (Art. 15): Appropriate levels of accuracy and robustness, with resilience against errors and attacks.

### Timeline

The AI Act entered into force on 1 August 2024. High-risk AI system requirements apply from 2 August 2026. Insurers deploying disease progression models must ensure compliance by this date.

---

## 6. Insurance-Specific Anti-Discrimination

### EU Gender Directive and Test-Achats

Following the CJEU ruling in Association Belge des Consommateurs Test-Achats (C-236/09), insurers in EU member states may not use gender as a factor in calculating premiums and benefits. This ruling applies to Germany and Austria but not directly to Switzerland (non-EU). However, Swiss insurers voluntarily align with this principle in many product lines.

### Age Differentiation

Age-based risk differentiation is generally permitted in insurance when actuarially justified. Disease progression models that use age as a feature are consistent with this principle. However, age discrimination in employment-related insurance products may be subject to additional restrictions under national employment law.

### Disability Discrimination

Insurers must not discriminate against applicants on the basis of disability beyond what is actuarially necessary. Disease progression predictions must distinguish between current health status (permissible for risk assessment) and disability status (subject to anti-discrimination protection).

---

## 7. EIOPA AI Governance Principles

The European Insurance and Occupational Pensions Authority (EIOPA) has published principles on the use of AI in insurance, building on its broader digital transformation strategy:

### Proportionality
AI governance measures should be proportionate to the complexity and impact of the AI system. A disease progression model used for indicative risk screening requires less rigorous governance than one making binding underwriting decisions.

### Fairness and Non-Discrimination
Insurers must ensure that AI systems do not lead to unfair discrimination. This requires regular testing for disparate impact across protected groups and documentation of any differential treatment with actuarial justification.

### Transparency and Explainability
Policyholders and applicants should receive meaningful information about how AI systems affect decisions about them. For complex models (e.g., deep learning survival models), this may require surrogate explanations or feature importance summaries rather than full model transparency.

### Human Oversight
EIOPA emphasises that AI should augment, not replace, human decision-making in insurance. Underwriters should retain the ability to override model recommendations, and such overrides should be logged and analysed.

### Data Quality and Governance
Training data must be fit for purpose, and insurers must have processes to identify and address data quality issues, bias, and drift over time.

---

## Summary Table

| Regulation | Jurisdiction | Key Requirement | Impact on Project |
|---|---|---|---|
| GDPR Art. 9 | EU (DE, AT) | Legal basis for health data processing | Requires consent or legal basis; DPIA mandatory |
| revDSG | CH | Sensitive data protection | Explicit consent; automated decision disclosure |
| GenDG | DE | Genetic data restrictions | No genetic/polygenic risk scores in models |
| AGG / Test-Achats | DE, AT | Gender-neutral pricing | Sex not usable as pricing factor |
| VVG / VersVG | DE, AT | Pre-contractual disclosure | Framework for health questions in underwriting |
| KVG/OKP | CH | Community rating in basic insurance | Models not applicable to OKP pricing |
| EU AI Act | EU (DE, AT) | High-risk AI requirements | Full compliance required by August 2026 |
| EIOPA principles | EU | AI governance in insurance | Fairness testing, human oversight, explainability |
