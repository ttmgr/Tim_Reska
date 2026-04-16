# Claude Deep Research

- Family: Claude
- Steps scored: 10
- Average composite score: 0.94
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling qc | 1.00 | C | C | P | S | R | Dorado SUP correct; track-specific QC from research |
| 2. taxonomic classification | 1.00 | C | C | P | S | R | Kraken2 + nt_core; SeqKit normalization |
| 3. metagenomic assembly | 1.00 | C | C | P | S | R | Found dual assembler strategy; metaFlye + nanoMDBG |
| 4. polishing annotation | 1.00 | C | C | P | S | R | Assembler-specific polishing from research |
| 5. pathogen identification | 0.90 | C | P | P | S | R | Found MEGAN-CE LCA through research |
| 6. amr virulence plasmid | 1.00 | C | C | P | S | R | Complete AMR + virulence + plasmid pipeline |
| 7. rna virome | 0.80 | A | P | P | S | R | nanoMDBG for virome; DIAMOND NR classification |
| 8. edna metabarcoding | 0.70 | A | P | P | Q | R | Found eDNA metabarcoding tools through search; partial pipeline |
| 9. aiv consensus | 1.00 | C | C | P | S | R | Complete AIV consensus workflow |
| 10. aiv phylogenetics | 1.00 | C | C | P | S | R | MAFFT + IQ-TREE2 with MFP and dual bootstrapping |
