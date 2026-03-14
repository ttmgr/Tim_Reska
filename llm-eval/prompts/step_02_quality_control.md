# Step 2: Quality Control and Read Statistics

## Metadata

- **Step Number:** 2
- **Step Name:** Quality control and read statistics
- **Objective:** Generate read-level quality summaries and length distributions without modifying the filtered FASTQ
- **Context Provided:** Output from step 1 is already basecalled, trimmed, and filtered FASTQ
- **Constraints:** Must accept already basecalled, trimmed, and filtered nanopore FASTQ input and produce reports rather than a transformed dataset

## Provenance Note

The prompt text below is a reconstruction derived from the preserved metadata, the aerobiome reference pipeline, and the scored notes in `results/tables/scoring_matrix.csv`. It is not a verbatim export of the original chat prompt.

## Prompt Text

> The reads have already been basecalled, adapter-trimmed, and filtered. Write the QC step for this nanopore metagenomics workflow. Use nanopore-appropriate tools to summarize read quality, read length distribution, and N50, and keep the data unchanged so the same FASTQ can proceed to the next analytical stage.

## Benchmark-Critical Constraints

- The input object is already basecalled, adapter-trimmed, and quality-filtered FASTQ from step 1.
- This is a report-only stage: the FASTQ should remain unchanged for the next analytical step.
- The answer must surface nanopore-specific read metrics such as length distribution, quality summary, and N50.

## Expected Ground Truth Response

**Tool:** NanoPlot or NanoStat

**Critical outputs:**
- read length distribution
- quality score summary
- N50 and related nanopore-specific run metrics

**Output format:** HTML, image, or tabular QC reports; the FASTQ remains unchanged

## Known Failure Modes Observed

- Recommending FastQC as the primary QC tool
- Ignoring nanopore-specific metrics and reporting only generic read counts
- Treating QC as an additional filtering step rather than an assessment step
- Returning a command that changes the data instead of generating reports

## Notes

This step is comparatively easy for modern systems. In the current matrix, 21 of 28 evaluated entries are fully correct here.
