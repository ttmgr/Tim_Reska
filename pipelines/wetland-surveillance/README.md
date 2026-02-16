# Wetland Surveillance Multi-Omics Pipeline

**Holistic pathogen, AMR, and host range characterization from passive water sampling**

From: Perlas A\*, Reska T\*, et al. — *Preprint* (2025)

---

## Overview

This pipeline implements an integrated One Health surveillance framework for wetland ecosystems. It processes **dual-extracted DNA and RNA** from passive water samplers (torpedo-shaped devices) through **four parallel analysis tracks**, combining untargeted community characterization with targeted pathogen detection.

The key innovation is the **passive sampling + multi-omics** approach: a single water collection yields metagenomic, virome, eDNA, and targeted viral data, enabling simultaneous characterization of pathogens, their antimicrobial resistances, and their potential vertebrate hosts.

## Workflow

```
Passive water sampling (torpedo device)
            │
    ┌───────┴───────┐
    │  Dual DNA/RNA │
    │  Extraction   │
    └───┬───────┬───┘
        │       │
   ┌────┴──┐  ┌─┴────┐
   │  DNA  │  │  RNA  │
   └──┬────┘  └──┬────┘
      │          │
      ├──────┐   ├──────────┐
      ▼      ▼   ▼          ▼
  ┌──────┐ ┌────────┐ ┌─────────┐ ┌──────────┐
  │TRACK │ │TRACK 3 │ │ TRACK 2 │ │ TRACK 4  │
  │  1   │ │  eDNA  │ │  RNA    │ │   AIV    │
  │Metag.│ │Metabar.│ │ Virome  │ │   WGS    │
  └──┬───┘ └───┬────┘ └────┬────┘ └────┬─────┘
     │         │           │            │
     ▼         ▼           ▼            ▼
  Taxonomy   Vertebrate   Viral       Influenza
  Pathogens  Host IDs     Community   Subtyping
  AMR genes                           Consensus
     │         │           │            │
     └─────────┴─────┬─────┴────────────┘
                     ▼
          ┌─────────────────────┐
          │  Host-Pathogen      │
          │  Association Matrix │
          └─────────┬───────────┘
                    ▼
          ┌─────────────────────┐
          │  Integrated Report  │
          └─────────────────────┘
```

## Analysis Tracks

### Track 1: Shotgun Metagenomics (DNA)

Characterizes the full microbial community and screens for pathogens and AMR.

| Step | Tool | Purpose |
|:-----|:-----|:--------|
| QC | Chopper, NanoPlot | Quality/length filtering |
| Host removal | minimap2 | Remove vertebrate DNA |
| Taxonomy | Kraken2 + Bracken | Species-level classification |
| Assembly | metaFlye | Metagenome assembly |
| AMR | ABRicate (CARD, ResFinder, NCBI) | Resistance gene detection |
| Pathogen screen | Custom script | Cross-ref vs. curated pathogen DB |

### Track 2: RNA Virome

Profiles the viral community from RNA extracts.

| Step | Tool | Purpose |
|:-----|:-----|:--------|
| QC | Chopper | RNA-specific quality filtering |
| Depletion | minimap2 | Remove rRNA and host transcripts |
| Assembly | metaFlye | Viral contig assembly |
| Classification | BLASTn vs. viral RefSeq | Viral taxonomy |

### Track 3: eDNA Metabarcoding

Identifies vertebrate species present at each site via environmental DNA.

| Step | Tool | Purpose |
|:-----|:-----|:--------|
| Barcode extraction | minimap2 | Extract 12S/cytb reads |
| Species ID | BLASTn vs. vertebrate DB | Vertebrate identification |

### Track 4: Avian Influenza WGS

Targeted whole-genome sequencing of avian influenza viruses.

| Step | Tool | Purpose |
|:-----|:-----|:--------|
| Screening | minimap2 | Map RNA reads to AIV segments |
| Assembly | IRMA (FLU-ONT) | Influenza genome assembly |
| Subtyping | IRMA output | HA/NA subtype determination |

## Quick Start

```bash
# 1. Edit config.yaml with sample paths and reference databases
vi config.yaml

# 2. Dry run
snakemake -n --cores 1

# 3. Run (16 cores recommended)
snakemake --cores 16 --use-conda

# 4. View report
open results/report/wetland_surveillance_report.html
```

## Study Design

| Parameter | Value |
|:----------|:------|
| Sampling method | Passive membrane adsorption (torpedo devices) |
| Nucleic acids | DNA + RNA (dual extraction) |
| Sites | 12 lentic wetlands (DE, FR, ES) |
| Replicates | 2 per site |
| Total samples | n = 24 |
| Comparison | Anthropogenic vs. natural ecosystems |

## Key Finding

> Anthropogenically impacted wetland ecosystems consistently exhibited **higher relative abundances of pathogens and AMR genes** compared to natural sites. Avian influenza was detected at **a third of monitored sites**.

## Output Structure

```
results/
├── metagenomics/
│   ├── qc/                    # NanoPlot + filtered reads
│   ├── filtered/              # Host-removed reads
│   ├── taxonomy/              # Kraken2 + Bracken results
│   ├── assembly/              # metaFlye assemblies
│   ├── amr/                   # AMR gene hits
│   └── pathogen/              # Pathogen screening results
├── virome/
│   ├── qc/                    # RNA quality filtered
│   ├── filtered/              # rRNA/host depleted
│   ├── assembly/              # Viral contig assemblies
│   └── *_virome_taxonomy.tsv  # Viral classifications
├── edna/
│   └── *_vertebrate_species.tsv  # Host species IDs
├── aiv/
│   ├── mapping/               # AIV read mappings
│   ├── irma/                  # IRMA assemblies
│   ├── *_aiv_consensus.fasta  # Consensus genomes
│   └── *_aiv_subtype.txt      # Subtype calls
└── report/
    ├── host_pathogen_associations.tsv
    └── wetland_surveillance_report.html
```
