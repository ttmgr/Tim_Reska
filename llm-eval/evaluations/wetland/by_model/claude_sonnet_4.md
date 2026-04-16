# Sonnet 4

- Family: Claude
- Steps scored: 10
- Average composite score: 0.55
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling qc | 0.60 | A | P | P | Q | M | Dorado + Porechop correct; wrong NanoFilt threshold; no track split |
| 2. taxonomic classification | 0.90 | C | P | P | S | R | Kraken2 + nt; wrong confidence flag; no normalization |
| 3. metagenomic assembly | 0.70 | A | P | P | Q | R | MetaFlye alone; acceptable; correct read type flag |
| 4. polishing annotation | 0.40 | A | P | F | Q | M | Racon polishing but wrong rounds; not assembler-specific |
| 5. pathogen identification | 0.60 | A | P | P | Q | M | Kraken2-based taxonomy; no MEGAN LCA |
| 6. amr virulence plasmid | 0.60 | A | P | P | Q | M | AMRFinderPlus on contigs; no --plus; no Prodigal |
| 7. rna virome | 0.40 | A | P | F | Q | M | Wrong assembly tool for virome; nucleotide classification |
| 8. edna metabarcoding | 0.10 | I | I | F | Q | N | Shotgun tools for amplicons; no OBITools4 |
| 9. aiv consensus | 0.60 | A | P | P | Q | M | minimap2 but single-pass |
| 10. aiv phylogenetics | 0.60 | A | P | P | Q | M | MAFFT + tree; partially correct |
