# Bioinformatics Pipelines

Reproducible Snakemake workflows from my first-author publications. Each pipeline documents the exact tools, versions, and parameters used in the corresponding study.

---

## Pipelines

### [`aerobiome/`](aerobiome/) — Air Monitoring by Nanopore Sequencing

**Publication:** Reska T, Pozdniakova S, Urban L — *ISME Communications* (2024)

Shotgun metagenomic analysis of ultra-low biomass air samples. Key steps:

| Step | Tools |
|:-----|:------|
| Basecalling | Guppy v6.3.2 / Dorado v4.3.0 (HAC) |
| QC | Porechop → NanoFilt (Q ≥ 8, ≥ 100 bp) |
| Normalization | SeqKit (5k–70k reads, phase-specific) |
| Taxonomy | Kraken2 (NCBI nt) + DIAMOND BLASTx (NCBI nr) |
| Assembly | metaFlye → 3× Racon polishing |
| Binning | metaWRAP + CheckM (relaxed ULB thresholds) |
| AMR / Virulence | AMRFinderPlus + ABRicate (VFDB) |

---

### [`wetland-surveillance/`](wetland-surveillance/) — Multi-Omics Wetland Surveillance

**Publication:** Perlas A\*, Reska T\*, et al. — *Preprint* (2025)

Four parallel analysis tracks from dual DNA/RNA extraction:

| Track | Approach | Key Tools |
|:------|:---------|:----------|
| 1. Metagenomics | Shotgun DNA | Kraken2, metaFlye + nanoMDBG, Racon + Medaka, AMRFinderPlus, PlasmidFinder |
| 2. RNA Virome | Viral community | nanoMDBG + Medaka, DIAMOND BLASTx (NCBI nr) |
| 3. eDNA Metabarcoding | Vertebrate host ID | OBITools4, Cutadapt, VSEARCH, MIDORI2 12S rRNA |
| 4. AIV WGS | Influenza genomes | minimap2, SAMtools, BCFtools, MAFFT, IQ-TREE2 |

---

## Technology Stack

- **Workflow manager:** Snakemake
- **Basecalling:** Guppy, Dorado (HAC / SUP models)
- **Sequencing platforms:** Oxford Nanopore Technologies (MinION, PromethION)
- **Languages:** Python 3, Bash
- **Analysis libraries:** Pandas, NumPy, scikit-bio, SciPy, Matplotlib

## Setup

```bash
# Install Snakemake
conda install -c bioconda snakemake

# Navigate to a pipeline
cd pipelines/aerobiome/
# or
cd pipelines/wetland-surveillance/

# Edit configuration
vi config.yaml

# Dry run
snakemake -n --cores 1

# Run
snakemake --cores 16
```

## Citation

If you use or adapt these pipelines, please cite the corresponding publications:

- **Air study:** Reska T, Pozdniakova S, Urban L. "Air monitoring by nanopore sequencing." *ISME Communications* (2024). DOI: 10.1093/ismeco/ycae058
- **Aquatic study:** Perlas A\*, Reska T\*, Sánchez-Cano A, et al. "Real-time genomic pathogen, resistance, and host range characterization from passive water sampling of wetland ecosystems." *Preprint* (2025).
