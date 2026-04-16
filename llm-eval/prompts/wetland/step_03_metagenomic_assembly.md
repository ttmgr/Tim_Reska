# Step 3: Metagenomic Assembly (Dual Assembler Strategy)

## Metadata

- **Step Number:** 3
- **Step Name:** Metagenomic assembly using a dual assembler strategy
- **Objective:** Assemble reads into contiguous sequences using two complementary assemblers to maximize recovery of microbial genomes and genomic elements
- **Context Provided:** Filtered FASTQ from Step 1 (shotgun track); SUP-basecalled nanopore long reads from environmental water samples; expectation that different assemblers recover different genomic content
- **Constraints:** Must use both metaFlye v2.9.6 (with `--meta` and `--nano-hq`) and nanoMDBG v1.1 as complementary assemblers; short-read assemblers are incorrect for this data

## Provenance Note

The prompt text below is a reconstruction derived from the preserved metadata, the wetland reference pipeline, and scored notes. It is not a verbatim export of the original chat prompt.

## Prompt Text

> Write the metagenomic assembly step for super-accuracy basecalled nanopore long reads from environmental water samples. The goal is to maximize recovery of diverse microbial genomes and genomic elements. Consider whether a single assembler is sufficient or whether complementary assembly strategies could improve recovery. Use assemblers appropriate for nanopore long-read metagenomic data and specify the correct read-type flags for SUP-basecalled data.

## Benchmark-Critical Constraints

- The validated workflow uses a dual assembler strategy: metaFlye v2.9.6 AND nanoMDBG v1.1.
- metaFlye must be invoked with both `--meta` (metagenomic mode) and `--nano-hq` (for SUP-basecalled reads, not `--nano-raw`).
- nanoMDBG uses a minimizer-space de Bruijn graph approach that complements metaFlye's overlap-layout-consensus approach.
- Short-read assemblers (MEGAHIT, SPAdes) are incorrect for nanopore long-read data.
- Each assembler produces a separate set of contigs that require different polishing strategies in Step 4.

## Expected Ground Truth Response

**Tools:**
1. metaFlye v2.9.6 (Flye with `--meta`)
2. nanoMDBG v1.1

**Critical parameters:**
- metaFlye: `--nano-hq` flag for SUP-basecalled reads, `--meta` for metagenomic data
- nanoMDBG: separate assembly run producing complementary contigs
- Two independent assembly outputs for downstream polishing

**Output format:** Two sets of assembled contigs (FASTA), one per assembler

**Acceptable alternatives:**
- metaFlye alone is partially acceptable (it was the primary assembler) but not the full validated workflow
- nanoMDBG alone is partially acceptable but less standard
- Other long-read assemblers (e.g., Canu, wtdbg2) are scientifically defensible but not the validated tools

## Known Failure Modes Observed

- Recommending only a single assembler (most models suggest only metaFlye or only Flye)
- Not knowing nanoMDBG exists (it is a relatively new tool)
- Using `--nano-raw` instead of `--nano-hq` for SUP-basecalled data
- Recommending short-read assemblers (MEGAHIT, SPAdes)
- Omitting the `--meta` flag for metagenomic data
- Not explaining why a dual assembler strategy provides complementary recovery

## Notes

The dual assembler strategy is a key distinguishing feature of the wetland pipeline. Pathogens identified by de novo assembly are highlighted separately in the study results. Most LLMs will suggest only metaFlye, which is the more established tool; nanoMDBG is relatively new and uses a fundamentally different graph-based approach (minimizer-space de Bruijn graph vs overlap-layout-consensus).
