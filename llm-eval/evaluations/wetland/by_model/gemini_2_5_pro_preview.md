# Gemini 2.5 Pro Preview

- Family: Gemini
- Steps scored: 10
- Average composite score: 0.68
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling qc | 0.90 | C | P | P | S | R | Dorado correct; Chopper acceptable; missed track-specific QC |
| 2. taxonomic classification | 1.00 | C | C | P | S | R | Kraken2 + nt correct |
| 3. metagenomic assembly | 0.70 | A | P | P | Q | R | MetaFlye alone; acceptable setup |
| 4. polishing annotation | 0.70 | A | P | P | Q | R | Medaka polishing; 1 round only; no Prokka |
| 5. pathogen identification | 0.70 | A | P | P | Q | R | Kraken2-based; no MEGAN |
| 6. amr virulence plasmid | 0.70 | A | P | P | Q | R | AMRFinderPlus; missing components |
| 7. rna virome | 0.40 | A | P | F | Q | M | Wrong assembly for virome; partial classification |
| 8. edna metabarcoding | 0.10 | I | I | F | Q | N | No eDNA metabarcoding tools |
| 9. aiv consensus | 0.90 | C | P | P | S | R | minimap2 + BCFtools reasonable |
| 10. aiv phylogenetics | 0.70 | A | P | P | Q | R | MAFFT + IQ-TREE2; partially correct |
