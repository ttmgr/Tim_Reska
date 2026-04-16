# Sonnet 3.5

- Family: Claude
- Steps scored: 10
- Average composite score: 0.32
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling qc | 0.60 | A | P | P | Q | M | Dorado but wrong mode; ignored track-specific QC |
| 2. taxonomic classification | 0.80 | C | P | P | Q | R | Kraken2 but PlusPF database; no normalization |
| 3. metagenomic assembly | 0.20 | A | I | F | Q | N | MetaFlye but wrong flags; no --meta; no dual assembler |
| 4. polishing annotation | 0.20 | A | I | F | Q | N | Medaka only; wrong polishing strategy; no Prokka |
| 5. pathogen identification | 0.10 | I | I | F | Q | N | No pathogen identification pipeline; used Kraken2 only |
| 6. amr virulence plasmid | 0.10 | I | I | F | Q | N | Prokka only; no AMR tools; no virulence screening |
| 7. rna virome | 0.00 | I | I | F | I | N | Applied DNA tools to RNA virome data |
| 8. edna metabarcoding | 0.00 | I | I | F | I | N | Shotgun metagenomics tools for amplicons |
| 9. aiv consensus | 0.60 | A | P | P | Q | M | minimap2 correct but incomplete workflow |
| 10. aiv phylogenetics | 0.60 | A | P | P | Q | M | Basic MAFFT + tree; wrong parameters |
