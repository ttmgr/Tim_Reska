# Step 1: Basecalling, Demultiplexing, Adapter Trimming, and QC Filtering

## Metadata

- **Step Number:** 1
- **Step Name:** Basecalling, demultiplexing, adapter trimming, and QC filtering
- **Objective:** Convert raw nanopore signals into basecalled, demultiplexed, adapter-trimmed, quality-filtered FASTQ reads ready for four parallel analysis tracks
- **Context Provided:** First step in the workflow; the model is told the sequencing platform (ONT MinION, R10.4.1), kits (SQK-RBK114.24 for shotgun, SQK-LSK114 for 12S metabarcoding, SQK-RPB114.24 for virome), that samples are environmental water from passive torpedo-shaped samplers deployed across 12 European wetland sites, and that dual DNA/RNA extraction was performed
- **Constraints:** Must use Dorado v5.0.0 in SUP mode (not HAC), include integrated demultiplexing, use Porechop for adapter/barcode trimming, apply track-specific QC thresholds via NanoFilt, and produce filtered FASTQ output for downstream tracks

## Provenance Note

The prompt text below is a reconstruction derived from the preserved metadata, the wetland reference pipeline, and scored notes. It is not a verbatim export of the original chat prompt.

## Prompt Text

> I am building a nanopore metagenomics and surveillance workflow for environmental water samples collected with passive torpedo-shaped samplers from 12 wetland sites across Germany, France, and Spain. Dual DNA/RNA extraction was performed. Sequencing used an ONT MinION with R10.4.1 flow cells and the Rapid Barcoding Kit SQK-RBK114.24 for shotgun and AIV libraries. Write the command sequence for the first processing stage: basecalling, demultiplexing, adapter/barcode trimming, and quality/length filtering. Use the current Dorado basecaller in super-accuracy mode, and note that this workflow feeds into four parallel analysis tracks (shotgun metagenomics, RNA virome, eDNA metabarcoding, and AIV whole-genome sequencing) that require track-specific QC thresholds.

## Benchmark-Critical Constraints

- Use Dorado v5.0.0 in SUP mode, not HAC. The basecalling model is `dna_r10.4.1_e8.2_400bps_sup@v5.0.0`.
- Demultiplexing must be integrated via `dorado demux` with the correct kit name, not a separate third-party tool.
- Adapter/barcode trimming uses Porechop v0.2.4 (Dorado's built-in trimming alone is insufficient).
- Track-specific QC thresholds via NanoFilt v2.8.0: shotgun and virome tracks use Q >= 9, >= 100 bp; AIV track uses Q >= 8, >= 150 bp.
- Output must be filtered FASTQ files per barcode, ready for the four parallel downstream tracks.

## Expected Ground Truth Response

**Tools:**
1. Dorado v5.0.0 (basecalling + demultiplexing, SUP mode)
2. SAMtools (BAM-to-FASTQ conversion per barcode)
3. Porechop v0.2.4 (adapter/barcode trimming)
4. NanoFilt v2.8.0 (quality and length filtering)

**Critical parameters:**
- Basecalling model: `dna_r10.4.1_e8.2_400bps_sup@v5.0.0`
- Kit: SQK-RBK114.24
- Shotgun/virome QC: Q >= 9, >= 100 bp
- AIV QC: Q >= 8, >= 150 bp
- Explicit four-stage sequence: basecall -> demux -> trim -> filter

**Output format:** Adapter-trimmed, quality-filtered FASTQ files per barcode

**Acceptable alternatives:**
- Dorado v4.x in SUP mode would be partially acceptable but not the validated version
- Chopper as a NanoFilt alternative is acceptable only if the correct thresholds are preserved

## Known Failure Modes Observed

- Using HAC mode instead of SUP (the aerobiome pipeline used HAC; this study requires SUP)
- Recommending Guppy instead of Dorado v5.0.0 (Guppy was deprecated by the time of this study)
- Applying a single QC threshold to all tracks instead of track-specific filtering
- Not performing demultiplexing as part of Dorado (recommending separate demux tools)
- Setting minimum read length too high for environmental water samples
- Omitting Porechop and relying solely on Dorado's built-in adapter trimming
- Using Illumina-appropriate quality thresholds (Q20-Q30)

## Notes

This step differs from the aerobiome pipeline in three key ways: (1) SUP mode replaces HAC, (2) Dorado v5.0.0 replaces Guppy/Dorado v4.3.0, and (3) track-specific QC thresholds replace a single threshold. Later stages inherit the output and parameter choices made here. Each sample was assigned two barcodes per sequencing run; reads from both barcodes are combined during downstream analysis.
