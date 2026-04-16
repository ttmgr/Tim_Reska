# Reference Pipeline — Wetland Surveillance

Ground truth pipeline for multi-omics One Health surveillance of wetland ecosystems. All tools, versions, and parameters are from the validated workflow published in Perlas A\*, Reska T\*, et al. — *Real-time genomic pathogen, resistance, and host range characterization from passive water sampling of wetland ecosystems*. Applied and Environmental Microbiology (2025/2026).

The pipeline processes **dual-extracted DNA and RNA** from passive water samplers through **four parallel analysis tracks**, combining untargeted community characterization with targeted pathogen and viral detection. Command blocks below use schematic filenames; database paths are grounded to the concrete defaults used in the wetland workflow (`../pipelines/wetland-surveillance/`).

**Sequencing context:**
- Platform: Oxford Nanopore Technologies (MinION Mk1c / Mk1d)
- Kit: Rapid Barcoding Kit (SQK-RBK114.24) for shotgun and AIV; Ligation Sequencing Kit (SQK-LSK114) for 12S metabarcoding; Rapid Barcoding Kit (SQK-RPB114.24) for virome
- Flow cells: R10.4.1
- Sample type: Environmental water samples from passive torpedo-shaped samplers (12 wetland sites across Germany, France, Spain; 2 replicates per site; dual DNA/RNA extraction)
- Data acquisition: MinKNOW v24.11.10, 5 kHz, 24-hour runs

**Key differences from the aerobiome ground truth:**
- **SUP basecalling** (not HAC)
- **Dorado v5.0.0** (not Guppy/Dorado v4.3.0)
- **Four parallel analysis tracks** (not one linear pipeline)
- **Dual assembler strategy** (metaFlye + nanoMDBG)
- **RNA virome track** (nanoMDBG + DIAMOND BLASTx against NCBI nr)
- **eDNA metabarcoding track** (OBITools4 + VSEARCH + MIDORI2)
- **AIV whole-genome sequencing track** (minimap2 + BCFtools + IQ-TREE2)
- **MEGAN-CE LCA** for pathogen identification (not just Kraken2)
- **Prodigal + AMRFinderPlus --plus** for protein-level AMR detection
- **PlasmidFinder** for AMR mobility assessment

---

## Step 1: Basecalling, Demultiplexing, Adapter Trimming, and QC Filtering

**Objective:** Convert raw nanopore signals to basecalled, demultiplexed, adapter-trimmed, quality-filtered reads ready for four parallel analysis tracks.

This step uses **Dorado in super-accuracy (SUP) mode** for basecalling and demultiplexing, followed by Porechop for adapter/barcode trimming and NanoFilt for quality and length filtering. Critically, the QC thresholds differ by analysis track.

| Parameter | Value |
|:----------|:------|
| **Basecaller** | Dorado v5.0.0 |
| **Basecalling model** | `dna_r10.4.1_e8.2_400bps_sup@v5.0.0` |
| **Mode** | Super-accuracy (SUP) |
| **Demultiplexing** | Dorado demux (integrated) |
| **Adapter/barcode trimming** | Porechop v0.2.4 |
| **Quality filtering** | NanoFilt v2.8.0 |
| **Shotgun/virome QC** | Q ≥ 9, ≥ 100 bp |
| **AIV QC** | Q ≥ 8, ≥ 150 bp |

**Input:** Raw POD5 files from MinION sequencing runs
**Output:** Adapter-trimmed, quality-filtered FASTQ files per barcode, ready for track-specific downstream analysis

**Key details:**
- SUP mode is used throughout (not HAC as in the aerobiome pipeline) because Dorado v5.0.0 was the current version at the time of the study.
- Each sample was assigned two barcodes per sequencing run; reads from both barcodes are combined during downstream analysis.
- Track-specific QC thresholds: shotgun metagenomics and RNA virome use Q ≥ 9 / ≥ 100 bp; AIV sequencing uses Q ≥ 8 / ≥ 150 bp (lower quality threshold but higher length threshold to retain more of the amplified segments).

**Common LLM errors at this step:**
- Using HAC mode instead of SUP — SUP was the validated mode for this study
- Recommending Guppy instead of Dorado v5.0.0 (Guppy was deprecated by the time of this study)
- Applying a single QC threshold to all tracks instead of track-specific filtering
- Not performing demultiplexing as part of Dorado (recommending separate demux tools)
- Setting minimum read length too high for environmental water samples
- Omitting Porechop and relying solely on Dorado's built-in adapter trimming
- Using Illumina-appropriate quality thresholds (Q20–Q30)

```bash
# Basecalling (SUP mode) + demultiplexing
dorado basecaller dna_r10.4.1_e8.2_400bps_sup@v5.0.0 raw_pod5/ \
  --kit-name SQK-RBK114.24 > basecalled.bam
dorado demux basecalled.bam --output-dir demux/ --kit-name SQK-RBK114.24

# Convert BAM to FASTQ per barcode
samtools fastq demux/SQK-RBK114.24_barcode01.bam > barcode01.fastq

# Adapter/barcode trimming
porechop -i barcode01.fastq -o trimmed_barcode01.fastq

# Quality filtering — shotgun metagenomics and virome tracks
NanoFilt -q 9 -l 100 < trimmed_barcode01.fastq > filtered_shotgun.fastq

# Quality filtering — AIV track
NanoFilt -q 8 -l 150 < trimmed_barcode01.fastq > filtered_aiv.fastq
```

---

## Step 2: Metagenomic Taxonomic Classification and Read Normalization

**Objective:** Assign taxonomic labels to individual reads for microbial community composition analysis, with read normalization for cross-sample comparison.

| Parameter | Value |
|:----------|:------|
| **Classifier** | Kraken2 v2.1.2 |
| **Database** | NCBI nt_core (May 2025) |
| **Normalization** | SeqKit v2.3.0 |
| **Normalization depth** | 87,000 reads |
| **Excluded samples** | GA3.1 (28,000 reads — insufficient depth) |
| **Beta-diversity** | Bray-Curtis dissimilarity on genus-level reads |
| **Visualization** | PCoA; top 20 genera at ≥ 1% relative abundance |

**Input:** Filtered FASTQ from Step 1 (shotgun track, Q ≥ 9 / ≥ 100 bp)
**Output:** Kraken2 report files + per-read classification output; normalized read counts

**Key details:**
- The database is **NCBI nt_core** (not the Standard database, not the full nt, not PlusPF). This is a critical distinction — nt_core is a curated subset of the full NCBI nucleotide database.
- Normalization to 87k reads using SeqKit ensures comparable cross-sample diversity metrics. One sample (GA3.1, 28k reads) was excluded for insufficient depth.
- No filtering was applied prior to beta-diversity analysis — all detected genera were retained for Bray-Curtis and PCoA.
- Visualization used stacked bar plots of the 20 most abundant genera at ≥ 1% relative abundance (Python v3.12, pandas, matplotlib).

**Common LLM errors at this step:**
- Recommending the wrong Kraken2 database (Standard, PlusPF, or full nt instead of nt_core)
- Not mentioning read normalization/downsampling before cross-sample comparison
- Using the wrong normalization tool or approach (e.g., rarefaction instead of SeqKit subsampling)
- Not noting that taxonomic classification success varied (16–54% of reads assignable)
- Applying a confidence threshold without discussing the trade-off
- Using an older Kraken2 version (v2.0.7 was used in the aerobiome pipeline; this study uses v2.1.2)

```bash
# Taxonomic classification
kraken2 --db /databases/kraken2/ncbi_nt_core \
  --threads 16 \
  --report sample_report.txt \
  --output sample_output.txt \
  filtered_shotgun.fastq

# Read normalization for cross-sample comparison
seqkit sample -n 87000 -s 42 filtered_shotgun.fastq > normalized.fastq
```

---

## Step 3: Metagenomic Assembly (Dual Assembler Strategy)

**Objective:** Assemble reads into contiguous sequences using two complementary assemblers to maximize recovery of microbial genomes and genomic elements.

This step is fundamentally different from the aerobiome pipeline: the wetland study uses a **dual assembler strategy** with both metaFlye and nanoMDBG, because they complement each other for different types of genomic content.

| Parameter | Value |
|:----------|:------|
| **Primary assembler** | metaFlye v2.9.6 (Flye with `--meta`) |
| **Alternative assembler** | nanoMDBG v1.1 |
| **Read type flag (metaFlye)** | `--nano-hq` (for SUP-basecalled reads) |
| **Meta mode (metaFlye)** | `--meta` (required for metagenomic data) |

**Input:** Filtered FASTQ from Step 1 (shotgun track)
**Output:** Two sets of assembled contigs (one per assembler), each requiring different polishing strategies in Step 4

**Key details:**
- metaFlye uses an overlap-layout-consensus approach optimized for long reads; it excels at recovering longer contiguous sequences.
- nanoMDBG uses a minimizer-space de Bruijn graph approach; it can recover different genomic elements, particularly shorter or more complex sequences that OLC assemblers may miss.
- The dual assembler strategy is validated by the study: pathogens identified by de novo assembly are highlighted separately in the results (bold values in Figure 2 of the publication).
- `--nano-hq` is the correct flag for SUP-basecalled data (not `--nano-raw` for uncorrected reads).

**Acceptable alternatives:**
- metaFlye alone is acceptable (it was the primary assembler) but not fully correct
- nanoMDBG alone is acceptable but less standard
- Short-read assemblers (MEGAHIT, SPAdes) are **incorrect** for nanopore long-read data

**Common LLM errors at this step:**
- Recommending only a single assembler (most models will suggest only metaFlye)
- Not knowing nanoMDBG exists (it is a relatively new tool)
- Using `--nano-raw` instead of `--nano-hq` for SUP-basecalled data
- Recommending short-read assemblers
- Omitting the `--meta` flag
- Not explaining why a dual assembler strategy provides complementary recovery

```bash
# Primary assembly with metaFlye
flye --nano-hq filtered_shotgun.fastq --out-dir assembly_metaflye/ --meta --threads 16

# Alternative assembly with nanoMDBG
nanoMDBG -i filtered_shotgun.fastq -o assembly_nanomdbg/ --threads 16
```

---

## Step 4: Assembly Polishing and Contig Annotation

**Objective:** Polish assembled contigs to reduce sequencing errors and annotate them for taxonomic and functional content.

Critically, the two assemblers from Step 3 require **different polishing strategies**.

| Parameter | Value |
|:----------|:------|
| **metaFlye polishing — aligner** | minimap2 v2.28 |
| **metaFlye polishing — consensus** | Racon v1.5.0 (3 rounds) |
| **metaFlye polishing — neural** | Medaka v1.7.2 |
| **nanoMDBG polishing** | Medaka v1.7.2 only |
| **Taxonomic annotation** | Kraken2 (on contigs) |
| **Functional annotation** | Prokka v1.14.5 |

**Input:** Assembly FASTA from Step 3 (both metaFlye and nanoMDBG outputs) + reads for polishing
**Output:** Polished, annotated contig FASTA files + Prokka annotation files (GFF, GBK, FNA)

**Key details:**
- metaFlye assemblies undergo a **three-stage polishing workflow**: (1) align reads back to contigs with minimap2, (2) three iterative rounds of Racon consensus correction, (3) one round of Medaka neural-network polishing.
- nanoMDBG assemblies are polished with **Medaka only** (no Racon). This is because nanoMDBG already produces relatively polished output from its minimizer-space approach.
- Assembled contigs are subsequently annotated using Kraken2 for taxonomic classification and Prokka v1.14.5 for functional gene prediction.

**Common LLM errors at this step:**
- Applying the same polishing strategy to both assemblers
- Omitting polishing entirely
- Using only Medaka or only Racon (without the full three-stage pipeline for metaFlye)
- Recommending only one round of Racon polishing instead of three
- Omitting the Prokka annotation step
- Not mentioning that contig-level Kraken2 classification provides an independent check on read-level taxonomy

```bash
# --- metaFlye polishing (3× Racon + Medaka) ---

# Three rounds of Racon polishing
for i in 1 2 3; do
  minimap2 -t 16 assembly_metaflye/assembly.fasta filtered_shotgun.fastq > alignments.paf
  racon -t 16 filtered_shotgun.fastq alignments.paf assembly_metaflye/assembly.fasta \
    > assembly_metaflye/polished_${i}.fasta
  cp assembly_metaflye/polished_${i}.fasta assembly_metaflye/assembly.fasta
done

# Medaka polishing
medaka_polish -i filtered_shotgun.fastq -d assembly_metaflye/assembly.fasta \
  -o assembly_metaflye/medaka/ -t 16

# --- nanoMDBG polishing (Medaka only) ---

medaka_polish -i filtered_shotgun.fastq -d assembly_nanomdbg/assembly.fasta \
  -o assembly_nanomdbg/medaka/ -t 16

# --- Contig annotation ---

# Taxonomic annotation of contigs
kraken2 --db /databases/kraken2/ncbi_nt_core \
  --threads 16 \
  --report contigs_report.txt \
  assembly_metaflye/medaka/consensus.fasta

# Functional annotation
prokka --outdir annotation/ --prefix sample \
  --metagenome --cpus 16 \
  assembly_metaflye/medaka/consensus.fasta
```

---

## Step 5: Pathogen Identification (MEGAN LCA)

**Objective:** Identify pathogenic species through stringent alignment-based taxonomic assignment using the lowest common ancestor (LCA) algorithm.

This step provides a **higher-confidence pathogen identification** than Kraken2 alone by using alignment-based classification with conservative LCA thresholds.

| Parameter | Value |
|:----------|:------|
| **Aligner** | minimap2 v2.28 |
| **LCA classifier** | MEGAN-CE v6.21.1 |
| **Reference database** | NCBI nt_core |
| **LCA threshold** | ≥ 50% near-best alignments matching same genus |
| **Pathogen list** | CZ ID Pathogen list v0.2.1 (05/06/2024) |
| **Minimum reads** | ≥ 5 reads per pathogenic species per replicate |
| **Input levels** | Reads and contigs |

**Input:** Filtered FASTQ + polished contig FASTA from Steps 1/4
**Output:** Taxonomic assignments with pathogen classifications; pathogen read/contig count tables

**Key details:**
- Both reads and contigs are aligned to NCBI nt_core using minimap2, then processed through MEGAN-CE's LCA algorithm.
- Taxonomic assignment is accepted only if more than 50% of near-best alignments for a read match the same genus. This is more conservative than Kraken2's k-mer approach and provides higher-confidence species-level assignments.
- Pathogenic species are identified by cross-referencing against the Chan Zuckerberg ID initiative pathogen species list (CZ ID Pathogen list v0.2.1).
- Only pathogenic species with at least 5 reads in a given replicate (or sampling site) are considered for downstream analysis.
- The publication identified 17 unique pathogenic species at anthropogenic sites vs 15 at natural sites, with >13-fold higher pathogen-associated read counts at anthropogenic sites.

**Acceptable alternatives:**
- Kraken2 alone for community-level classification (but insufficient for stringent pathogen ID)
- DIAMOND BLASTx for protein-level classification (slower but more sensitive)
- BLAST for individual read verification

**Common LLM errors at this step:**
- Not knowing MEGAN-CE or recommending generic BLAST without the LCA step
- Using Kraken2 alone for pathogen identification (it provides community composition, not stringent pathogen calls)
- Not specifying the LCA threshold or using default thresholds without discussion
- Not mentioning the CZ ID pathogen list for pathogen classification
- Not applying the minimum read threshold for pathogen calls
- Not performing pathogen ID on both reads and contigs

```bash
# Align reads to NCBI nt_core
minimap2 -a -x map-ont -t 16 /databases/ncbi_nt_core.fasta filtered_shotgun.fastq \
  | samtools sort -o reads_vs_nt.bam
samtools index reads_vs_nt.bam

# Align contigs to NCBI nt_core
minimap2 -a -x asm20 -t 16 /databases/ncbi_nt_core.fasta assembly_metaflye/medaka/consensus.fasta \
  | samtools sort -o contigs_vs_nt.bam
samtools index contigs_vs_nt.bam

# MEGAN LCA classification (performed via MEGAN-CE GUI or command-line tools)
# Taxonomic assignment accepted if ≥50% of near-best alignments match same genus

# Cross-reference with CZ ID pathogen list
# Filter for pathogenic species with ≥5 reads per replicate
```

---

## Step 6: AMR, Virulence, and Plasmid Detection

**Objective:** Detect antimicrobial resistance genes, virulence factors, and plasmid-borne elements to characterize the resistance and pathogenic potential of the wetland microbiome.

This step is substantially more complex than the aerobiome pipeline's functional annotation: it combines AMRFinderPlus in `--plus` mode with Prodigal ORF prediction, targeted virulence screening via DIAMOND BLASTx against VFDB, and plasmid detection via PlasmidFinder.

| Parameter | Value |
|:----------|:------|
| **AMR detection** | AMRFinderPlus v4.0.23 |
| **AMRFinderPlus mode** | `--plus` (includes stress, biocide, and virulence genes) |
| **Minimum identity** | 90% (default) |
| **ORF prediction** | Prodigal v2.6.3 |
| **Virulence screening** | DIAMOND BLASTx v2.1.13 against VFDB |
| **Targeted screening** | ctxA and ctxB cholera toxin genes |
| **Plasmid detection** | PlasmidFinder v2.1.6 |
| **Application levels** | Reads + contigs |

**Input:** Filtered FASTQ (reads) + polished contig FASTA from Steps 1/4
**Output:** AMR gene tables, virulence factor reports, plasmid identification results

**Key details:**
- AMRFinderPlus is run in `--plus` mode, which extends detection beyond AMR to include stress response, biocide resistance, and virulence genes.
- For assembled contigs, open reading frames are first predicted with Prodigal v2.6.3, enabling nucleotide- AND protein-level analyses with AMRFinderPlus to maximize sensitivity.
- Targeted virulence screening for *Vibrio cholerae* toxin genes (ctxA, ctxB) is performed using DIAMOND BLASTx against the core protein dataset of the Virulence Factor Database (VFDB).
- Pathogen-AMR associations are considered high-confidence when the same resistance gene is detected on both reads and contigs from a sample, and when those reads/contigs are taxonomically linked to the same pathogen.
- Assembled contigs are screened for plasmids using PlasmidFinder v2.1.6 to assess the mobility potential of detected AMR genes.

**Common LLM errors at this step:**
- Using AMRFinderPlus without `--plus` mode (misses virulence and stress genes)
- Not using Prodigal for ORF prediction before protein-level AMRFinderPlus analysis
- Omitting the VFDB virulence screening entirely
- Not mentioning PlasmidFinder for AMR mobility assessment
- Applying AMR detection at only one level (contigs only) instead of both reads and contigs
- Not mentioning the pathogen-AMR association logic (cross-referencing AMR with taxonomy)
- Recommending only ABRicate without AMRFinderPlus (ABRicate was used in the aerobiome pipeline but not in this study)

```bash
# --- AMR detection on reads ---
amrfinder -n filtered_shotgun.fastq --plus -o amr_reads.tsv --threads 16

# --- AMR detection on contigs (with ORF prediction) ---

# Predict ORFs with Prodigal
prodigal -i assembly_metaflye/medaka/consensus.fasta \
  -o prodigal_genes.gff -a prodigal_proteins.faa \
  -p meta -f gff

# Run AMRFinderPlus with both nucleotide and protein input
amrfinder -n assembly_metaflye/medaka/consensus.fasta \
  -p prodigal_proteins.faa \
  --plus -o amr_contigs.tsv --threads 16

# --- Targeted virulence screening (VFDB) ---
diamond blastx --db /databases/vfdb_core \
  --query filtered_shotgun.fastq \
  --out vfdb_reads.tsv \
  --outfmt 6 --threads 16 --sensitive
# Specifically search for ctxA and ctxB cholera toxin subunit genes

# --- Plasmid detection ---
plasmidfinder.py -i assembly_metaflye/medaka/consensus.fasta \
  -o plasmid_results/ -p plasmidfinder_db/
```

---

## Step 7: RNA Virome Assembly and Classification

**Objective:** Assemble and classify RNA viral sequences from the RNA virome data to characterize the virome composition of wetland water samples.

This is a **completely separate analysis track** (Track 2) that processes RNA, not DNA. The approach uses nanoMDBG for assembly (not metaFlye), Medaka for polishing, and DIAMOND BLASTx against the NCBI non-redundant protein database for viral classification.

| Parameter | Value |
|:----------|:------|
| **Assembly** | nanoMDBG v1.1 |
| **Polishing** | Medaka v1.7.2 |
| **Classification** | DIAMOND BLASTx v2.1.13 |
| **Reference database** | NCBI non-redundant protein database (NR, accessed May 2025) |
| **Viral filter** | Kingdom "Viruses" (NCBI taxid: 10239) |
| **Identity threshold** | ≥ 80% |

**Input:** Filtered FASTQ from Step 1 (virome track, Q ≥ 9 / ≥ 100 bp) — these are RNA reads converted to cDNA via the Rapid SMART-9N protocol
**Output:** Polished viral contig FASTA + DIAMOND classification tables

**Key details:**
- RNA extracts were processed using the Rapid SMART-9N protocol with random priming and template-switching to generate long-length cDNA flanked by known sequences for PCR barcoding.
- nanoMDBG is used for assembly (not metaFlye) because it is well-suited for the shorter, more variable reads typical of virome sequencing.
- Polishing is with Medaka only (no Racon), consistent with the nanoMDBG polishing strategy.
- Classification uses DIAMOND BLASTx at the protein level against NCBI NR. Contigs with percentage identity above 80% matched to the kingdom "Viruses" (NCBI taxid: 10239) are annotated as viral contigs.
- The study detected viruses from mammals, birds, fish, insects, and plants across the wetland sites.

**Common LLM errors at this step:**
- Using metaFlye instead of nanoMDBG for virome assembly
- Using BLAST against nucleotide databases instead of DIAMOND BLASTx against NR (protein-level)
- Not applying the viral taxid filter (10239)
- Not specifying the identity threshold (≥ 80%)
- Applying DNA-appropriate tools to RNA virome data
- Recommending Kraken2 for virome classification (k-mer approaches are less sensitive for divergent viral sequences)
- Not understanding that this is a separate track processing RNA, not DNA

```bash
# Assembly with nanoMDBG
nanoMDBG -i filtered_virome.fastq -o virome_assembly/ --threads 16

# Polishing with Medaka
medaka_polish -i filtered_virome.fastq -d virome_assembly/assembly.fasta \
  -o virome_assembly/medaka/ -t 16

# Classification with DIAMOND BLASTx against NCBI NR
diamond blastx --db /databases/ncbi_nr \
  --query virome_assembly/medaka/consensus.fasta \
  --out virome_diamond.tsv \
  --outfmt 6 qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore staxids \
  --threads 16 --sensitive

# Filter for viral contigs (taxid 10239, ≥80% identity)
# Contigs matching kingdom "Viruses" with ≥80% identity are classified as viral
```

---

## Step 8: eDNA Vertebrate Metabarcoding

**Objective:** Identify vertebrate species present in the wetland environment using environmental DNA (eDNA) metabarcoding of the mitochondrial 12S rRNA gene.

This is **Track 3** and represents a fundamentally different analytical paradigm: **amplicon-based OTU clustering**, not shotgun metagenomics. The entire toolchain differs from Tracks 1–2.

| Parameter | Value |
|:----------|:------|
| **Demultiplexing** | OBITools4 obimultiplex v1.3.1 |
| **Tag structure** | 9 bp symmetrical tags, ≤ 2 mismatches allowed |
| **Primer removal** | Cutadapt v4.2 |
| **Primer set** | 12SV05 (Riaz et al. 2011): ~97 bp V5 region of 12S rRNA |
| **QC + clustering** | VSEARCH v2.21 |
| **Expected error filter** | maxEE 1.0 |
| **Chimera removal** | VSEARCH uchime_denovo |
| **Singleton removal** | Yes (dereplicated, singletons discarded) |
| **OTU clustering** | 97% similarity |
| **Taxonomy database** | MIDORI2 12S rRNA (version "Unique 266") |
| **Alignment** | Global alignment |
| **Avian filter** | Aves class only |
| **Quality thresholds** | ≥ 80% alignment coverage, ≥ 98% identity, ≥ 5 reads per OTU |
| **Biogeographic validation** | eBird regional occurrence |
| **Human blocking oligo** | 3 µM blocking oligonucleotide to suppress human DNA amplification |

**Input:** Basecalled 12S rRNA amplicon reads (from DNA extract, sequenced with SQK-LSK114)
**Output:** OTU table with vertebrate species assignments; validated avian species list per site

**Key details:**
- This track uses 12S rRNA amplicons (NOT shotgun reads). The ~97 bp V5 region was PCR-amplified with the 12SV05 primer set.
- Demultiplexing uses OBITools4 (NOT Dorado) because the amplicons use custom 9 bp tags appended to the primers, not ONT barcodes.
- The pipeline follows the standard amplicon/metabarcoding workflow: demultiplex → trim primers → filter by expected error → dereplicate → remove chimeras → cluster into OTUs → assign taxonomy.
- Taxonomy is assigned by global alignment against MIDORI2 12S rRNA database (version "Unique 266").
- Assignments are limited to bird species (Aves class) and accepted as robust if: alignment covers ≥ 80% of the query, identity ≥ 98%, and the taxonomic assignment has ≥ 5 reads after OTU aggregation.
- Biogeographically implausible species (not present in the sampled area per eBird) are collapsed to a higher rank or removed.
- A human-blocking oligonucleotide was included in PCR to suppress human DNA amplification.

**Common LLM errors at this step:**
- Treating this as shotgun metagenomics (recommending Kraken2, MetaPhlAn, or other shotgun classifiers)
- Not knowing OBITools4 exists (it is a niche eDNA/metabarcoding tool)
- Recommending DADA2 or other Illumina-focused amplicon tools without considering long-read adaptation
- Not understanding OTU clustering at 97% similarity
- Using BLAST against NCBI nt instead of MIDORI2 for 12S rRNA taxonomy
- Omitting chimera removal
- Not mentioning the expected error filter (maxEE)
- Not knowing the 12SV05 primer set or the V5 region of 12S rRNA
- Treating this as the same pipeline as shotgun metagenomics

```bash
# Demultiplexing with OBITools4 (9 bp tags, ≤2 mismatches)
obi import --fastq amplicon_reads.fastq reads/reads
obi import --ngsfilter ngsfilter.txt reads/ngsfilter
obi obimultiplex -t reads/ngsfilter reads/reads reads/assigned

# Primer removal with Cutadapt
cutadapt -g TTAGATACCCCACTATGC -G TAGAACAGGCTCCTCTAG \
  -o trimmed_R1.fastq -p trimmed_R2.fastq \
  assigned_R1.fastq assigned_R2.fastq

# Quality filtering, dereplication, chimera removal, OTU clustering with VSEARCH
vsearch --fastq_filter trimmed.fastq --fastq_maxee 1.0 --fastaout filtered.fasta
vsearch --derep_fulllength filtered.fasta --output derep.fasta --sizeout --minuniquesize 2
vsearch --uchime_denovo derep.fasta --nonchimeras nochim.fasta
vsearch --cluster_size nochim.fasta --id 0.97 --centroids otus.fasta --otutabout otu_table.txt

# Taxonomic assignment against MIDORI2 12S rRNA
vsearch --usearch_global otus.fasta --db /databases/midori2_unique266_12S.fasta \
  --id 0.98 --query_cov 0.80 --blast6out taxonomy.tsv --maxaccepts 10

# Filter to Aves class, ≥5 reads, cross-reference with eBird
```

---

## Step 9: AIV Whole-Genome Consensus

**Objective:** Generate consensus sequences for all eight influenza A virus genome segments from qPCR-positive samples using reference-based mapping.

This is **Track 4** — a reference-based analysis approach, fundamentally different from the de novo approaches in Tracks 1–3.

| Parameter | Value |
|:----------|:------|
| **Aligner** | minimap2 v2.28 |
| **Mapping preset** | `-ax map-ont` |
| **Reference database** | NCBI Influenza Virus Database (European AIV sequences, accessed 04/03/2023) |
| **BAM processing** | SAMtools v1.17 (sort, index, idxstats) |
| **Reference selection** | Best reference per segment (by read count via idxstats) |
| **Consensus calling** | BCFtools v1.17 |

**Input:** Filtered FASTQ from Step 1 (AIV track, Q ≥ 8 / ≥ 150 bp) — these are reads from M-RTPCR amplification of all 8 influenza A segments
**Output:** Consensus FASTA for each of the 8 AIV genome segments; genome coverage distributions

**Key details:**
- AIV detection was first performed by qPCR targeting the influenza matrix 1 (M1) gene. Whole-genome sequencing was performed only on qPCR-positive samples.
- Multi-segment amplification used M-RTPCR with MBTuni-12/MBTuni-13 universal primers that target conserved sequences of all 8 influenza A segments.
- Reference mapping uses segment-specific references from the NCBI Influenza Virus Database (European AIV nucleotide sequences).
- The reference selection workflow is iterative: (1) map all reads against the complete reference database, (2) use `samtools idxstats` to identify which reference gets the most reads per segment, (3) re-map all reads to the best reference set.
- Consensus calling uses BCFtools v1.17 to generate the final consensus sequence per segment.

**Common LLM errors at this step:**
- Using de novo assembly instead of reference-based mapping for viral WGS
- Not understanding the 8-segment structure of influenza A genomes
- Not performing segment-specific reference selection
- Using a generic viral database instead of the NCBI Influenza Virus Database
- Not specifying the `-ax map-ont` preset for minimap2
- Not mentioning the two-pass mapping strategy (initial mapping → best reference selection → re-mapping)
- Omitting the samtools idxstats step for reference selection
- Using iVar or other tools instead of BCFtools for consensus calling

```bash
# First pass: map reads against full European AIV reference database
minimap2 -ax map-ont -t 16 /databases/ncbi_influenza_europe.fasta filtered_aiv.fastq \
  | samtools sort -o aiv_initial.bam
samtools index aiv_initial.bam

# Select best reference per segment using idxstats
samtools idxstats aiv_initial.bam > idxstats.tsv
# Parse idxstats to identify the reference with most mapped reads for each of the 8 segments

# Second pass: re-map to best reference set
minimap2 -ax map-ont -t 16 best_references.fasta filtered_aiv.fastq \
  | samtools sort -o aiv_final.bam
samtools index aiv_final.bam

# Generate consensus for each segment
bcftools mpileup -f best_references.fasta aiv_final.bam | bcftools call -c | \
  bcftools consensus -f best_references.fasta -o aiv_consensus.fasta
```

---

## Step 10: AIV Phylogenetics and Subtyping

**Objective:** Determine the AIV subtype and place the recovered viral sequences in a phylogenetic context to understand their evolutionary relationships.

| Parameter | Value |
|:----------|:------|
| **Subtyping tools** | GISAID BLAST tool + FluSurver |
| **Subtyping target** | HA (hemagglutinin) segment |
| **Reference sequences** | All publicly available full-length H4 HA sequences from GISAID since 2015 |
| **Subsampling** | Stratified by host, country, and year (up to 3 representatives per group) |
| **MSA** | MAFFT v7.526 |
| **Phylogenetic inference** | IQ-TREE2 v2.3.4 |
| **Model selection** | ModelFinder Plus (`-m MFP`) |
| **Branch support** | 1,000 ultrafast bootstrap (`-bb 1000`) + 1,000 SH-aLRT (`-alrt 1000`) |
| **Visualization** | iTOL v7 |

**Input:** Consensus FASTA from Step 9 (specifically the HA segment)
**Output:** Phylogenetic tree with bootstrap support; AIV subtype classification

**Key details:**
- Subtyping is performed on the HA (hemagglutinin) consensus segment using the GISAID BLAST tool and FluSurver.
- To contextualize the sequence, all publicly available full-length H4 HA sequences since 2015 were downloaded from GISAID. A stratified subsampling approach reduced redundancy (grouped by host, country, year; up to 3 representatives per group).
- Multiple sequence alignment uses MAFFT v7.526.
- Phylogenetic inference uses IQ-TREE2 v2.3.4 with automatic model selection via ModelFinder Plus (`-m MFP`), which tests substitution models and selects the best-fit model by BIC.
- Branch support is assessed with 1,000 ultrafast bootstrap replicates AND 1,000 SH-aLRT replicates — both are recommended for robust support evaluation.
- The resulting tree was visualized in iTOL v7 with metadata annotations (host, location, collection date).
- The study classified the recovered AIV as low pathogenicity (LPAIV).

**Common LLM errors at this step:**
- Not knowing GISAID or FluSurver for influenza subtyping
- Recommending NCBI BLAST alone without influenza-specific databases
- Using standard bootstrap instead of ultrafast bootstrap with SH-aLRT
- Not specifying ModelFinder Plus (`-m MFP`) for automatic model selection
- Using a fixed substitution model instead of model selection
- Recommending RAxML or PhyML without the IQ-TREE2 ModelFinder advantage
- Not performing both UFboot and SH-aLRT (using only one support metric)
- Not understanding the importance of stratified subsampling for large reference datasets
- Using neighbor-joining or distance-based methods instead of maximum likelihood

```bash
# Download H4 HA references from GISAID (stratified subsample)
# Combine consensus HA with reference sequences
cat aiv_consensus_HA.fasta gisaid_h4_ha_references.fasta > alignment_input.fasta

# Multiple sequence alignment with MAFFT
mafft --auto --thread 16 alignment_input.fasta > aligned.fasta

# Maximum-likelihood phylogenetic inference with IQ-TREE2
iqtree2 -s aligned.fasta \
  -m MFP \
  -bb 1000 \
  -alrt 1000 \
  -nt AUTO \
  -pre aiv_phylogeny

# Visualize in iTOL (upload aligned.fasta.treefile to itol.embl.de)
```

---

## Pipeline Data Flow Summary

```
Passive water sampling (torpedo device, 3 days deployment)
            │
    ┌───────┴───────┐
    │  Dual DNA/RNA │
    │  Extraction   │
    │  (AllPrep)    │
    └───┬───────┬───┘
        │       │
   ┌────┴──┐  ┌─┴────┐
   │  DNA  │  │  RNA  │
   └──┬────┘  └──┬────┘
      │          │
      │    ┌─────┴──────────────────────────┐
      │    │                                │
      │    │                                │
      ▼    ▼                                ▼
Step 1: Dorado v5.0.0 SUP basecalling + Porechop v0.2.4 adapter trimming
      │
      ├── NanoFilt Q≥9, ≥100 bp (shotgun + virome tracks)
      │       │
      │       ├──────────────────────────────┐
      │       │                              │
      │       ▼                              ▼
      │  TRACK 1: Shotgun Metagenomics  TRACK 2: RNA Virome
      │       │                              │
      │  Step 2: Kraken2 v2.1.2 (nt_core)   Step 7: nanoMDBG v1.1
      │       │  + SeqKit 87k norm.          │  → Medaka v1.7.2
      │       │                              │  → DIAMOND BLASTx (NR)
      │  Step 3: metaFlye v2.9.6             │  → viral taxid 10239
      │       │  + nanoMDBG v1.1             │     ≥80% identity
      │       │                              │
      │  Step 4: 3×Racon + Medaka (metaFlye) │  → viral contig FASTA
      │       │  Medaka only (nanoMDBG)      │     + classification tables
      │       │  + Prokka v1.14.5            │
      │       │                              
      │  Step 5: minimap2 → MEGAN-CE LCA    
      │       │  + CZ ID pathogen list       
      │       │  (≥5 reads, ≥50% LCA)       
      │       │                              
      │  Step 6: AMRFinderPlus v4.0.23 --plus
      │       │  + Prodigal v2.6.3 (ORFs)
      │       │  + DIAMOND VFDB (virulence)
      │       │  + PlasmidFinder v2.1.6
      │       │
      │       └── pathogen + AMR + virulence + plasmid tables
      │
      ├── 12S rRNA amplicons (from DNA, SQK-LSK114)
      │       │
      │       ▼
      │  TRACK 3: eDNA Metabarcoding
      │       │
      │  Step 8: OBITools4 v1.3.1 (demux)
      │       │  → Cutadapt v4.2 (primers)
      │       │  → VSEARCH v2.21 (QC + 97% OTU)
      │       │  → MIDORI2 12S (Unique 266)
      │       │  → eBird validation
      │       │
      │       └── vertebrate species list per site
      │
      └── NanoFilt Q≥8, ≥150 bp (AIV track)
              │
              ▼
         TRACK 4: AIV Whole-Genome Sequencing
              │
         Step 9: minimap2 v2.28 → SAMtools v1.17
              │  → samtools idxstats (best ref per segment)
              │  → BCFtools v1.17 consensus
              │
         Step 10: GISAID BLAST + FluSurver (subtyping)
              │   → MAFFT v7.526 (MSA)
              │   → IQ-TREE2 v2.3.4 (-m MFP)
              │   → 1000 UFboot + 1000 SH-aLRT
              │
              └── AIV consensus + phylogenetic tree + subtype
```
