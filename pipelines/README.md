# Bioinformatics Pipelines

Representative Snakemake workflows from my first-author publications, demonstrating end-to-end nanopore metagenomic analysis for environmental health surveillance.

## Pipelines

### [`aerobiome/`](aerobiome/) — Airborne Metagenomics (ISME Communications, 2024)

Shotgun metagenomic analysis of ultra-low biomass (ULB) air samples using nanopore sequencing. Handles the unique challenges of aerobiome profiling: sparse DNA recovery, stringent contamination control against negative controls, and species-level taxonomic resolution.

**Workflow:** Raw reads → QC & filtering → Contamination control → Taxonomic classification → Species profiling → AMR screening → Report

---

### [`wetland-surveillance/`](wetland-surveillance/) — Multi-Omics Wetland Surveillance (Preprint, 2025)

Holistic pathogen, AMR, and host range characterization from passive water sampling. Integrates four sequencing approaches in a single workflow: shotgun metagenomics, RNA virome analysis, vertebrate eDNA metabarcoding, and targeted avian influenza whole-genome sequencing.

**Workflow:** Dual-extracted DNA/RNA → Parallel analysis tracks → Integrated pathogen-host-AMR report

---

## Technology Stack

| Tool | Purpose |
|:---|:---|
| [Snakemake](https://snakemake.github.io/) | Workflow management |
| [Chopper](https://github.com/wdecoster/chopper) / [NanoPlot](https://github.com/wdecoster/NanoPlot) | Nanopore read QC |
| [minimap2](https://github.com/lh3/minimap2) | Read alignment |
| [Kraken2](https://github.com/DerrickWood/kraken2) / [Bracken](https://github.com/jenniferlu717/Bracken) | Taxonomic classification |
| [Flye](https://github.com/fenderglass/Flye) | Metagenomic assembly |
| [ABRicate](https://github.com/tseemann/abricate) / [AMRFinderPlus](https://github.com/ncbi/amr) | AMR detection |
| [BLAST](https://blast.ncbi.nlm.nih.gov/) | Sequence similarity |
| [IRMA](https://wonder.cdc.gov/amd/flu/irma/) | Influenza genome assembly |

## Requirements

```bash
conda create -n surveillance-pipelines -c bioconda -c conda-forge \
    snakemake chopper nanoplot minimap2 samtools \
    kraken2 bracken flye abricate ncbi-amrfinderplus \
    blast irma python=3.11
```

## Citation

If you use or adapt these workflows, please cite:

- **Reska T**, Pozdniakova S, Urban L. Air monitoring by nanopore sequencing. *ISME Communications* (2024)
- Perlas A\*, **Reska T**\*, et al. Real-time genomic pathogen, resistance, and host range characterization from passive water sampling. *Preprint* (2025)
