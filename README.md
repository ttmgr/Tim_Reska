# Tim Reska

PhD researcher in genomics and bioinformatics working on One Health genomic surveillance, long-read metagenomics, and evaluation of large language models for scientific pipeline development.

Affiliation: Helmholtz Munich and the Technical University of Munich, Munich, Germany. I also contribute to the broader [GenomicsForOneHealth](https://github.com/ttmgr/GenomicsForOneHealth) collection developed by the One Health group under the supervision of [Lara Urban](https://sites.google.com/view/urban-lab/home). As described in that repository, the group is based at the University of Zurich and its Food Safety and One Health Institutes, with affiliations to Helmholtz AI.

Links: [Email](mailto:timreska@gmail.com) | [LinkedIn](https://linkedin.com/in/timreska) | [Google Scholar](https://scholar.google.com)

## Research focus

My work combines sampling strategy, nanopore sequencing, and reproducible bioinformatics for pathogen surveillance across air, water, food, and clinical settings. A second line of work examines whether large language models can produce bioinformatics workflows that remain scientifically valid beyond superficial code correctness.

## Repository context

This repository contains project-focused material from the same research program represented more broadly in [GenomicsForOneHealth](https://github.com/ttmgr/GenomicsForOneHealth).

| Section | Scope | Connection |
|:---|:---|:---|
| [`pipelines/aerobiome/`](./pipelines/aerobiome/) | Air metagenomics workflow | First-author pipeline corresponding to the group repository's [Air Metagenomics](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Environmental_Metagenomics/Air_Metagenomics) workflow |
| [`pipelines/wetland-surveillance/`](./pipelines/wetland-surveillance/) | Wetland multi-omics surveillance workflow | Shared first-author pipeline corresponding to the group repository's [Wetland Health](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Environmental_Metagenomics/Wetland_Health) workflow |
| [`llm-eval/`](./llm-eval/) | Evaluation framework for large language model-generated nanopore metagenomics pipelines | Uses the validated air metagenomics workflow as the reference pipeline |
| [GenomicsForOneHealth](https://github.com/ttmgr/GenomicsForOneHealth) | Group-wide One Health pipeline collection | Includes the broader environmental metagenomics, food safety, clinical, veterinary, eDNA, and viability workflows |

Within the group collection, my main contributions are in environmental metagenomics and food safety: [Air Metagenomics](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Environmental_Metagenomics/Air_Metagenomics), [Wetland Health](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Environmental_Metagenomics/Wetland_Health), and [Listeria Adaptive Sampling](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Food_Safety/Listeria-Adaptive-Sampling).

## Selected projects

### Air monitoring by nanopore sequencing

First-author workflow for long-read metagenomic characterization of bioaerosol communities collected by liquid impingement. The pipeline covers basecalling, quality control, taxonomic classification, de novo assembly, metagenomic binning, and functional annotation.

Links: [Local workflow](./pipelines/aerobiome/) | [Group workflow](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Environmental_Metagenomics/Air_Metagenomics) | [Publication](https://doi.org/10.1093/ismeco/ycae058)

### Real-time genomic pathogen, resistance, and host range characterization from passive water sampling of wetland ecosystems

Shared first-author workflow integrating DNA shotgun metagenomics, RNA viromics, avian influenza whole-genome sequencing, and vertebrate eDNA metabarcoding across 12 wetlands in Germany, France, and Spain along the East Atlantic Flyway.

Links: [Local workflow](./pipelines/wetland-surveillance/) | [Group workflow](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Environmental_Metagenomics/Wetland_Health) | [Preprint](https://doi.org/10.1101/2025.09.05.674394)

### Listeria adaptive sampling

First-author food-safety workflow for nanopore adaptive sampling of *Listeria monocytogenes* from complex samples. In the group repository, this project is listed under the [Food Safety](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Food_Safety) section and described as a publication in preparation.

Links: [Group workflow](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Food_Safety/Listeria-Adaptive-Sampling) | [Food Safety overview](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Food_Safety)

### Systematic evaluation of large language models for nanopore metagenomics pipeline development

A structured benchmark of 22 model versions across 7 pipeline stages, using the published air metagenomics workflow as ground truth. The emphasis is on scientific validity, parameter choice, and compatibility between sequential workflow steps rather than isolated code snippets.

Links: [Study](./llm-eval/) | [Evaluation framework](./llm-eval/methodology/evaluation_framework.md) | [Reference pipeline](./pipelines/aerobiome/)

## Selected publications

- Reska T, Pozdniakova S, Urban L. [Air monitoring by nanopore sequencing](https://doi.org/10.1093/ismeco/ycae058). *ISME Communications* (2024).
- Perlas A, Reska T, Sanchez-Cano A, et al. [Real-time genomic pathogen, resistance, and host range characterization from passive water sampling of wetland ecosystems](https://doi.org/10.1101/2025.09.05.674394). *bioRxiv* preprint (2025, shared first authorship).
- Urban L, Perlas A, Francino O, et al. [Real-time genomics for One Health](https://doi.org/10.15252/msb.202311686). *Molecular Systems Biology* (2023).
- Sauerborn E, Corredor NC, Reska T, et al. [Detection of hidden antibiotic resistance through real-time genomics](https://www.nature.com/articles/s41467-024-49851-4). *Nature Communications* (2024).

A fuller publication record is available on [Google Scholar](https://scholar.google.com).

## Methods and technical areas

- Long-read sequencing workflows for environmental, food-safety, and clinical surveillance
- Bioinformatics pipeline development in Snakemake, Python, and Bash
- Taxonomic classification, de novo assembly, AMR detection, virome analysis, and eDNA metabarcoding
- Benchmark design and failure analysis for large language model-generated scientific code

## Contact

[timreska@gmail.com](mailto:timreska@gmail.com)
