# Step 5: Pathogen Identification (MEGAN LCA)

## Metadata

- **Step Number:** 5
- **Step Name:** Pathogen identification via alignment-based LCA classification
- **Objective:** Identify pathogenic species through stringent alignment-based taxonomic assignment using the lowest common ancestor (LCA) algorithm, providing higher-confidence pathogen calls than k-mer-based classification alone
- **Context Provided:** Filtered FASTQ reads and polished contig FASTA from Steps 1/4; Kraken2 community composition from Step 2; the need for a more stringent pathogen identification approach beyond k-mer classification
- **Constraints:** Must use minimap2 alignment to NCBI nt_core followed by MEGAN-CE LCA classification, cross-reference with the CZ ID pathogen list, apply minimum read thresholds, and perform pathogen ID on both reads and contigs

## Provenance Note

The prompt text below is a reconstruction derived from the preserved metadata, the wetland reference pipeline, and scored notes. It is not a verbatim export of the original chat prompt.

## Prompt Text

> Write the pathogen identification step for a wetland metagenomics surveillance workflow. Kraken2 has already been used for community-level taxonomic classification, but a more stringent alignment-based approach is needed to identify pathogenic species with higher confidence. The analysis should work at both the read level and the contig level, use a conservative lowest common ancestor approach, and cross-reference detections against a curated pathogen species list. Specify minimum read thresholds for confident pathogen calls.

## Benchmark-Critical Constraints

- Alignment uses minimap2 v2.28 against NCBI nt_core for both reads and contigs.
- LCA classification uses MEGAN-CE v6.21.1 with a threshold of >= 50% near-best alignments matching the same genus.
- Pathogenic species are identified by cross-referencing against the CZ ID Pathogen list v0.2.1 (05/06/2024).
- Only pathogenic species with >= 5 reads per replicate are considered for downstream analysis.
- Pathogen ID must be performed on both reads and contigs (not contigs alone).

## Expected Ground Truth Response

**Tools:**
1. minimap2 v2.28 (alignment to NCBI nt_core)
2. SAMtools (BAM processing)
3. MEGAN-CE v6.21.1 (LCA classification)

**Critical parameters:**
- Reference database: NCBI nt_core
- LCA threshold: >= 50% near-best alignments matching same genus
- Pathogen list: CZ ID Pathogen list v0.2.1
- Minimum reads: >= 5 per pathogenic species per replicate
- minimap2 presets: `-x map-ont` for reads, `-x asm20` for contigs
- Input levels: both reads and contigs

**Output format:** Taxonomic assignments with pathogen classifications; pathogen read/contig count tables

**Acceptable alternatives:**
- DIAMOND BLASTx for protein-level classification (slower but more sensitive)
- BLAST for individual read verification as a supplementary step
- Kraken2 alone is insufficient for stringent pathogen ID but acceptable for community composition

## Known Failure Modes Observed

- Not knowing MEGAN-CE or recommending generic BLAST without the LCA step
- Using Kraken2 alone for pathogen identification (it provides community composition, not stringent pathogen calls)
- Not specifying the LCA threshold or using default thresholds without discussion
- Not mentioning the CZ ID pathogen list for pathogen classification
- Not applying the minimum read threshold for pathogen calls
- Not performing pathogen ID on both reads and contigs

## Notes

This step provides a higher-confidence pathogen identification layer compared to Kraken2 alone. The study identified 17 unique pathogenic species at anthropogenic sites versus 15 at natural sites, with a greater than 13-fold higher pathogen-associated read count at anthropogenic sites. MEGAN-CE is a specialized tool that many LLMs do not know well, making this step a strong discriminator of pipeline knowledge.
