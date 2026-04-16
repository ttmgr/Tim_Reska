# Step 2: Metagenomic Taxonomic Classification and Read Normalization

## Metadata

- **Step Number:** 2
- **Step Name:** Metagenomic taxonomic classification and read normalization
- **Objective:** Assign taxonomic labels to individual reads for microbial community composition analysis, with read normalization for cross-sample comparison
- **Context Provided:** Filtered FASTQ from Step 1 (shotgun track, Q >= 9 / >= 100 bp); 12 wetland sites across three countries; 2 replicates per site; variable sequencing depth across samples
- **Constraints:** Must use Kraken2 v2.1.2 with the NCBI nt_core database (not Standard, not full nt, not PlusPF), normalize to 87,000 reads with SeqKit for cross-sample comparison, and exclude samples below the normalization threshold

## Provenance Note

The prompt text below is a reconstruction derived from the preserved metadata, the wetland reference pipeline, and scored notes. It is not a verbatim export of the original chat prompt.

## Prompt Text

> Write the taxonomic classification step for nanopore metagenomic reads from environmental water samples collected at 12 wetland sites across Germany, France, and Spain. Use Kraken2 with an appropriate nucleotide database, produce both a per-read classification output and a summary report, and describe the read normalization strategy needed for cross-sample beta-diversity comparison given variable sequencing depths across samples.

## Benchmark-Critical Constraints

- The classification database is NCBI nt_core (a curated subset of the full NCBI nucleotide database). Not the Kraken2 Standard database, not PlusPF, and not the full nt.
- Read normalization to 87,000 reads using SeqKit v2.3.0 is required for comparable cross-sample diversity metrics.
- One sample (GA3.1, 28,000 reads) was excluded for insufficient sequencing depth.
- Both summary report and per-read classification output must be produced.
- Beta-diversity uses Bray-Curtis dissimilarity on genus-level reads; visualization uses PCoA and stacked bar plots of the top 20 genera at >= 1% relative abundance.

## Expected Ground Truth Response

**Tools:**
1. Kraken2 v2.1.2
2. SeqKit v2.3.0 (read normalization/downsampling)

**Critical parameters:**
- Database: NCBI nt_core (May 2025)
- Normalization depth: 87,000 reads
- Excluded samples: GA3.1 (28,000 reads, insufficient depth)
- Output: report file (`--report`) and per-read classification (`--output`)
- Taxonomic classification success: 16-54% of reads assignable

**Output format:** Kraken2 report files + per-read classification output; normalized read counts for downstream beta-diversity analysis

**Acceptable alternatives:**
- Kraken2 v2.1.x versions are acceptable
- Alternative normalization tools (e.g., seqtk) are acceptable if the depth and logic are preserved

## Known Failure Modes Observed

- Recommending the wrong Kraken2 database (Standard, PlusPF, or full nt instead of nt_core)
- Not mentioning read normalization/downsampling before cross-sample comparison
- Using the wrong normalization tool or approach (e.g., rarefaction instead of SeqKit subsampling)
- Not noting that taxonomic classification success varied (16-54% of reads assignable)
- Applying a confidence threshold without discussing the trade-off
- Using an older Kraken2 version (v2.0.7 was used in the aerobiome pipeline; this study uses v2.1.2)

## Notes

Database choice is the most common source of incorrect answers at this step. The distinction between nt_core (curated subset) and the full nt or Standard databases is critical and frequently missed. The normalization step using SeqKit ensures comparable diversity metrics and is distinct from rarefaction approaches sometimes recommended by models.
