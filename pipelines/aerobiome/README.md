# Aerobiome Metagenomics Pipeline

**PCR-free nanopore surveillance of ultra-low biomass air samples**

From: Reska T, Pozdniakova S, Urban L — *ISME Communications* (2024)

---

## Overview

This pipeline performs shotgun metagenomic analysis of air samples collected via active liquid impingement. It is specifically designed for **ultra-low biomass (ULB)** environments where reagent and environmental contaminants can dominate the sequencing signal.

The key innovation is a **negative-control-driven contamination filter** that compares taxonomic profiles between real samples and extraction/sampling blanks, retaining only taxa that are significantly enriched in real samples.

## Workflow

```
Raw nanopore reads (FASTQ)
        │
        ▼
  ┌─────────────┐
  │  NanoPlot   │ ── QC metrics & read length distributions
  │  Chopper    │ ── Quality & length filtering
  └─────┬───────┘
        │
        ▼
  ┌─────────────────────┐
  │  Host Read Removal  │ ── minimap2 vs. GRCh38
  └─────┬───────────────┘
        │
        ▼
  ┌──────────────────────────────────┐
  │  Contamination Control (ULB)    │ ── Fold-change filter vs.
  │  ★ Critical for air samples ★   │    negative controls
  └─────┬────────────────────────────┘
        │
        ├──────────────────────┐
        ▼                      ▼
  ┌───────────────┐    ┌──────────────┐
  │  Kraken2      │    │  metaFlye    │
  │  Bracken      │    │  Assembly    │
  │  (Species ID) │    └──────┬───────┘
  └───────────────┘           │
                              ▼
                       ┌──────────────┐
                       │  ABRicate    │
                       │  (AMR genes) │
                       └──────────────┘
        │                      │
        └──────────┬───────────┘
                   ▼
          ┌────────────────┐
          │  HTML Report   │
          └────────────────┘
```

## Quick Start

```bash
# 1. Edit config.yaml with your sample paths and reference databases
vi config.yaml

# 2. Dry run (check workflow)
snakemake -n --cores 1

# 3. Run
snakemake --cores 16 --use-conda

# 4. View report
open results/report/aerobiome_report.html
```

## Key Design Decisions

### Contamination Control

ULB samples (such as air) typically contain **more contaminant DNA than target DNA**. Standard metagenomic analyses without contamination filtering will produce misleading results. Our approach:

1. Sequence negative controls (extraction blanks, sampling blanks) alongside real samples
2. Build a contaminant taxonomic profile from all controls
3. For each taxon in a real sample, compute fold-change over mean control abundance
4. Remove reads assigned to taxa below the fold-change threshold (default: 5×)

See [`scripts/contamination_filter.py`](scripts/contamination_filter.py) for the implementation.

### Why Nanopore?

- **Field-deployable**: MinION runs on a laptop, enabling on-site sequencing
- **Long reads**: Species-level resolution without amplification bias
- **Real-time**: Results accumulate during the sequencing run
- **PCR-free**: Eliminates amplification bias inherent to 16S/ITS approaches

## Study Sites

| Site | Environment | Samples |
|:-----|:------------|:--------|
| Munich Greenhouse | Controlled | 12 |
| Munich Natural | Outdoor | 6 |
| Barcelona Urban | Urban campaign | 30 |
| Negative Controls | Blanks | Variable |

**Total: n = 48 samples**

## Configuration

All parameters are in [`config.yaml`](config.yaml):

- **Samples**: FASTQ paths, sample types, site assignments
- **QC**: Quality/length thresholds
- **Contamination**: Fold-change threshold, minimum control reads
- **Taxonomy**: Kraken2 confidence, Bracken parameters
- **Assembly**: Expected metagenome size
- **AMR**: Identity/coverage thresholds, databases

## Output Structure

```
results/
├── qc/                          # NanoPlot reports per sample
├── filtered/                    # QC'd, host-removed, decontaminated reads
├── contamination/               # Contaminant lists and statistics
├── taxonomy/                    # Kraken2 reports, Bracken species tables
├── assembly/                    # metaFlye assemblies per sample
├── amr/                         # AMR gene hits and summaries
└── report/
    └── aerobiome_report.html    # Integrated HTML report
```
