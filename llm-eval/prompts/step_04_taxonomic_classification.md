# Step 4: Taxonomic Classification of Reads

## Metadata

- **Step Number:** 4
- **Step Name:** Taxonomic classification of reads
- **Objective:** Assign taxonomic labels to nanopore reads and produce outputs that support downstream community analysis
- **Context Provided:** Filtered FASTQ from the earlier stages, with host-depletion status made explicit
- **Constraints:** Must use Kraken2 against the full NCBI nt database, produce both report-level and read-level outputs, and preserve the cross-sample comparison context

## Provenance Note

The prompt text below is a reconstruction derived from the preserved metadata, the aerobiome reference pipeline, and the scored notes in `results/tables/scoring_matrix.csv`. It is not a verbatim export of the original chat prompt.

## Prompt Text

> Write the taxonomic classification step for nanopore metagenomic reads from low-biomass air samples. Use Kraken2 with the full NCBI nt database, produce both a per-read classification output and a summary report, and note any additional handling needed for cross-sample comparison.

## Benchmark-Critical Constraints

- The classification database is the full NCBI nt database, not Kraken2 Standard or PlusPF.
- The answer must preserve both output branches: a summary report and a per-read classification file.
- Note the phase-specific downsampling used for downstream cross-sample community comparison.
- Keep the answer within a practical long-read metagenomics classification workflow rather than a generic BLAST-style suggestion.

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

Database choice and output chaining remain common sources of non-correct answers at this step.
