# Step 4: Taxonomic Classification of Reads

## Metadata

- **Step Number:** 4
- **Step Name:** Taxonomic classification of reads
- **Objective:** Assign taxonomic labels to nanopore reads and produce outputs that support downstream community analysis
- **Context Provided:** Filtered FASTQ from the earlier stages, with host-depletion status made explicit
- **Constraints:** Must produce both report-level and read-level outputs and must use a database choice appropriate to the validated workflow

## Provenance Note

The prompt text below is a reconstruction derived from the preserved metadata, the aerobiome reference pipeline, and the scored notes in `results/tables/scoring_matrix.csv`. It is not a verbatim export of the original chat prompt.

## Prompt Text

> Write the taxonomic classification step for nanopore metagenomic reads from low-biomass air samples. The command should produce a per-read classification output and a summary report. Use a database choice that is appropriate to the validated workflow and note any additional handling needed for cross-sample comparison.

## Expected Ground Truth Response

**Tool:** Kraken2 v2.0.7

**Critical parameters and context:**
- NCBI nt database
- explicit report file and per-read output file
- awareness that downstream community comparison used phase-specific downsampling

**Output format:** Kraken2 report plus per-read classification output

## Known Failure Modes Observed

- Using the wrong Kraken2 database, especially Standard or PlusPF in place of nt
- Omitting the report or output flags
- Ignoring the downsampling context used in the validated cross-sample analysis
- Returning only a generic BLAST-style answer without a practical metagenomics classification workflow

## Notes

Taxonomic classification is no longer the primary bottleneck for stronger entries in the matrix, but database choice and output chaining still separate merely plausible answers from correct ones.
