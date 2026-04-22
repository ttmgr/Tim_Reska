# Tim Reska

PhD researcher in genomics and bioinformatics working on One Health genomic surveillance, long-read metagenomics, food-safety sequencing, and large language model evaluation for scientific workflow construction.

Affiliation: Helmholtz Munich and the Technical University of Munich, Munich, Germany. I also contribute to the broader [GenomicsForOneHealth](https://github.com/ttmgr/GenomicsForOneHealth) collection developed by the One Health group under the supervision of [Lara Urban](https://sites.google.com/view/urban-lab/home). As described in that repository, the group is based at the University of Zurich and its Food Safety and One Health Institutes, with affiliations to Helmholtz AI.

Links: [Email](mailto:timreska@gmail.com) | [LinkedIn](https://linkedin.com/in/timreska)

## Research focus

My work combines sampling strategy, nanopore sequencing, and reproducible bioinformatics for pathogen surveillance across air, water, food, and clinical settings. A second line of work examines whether large language models can produce bioinformatics workflows that remain scientifically valid beyond superficial code correctness.

## Featured benchmark

[`Against Plausibility: LLM Evaluation`](./llm-eval/) is a side project, but it is also the clearest benchmark in this repository for testing whether modern LLMs can build a real scientific workflow rather than just produce locally plausible code. It evaluates 28 entries across 196 scored step-results using a validated nanopore metagenomics pipeline as ground truth.

The benchmark is designed around sequential failure: wrong tools, wrong parameters, broken output chaining, and analytically indefensible choices that look competent at first glance. That makes it relevant not only to bioinformatics, but also to AI labs, agent teams, and technical consultancies interested in workflow reliability rather than demo-level code generation.

## Repository context

This repository is the polished personal counterpart to the broader [GenomicsForOneHealth](https://github.com/ttmgr/GenomicsForOneHealth) collection. The material here emphasizes project overviews, study-linked pipeline documentation, and benchmark interpretation, while the group repository retains collaborative project metadata, accession context, helper scripts, and wider One Health coverage.

If you need to decide across the wider group collection rather than the curated subset here, use the canonical [GenomicsForOneHealth Pipeline Selector](https://ttmgr.github.io/GenomicsForOneHealth/).

| Section | Scope | Connection |
|:---|:---|:---|
| [`llm-eval/`](./llm-eval/) | `Against Plausibility: LLM Evaluation` | Structured LLM benchmark for sequential scientific workflow construction |
| [`pipelines/aerobiome/`](./pipelines/aerobiome/) | Air metagenomics pipeline overview | First-author workflow paired with the group repository's [Air Metagenomics](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Environmental_Metagenomics/Air_Metagenomics) study materials |
| [`pipelines/wetland-surveillance/`](./pipelines/wetland-surveillance/) | Wetland multi-omics surveillance workflow | Shared first-author workflow paired with the group repository's [Wetland Health](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Environmental_Metagenomics/Wetland_Health) study materials |
| [`pipelines/listeria-adaptive-sampling/`](./pipelines/listeria-adaptive-sampling/) | Food-safety adaptive sampling workflow overview | First-author project overview paired with the group repository's [Listeria Adaptive Sampling](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Food_Safety/Listeria-Adaptive-Sampling) pipeline scaffold |
| [GenomicsForOneHealth](https://github.com/ttmgr/GenomicsForOneHealth) | Group-wide One Health pipeline collection | Environmental metagenomics, food safety, clinical, veterinary, eDNA, viability, and collaborative project infrastructure |
| [`disease-progression/`](./disease-progression/) | Disease progression modeling framework | Survival analysis, competing risks, and transformer architectures on longitudinal EHR data for risk quantification |
| [`disease-network/`](./disease-network/) | Interactive clinical atlas | D3.js dashboard for exploring disease state transitions and underwriting scenarios |
| [`pkv-ml-explorer/`](./pkv-ml-explorer/) | PKV ML framework reference explorer | Interactive catalog of ML and actuarial methods (logistic regression, random forest, LSTM, autoencoder, Z-score/Mahalanobis, life tables, survival analysis, agentic AI) for private health insurance workflows |
| [`medrisk-adh/`](./medrisk-adh/) | AI underwriting with failure mode detection | Streamlit platform demonstrating plausible-but-wrong detection via data quality–confidence mismatch |

Within the group collection, my main contributions are in environmental metagenomics and food safety: [Air Metagenomics](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Environmental_Metagenomics/Air_Metagenomics), [Wetland Health](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Environmental_Metagenomics/Wetland_Health), and [Listeria Adaptive Sampling](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Food_Safety/Listeria-Adaptive-Sampling).

## Selected projects

### Against Plausibility: LLM Evaluation

A structured LLM evaluation benchmark of 28 evaluated entries and 196 scored step-results across seven nanopore metagenomics workflow stages. The study uses the validated air metagenomics pipeline as ground truth and scores tool choice, parameter accuracy, output compatibility, scientific validity, and executability under sequential workflow construction.

This benchmark is designed to expose a failure mode that matters in real technical deployments: outputs that are plausible at the single-step level but unstable, incompatible, or analytically wrong once chained into a full workflow.

Links: [Pipeline overview](./llm-eval/) | [Evaluation framework](./llm-eval/methodology/evaluation_framework.md) | [Curated findings](./llm-eval/evaluations/summary.md) | [Reference pipeline](./pipelines/aerobiome/)

### Air monitoring by nanopore sequencing

First-author workflow for long-read metagenomic characterization of bioaerosol communities collected by liquid impingement. The personal repository documents the validated pipeline structure, while the paired group repository retains accession context, preprocessing notes, helper scripts, and execution details tied to the published study.

Links: [Pipeline overview](./pipelines/aerobiome/) | [Study repository and metadata](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Environmental_Metagenomics/Air_Metagenomics) | [Publication](https://doi.org/10.1093/ismeco/ycae058)

### Real-time genomic pathogen, resistance, and host range characterization from passive water sampling of wetland ecosystems

Shared first-author workflow integrating DNA shotgun metagenomics, RNA viromics, avian influenza whole-genome sequencing, and vertebrate eDNA metabarcoding across 12 wetlands in Germany, France, and Spain along the East Atlantic Flyway. The local overview emphasizes analytical design; the group repository retains sample mapping, accession references, and workflow-specific operational context.

Links: [Pipeline overview](./pipelines/wetland-surveillance/) | [Study repository and metadata](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Environmental_Metagenomics/Wetland_Health) | [Preprint](https://doi.org/10.1101/2025.09.05.674394)

### Listeria adaptive sampling

First-author food-safety workflow for Oxford Nanopore adaptive sampling of *Listeria monocytogenes* from complex microbiome samples. The personal repository provides a project-level analytical overview, while the group repository retains the full script scaffold, installation notes, execution guide, and adaptation details for matched adaptive-sampling versus native-run comparisons.

Status: manuscript in preparation.

Links: [Pipeline overview](./pipelines/listeria-adaptive-sampling/) | [Study repository and metadata](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Food_Safety/Listeria-Adaptive-Sampling)

### Disease progression modeling

A reproducible Python framework for predicting patient trajectories through discrete disease states using survival analysis and deep learning. Ingests synthetic FHIR bundles via Synthea, transforms them to an OMOP-lite schema, and benchmarks Cox PH, multistate Markov chains, DeepSurv, DeepHit, and SurvTRACE (transformer-based competing-risks survival) against two clinical tracks: cardiovascular disease and Type 2 diabetes. Includes fairness auditing, model cards, a GDPR/EU AI Act regulatory context document, and a full pytest suite.

Stack: Python 3.10+, PyTorch, lifelines, pycox, scikit-survival, hmmlearn, FHIR.resources.

Links: [`disease-progression/`](./disease-progression/)

---

### Interactive clinical atlas

A standalone browser dashboard built in vanilla JavaScript (D3.js, Chart.js) for visualising disease state transitions and comparing intervention scenarios in a German medical underwriting context. Eight disease nodes with evidence-linked uncertainty bands, patient profile controls, and timeline/network/trajectory views. No framework dependencies — the entire application ships as a single HTML entry point.

Stack: ES6 modules, D3.js, Chart.js, HTML5, CSS3.

Links: [`disease-network/`](./disease-network/)

---

### PKV ML framework explorer

A self-contained browser dashboard cataloguing the machine-learning and actuarial methods relevant to German private health insurance (PKV) underwriting and portfolio management. Covers logistic regression, random forest, LSTM, autoencoder, Z-score and Mahalanobis outlier detection, actuarial life tables, moving average and exponential smoothing, survival analysis, and an agentic AI orchestration layer — each with problem framing, worked example, and trade-offs. Written in German; single HTML entry point with no build step.

Stack: vanilla HTML5, CSS3, JavaScript (no framework dependencies).

Links: [`pkv-ml-explorer/`](./pkv-ml-explorer/)

---

### MedRisk-ADH — AI underwriting with failure mode detection

A Streamlit multi-page application demonstrating a validation layer for automated underwriting. The core idea: automated underwriting AI fails most dangerously not when it is obviously wrong, but when it is **confidently wrong on low-quality data** (the plausible-but-wrong failure mode). The platform computes a Data Quality Score (DQS) for each patient before inference and flags cases where model confidence exceeds what the input data can actually support.

Three risk models (XGBoost binary classifier, Cox PH survival model, CTMC multistate Markov chain) feed a validation layer that checks Calibration-Confidence Mismatch (CCM) and Epistemic Prediction Uncertainty (EPU). A GDPR-safe multi-market synthetic cohort generator with controlled data degradation across four market profiles (DE / FR / ES / INT) enables reproducible failure mode experiments.

Stack: Python 3.11+, Streamlit, XGBoost, lifelines, PyTorch, Plotly, reportlab, python-pptx.

Links: [`medrisk-adh/`](./medrisk-adh/)

---

## Selected publications

- Reska T, Pozdniakova S, Urban L. [Air monitoring by nanopore sequencing](https://doi.org/10.1093/ismeco/ycae058). *ISME Communications* (2024).
- Perlas A, Reska T, Sanchez-Cano A, et al. [Real-time genomic pathogen, resistance, and host range characterization from passive water sampling of wetland ecosystems](https://doi.org/10.1101/2025.09.05.674394). *bioRxiv* preprint (2025, shared first authorship).
- Urban L, Perlas A, Francino O, et al. [Real-time genomics for One Health](https://doi.org/10.15252/msb.202311686). *Molecular Systems Biology* (2023).
- Sauerborn E, Corredor NC, Reska T, et al. [Detection of hidden antibiotic resistance through real-time genomics](https://www.nature.com/articles/s41467-024-49851-4). *Nature Communications* (2024).

A fuller publication record is available on [LinkedIn](https://linkedin.com/in/timreska).

## Methods and technical areas

- Long-read sequencing workflows for environmental, food-safety, and clinical surveillance
- Bioinformatics pipeline development in Snakemake, Python, and Bash
- Taxonomic classification, de novo assembly, adaptive sampling, AMR detection, virome analysis, and eDNA metabarcoding
- Benchmark design and failure analysis for LLM-generated scientific workflows and agentic pipeline construction

## Contact

[timreska@gmail.com](mailto:timreska@gmail.com)
