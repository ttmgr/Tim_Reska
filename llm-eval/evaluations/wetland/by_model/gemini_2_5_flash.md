# Gemini 2.5 Flash

- Family: Gemini
- Steps scored: 10
- Average composite score: 0.41
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling qc | 0.60 | A | P | P | Q | M | Dorado correct; Chopper with wrong flags; wrong thresholds |
| 2. taxonomic classification | 0.80 | C | P | P | Q | R | Kraken2 + nt but wrong report flags |
| 3. metagenomic assembly | 0.40 | A | P | F | Q | M | MetaFlye but wrong read flag; no dual assembler |
| 4. polishing annotation | 0.40 | A | P | F | Q | M | Racon but wrong rounds; not assembler-specific |
| 5. pathogen identification | 0.20 | A | I | F | Q | N | Wrong pathogen ID approach; wrong flags |
| 6. amr virulence plasmid | 0.20 | A | I | F | Q | N | AMRFinderPlus contigs only; wrong flags |
| 7. rna virome | 0.30 | A | P | F | Q | N | Wrong virome approach; broken output |
| 8. edna metabarcoding | 0.00 | I | I | F | I | N | No metabarcoding awareness |
| 9. aiv consensus | 0.60 | A | P | P | Q | M | minimap2 but incomplete |
| 10. aiv phylogenetics | 0.60 | A | P | P | Q | M | Basic tree; wrong parameters |
