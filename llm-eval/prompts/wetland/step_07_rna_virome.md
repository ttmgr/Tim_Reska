# Step 7: RNA Virome Assembly and Classification

## Metadata

- **Step Number:** 7
- **Step Name:** RNA virome assembly and classification
- **Objective:** Assemble and classify RNA viral sequences from the RNA virome data to characterize the virome composition of wetland water samples
- **Context Provided:** This is a completely separate analysis track (Track 2) processing RNA, not DNA; reads were generated from RNA extracts via the Rapid SMART-9N protocol with random priming; sequenced with SQK-RPB114.24 on R10.4.1 flow cells; filtered FASTQ from Step 1 (virome track, Q >= 9 / >= 100 bp)
- **Constraints:** Must use nanoMDBG for assembly (not metaFlye), Medaka only for polishing (no Racon), DIAMOND BLASTx against NCBI NR protein database with viral taxid 10239 filter at >= 80% identity

## Provenance Note

The prompt text below is a reconstruction derived from the preserved metadata, the wetland reference pipeline, and scored notes. It is not a verbatim export of the original chat prompt.

## Prompt Text

> Write the RNA virome analysis track for a wetland surveillance workflow. RNA was extracted from environmental water samples and converted to cDNA via the Rapid SMART-9N protocol with random priming and template-switching for PCR barcoding. The data was sequenced on ONT MinION with R10.4.1 flow cells using the SQK-RPB114.24 kit. Describe the assembly, polishing, and classification workflow for identifying viral contigs. Use a protein-level classification approach against a comprehensive reference database rather than nucleotide-level k-mer classification, and apply appropriate filters to identify viral sequences.

## Benchmark-Critical Constraints

- Assembly uses nanoMDBG v1.1 (not metaFlye), because it is well-suited for the shorter, more variable reads typical of virome sequencing.
- Polishing uses Medaka v1.7.2 only (no Racon), consistent with the nanoMDBG polishing strategy from Step 4.
- Classification uses DIAMOND BLASTx v2.1.13 at the protein level against the NCBI non-redundant protein database (NR).
- Viral contigs are identified by filtering for kingdom "Viruses" (NCBI taxid: 10239) at >= 80% identity.
- This is a separate track processing RNA-derived cDNA, not DNA shotgun reads.

## Expected Ground Truth Response

**Tools:**
1. nanoMDBG v1.1 (assembly)
2. Medaka v1.7.2 (polishing)
3. DIAMOND BLASTx v2.1.13 (classification)

**Critical parameters:**
- Assembly: nanoMDBG (not metaFlye)
- Polishing: Medaka only (no Racon)
- Reference database: NCBI NR (non-redundant protein, accessed May 2025)
- Viral filter: NCBI taxid 10239 (kingdom Viruses)
- Identity threshold: >= 80%
- DIAMOND output format must include staxids for taxonomic filtering

**Output format:** Polished viral contig FASTA + DIAMOND classification tables with taxonomic annotations

**Acceptable alternatives:**
- BLASTx against NCBI NR (functionally equivalent but slower)
- metaFlye as an alternative assembler (scientifically defensible but not the validated choice for virome data)
- A lower identity threshold with manual curation is defensible for divergent viruses

## Known Failure Modes Observed

- Using metaFlye instead of nanoMDBG for virome assembly
- Using BLAST against nucleotide databases instead of DIAMOND BLASTx against NR (protein-level)
- Not applying the viral taxid filter (10239)
- Not specifying the identity threshold (>= 80%)
- Applying DNA-appropriate tools to RNA virome data
- Recommending Kraken2 for virome classification (k-mer approaches are less sensitive for divergent viral sequences)
- Not understanding that this is a separate track processing RNA, not DNA

## Notes

This is a completely separate analysis track from the shotgun metagenomics pipeline. The study detected viruses from mammals, birds, fish, insects, and plants across the wetland sites. The choice of nanoMDBG over metaFlye for virome assembly and DIAMOND BLASTx over Kraken2 for classification reflects the specialized requirements of RNA virome analysis, where divergent viral sequences benefit from protein-level rather than nucleotide-level comparison.
