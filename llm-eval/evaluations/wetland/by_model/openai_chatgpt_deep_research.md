# ChatGPT Deep Research

- Family: OpenAI
- Steps scored: 10
- Average composite score: 0.94
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling qc | 1.00 | C | C | P | S | R | Dorado SUP correct; track-specific QC from publication search |
| 2. taxonomic classification | 1.00 | C | C | P | S | R | Kraken2 + nt_core; SeqKit normalization |
| 3. metagenomic assembly | 1.00 | C | C | P | S | R | Found dual assembler strategy through research; metaFlye + nanoMDBG |
| 4. polishing annotation | 1.00 | C | C | P | S | R | Assembler-specific polishing from publication details |
| 5. pathogen identification | 0.90 | C | P | P | S | R | Found MEGAN-CE LCA approach; missed exact threshold |
| 6. amr virulence plasmid | 1.00 | C | C | P | S | R | AMRFinderPlus --plus + Prodigal + VFDB + PlasmidFinder |
| 7. rna virome | 0.80 | A | P | P | S | R | nanoMDBG for virome found via search; correct classification approach |
| 8. edna metabarcoding | 0.70 | A | P | P | Q | R | Found eDNA metabarcoding tools through research; partial OBITools4 knowledge |
| 9. aiv consensus | 1.00 | C | C | P | S | R | Complete reference-based AIV consensus workflow |
| 10. aiv phylogenetics | 1.00 | C | C | P | S | R | MAFFT + IQ-TREE2 with MFP; both bootstrap metrics |
