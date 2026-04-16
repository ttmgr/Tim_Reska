# Step 9: AIV Whole-Genome Consensus

## Metadata

- **Step Number:** 9
- **Step Name:** AIV whole-genome consensus generation
- **Objective:** Generate consensus sequences for all eight influenza A virus genome segments from qPCR-positive samples using reference-based mapping
- **Context Provided:** This is Track 4, a reference-based analysis approach; filtered FASTQ from Step 1 (AIV track, Q >= 8 / >= 150 bp); reads are from M-RTPCR amplification of all 8 influenza A segments using MBTuni-12/MBTuni-13 universal primers; AIV detection was first performed by qPCR targeting the influenza matrix 1 (M1) gene
- **Constraints:** Must use a two-pass minimap2 mapping strategy with segment-specific reference selection via samtools idxstats, reference database must be the NCBI Influenza Virus Database (European AIV sequences), and consensus calling must use BCFtools

## Provenance Note

The prompt text below is a reconstruction derived from the preserved metadata, the wetland reference pipeline, and scored notes. It is not a verbatim export of the original chat prompt.

## Prompt Text

> Write the AIV whole-genome consensus generation step for a wetland surveillance workflow. Influenza A-positive samples were identified by qPCR targeting the M1 gene, then all 8 genome segments were amplified by multi-segment RT-PCR (M-RTPCR) with universal primers and sequenced on ONT MinION. Describe the reference-based mapping workflow to generate consensus sequences for each of the 8 influenza A genome segments. Use an iterative reference selection approach: first map all reads to a comprehensive reference database, identify the best reference per segment, then re-map to the selected references for final consensus calling.

## Benchmark-Critical Constraints

- Alignment uses minimap2 v2.28 with the `-ax map-ont` preset.
- Reference database is the NCBI Influenza Virus Database (European AIV nucleotide sequences, accessed 04/03/2023).
- A two-pass mapping strategy is required: (1) initial mapping to the full reference database, (2) samtools idxstats to identify the best reference per segment by read count, (3) re-mapping to the best reference set.
- BAM processing uses SAMtools v1.17 (sort, index, idxstats).
- Consensus calling uses BCFtools v1.17 (mpileup + call + consensus).
- Must handle all 8 influenza A genome segments (PB2, PB1, PA, HA, NP, NA, M, NS).

## Expected Ground Truth Response

**Tools:**
1. minimap2 v2.28 (read-to-reference alignment)
2. SAMtools v1.17 (sort, index, idxstats)
3. BCFtools v1.17 (consensus calling)

**Critical parameters:**
- minimap2 preset: `-ax map-ont`
- Reference database: NCBI Influenza Virus Database (European AIV sequences)
- Two-pass strategy: initial mapping -> idxstats best-reference selection per segment -> re-mapping
- Consensus: BCFtools mpileup + call + consensus
- All 8 segments must be addressed

**Output format:** Consensus FASTA for each of the 8 AIV genome segments; genome coverage distributions

**Acceptable alternatives:**
- iVar for consensus calling (common in viral genomics but not the validated tool here)
- A single-pass mapping approach with a well-curated reference set (less optimal but defensible)
- Medaka for consensus polishing as a supplementary step

## Known Failure Modes Observed

- Using de novo assembly instead of reference-based mapping for viral WGS
- Not understanding the 8-segment structure of influenza A genomes
- Not performing segment-specific reference selection
- Using a generic viral database instead of the NCBI Influenza Virus Database
- Not specifying the `-ax map-ont` preset for minimap2
- Not mentioning the two-pass mapping strategy (initial mapping -> best reference selection -> re-mapping)
- Omitting the samtools idxstats step for reference selection
- Using iVar or other tools instead of BCFtools for consensus calling

## Notes

This is a reference-based analysis approach, fundamentally different from the de novo approaches in Tracks 1-3. The two-pass mapping strategy with idxstats-based reference selection is a practical detail that most LLMs miss, typically suggesting a single-pass approach with a pre-selected reference. The study used M-RTPCR with MBTuni-12/MBTuni-13 universal primers that target conserved sequences across all 8 influenza A segments. AIV detection was first confirmed by qPCR (M1 gene), so whole-genome sequencing was performed only on confirmed positive samples.
