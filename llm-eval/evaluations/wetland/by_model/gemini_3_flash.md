# Gemini 3 Flash

- Family: Gemini
- Steps scored: 10
- Average composite score: 0.54
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling qc | 0.60 | A | P | P | Q | M | Dorado + Chopper; wrong quality threshold; no track split |
| 2. taxonomic classification | 0.90 | C | P | P | S | R | Kraken2 + nt; wrong report flag |
| 3. metagenomic assembly | 0.70 | A | P | P | Q | R | MetaFlye alone; wrong read flag |
| 4. polishing annotation | 0.40 | A | P | F | Q | M | 2x Racon; not assembler-specific |
| 5. pathogen identification | 0.60 | A | P | P | Q | M | Kraken2-based; no MEGAN |
| 6. amr virulence plasmid | 0.60 | A | P | P | Q | M | AMRFinderPlus; missed read-level; wrong flags |
| 7. rna virome | 0.40 | A | P | F | Q | M | Wrong virome assembly approach |
| 8. edna metabarcoding | 0.00 | I | I | F | I | N | No metabarcoding tools |
| 9. aiv consensus | 0.60 | A | P | P | Q | M | minimap2 but incomplete workflow |
| 10. aiv phylogenetics | 0.60 | A | P | P | Q | M | Basic phylogenetics; incomplete parameters |
