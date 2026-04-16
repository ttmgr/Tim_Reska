# Gemini 3.1 Pro

- Family: Gemini
- Steps scored: 10
- Average composite score: 0.88
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling qc | 1.00 | C | C | P | S | R | Dorado SUP + Porechop + NanoFilt; track-specific QC |
| 2. taxonomic classification | 1.00 | C | C | P | S | R | Kraken2 + nt_core; comprehensive |
| 3. metagenomic assembly | 0.90 | A | C | P | S | R | MetaFlye excellent; acknowledged complementary assemblers |
| 4. polishing annotation | 0.90 | C | P | P | S | R | Assembler-aware polishing; Prokka |
| 5. pathogen identification | 0.80 | A | P | P | S | R | Alignment-based pathogen ID; LCA logic |
| 6. amr virulence plasmid | 0.90 | C | P | P | S | R | AMRFinderPlus --plus + Prodigal; noted VFDB |
| 7. rna virome | 0.80 | A | P | P | S | R | Virome with DIAMOND NR; correct concept |
| 8. edna metabarcoding | 0.50 | A | P | F | Q | R | Good amplicon awareness; VSEARCH; missed OBITools4 |
| 9. aiv consensus | 1.00 | C | C | P | S | R | Complete AIV consensus |
| 10. aiv phylogenetics | 1.00 | C | C | P | S | R | MAFFT + IQ-TREE2 with MFP; dual bootstrapping |
