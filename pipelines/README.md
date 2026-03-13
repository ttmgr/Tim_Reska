# Bioinformatics Pipelines

Project-linked nanopore and metagenomics workflows spanning environmental surveillance and food safety. This directory provides polished overview documentation for the main study pipelines in the personal repository; detailed accession context, helper scripts, and project-specific execution scaffolding remain linked from [GenomicsForOneHealth](https://github.com/ttmgr/GenomicsForOneHealth).

The validated air pipeline in this directory is also the ground truth used in [`Against Plausibility: LLM Evaluation`](../llm-eval/), a scored benchmark for sequential scientific workflow generation by large language models.

---

## Pipelines

### [`aerobiome/`](aerobiome/) — Air Monitoring by Nanopore Sequencing

**Publication:** Reska T, Pozdniakova S, Urban L — *ISME Communications* (2024) · [DOI](https://doi.org/10.1093/ismeco/ycae058)

Shotgun metagenomic analysis of ultra-low biomass air samples collected by liquid impingement. This is the validated ground-truth workflow used in [`Against Plausibility: LLM Evaluation`](../llm-eval/).

| Step | Tools | Key Parameters |
|:-----|:------|:---------------|
| Basecalling | Guppy v6.3.2 / Dorado v4.3.0 (HAC) | R10.4.1 chemistry, high-accuracy mode |
| QC & filtering | Porechop v0.2.3 → NanoFilt v2.8.0 | Q >= 8, >= 100 bp |
| Normalization | SeqKit v2.8.2 | 5k-70k reads (phase-specific downsampling) |
| Taxonomy | Kraken2 v2.0.7 (NCBI nt) + DIAMOND BLASTx (NCBI nr) | Dual classification approach |
| Assembly | metaFlye v2.9.1 → 3x Racon v1.5 polishing | `--meta --nano-hq` |
| Binning | metaWRAP v1.3 + CheckM v1.2.2 | >= 30% completeness, <= 10% contamination |
| AMR / virulence | AMRFinderPlus v3.12.8 + ABRicate v1.0.1 (VFDB) | Reads, contigs, and bins |

Links: [Pipeline overview](./aerobiome/) | [Study repository and metadata](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Environmental_Metagenomics/Air_Metagenomics) | [Publication](https://doi.org/10.1093/ismeco/ycae058)

---

### [`wetland-surveillance/`](wetland-surveillance/) — Multi-Omics Wetland Surveillance

**Publication:** Perlas A\*, Reska T\*, et al. — *Preprint* (2025) · [DOI](https://doi.org/10.1101/2025.09.05.674394)

Integrated One Health monitoring from passive water samplers using dual DNA/RNA extraction and four parallel analysis tracks: shotgun metagenomics, RNA viromics, vertebrate eDNA metabarcoding, and avian influenza whole-genome sequencing.

| Track | Approach | Key tools | Target |
|:------|:---------|:----------|:-------|
| 1. Metagenomics | Shotgun DNA | Kraken2, metaFlye + nanoMDBG, Racon + Medaka, AMRFinderPlus, PlasmidFinder | Microbial community and AMR |
| 2. RNA virome | Viral community | nanoMDBG + Medaka, DIAMOND BLASTx (NCBI nr) | Viral diversity |
| 3. eDNA metabarcoding | Vertebrate host ID | OBITools4, Cutadapt, VSEARCH, MIDORI2 12S rRNA | Wildlife host range |
| 4. AIV WGS | Influenza genomes | minimap2, SAMtools, BCFtools, MAFFT, IQ-TREE2 | Avian influenza characterization |

*\*Shared first authorship*

Links: [Pipeline overview](./wetland-surveillance/) | [Study repository and metadata](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Environmental_Metagenomics/Wetland_Health) | [Preprint](https://doi.org/10.1101/2025.09.05.674394)

---

### [`listeria-adaptive-sampling/`](listeria-adaptive-sampling/) — Listeria Adaptive Sampling

**Status:** Manuscript in preparation

Targeted Oxford Nanopore adaptive sampling workflow for *Listeria monocytogenes* in complex food-safety samples. The project is designed around matched adaptive-sampling versus native runs and emphasizes enrichment quantification, assembly recovery, AMR profiling, and report generation.

| Module | Core tools | Purpose |
|:-------|:-----------|:--------|
| Input conversion and QC | samtools, Porechop, NanoFilt, NanoStat | Convert BAM inputs, trim adapters, filter short reads, and summarize yield |
| Taxonomy and target extraction | Kraken2, seqtk, SeqKit | Quantify microbiome background and isolate *Listeria* reads |
| Assembly comparison | metaMDBG, Myloasm, Flye, Dorado polish | Compare long-read assembly strategies for enriched versus native data |
| Functional profiling | AMRFinderPlus, Kraken2 contig classification | Recover AMR markers and target-specific contigs |
| Reporting | Bash/Python reporting scripts | Summarize AS versus N performance in HTML and tabular outputs |

Links: [Pipeline overview](./listeria-adaptive-sampling/) | [Study repository and metadata](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Food_Safety/Listeria-Adaptive-Sampling)

---

## Repository Role

Use the personal repository for concise, study-linked pipeline overviews. Use [GenomicsForOneHealth](https://github.com/ttmgr/GenomicsForOneHealth) when you need accession context, full helper-script collections, sample tables, installation notes, or extended execution guidance tied to the collaborative project repositories.

## Citation

If you use or adapt these workflows, cite the corresponding study or project status:

- Reska T, Pozdniakova S, Urban L. *Air monitoring by nanopore sequencing*. *ISME Communications* (2024). DOI: [10.1093/ismeco/ycae058](https://doi.org/10.1093/ismeco/ycae058)
- Perlas A\*, Reska T\*, Sanchez-Cano A, et al. *Real-time genomic pathogen, resistance, and host range characterization from passive water sampling of wetland ecosystems*. *bioRxiv* preprint (2025). DOI: [10.1101/2025.09.05.674394](https://doi.org/10.1101/2025.09.05.674394)
- Listeria adaptive sampling project: manuscript in preparation
