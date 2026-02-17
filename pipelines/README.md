# Bioinformatics Pipelines

Production-grade Snakemake workflows from peer-reviewed publications. Each pipeline documents the exact tools, versions, and parameters used in the corresponding study — designed for full reproducibility and validated through independent peer review.

---

## Pipelines

### [`aerobiome/`](aerobiome/) — Air Monitoring by Nanopore Sequencing

**Publication:** Reska T, Pozdniakova S, Urban L — *ISME Communications* (2024) · [DOI](https://doi.org/10.1093/ismeco/ycae058)

Shotgun metagenomic analysis of ultra-low biomass air samples. This pipeline also serves as the **ground truth** for our [LLM evaluation study](../llm-eval/).

| Step | Tools | Key Parameters |
|:-----|:------|:---------------|
| Basecalling | Guppy v6.3.2 / Dorado v4.3.0 (HAC) | R10.4.1 chemistry, high-accuracy mode |
| QC & filtering | Porechop v0.2.3 → NanoFilt v2.8.0 | Q ≥ 8, ≥ 100 bp |
| Normalization | SeqKit v2.8.2 | 5k–70k reads (phase-specific downsampling) |
| Taxonomy | Kraken2 v2.0.7 (NCBI nt) + DIAMOND BLASTx (NCBI nr) | Dual classification approach |
| Assembly | MetaFlye v2.9.1 → 3× Racon v1.5 polishing | `--meta --nano-hq` |
| Binning | metaWRAP v1.3 + CheckM v1.2.2 | ≥ 30% completeness, ≤ 10% contamination |
| AMR / Virulence | AMRFinderPlus v3.12.8 + ABRicate v1.0.1 (VFDB) | Applied at 3 levels: reads, contigs, bins |

**Key design decisions:**
- Relaxed binning thresholds (30% completeness) — specifically calibrated for ultra-low biomass air samples where high completeness is not achievable
- Three-tool basecalling sequence (basecaller → Porechop → NanoFilt) rather than integrated Dorado trimming — provides explicit control over each processing stage
- AMR screening at three levels (reads, contigs, bins) rather than contigs alone — captures resistance genes that don't assemble due to low coverage

---

### [`wetland-surveillance/`](wetland-surveillance/) — Multi-Omics Wetland Surveillance

**Publication:** Perlas A\*, Reska T\*, et al. — *Preprint* (2025) · [DOI](https://doi.org/10.1101/2025.09.05.674394)

Four parallel analysis tracks from dual DNA/RNA extraction, implementing a comprehensive One Health monitoring approach:

| Track | Approach | Key Tools | Target |
|:------|:---------|:----------|:-------|
| 1. Metagenomics | Shotgun DNA | Kraken2, MetaFlye + nanoMDBG, Racon + Medaka, AMRFinderPlus, PlasmidFinder | Microbial community & AMR |
| 2. RNA Virome | Viral community | nanoMDBG + Medaka, DIAMOND BLASTx (NCBI nr) | Viral diversity |
| 3. eDNA Metabarcoding | Vertebrate host ID | OBITools4, Cutadapt, VSEARCH, MIDORI2 12S rRNA | Wildlife host range |
| 4. AIV WGS | Influenza genomes | minimap2, SAMtools, BCFtools, MAFFT, IQ-TREE2 | Avian influenza characterization |

*\*Shared first authorship*

---

## Technology Stack

| Category | Tools |
|:---------|:------|
| **Workflow manager** | Snakemake (reproducible, scalable) |
| **Basecalling** | Guppy, Dorado (HAC / SUP models) |
| **Sequencing platforms** | Oxford Nanopore Technologies (MinION, PromethION) |
| **Languages** | Python 3, Bash |
| **Analysis libraries** | Pandas, NumPy, scikit-bio, SciPy, Matplotlib |
| **Infrastructure** | HPC cluster deployment, containerized environments |

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

- **Air study:** Reska T, Pozdniakova S, Urban L. "Air monitoring by nanopore sequencing." *ISME Communications* (2024). DOI: [10.1093/ismeco/ycae058](https://doi.org/10.1093/ismeco/ycae058)
- **Aquatic study:** Perlas A\*, Reska T\*, Sánchez-Cano A, et al. "Real-time genomic pathogen, resistance, and host range characterization from passive water sampling of wetland ecosystems." *Preprint* (2025). DOI: [10.1101/2025.09.05.674394](https://doi.org/10.1101/2025.09.05.674394)
