# Gemini 2.0 Flash

- Family: Gemini
- Steps scored: 10
- Average composite score: 0.03
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling qc | 0.00 | I | I | F | I | N | Wrong basecaller; Illumina parameters; wrong pipeline order |
| 2. taxonomic classification | 0.20 | A | I | F | Q | N | Kraken2 but Standard database; wrong flags; no normalization |
| 3. metagenomic assembly | 0.00 | I | I | F | I | N | Short-read assembler; no long-read or meta mode |
| 4. polishing annotation | 0.00 | I | I | F | I | N | No polishing; wrong annotation approach entirely |
| 5. pathogen identification | 0.00 | I | I | F | I | N | No pathogen identification logic |
| 6. amr virulence plasmid | 0.00 | I | I | F | I | N | Wrong tools; no AMR pipeline |
| 7. rna virome | 0.00 | I | I | F | I | N | Completely wrong approach for RNA virome |
| 8. edna metabarcoding | 0.00 | I | I | F | I | N | Shotgun tools for amplicons; no metabarcoding awareness |
| 9. aiv consensus | 0.00 | I | I | F | I | N | Wrong analysis approach |
| 10. aiv phylogenetics | 0.10 | I | I | F | Q | N | No phylogenetic analysis; wrong tools |
