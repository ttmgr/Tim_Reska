# Step 6: AMR, Virulence, and Plasmid Detection

## Metadata

- **Step Number:** 6
- **Step Name:** Antimicrobial resistance, virulence factor, and plasmid detection
- **Objective:** Detect AMR genes, virulence factors, and plasmid-borne elements to characterize the resistance and pathogenic potential of the wetland microbiome
- **Context Provided:** Filtered FASTQ reads and polished contig FASTA from Steps 1/4; Prokka annotation from Step 4; dual DNA extraction from environmental water samples; known Vibrio cholerae detection at wetland sites
- **Constraints:** Must use AMRFinderPlus in `--plus` mode with Prodigal ORF prediction for protein-level analysis, DIAMOND BLASTx against VFDB for targeted virulence screening (including ctxA/ctxB cholera toxin genes), and PlasmidFinder for AMR mobility assessment; must apply detection at both read and contig levels

## Provenance Note

The prompt text below is a reconstruction derived from the preserved metadata, the wetland reference pipeline, and scored notes. It is not a verbatim export of the original chat prompt.

## Prompt Text

> Write the AMR, virulence, and plasmid detection stage for a wetland metagenomics surveillance workflow. The analysis should cover antimicrobial resistance genes, virulence factors (with specific attention to cholera toxin genes), and plasmid detection for AMR mobility assessment. Use AMRFinderPlus in its extended mode for AMR detection, predict open reading frames for protein-level analysis, screen for virulence factors against the VFDB, and detect plasmids. Apply the analysis to both reads and assembled contigs.

## Benchmark-Critical Constraints

- AMRFinderPlus v4.0.23 must be run in `--plus` mode (extends detection to stress response, biocide resistance, and virulence genes beyond standard AMR).
- Open reading frames must be predicted with Prodigal v2.6.3 before protein-level AMRFinderPlus analysis on contigs.
- AMRFinderPlus on contigs takes both nucleotide (`-n`) and protein (`-p`) input for maximum sensitivity.
- Virulence screening uses DIAMOND BLASTx v2.1.13 against the VFDB core protein dataset, with targeted screening for ctxA and ctxB cholera toxin subunit genes.
- Plasmid detection uses PlasmidFinder v2.1.6 to assess mobility potential of detected AMR genes.
- AMR detection must be applied at both read and contig levels.
- Pathogen-AMR associations are high-confidence when the same resistance gene is detected on both reads and contigs from a sample.

## Expected Ground Truth Response

**Tools:**
1. AMRFinderPlus v4.0.23 (`--plus` mode)
2. Prodigal v2.6.3 (ORF prediction)
3. DIAMOND BLASTx v2.1.13 (virulence screening against VFDB)
4. PlasmidFinder v2.1.6 (plasmid detection)

**Critical parameters:**
- AMRFinderPlus: `--plus` flag, 90% minimum identity (default)
- Prodigal: `-p meta` for metagenomic input
- DIAMOND: `--sensitive` mode against VFDB core
- Targeted virulence genes: ctxA and ctxB (Vibrio cholerae cholera toxin)
- Application levels: reads and contigs

**Output format:** AMR gene tables, virulence factor reports, plasmid identification results

**Acceptable alternatives:**
- ABRicate as a supplementary screening tool (but not as a replacement for AMRFinderPlus `--plus`)
- RGI/CARD as an alternative AMR database (scientifically defensible but not the validated tool)

## Known Failure Modes Observed

- Using AMRFinderPlus without `--plus` mode (misses virulence and stress genes)
- Not using Prodigal for ORF prediction before protein-level AMRFinderPlus analysis
- Omitting the VFDB virulence screening entirely
- Not mentioning PlasmidFinder for AMR mobility assessment
- Applying AMR detection at only one level (contigs only) instead of both reads and contigs
- Not mentioning the pathogen-AMR association logic (cross-referencing AMR with taxonomy)
- Recommending only ABRicate without AMRFinderPlus (ABRicate was used in the aerobiome pipeline but not in this study)

## Notes

This step is substantially more complex than the aerobiome pipeline's functional annotation. The aerobiome pipeline used AMRFinderPlus + ABRicate; the wetland pipeline replaces ABRicate with DIAMOND-against-VFDB for targeted virulence screening and adds PlasmidFinder for mobility assessment and Prodigal for ORF prediction. The `--plus` mode of AMRFinderPlus is frequently missed by models that default to standard AMR-only detection.
