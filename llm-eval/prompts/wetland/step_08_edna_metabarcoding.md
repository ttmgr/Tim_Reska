# Step 8: eDNA Vertebrate Metabarcoding

## Metadata

- **Step Number:** 8
- **Step Name:** eDNA vertebrate metabarcoding (12S rRNA)
- **Objective:** Identify vertebrate species present in the wetland environment using environmental DNA metabarcoding of the mitochondrial 12S rRNA gene
- **Context Provided:** This is Track 3, a fundamentally different analytical paradigm using amplicon-based OTU clustering rather than shotgun metagenomics; basecalled 12S rRNA amplicon reads from DNA extract sequenced with SQK-LSK114 on R10.4.1 flow cells; the 12SV05 primer set targeting the ~97 bp V5 region of 12S rRNA; custom 9 bp symmetrical tags for demultiplexing; a human-blocking oligonucleotide was used during PCR
- **Constraints:** Must use OBITools4 for demultiplexing (not Dorado), Cutadapt for primer removal, VSEARCH for QC/clustering/chimera removal, and MIDORI2 12S rRNA database for taxonomy; must apply maxEE 1.0, 97% OTU clustering, >= 98% identity, >= 80% coverage, >= 5 reads thresholds, and eBird biogeographic validation

## Provenance Note

The prompt text below is a reconstruction derived from the preserved metadata, the wetland reference pipeline, and scored notes. It is not a verbatim export of the original chat prompt.

## Prompt Text

> Write the eDNA metabarcoding analysis track for a wetland surveillance workflow. DNA was extracted from environmental water samples and the mitochondrial 12S rRNA V5 region (~97 bp) was PCR-amplified using the 12SV05 primer set with custom 9 bp symmetrical tags. A human-blocking oligonucleotide was included in PCR. The amplicons were sequenced on ONT MinION with R10.4.1 flow cells using the SQK-LSK114 ligation kit. Describe the full amplicon analysis pipeline: demultiplexing by tag (not ONT barcode), primer removal, quality filtering, dereplication, chimera removal, OTU clustering, and taxonomic assignment against a curated 12S rRNA database. Focus the final output on avian species detection with biogeographic validation.

## Benchmark-Critical Constraints

- Demultiplexing uses OBITools4 v1.3.1 obimultiplex (not Dorado), because the amplicons use custom 9 bp tags appended to primers, not ONT barcodes. Tag matching allows <= 2 mismatches.
- Primer removal uses Cutadapt v4.2 with the 12SV05 primer sequences.
- Quality filtering uses VSEARCH v2.21 with maxEE 1.0.
- Dereplication discards singletons (minuniquesize 2).
- Chimera removal uses VSEARCH uchime_denovo.
- OTU clustering at 97% similarity.
- Taxonomy assignment uses global alignment against MIDORI2 12S rRNA database (version "Unique 266").
- Final assignments are filtered to the Aves class only, with >= 80% alignment coverage, >= 98% identity, and >= 5 reads per OTU.
- Biogeographically implausible species are validated against eBird regional occurrence data and collapsed to a higher rank or removed.

## Expected Ground Truth Response

**Tools:**
1. OBITools4 v1.3.1 (demultiplexing by 9 bp tags)
2. Cutadapt v4.2 (primer removal)
3. VSEARCH v2.21 (quality filtering, dereplication, chimera removal, OTU clustering, taxonomy)

**Critical parameters:**
- OBITools4: 9 bp symmetrical tags, <= 2 mismatches
- Cutadapt: 12SV05 primer sequences
- VSEARCH: maxEE 1.0, minuniquesize 2, uchime_denovo, 97% OTU clustering
- Taxonomy database: MIDORI2 12S rRNA (Unique 266)
- Quality thresholds: >= 80% coverage, >= 98% identity, >= 5 reads per OTU
- Focus: Aves class; eBird biogeographic validation

**Output format:** OTU table with vertebrate species assignments; validated avian species list per site

**Acceptable alternatives:**
- DADA2 adapted for long reads is scientifically defensible but not the validated approach
- BLAST against NCBI nt for 12S assignment is defensible but less curated than MIDORI2
- mothur as an alternative amplicon pipeline framework

## Known Failure Modes Observed

- Treating this as shotgun metagenomics (recommending Kraken2, MetaPhlAn, or other shotgun classifiers)
- Not knowing OBITools4 exists (it is a niche eDNA/metabarcoding tool)
- Recommending DADA2 or other Illumina-focused amplicon tools without considering long-read adaptation
- Not understanding OTU clustering at 97% similarity
- Using BLAST against NCBI nt instead of MIDORI2 for 12S rRNA taxonomy
- Omitting chimera removal
- Not mentioning the expected error filter (maxEE)
- Not knowing the 12SV05 primer set or the V5 region of 12S rRNA
- Treating this as the same pipeline as shotgun metagenomics

## Notes

This track represents a fundamentally different analytical paradigm from the shotgun metagenomics and virome tracks. The entire toolchain (OBITools4, Cutadapt, VSEARCH, MIDORI2) is specific to amplicon-based eDNA metabarcoding and does not overlap with the shotgun tools. Most LLMs perform poorly on this step because eDNA metabarcoding is a niche field with specialized tools that are underrepresented in training data. The human-blocking oligonucleotide (3 uM) suppresses human DNA amplification, which is a practical detail frequently omitted.
