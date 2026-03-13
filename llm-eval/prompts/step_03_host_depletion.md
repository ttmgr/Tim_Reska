# Step 3: Host/Human DNA Depletion

## Metadata

- **Step Number:** 3
- **Step Name:** Host/human DNA depletion
- **Objective:** Remove host-associated reads if present, while preserving compatibility with the downstream metagenomics workflow
- **Context Provided:** Filtered FASTQ input from steps 1 and 2; environmental air sample context is preserved
- **Constraints:** Must use long-read-aware alignment logic and return a FASTQ suitable for downstream classification and assembly

## Provenance Note

The prompt text below is a reconstruction derived from the preserved metadata, the aerobiome reference pipeline, and the scored notes in `results/tables/scoring_matrix.csv`. It is not a verbatim export of the original chat prompt.

## Prompt Text

> The current input is nanopore FASTQ from low-biomass environmental air samples. Write the host-depletion step that would be appropriate before downstream taxonomic classification and assembly. If this step may not be necessary for this sample type, say so explicitly, but still show what a defensible long-read host-depletion command would look like.

## Expected Ground Truth Response

**Ground-truth status:** Not performed in the published aerobiome pipeline

**Expected defensible recommendation:** minimap2 with `-x map-ont`, followed by extraction of unmapped reads

**Output format:** Host-depleted FASTQ, or a justified statement that the original FASTQ can proceed unchanged

## Known Failure Modes Observed

- Using Bowtie2 or BWA instead of a long-read aligner
- Treating host depletion as mandatory without considering air-sample context
- Using the wrong minimap2 preset
- Failing to explain why host depletion is optional in the validated air workflow

## Notes

This step intentionally measures whether a model can distinguish between a generally sensible metagenomics convention and what was actually required for this sample type. In the current matrix, 14 of 28 evaluated entries are fully correct here.
