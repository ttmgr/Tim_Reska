# Aerobiome Metagenomics Pipeline

**PCR-free nanopore surveillance of ultra-low biomass air samples**

From: Reska T, Pozdniakova S, Urban L — *ISME Communications* (2024)

---

## Overview

This pipeline performs shotgun metagenomic analysis of air samples collected via active liquid impingement. It is specifically designed for **ultra-low biomass (ULB)** environments where maximizing DNA recovery from sparse material is the primary methodological challenge.

## Tool Stack

All tools and versions match those used in the publication:

| Step | Tool | Version |
|:-----|:-----|:--------|
| Basecalling | Guppy (HAC) / Dorado (HAC) | 6.3.2 / 4.3.0 |
| Adapter trimming | Porechop | 0.2.3 / 0.2.4 |
| Quality filtering | NanoFilt | 2.8.0 |
| Read normalization | SeqKit | 2.1.2 |
| Taxonomic classification | Kraken2 (NCBI nt) | 2.0.7 |
| Taxonomic validation | DIAMOND BLASTx (NCBI nr) | 2.1.11 |
| Taxonomic validation | Chan Zuckerberg ID (CZID) | — |
| Assembly | metaFlye | 2.9.1 |
| Polishing | minimap2 + Racon (3×) | 2.17 / 1.5 |
| Binning | metaWRAP | 1.3 |
| Bin quality | CheckM | 1.2.2 |
| AMR detection | AMRFinderPlus | 3.12.8 |
| AMR detection | ABRicate | 1.0.1 |
| Virulence detection | ABRicate (VFDB) | 1.0.1 |
| FASTA conversion | SeqKit | 2.8.2 |
| Community analysis | Python (Pandas, NumPy, scikit-bio, SciPy, Matplotlib) | — |

## Workflow

```
Raw nanopore signals (FAST5/POD5)
        │
        ▼
  ┌──────────────────────┐
  │  Basecalling         │ ── Guppy v6.3.2 (HAC) or Dorado v4.3.0 (HAC)
  │  Adapter trimming    │ ── Porechop v0.2.4
  │  Quality filtering   │ ── NanoFilt v2.8.0 (Q ≥ 8, ≥ 100 bp)
  └──────┬───────────────┘
         │
         ▼
  ┌──────────────────────┐
  │  Read normalization  │ ── SeqKit v2.1.2
  │  (phase-specific     │    5k (1h GH), 15k (3h GH),
  │   subsampling)       │    70k (natural), 30k (urban)
  └──────┬───────────────┘
         │
         ├─────────────────────────────┐
         ▼                             ▼
  ┌──────────────┐             ┌──────────────────────┐
  │  Kraken2     │             │  De novo assembly    │
  │  (NCBI nt)   │             │  metaFlye v2.9.1     │
  └──────┬───────┘             └──────┬───────────────┘
         │                            │
         │                            ▼
         │                     ┌──────────────────────┐
         │                     │  Polishing            │
  ┌──────┴───────┐             │  3× minimap2 + Racon │
  │  DIAMOND     │             └──────┬───────────────┘
  │  BLASTx      │                    │
  │  (NCBI nr)   │                    ▼
  │  validation  │             ┌──────────────────────┐
  └──────────────┘             │  Binning (metaWRAP)  │
                               │  QC (CheckM)         │
                               └──────┬───────────────┘
                                      │
                               ┌──────┴───────────────┐
                               ▼                       ▼
                        ┌────────────┐          ┌────────────┐
                        │ AMRFinder+ │          │ ABRicate   │
                        │ (AMR)      │          │ (VFDB)     │
                        └────────────┘          └────────────┘
         │
         ▼
  ┌──────────────────────┐
  │  Community Analysis  │ ── Bray-Curtis, PCoA, rarefaction
  │  (Python/scikit-bio) │
  └──────────────────────┘
```

## Quick Start

```bash
# 1. Edit config.yaml with your sample paths and reference databases
vi config.yaml

# 2. Dry run
snakemake -n --cores 1

# 3. Run
snakemake --cores 16

# 4. Outputs in results/
ls results/taxonomy/ results/assembly/ results/amr/ results/community/
```

## Key Design Decisions

### Phase-Specific Subsampling

Different environments yield dramatically different read counts:
- Greenhouse 1h: ~5k reads (minimal biomass)
- Greenhouse 3h: ~15k reads
- Natural outdoor: ~70k reads
- Urban campaign: ~30k reads

To ensure fair community comparisons, reads are subsampled to phase-specific thresholds using SeqKit before taxonomic classification.

### Triple Taxonomic Validation

ULB samples are particularly susceptible to misclassification. We validate Kraken2 (nucleotide) results with:
1. **DIAMOND BLASTx** (protein-level) — independent confirmation
2. **CZID** (hybrid pipeline) — additional cross-validation

### Relaxed Binning Thresholds

Standard MAG quality criteria (≥50% completeness, ≤10% contamination) would discard nearly all ULB bins. We use relaxed thresholds (≥30% completeness) to retain partial genomes that still provide useful biological information.

### AMR on Both Reads and Contigs

Functional annotation is applied to both individual reads and assembled contigs/bins, because many AMR genes span short regions that can be detected at the read level even when assembly fails.

## Study Sites

| Site | Environment | Samples | Subsample Depth |
|:-----|:------------|:--------|:----------------|
| Munich Greenhouse | Controlled (1h) | 6 | 5,000 |
| Munich Greenhouse | Controlled (3h) | 6 | 15,000 |
| Munich Natural | Outdoor | 6 | 70,000 |
| Barcelona Urban | Urban campaign | 30 | 30,000 |
| Negative Controls | Blanks | Variable | — |

## Output Structure

```
results/
├── basecalling/           # BAM files from Dorado
├── trimmed/               # Porechop adapter-trimmed reads
├── qc/                    # NanoFilt quality-filtered reads
├── normalized/            # SeqKit subsampled reads
├── taxonomy/
│   ├── *_kraken2.report   # Kraken2 classification reports
│   └── *_diamond.tsv      # DIAMOND BLASTx validation
├── assembly/
│   └── {sample}/
│       ├── assembly.fasta           # Raw metaFlye assembly
│       └── assembly_polished.fasta  # 3× Racon-polished
├── binning/
│   └── {sample}/
│       ├── metawrap_bins/   # MAG bins
│       └── checkm/          # Bin quality reports
├── amr/
│   ├── *_amrfinderplus.tsv  # AMRFinderPlus results
│   └── *_abricate.tsv       # ABRicate results
├── virulence/
│   └── *_vfdb.tsv           # VFDB virulence factor hits
└── community/
    ├── bray_curtis_matrix.tsv
    ├── pcoa_coordinates.tsv
    └── rarefaction_curves.png
```
