# o3-mini

- Family: OpenAI
- Steps scored: 10
- Average composite score: 0.52
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling qc | 0.60 | A | P | P | Q | M | Dorado correct but wrong mode; Chopper instead of Porechop+NanoFilt |
| 2. taxonomic classification | 0.80 | C | P | P | Q | R | Kraken2 + nt; wrong report flags; no normalization |
| 3. metagenomic assembly | 0.70 | A | P | P | Q | R | MetaFlye alone; acceptable |
| 4. polishing annotation | 0.40 | A | P | F | Q | M | Single polishing approach; no annotation |
| 5. pathogen identification | 0.50 | A | I | P | Q | M | Kraken2 only; no MEGAN; no pathogen list |
| 6. amr virulence plasmid | 0.60 | A | P | P | Q | M | AMRFinderPlus on contigs only; no --plus; no Prodigal |
| 7. rna virome | 0.40 | A | P | F | Q | M | Wrong assembly tool for virome |
| 8. edna metabarcoding | 0.00 | I | I | F | I | N | Shotgun tools for amplicons |
| 9. aiv consensus | 0.60 | A | P | P | Q | M | minimap2 but incomplete workflow |
| 10. aiv phylogenetics | 0.60 | A | P | P | Q | M | Basic phylogenetics; wrong parameters |
