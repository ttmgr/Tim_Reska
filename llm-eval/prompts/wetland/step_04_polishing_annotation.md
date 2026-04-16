# Step 4: Assembly Polishing and Contig Annotation

## Metadata

- **Step Number:** 4
- **Step Name:** Assembler-specific polishing and contig annotation
- **Objective:** Polish assembled contigs to reduce sequencing errors and annotate them for taxonomic and functional content, using assembler-appropriate polishing strategies
- **Context Provided:** Two sets of assembled contigs from Step 3 (metaFlye and nanoMDBG outputs); filtered FASTQ reads for polishing; the two assemblers produce outputs with different error profiles requiring different polishing approaches
- **Constraints:** Must apply assembler-specific polishing (three-round Racon + Medaka for metaFlye; Medaka only for nanoMDBG), use Prokka for functional annotation, and include Kraken2 contig-level classification as an independent taxonomic check

## Provenance Note

The prompt text below is a reconstruction derived from the preserved metadata, the wetland reference pipeline, and scored notes. It is not a verbatim export of the original chat prompt.

## Prompt Text

> Write the polishing and annotation stage for assembled contigs from a dual assembler strategy that used metaFlye and nanoMDBG on nanopore long reads. The two assemblers produce outputs with different error profiles. Describe the polishing workflow for each assembler's output, followed by taxonomic and functional annotation of the polished contigs.

## Benchmark-Critical Constraints

- metaFlye assemblies require a three-stage polishing workflow: (1) align reads to contigs with minimap2 v2.28, (2) three iterative rounds of Racon v1.5.0 consensus correction, (3) one round of Medaka v1.7.2 neural-network polishing.
- nanoMDBG assemblies are polished with Medaka v1.7.2 only (no Racon), because nanoMDBG already produces relatively polished output from its minimizer-space approach.
- Taxonomic annotation of contigs uses Kraken2 (nt_core), providing an independent check on read-level taxonomy from Step 2.
- Functional annotation uses Prokka v1.14.5 with `--metagenome` flag.

## Expected Ground Truth Response

**Tools:**
1. minimap2 v2.28 (read-to-contig alignment for Racon)
2. Racon v1.5.0 (3 rounds, metaFlye only)
3. Medaka v1.7.2 (both assemblers)
4. Kraken2 (contig-level taxonomic classification)
5. Prokka v1.14.5 (functional annotation)

**Critical parameters:**
- metaFlye polishing: minimap2 alignment -> 3x Racon -> 1x Medaka
- nanoMDBG polishing: 1x Medaka only
- Prokka: `--metagenome` flag for metagenomic input

**Output format:** Polished contig FASTA files + Prokka annotation files (GFF, GBK, FNA) for each assembler's output

**Acceptable alternatives:**
- Two rounds of Racon instead of three is defensible but not the validated configuration
- Medaka followed by a final Racon round (reversed order) is scientifically plausible but not the validated workflow

## Known Failure Modes Observed

- Applying the same polishing strategy to both assemblers (not recognizing the different error profiles)
- Omitting polishing entirely
- Using only Medaka or only Racon (without the full three-stage pipeline for metaFlye)
- Recommending only one round of Racon polishing instead of three
- Omitting the Prokka annotation step
- Not mentioning that contig-level Kraken2 classification provides an independent check on read-level taxonomy

## Notes

The assembler-specific polishing strategy is a key design feature of this pipeline. Models that recommend a generic polishing workflow for both assemblers miss the validated distinction. The Prokka annotation step feeds directly into the AMR/virulence detection in Step 6 by providing gene predictions on the polished contigs.
