# Step 10: AIV Phylogenetics and Subtyping

## Metadata

- **Step Number:** 10
- **Step Name:** AIV phylogenetics and subtyping
- **Objective:** Determine the AIV subtype and place the recovered viral sequences in a phylogenetic context to understand their evolutionary relationships
- **Context Provided:** Consensus FASTA from Step 9 (specifically the HA segment); the recovered AIV was classified as low pathogenicity (LPAIV); GISAID is the primary influenza sequence database; phylogenetic context requires reference sequences from related subtypes
- **Constraints:** Must use GISAID BLAST + FluSurver for subtyping, MAFFT for multiple sequence alignment, IQ-TREE2 with ModelFinder Plus for phylogenetic inference, and both ultrafast bootstrap and SH-aLRT for branch support

## Provenance Note

The prompt text below is a reconstruction derived from the preserved metadata, the wetland reference pipeline, and scored notes. It is not a verbatim export of the original chat prompt.

## Prompt Text

> Write the AIV subtyping and phylogenetic analysis step for a wetland surveillance workflow. A consensus sequence for the HA (hemagglutinin) segment has been generated from an influenza A-positive environmental water sample. Describe how to determine the AIV subtype using influenza-specific databases and tools, then place the sequence in a phylogenetic context. For the phylogenetic analysis, download reference sequences from GISAID with a stratified subsampling strategy, perform multiple sequence alignment, and infer a maximum-likelihood phylogenetic tree with robust branch support using both ultrafast bootstrap and SH-aLRT.

## Benchmark-Critical Constraints

- Subtyping uses the GISAID BLAST tool and FluSurver, not generic NCBI BLAST alone.
- Reference sequences: all publicly available full-length H4 HA sequences from GISAID since 2015.
- Stratified subsampling of reference sequences: grouped by host, country, and year (up to 3 representatives per group) to reduce redundancy.
- Multiple sequence alignment uses MAFFT v7.526.
- Phylogenetic inference uses IQ-TREE2 v2.3.4.
- Model selection uses ModelFinder Plus (`-m MFP`), which tests substitution models and selects the best fit by BIC.
- Branch support requires both 1,000 ultrafast bootstrap (`-bb 1000`) AND 1,000 SH-aLRT (`-alrt 1000`) replicates.
- Visualization uses iTOL v7 with metadata annotations (host, location, collection date).

## Expected Ground Truth Response

**Tools:**
1. GISAID BLAST tool + FluSurver (subtyping)
2. MAFFT v7.526 (multiple sequence alignment)
3. IQ-TREE2 v2.3.4 (phylogenetic inference)
4. iTOL v7 (visualization)

**Critical parameters:**
- Subtyping target: HA segment
- Reference dataset: full-length H4 HA from GISAID since 2015, stratified subsample (host/country/year, up to 3 per group)
- MAFFT: `--auto` flag
- IQ-TREE2: `-m MFP` (ModelFinder Plus), `-bb 1000` (ultrafast bootstrap), `-alrt 1000` (SH-aLRT)
- Both UFboot and SH-aLRT are required (not just one)

**Output format:** Phylogenetic tree with bootstrap support; AIV subtype classification

**Acceptable alternatives:**
- RAxML-NG as a phylogenetic inference tool (scientifically defensible but lacks the ModelFinder advantage)
- Standard bootstrap instead of ultrafast bootstrap (more conservative but computationally expensive)
- NCBI BLAST for initial subtyping (less comprehensive than GISAID for influenza)
- FigTree as an alternative to iTOL for visualization

## Known Failure Modes Observed

- Not knowing GISAID or FluSurver for influenza subtyping
- Recommending NCBI BLAST alone without influenza-specific databases
- Using standard bootstrap instead of ultrafast bootstrap with SH-aLRT
- Not specifying ModelFinder Plus (`-m MFP`) for automatic model selection
- Using a fixed substitution model instead of model selection
- Recommending RAxML or PhyML without the IQ-TREE2 ModelFinder advantage
- Not performing both UFboot and SH-aLRT (using only one support metric)
- Not understanding the importance of stratified subsampling for large reference datasets
- Using neighbor-joining or distance-based methods instead of maximum likelihood

## Notes

This is the final step of the AIV analysis track (Track 4). The study classified the recovered AIV as low pathogenicity (LPAIV). The combination of GISAID-specific tools for subtyping and IQ-TREE2 with dual branch support metrics represents current best practice in influenza phylogenetics. Models frequently recommend generic phylogenetic approaches without the influenza-specific subtyping step or recommend only one branch support method instead of both UFboot and SH-aLRT.
