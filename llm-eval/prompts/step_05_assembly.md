# Step 5: Metagenomic Assembly

## Metadata

- **Step Number:** 5
- **Step Name:** Metagenomic assembly
- **Objective:** Assemble nanopore metagenomic reads into polished contigs suitable for binning and annotation
- **Context Provided:** Long-read FASTQ input from the earlier steps, plus the fact that the data are mixed-community and ultra-low biomass
- **Constraints:** Must use a long-read metagenome-aware assembler for high-quality nanopore metagenomic reads and include explicit polishing

## Provenance Note

The prompt text below is a reconstruction derived from the preserved metadata, the aerobiome reference pipeline, and the scored notes in `results/tables/scoring_matrix.csv`. It is not a verbatim export of the original chat prompt.

## Prompt Text

> Write the assembly stage for this nanopore low-biomass metagenomics workflow. Use a long-read metagenome-aware assembler for high-quality nanopore metagenomic reads, then polish the assembly in three iterative rounds using read overlaps. Return a polished assembly that can be used for binning and downstream annotation.

## Benchmark-Critical Constraints

- The assembly is performed with Flye/MetaFlye in metagenomic mode (`--meta`) rather than isolate or short-read assembly logic.
- The validated read flag corresponds to HAC-basecalled reads in `--nano-hq` mode.
- Polishing uses minimap2 plus Racon for three rounds.
- The output must remain a polished assembly suitable for direct handoff into the binning stage.

## Expected Ground Truth Response

**Assembler:** MetaFlye / Flye with `--meta`

**Polishing:** minimap2 + Racon for 3 rounds

**Critical parameters:**
- `--nano-hq`
- `--meta`
- explicit polishing rounds rather than a single pass or no polishing

**Output format:** Polished assembly FASTA

## Known Failure Modes Observed

- Recommending short-read assemblers such as SPAdes or MEGAHIT
- Omitting polishing entirely
- Replacing the validated 3x Racon strategy with only one round or the wrong polishing stack
- Using the wrong Flye read flag
- Ignoring the low-biomass metagenomic context

## Notes

Assembly remains one of the hardest stages in the benchmark. In the current matrix, 17 of 28 evaluated entries are not fully correct here.
