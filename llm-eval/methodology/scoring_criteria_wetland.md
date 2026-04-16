# Scoring Criteria — Wetland Pipeline Extensions

Supplemental scoring guidance for the wetland surveillance pipeline evaluation. This document extends the base rubric in [`scoring_criteria.md`](scoring_criteria.md) with wetland-specific scoring considerations.

The five scoring dimensions (Tool Selection, Parameter Accuracy, Output Compatibility, Scientific Validity, Executability) and their three-level scales are unchanged. This document clarifies how those dimensions apply to the 10-step, 4-track wetland pipeline.

---

## General Principle: Track Awareness

The wetland pipeline's 4-track structure introduces a new evaluation surface not present in the aerobiome benchmark: **track routing**. A model must understand which tools and parameters belong to which analysis track. Applying Track 1 tools to Track 2 data (or vice versa) is scored as a domain error regardless of whether the tool would technically run.

---

## Step-Specific Scoring Notes

### Step 1: Basecalling, Demux, Adapter Trimming, QC

| Dimension | Scoring consideration |
|:----------|:---------------------|
| Tool Selection | Dorado v5.0.0 = Correct. Guppy = Incorrect (deprecated at study time). Dorado v4.x = Acceptable. |
| Parameter Accuracy | SUP mode = Correct. HAC mode = Partially Correct (functional but not validated). Track-specific QC thresholds (Q9/100bp for shotgun/virome, Q8/150bp for AIV) = Correct. Single threshold for all tracks = Partially Correct. |
| Output Compatibility | Must produce track-specific filtered FASTQs. A single output without track differentiation = Fail. |
| Scientific Validity | Acknowledging the reason for track-specific thresholds = Sound. Blanket application without context = Questionable. |
| Executability | Standard. |

### Step 2: Taxonomic Classification + Normalization

| Dimension | Scoring consideration |
|:----------|:---------------------|
| Tool Selection | Kraken2 = Correct. MetaPhlAn = Acceptable. Centrifuge = Acceptable. |
| Parameter Accuracy | nt_core database = Correct. Standard = Partially Correct. Full nt = Partially Correct. PlusPF = Partially Correct. SeqKit normalization to a fixed depth = Correct. No normalization = Partially Correct (functional but not comparable). |
| Scientific Validity | Mentioning normalization before cross-sample comparison = Sound. Comparing raw unnormalized counts = Questionable. |

### Step 3: Metagenomic Assembly (Dual Assembler)

| Dimension | Scoring consideration |
|:----------|:---------------------|
| Tool Selection | metaFlye + nanoMDBG (dual strategy) = Correct. metaFlye alone = Acceptable. nanoMDBG alone = Acceptable. Any short-read assembler = Incorrect. |
| Parameter Accuracy | `--nano-hq` for SUP data = Correct. `--nano-raw` = Partially Correct. `--meta` flag = required. |
| Scientific Validity | Explaining why a dual assembler strategy provides complementary recovery = Sound. Single assembler without acknowledging alternatives = Questionable. |

### Step 4: Polishing and Contig Annotation

| Dimension | Scoring consideration |
|:----------|:---------------------|
| Tool Selection | Assembler-specific polishing (3×Racon + Medaka for metaFlye; Medaka only for nanoMDBG) = Correct. Same polishing for both = Partially Correct. No polishing = Incorrect. |
| Parameter Accuracy | Three rounds of Racon = Correct. One round = Partially Correct. |
| Output Compatibility | Polished contigs must be FASTA and usable by Prokka, AMRFinderPlus, and MEGAN in subsequent steps. |

### Step 5: Pathogen Identification (MEGAN LCA)

| Dimension | Scoring consideration |
|:----------|:---------------------|
| Tool Selection | minimap2 + MEGAN-CE (LCA) = Correct. Kraken2 alone for pathogen ID = Acceptable (provides community context but not stringent pathogen calls). BLAST + LCA manually = Acceptable. |
| Parameter Accuracy | ≥50% near-best LCA threshold = Correct. Default MEGAN thresholds without discussion = Partially Correct. CZ ID pathogen list cross-reference = Correct. Ad-hoc pathogen definition = Partially Correct. ≥5 read minimum = Correct. |
| Scientific Validity | Dual-level pathogen ID (reads + contigs) = Sound. Single level only = Questionable. |

### Step 6: AMR, Virulence, and Plasmid Detection

| Dimension | Scoring consideration |
|:----------|:---------------------|
| Tool Selection | AMRFinderPlus `--plus` + Prodigal + DIAMOND VFDB + PlasmidFinder = Correct. AMRFinderPlus without `--plus` = Acceptable. AMRFinderPlus without Prodigal = Partially Correct (misses protein-level sensitivity). Missing PlasmidFinder = Partially Correct. Missing VFDB screening = Partially Correct. |
| Parameter Accuracy | `--plus` mode = Correct. Default mode = Partially Correct. |
| Scientific Validity | Pathogen-AMR association logic (cross-referencing taxonomy with AMR on same reads/contigs) = Sound. AMR detection without pathogen context = Questionable. |

### Step 7: RNA Virome

| Dimension | Scoring consideration |
|:----------|:---------------------|
| Tool Selection | nanoMDBG + Medaka + DIAMOND BLASTx (NR) = Correct. metaFlye for virome = Acceptable. Kraken2 for viral classification = Partially Correct (less sensitive for divergent viruses). Short-read assemblers = Incorrect. |
| Parameter Accuracy | NCBI NR database = Correct. NCBI nt = Partially Correct. Viral taxid 10239 filter = Correct. ≥80% identity threshold = Correct. |
| Output Compatibility | Must clearly indicate this is RNA/cDNA data, not DNA. Using DNA parameters on RNA data = Fail. |
| Scientific Validity | Understanding that protein-level classification (BLASTx) is preferred for divergent viruses = Sound. Nucleotide-only approach = Questionable. |

### Step 8: eDNA Metabarcoding

| Dimension | Scoring consideration |
|:----------|:---------------------|
| Tool Selection | OBITools4 + Cutadapt + VSEARCH + MIDORI2 = Correct. DADA2 = Acceptable (common for amplicons but Illumina-focused). Shotgun metagenomics tools (Kraken2, MetaPhlAn) = Incorrect. |
| Parameter Accuracy | 97% OTU clustering = Correct. 99% ASV approach = Acceptable. maxEE 1.0 = Correct. MIDORI2 Unique 266 for 12S = Correct. NCBI nt for 12S = Partially Correct. eBird cross-validation = Correct. |
| Scientific Validity | Understanding amplicon vs shotgun paradigm = Sound. Treating amplicons as shotgun reads = Incorrect. Understanding OTU vs ASV debate = Sound. |

### Step 9: AIV Consensus

| Dimension | Scoring consideration |
|:----------|:---------------------|
| Tool Selection | minimap2 + SAMtools + BCFtools = Correct. De novo assembly for viral WGS = Incorrect (reference-based is the validated approach for influenza). iVar = Acceptable. |
| Parameter Accuracy | `-ax map-ont` = Correct. NCBI Influenza Virus Database = Correct. Generic viral database = Partially Correct. Two-pass mapping (initial → idxstats → best ref → re-map) = Correct. Single-pass = Partially Correct. |
| Scientific Validity | Understanding 8-segment influenza genome structure = Sound. Treating as single-segment = Questionable. Segment-specific reference selection = Sound. |

### Step 10: AIV Phylogenetics

| Dimension | Scoring consideration |
|:----------|:---------------------|
| Tool Selection | MAFFT + IQ-TREE2 = Correct. MAFFT + RAxML = Acceptable. MUSCLE + IQ-TREE2 = Acceptable. Neighbor-joining / UPGMA = Incorrect. |
| Parameter Accuracy | `-m MFP` (ModelFinder Plus) = Correct. Fixed substitution model = Partially Correct. UFboot 1000 + SH-aLRT 1000 = Correct. Standard bootstrap = Acceptable. No bootstrap = Incorrect. |
| Scientific Validity | Stratified subsampling of references = Sound. Including all references without subsampling = Questionable. Using both UFboot and SH-aLRT = Sound. Only one support metric = Acceptable. |

---

## Cross-Track Failure Modes

These failure patterns are unique to the multi-track wetland pipeline:

1. **Track conflation**: Applying shotgun metagenomics tools to amplicon data or vice versa. This is an Incorrect Tool Selection score.

2. **QC threshold confusion**: Using the same quality/length thresholds for all tracks when the validated pipeline uses track-specific parameters. This is Partially Correct Parameter Accuracy at best.

3. **Assembler misrouting**: Using metaFlye for virome assembly when nanoMDBG is the validated tool (or vice versa for the shotgun track). This is Acceptable Tool Selection (both tools work) but Questionable Scientific Validity if no rationale is given.

4. **DNA/RNA confusion**: Not distinguishing between DNA-based tracks (1, 3) and RNA-based tracks (2, 4). Failing to acknowledge RNA-to-cDNA conversion or RNA-specific considerations is Questionable Scientific Validity.

5. **Missing tracks**: Omitting an entire analysis track when the prompt specifies the full multi-omics workflow. The wetland study's strength is its integrated 4-track approach — missing a track is a fundamental gap.
