# Tim Reska

PhD researcher in genomics and bioinformatics working on One Health genomic surveillance, long-read metagenomics, food-safety sequencing, and large language model evaluation for scientific workflow construction.

Affiliation: Helmholtz Munich and the Technical University of Munich, Munich, Germany. I also contribute to the broader [GenomicsForOneHealth](https://github.com/ttmgr/GenomicsForOneHealth) collection developed by the One Health group under the supervision of [Lara Urban](https://sites.google.com/view/urban-lab/home). As described in that repository, the group is based at the University of Zurich and its Food Safety and One Health Institutes, with affiliations to Helmholtz AI.

Links: [Email](mailto:timreska@gmail.com) | [LinkedIn](https://linkedin.com/in/timreska) | [Google Scholar](https://scholar.google.com)

## Research focus

My work combines sampling strategy, nanopore sequencing, and reproducible bioinformatics for pathogen surveillance across air, water, food, and clinical settings. A second line of work examines whether large language models can produce bioinformatics workflows that remain scientifically valid beyond superficial code correctness.

## Repository context

This repository is the polished personal counterpart to the broader [GenomicsForOneHealth](https://github.com/ttmgr/GenomicsForOneHealth) collection. The material here emphasizes project overviews, study-linked pipeline documentation, and benchmark interpretation, while the group repository retains collaborative project metadata, accession context, helper scripts, and wider One Health coverage.

| Section | Scope | Connection |
|:---|:---|:---|
| [`pipelines/aerobiome/`](./pipelines/aerobiome/) | Air metagenomics pipeline overview | First-author workflow paired with the group repository's [Air Metagenomics](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Environmental_Metagenomics/Air_Metagenomics) study materials |
| [`pipelines/wetland-surveillance/`](./pipelines/wetland-surveillance/) | Wetland multi-omics surveillance workflow | Shared first-author workflow paired with the group repository's [Wetland Health](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Environmental_Metagenomics/Wetland_Health) study materials |
| [`pipelines/listeria-adaptive-sampling/`](./pipelines/listeria-adaptive-sampling/) | Food-safety adaptive sampling workflow overview | First-author project overview paired with the group repository's [Listeria Adaptive Sampling](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Food_Safety/Listeria-Adaptive-Sampling) pipeline scaffold |
| [`llm-eval/`](./llm-eval/) | `Against Plausibility: LLM Evaluation` | Structured LLM evaluation benchmark using the validated air metagenomics workflow as ground truth |
| [GenomicsForOneHealth](https://github.com/ttmgr/GenomicsForOneHealth) | Group-wide One Health pipeline collection | Environmental metagenomics, food safety, clinical, veterinary, eDNA, viability, and collaborative project infrastructure |

Within the group collection, my main contributions are in environmental metagenomics and food safety: [Air Metagenomics](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Environmental_Metagenomics/Air_Metagenomics), [Wetland Health](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Environmental_Metagenomics/Wetland_Health), and [Listeria Adaptive Sampling](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Food_Safety/Listeria-Adaptive-Sampling).

## Selected projects

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

### Against Plausibility: LLM Evaluation

A structured LLM evaluation benchmark of 28 evaluated entries and 196 scored step-results across seven nanopore metagenomics workflow stages. The study uses the validated air metagenomics pipeline as ground truth and evaluates tool choice, parameter accuracy, output compatibility, scientific validity, and executability under sequential workflow construction.

Links: [Pipeline overview](./llm-eval/) | [Evaluation framework](./llm-eval/methodology/evaluation_framework.md) | [Reference pipeline](./pipelines/aerobiome/)

## Selected publications

- Reska T, Pozdniakova S, Urban L. [Air monitoring by nanopore sequencing](https://doi.org/10.1093/ismeco/ycae058). *ISME Communications* (2024).
- Perlas A, Reska T, Sanchez-Cano A, et al. [Real-time genomic pathogen, resistance, and host range characterization from passive water sampling of wetland ecosystems](https://doi.org/10.1101/2025.09.05.674394). *bioRxiv* preprint (2025, shared first authorship).
- Urban L, Perlas A, Francino O, et al. [Real-time genomics for One Health](https://doi.org/10.15252/msb.202311686). *Molecular Systems Biology* (2023).
- Sauerborn E, Corredor NC, Reska T, et al. [Detection of hidden antibiotic resistance through real-time genomics](https://www.nature.com/articles/s41467-024-49851-4). *Nature Communications* (2024).

A fuller publication record is available on [Google Scholar](https://scholar.google.com).

## Methods and technical areas

- Long-read sequencing workflows for environmental, food-safety, and clinical surveillance
- Bioinformatics pipeline development in Snakemake, Python, and Bash
- Taxonomic classification, de novo assembly, adaptive sampling, AMR detection, virome analysis, and eDNA metabarcoding
- Benchmark design and failure analysis for LLM-generated scientific workflows

## Contact

[timreska@gmail.com](mailto:timreska@gmail.com)
