# Haiku 4.5

- Family: Claude
- Steps scored: 10
- Average composite score: 0.68
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling qc | 0.90 | C | P | P | S | R | Dorado SUP correct; Chopper acceptable; Q10 threshold |
| 2. taxonomic classification | 1.00 | C | C | P | S | R | Kraken2 + nt correct |
| 3. metagenomic assembly | 0.70 | A | P | P | Q | R | MetaFlye alone; correct basic setup |
| 4. polishing annotation | 0.70 | A | P | P | Q | R | 2 rounds Racon; not assembler-specific |
| 5. pathogen identification | 0.70 | A | P | P | Q | R | Kraken2-based; no MEGAN LCA |
| 6. amr virulence plasmid | 0.70 | A | P | P | Q | R | AMRFinderPlus; CheckM2; missing components |
| 7. rna virome | 0.40 | A | P | F | Q | M | Wrong virome assembly approach |
| 8. edna metabarcoding | 0.10 | I | I | F | Q | N | No eDNA metabarcoding tools |
| 9. aiv consensus | 0.90 | C | P | P | S | R | minimap2 + SAMtools + BCFtools |
| 10. aiv phylogenetics | 0.70 | A | P | P | Q | R | MAFFT + tree; acceptable approach |
