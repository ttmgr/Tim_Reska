# GLM-5

- Family: Zhipu
- Steps scored: 10
- Average composite score: 0.28
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling qc | 0.70 | C | P | P | Q | M | Dorado correct; minor flag issues |
| 2. taxonomic classification | 0.90 | C | P | P | S | R | Kraken2 + nt reasonable |
| 3. metagenomic assembly | 0.00 | I | I | F | I | N | Failed assembly; wrong tool/flags |
| 4. polishing annotation | 0.00 | I | I | F | I | N | No polishing; wrong approach |
| 5. pathogen identification | 0.00 | I | I | F | I | N | No pathogen identification |
| 6. amr virulence plasmid | 0.60 | A | P | P | Q | M | Some AMR tools; incomplete |
| 7. rna virome | 0.00 | I | I | F | I | N | Wrong virome approach |
| 8. edna metabarcoding | 0.00 | I | I | F | I | N | No metabarcoding tools |
| 9. aiv consensus | 0.60 | A | P | P | Q | M | minimap2 reasonable |
| 10. aiv phylogenetics | 0.00 | I | I | F | I | N | No phylogenetic analysis |
