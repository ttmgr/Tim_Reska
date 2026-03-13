# Step 1: Basecalling, Adapter Trimming, and Length Filtering

## Metadata

- **Step Number:** 1
- **Step Name:** Basecalling, adapter trimming, and length filtering
- **Objective:** Convert raw nanopore signals into basecalled, adapter-trimmed, quality-filtered FASTQ reads that can be used for downstream QC, taxonomy, assembly, and annotation
- **Context Provided:** First step in the workflow; the model is told the sequencing platform, ONT chemistry, kit, and that the samples are low-biomass environmental air samples
- **Constraints:** Must produce runnable commands, preserve long-read context, and return filtered FASTQ output for the next stage

## Provenance Note

The prompt text below is a reconstruction derived from the preserved metadata, the aerobiome reference pipeline, and the scored notes in `results/tables/scoring_matrix.csv`. It is not a verbatim export of the original chat prompt.

## Prompt Text

> I am building a nanopore metagenomics workflow for ultra-low biomass environmental air samples generated with Oxford Nanopore chemistry R10.4.1 and the Rapid Barcoding Kit RBK114.24. Write the command sequence for the first processing stage: basecalling, adapter trimming, and quality/length filtering. Use tools appropriate for nanopore long reads, specify the critical model or preset, and make sure the output is a filtered FASTQ that can be passed into downstream QC and taxonomic classification.

## Expected Ground Truth Response

**Tools:**
1. Guppy v6.3.2 or Dorado v4.3.0 in HAC mode
2. Porechop for adapter trimming
3. NanoFilt v2.8.0 for quality and length filtering

**Critical parameters:**
- R10.4.1 HAC model
- Q ≥ 8
- minimum read length ≥ 100 bp
- explicit three-stage sequence rather than a single collapsed command

**Output format:** Adapter-trimmed, quality-filtered FASTQ

## Known Failure Modes Observed

- Recommending deprecated or inappropriate tools such as Albacore
- Using the wrong ONT model name or ignoring the R10.4.1 chemistry
- Applying Illumina-style thresholds such as Q20 or Q30
- Omitting Porechop or collapsing the basecall → trim → filter chain into an analytically incomplete answer
- Substituting Chopper or another filter without preserving the validated tool-chain logic

## Notes

This is one of the most important steps in the benchmark because later stages inherit every assumption made here. In the current matrix, 17 of 28 evaluated entries are not fully correct at this stage.
