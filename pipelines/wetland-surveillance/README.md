# Wetland Surveillance Multi-Omics Pipeline

**Holistic pathogen, AMR, and host range characterization from passive water sampling**

From: Perlas A\*, Reska T\*, et al. — *Preprint* (2025)

---

## Overview

This pipeline implements an integrated One Health surveillance framework for wetland ecosystems. It processes **dual-extracted DNA and RNA** from passive water samplers through **four parallel analysis tracks**, combining untargeted community characterization with targeted pathogen and viral detection.

## Tool Stack

All tools and versions match those used in the publication:

| Step | Tool | Version |
|:-----|:-----|:--------|
| Basecalling | Dorado (SUP) | 5.0.0 |
| Demultiplexing | Dorado Demux | 5.0.0 |
| Adapter trimming | Porechop | 0.2.4 |
| Quality filtering | NanoFilt | 2.8.0 |
| Read normalization | SeqKit | 2.3.0 |
| **Metagenomics** | | |
| Taxonomic classification | Kraken2 (NCBI nt_core) | 2.1.2 |
| Assembly (primary) | metaFlye | 2.9.6 |
| Assembly (alternative) | nanoMDBG | 1.1 |
| Polishing (metaFlye) | Racon (3×) + Medaka | 1.5 / 1.7.2 |
| Polishing (nanoMDBG) | Medaka only | 1.7.2 |
| Read alignment | minimap2 | 2.28 |
| Gene prediction | Prokka | 1.14.5 |
| Pathogen identification | minimap2 → MEGAN CE (LCA) | 2.28 / 6.21.1 |
| ORF prediction | Prodigal | 2.6.3 |
| AMR / virulence | AMRFinderPlus (--plus) | 4.0.23 |
| Virulence screening | DIAMOND BLASTx (VFDB) | 2.1.13 |
| Plasmid detection | PlasmidFinder | 2.1.6 |
| **RNA Virome** | | |
| Assembly | nanoMDBG | 1.1 |
| Polishing | Medaka | 1.7.2 |
| Classification | DIAMOND BLASTx (NCBI nr) | 2.1.13 |
| **eDNA Metabarcoding** | | |
| Demultiplexing | OBITools4 obimultiplex | 1.3.1 |
| Primer removal | Cutadapt | 4.2 |
| QC / OTU clustering | VSEARCH | 2.21 |
| Taxonomy | Global alignment to MIDORI2 12S rRNA | v. Unique 266 |
| **AIV WGS** | | |
| Read mapping | minimap2 | 2.28 |
| BAM processing | SAMtools | 1.17 |
| Consensus calling | BCFtools | 1.17 |
| MSA | MAFFT | 7.526 |
| Phylogenetics | IQ-TREE2 (ModelFinder Plus) | 2.3.4 |

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
      │          ├──────────────────┐
      │          │                  │
      ▼          ▼                  ▼
 ┌──────────┐ ┌──────────────┐ ┌─────────────┐
 │ TRACK 1  │ │   TRACK 2    │ │   TRACK 4   │
 │ Shotgun  │ │  RNA Virome  │ │  AIV WGS    │
 │ Metagen. │ │  nanoMDBG    │ │  minimap2   │
 └────┬─────┘ │  Medaka      │ │  BCFtools   │
      │       │  DIAMOND nr  │ │  IQ-TREE2   │
      │       └──────────────┘ └─────────────┘
      │
      ├─ Kraken2 (nt_core)
      ├─ metaFlye + 3×Racon + Medaka
      ├─ nanoMDBG + Medaka
      ├─ Prokka gene prediction
      ├─ minimap2 → MEGAN LCA (pathogen ID)
      ├─ AMRFinderPlus --plus (AMR + virulence)
      ├─ DIAMOND VFDB (virulence)
      └─ PlasmidFinder (plasmids)

      │ (from DNA reads)
      ▼
 ┌──────────┐
 │ TRACK 3  │
 │ eDNA     │ ── OBITools4, Cutadapt, VSEARCH, MIDORI2
 │ Metabar. │
 └──────────┘
```

## Analysis Tracks

### Track 1: Shotgun Metagenomics (DNA)

| Step | Tool | Details |
|:-----|:-----|:--------|
| QC | NanoFilt | Q ≥ 9, ≥ 100 bp |
| Normalization | SeqKit | Subsampled to 87k reads |
| Taxonomy | Kraken2 v2.1.2 | Against NCBI nt_core |
| Assembly | metaFlye v2.9.6 + nanoMDBG v1.1 | Dual assembler strategy |
| Polishing | 3× Racon + Medaka (metaFlye) / Medaka only (nanoMDBG) | |
| Pathogen ID | minimap2 → MEGAN CE v6.21.1 (LCA) | ≥5 reads or ≥1 contig |
| AMR | AMRFinderPlus v4.0.23 (--plus) + Prodigal | Reads + contigs |
| Virulence | DIAMOND BLASTx v2.1.13 (VFDB) | e.g. ctxA, ctxB |
| Plasmids | PlasmidFinder v2.1.6 | |

### Track 2: RNA Virome

| Step | Tool | Details |
|:-----|:-----|:--------|
| QC | NanoFilt | Q ≥ 9, ≥ 100 bp |
| Assembly | nanoMDBG v1.1 | |
| Polishing | Medaka v1.7.2 | |
| Classification | DIAMOND BLASTx v2.1.13 (NCBI nr) | Viral taxid 10239, ≥80% identity |

### Track 3: eDNA Metabarcoding

| Step | Tool | Details |
|:-----|:-----|:--------|
| Demultiplexing | OBITools4 v1.3.1 | 9 bp symmetrical tags, ≤2 mismatches |
| Primer removal | Cutadapt v4.2 | |
| QC + clustering | VSEARCH v2.21 | maxEE 1.0, singleton removal, 97% OTU |
| Taxonomy | MIDORI2 12S rRNA (v. Unique 266) | Global alignment |
| Avian filter | Custom script | ≥80% coverage, ≥98% identity, ≥5 reads |
| Validation | | Cross-ref with eBird regional occurrence |

### Track 4: AIV Whole-Genome Sequencing

| Step | Tool | Details |
|:-----|:-----|:--------|
| QC | NanoFilt | Q ≥ 8, ≥ 150 bp |
| Mapping | minimap2 v2.28 | Against European AIV references per segment |
| Reference selection | samtools idxstats | Best reference per segment |
| Consensus | BCFtools v1.17 | Re-map to optimal reference set |
| Subtyping | GISAID BLAST + FluSurver | HA segment |
| Phylogenetics | MAFFT v7.526 → IQ-TREE2 v2.3.4 | 1000 UFboot + 1000 SH-aLRT |

## Quick Start

```bash
# 1. Edit config.yaml with sample paths and reference databases
vi config.yaml

# 2. Dry run
snakemake -n --cores 1

# 3. Run
snakemake --cores 16

# 4. Outputs in results/
ls results/metagenomics/ results/virome/ results/edna/ results/aiv/
```

## Study Design

| Parameter | Value |
|:----------|:------|
| Sampling method | Passive membrane adsorption (torpedo devices) |
| Nucleic acids | DNA + RNA (dual extraction) |
| Sites | 12 lentic wetlands across Germany, France, Spain |
| Replicates | 2 per site |
| Total samples | n = 24 |
| Comparison | Anthropogenic vs. natural ecosystems |
| Normalization | 87k reads (1 sample excluded for insufficient depth) |

## Output Structure

```
results/
├── basecalling/                        # Dorado basecalls
├── demux/                              # Demultiplexed reads
├── trimmed/                            # Adapter-trimmed reads
├── metagenomics/
│   ├── qc/                             # NanoFilt filtered (Q≥9)
│   ├── normalized/                     # SeqKit subsampled (87k)
│   ├── taxonomy/                       # Kraken2 reports
│   ├── assembly_metaflye/              # metaFlye + 3×Racon + Medaka
│   ├── assembly_nanomdbg/              # nanoMDBG + Medaka
│   ├── annotation/                     # Prokka + Prodigal
│   ├── pathogen/                       # MEGAN LCA assignments
│   ├── amr/                            # AMRFinderPlus results
│   ├── virulence/                      # DIAMOND VFDB hits
│   └── plasmids/                       # PlasmidFinder results
├── virome/
│   ├── qc/                             # NanoFilt filtered RNA
│   ├── assembly/                       # nanoMDBG assemblies
│   ├── *_viral_contigs_polished.fasta  # Medaka-polished
│   └── *_virome_diamond.tsv            # DIAMOND classifications
├── edna/
│   ├── demux/                          # OBITools4 demultiplexed
│   ├── trimmed/                        # Cutadapt primer-trimmed
│   ├── otus/                           # VSEARCH OTU tables
│   └── *_vertebrate_species.tsv        # MIDORI2 assignments
├── aiv/
│   ├── qc/                             # NanoFilt filtered (Q≥8)
│   ├── mapping/                        # minimap2 + idxstats
│   ├── *_consensus.fasta               # BCFtools consensus
│   └── phylo/                          # MAFFT + IQ-TREE2
└── community/
    ├── bray_curtis_matrix.tsv
    └── pcoa_coordinates.tsv
```
