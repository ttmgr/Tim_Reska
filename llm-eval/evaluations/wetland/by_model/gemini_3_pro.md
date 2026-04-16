# Gemini 3 Pro

- Family: Gemini
- Steps scored: 10
- Average composite score: 0.86
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling qc | 1.00 | C | C | P | S | R | Dorado SUP + Porechop + NanoFilt; track-specific QC |
| 2. taxonomic classification | 1.00 | C | C | P | S | R | Kraken2 + nt_core; DIAMOND alternative mentioned |
| 3. metagenomic assembly | 0.90 | A | C | P | S | R | MetaFlye excellent; noted alternatives but not nanoMDBG |
| 4. polishing annotation | 0.90 | C | P | P | S | R | Good polishing strategy; Prokka annotation |
| 5. pathogen identification | 0.80 | A | P | P | S | R | Alignment-based pathogen ID; LCA approach discussed |
| 6. amr virulence plasmid | 0.90 | C | P | P | S | R | AMRFinderPlus --plus + Prodigal; missed PlasmidFinder |
| 7. rna virome | 0.80 | A | P | P | S | R | Virome assembly; correct DIAMOND NR classification |
| 8. edna metabarcoding | 0.40 | A | P | F | Q | M | Knew amplicon paradigm; VSEARCH; missed OBITools4/MIDORI2 |
| 9. aiv consensus | 1.00 | C | C | P | S | R | Complete reference-based consensus |
| 10. aiv phylogenetics | 0.90 | C | P | P | S | R | MAFFT + IQ-TREE2; mostly correct parameters |
