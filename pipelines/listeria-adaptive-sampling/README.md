# Listeria Adaptive Sampling Pipeline

**Targeted Oxford Nanopore enrichment and quasi-metagenomic reconstruction of _Listeria monocytogenes_**

From: Reska T, et al. — *Manuscript in preparation*

---

## Overview

This workflow analyzes Oxford Nanopore adaptive sampling and matched native sequencing runs from complex food-safety samples to quantify target enrichment, recover _Listeria monocytogenes_ assemblies, and compare adaptive sampling against non-enriched sequencing on the same material.

The pipeline is organized as a modular Bash workflow that starts from basecalled BAM inputs, performs taxonomic profiling and target-read extraction, compares multiple long-read assembly strategies, screens for AMR markers, and compiles HTML and tabular reports for adaptive-sampling versus native-run comparisons.

## Why adaptive sampling is compared to native sequencing

Adaptive sampling makes it possible to enrich a target organism during sequencing by rejecting off-target molecules in real time. In this project, that strategy is evaluated directly against matched native runs to test whether enrichment improves the recovery of _Listeria_ signal, target-specific assemblies, and downstream functional interpretation without waiting for classical isolate-first workflows.

This use case sits close to quasi-metagenomics: a short enrichment or targeted-sequencing strategy increases the relative abundance of the pathogen of interest, even though the broader community composition is no longer interpreted as an undisturbed metagenome. The practical objective is faster target recovery and comparison of adaptive-sampling yield versus native sequencing yield.

## Tool Stack

| Module | Core tools | Role |
|:-------|:-----------|:-----|
| Input conversion | samtools | Convert basecalled BAM files to FASTQ |
| Adapter trimming and filtering | Porechop, NanoFilt | Remove adapters and short reads |
| QC | NanoStat | Summarize read yield and length distributions |
| Read-level taxonomy | Kraken2 | Profile the full dataset before target extraction |
| Target extraction | seqtk, SeqKit, project scripts | Isolate _Listeria_ reads and compile per-sample summaries |
| Assembly comparison | metaMDBG, Myloasm, Flye | Compare long-read assembly strategies on target-enriched reads |
| Polishing | Dorado aligner, Dorado polish | Improve bacterial assembly consensus quality |
| Functional profiling | AMRFinderPlus | Screen reads and contigs for AMR-associated markers |
| Contig-level taxonomy | Kraken2 contig classification | Confirm target-specific contigs after assembly |
| Reporting | Project Bash and Python scripts | Generate overview tables, comparative summaries, and HTML reports |

## Workflow

```text
Basecalled BAM files
    -> BAM to FASTQ conversion
    -> adapter trimming and length filtering
    -> read-level QC and Kraken2 classification
    -> target-read extraction for Listeria
    -> assembly with metaMDBG, Myloasm, and Flye
    -> Dorado-based polishing of draft assemblies
    -> contig extraction and contig-level classification
    -> AMRFinderPlus screening on reads and contigs
    -> per-sample overview tables
    -> HTML reporting and AS-versus-native comparison summaries
```

## Analytical Focus

- Compare adaptive sampling (AS) against matched native (N) runs on the same sample pairs.
- Quantify target enrichment relative to the full microbiome background.
- Evaluate whether AS improves recovery of longer or more complete _Listeria_ assemblies.
- Summarize AMR-associated markers and target contig recovery in a project-level report.
- Preserve paired reporting so adaptive-sampling gains and tradeoffs can be inspected directly.

## Major Outputs

- Read-level quality-control summaries and length-distribution metrics.
- Kraken2-based taxonomic profiles for full samples and extracted target fractions.
- Target-specific assemblies from three long-read assembly strategies.
- Polished contigs and contig-level _Listeria_ summaries.
- AMRFinderPlus outputs for reads and contigs.
- Overview tables for enrichment, assembly statistics, and target-contig recovery.
- HTML reports for full pipeline output and adaptive-sampling versus native comparisons.

## Execution Model

The workflow is written as a script-based pipeline oriented toward SLURM execution for larger datasets. The same project can also be run locally for smaller tests or partial analyses by exporting the expected array variables and calling the scripts directly.

The group repository contains the full execution scaffold, including:

- the interactive wrapper script
- installation guidance
- script-by-script workflow documentation
- SLURM orchestration notes
- troubleshooting and adaptation notes for other target organisms

## Related Project Materials

- [Study repository and metadata](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Food_Safety/Listeria-Adaptive-Sampling)
- [Installation and setup guide](https://github.com/ttmgr/GenomicsForOneHealth/blob/main/Food_Safety/Listeria-Adaptive-Sampling/docs/01_installation.md)
- [Pipeline workflow and script architecture](https://github.com/ttmgr/GenomicsForOneHealth/blob/main/Food_Safety/Listeria-Adaptive-Sampling/docs/02_pipeline_steps.md)
- [Execution and troubleshooting guide](https://github.com/ttmgr/GenomicsForOneHealth/blob/main/Food_Safety/Listeria-Adaptive-Sampling/docs/03_execution_guide.md)
- [Pipeline adaptation guide](https://github.com/ttmgr/GenomicsForOneHealth/blob/main/Food_Safety/Listeria-Adaptive-Sampling/docs/04_adapting_pipeline.md)
- [Food Safety overview](https://github.com/ttmgr/GenomicsForOneHealth/tree/main/Food_Safety)

## Notes

This page is the concise project overview for the personal repository. For the original helper scripts, placeholder-path configuration, local versus cluster execution details, and project-specific reporting utilities, use the paired group repository materials listed above.
