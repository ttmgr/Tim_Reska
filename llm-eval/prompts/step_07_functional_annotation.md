# Step 7: Functional Annotation

## Metadata

- **Step Number:** 7
- **Step Name:** Functional annotation
- **Objective:** Annotate reads, contigs, and bins for AMR and virulence features in a way that preserves the multi-level design of the validated workflow
- **Context Provided:** Assembly and binning outputs from prior stages, plus the existence of the original read branch
- **Constraints:** Must support metagenomic input, preserve the read/contig/bin multi-level design, and include specialized AMR / virulence logic rather than only general-purpose annotation

## Provenance Note

The prompt text below is a reconstruction derived from the preserved metadata, the aerobiome reference pipeline, and the scored notes in `results/tables/scoring_matrix.csv`. It is not a verbatim export of the original chat prompt.

## Prompt Text

> Write the functional annotation stage for this nanopore metagenomics workflow. Cover antimicrobial resistance and virulence screening across reads, contigs, and bins, and include any required file-format conversion needed for read-level screening as well as the contig- and bin-level branches.

## Benchmark-Critical Constraints

- The validated workflow keeps the annotation design multi-level across reads, contigs, and bins.
- Read-level AMR screening requires FASTQ to FASTA conversion with `seqkit` before AMRFinderPlus.
- AMRFinderPlus and ABRicate are both required to preserve the validated AMR and virulence branches.
- Answers that collapse the workflow to contigs only or to general-purpose annotation tools are not faithful to the benchmarked design.

## Expected Ground Truth Response

**AMR detection:** AMRFinderPlus v3.12.8

**Virulence / resistance screening:** ABRicate v1.0.1

**Critical design details:**
- annotation is applied to reads, contigs, and bins
- read-level screening requires FASTQ → FASTA conversion with `seqkit`
- the answer should preserve the fact that AMR and virulence screening are not confined to contigs alone

**Output format:** AMR and virulence result tables for the relevant levels

## Known Failure Modes Observed

- Restricting annotation to contigs only
- Omitting read-level screening entirely
- Missing the `seqkit` conversion step for read-level AMRFinderPlus use
- Recommending only Prokka or Bakta without AMR-focused screening
- Returning AMR logic without the virulence-screening branch

## Notes

Functional annotation ties together whether the model has preserved the full pipeline state. In the current matrix, only 9 of 28 evaluated entries are fully correct at this stage.
