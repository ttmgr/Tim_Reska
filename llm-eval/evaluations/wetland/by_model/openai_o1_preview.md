# o1-preview

- Family: OpenAI
- Steps scored: 10
- Average composite score: 0.41
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling qc | 0.60 | A | P | P | Q | M | Dorado acceptable but wrong mode; single QC threshold |
| 2. taxonomic classification | 0.80 | C | P | P | Q | R | Kraken2 with Standard database instead of nt_core; no normalization |
| 3. metagenomic assembly | 0.20 | A | I | F | Q | N | MetaFlye correct but no nanoMDBG; wrong read type flag |
| 4. polishing annotation | 0.30 | A | P | F | Q | N | Medaka polishing but not assembler-specific; no Prokka |
| 5. pathogen identification | 0.20 | A | I | F | Q | N | Kraken2 alone; no MEGAN LCA; no pathogen list |
| 6. amr virulence plasmid | 0.50 | A | I | P | Q | M | AMRFinderPlus without --plus; no Prodigal; no PlasmidFinder |
| 7. rna virome | 0.30 | A | P | F | Q | N | Used metaFlye for virome; wrong classification approach |
| 8. edna metabarcoding | 0.00 | I | I | F | I | N | Shotgun metagenomics tools for amplicon data |
| 9. aiv consensus | 0.60 | A | P | P | Q | M | minimap2 correct but single-pass; incomplete consensus workflow |
| 10. aiv phylogenetics | 0.60 | A | P | P | Q | M | MAFFT + basic tree but wrong model selection; no bootstrapping |
