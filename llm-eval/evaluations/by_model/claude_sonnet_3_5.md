# Sonnet 3.5

- Family: Claude
- Steps scored: 7
- Average composite score: 0.29
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling | 0.00 | I | I | F | I | N | Guppy with completely wrong config; ignored R10.4.1 input; wrong pipeline order |
| 2. quality control | 0.70 | A | P | P | Q | R | FastQC as primary (wrong tool for nanopore) |
| 3. host depletion | 0.20 | A | I | F | Q | N | minimap2 but with wrong preset and wrong flags |
| 4. taxonomic classification | 0.80 | C | P | P | Q | R | Kraken2 but PlusPF database; wrong report flags |
| 5. assembly | 0.20 | A | I | F | Q | N | MetaFlye but Medaka polishing with wrong flags; no --meta flag |
| 6. binning | 0.00 | I | I | F | I | N | MetaBAT2 with wrong input; 90% completeness; no quality assessment |
| 7. functional annotation | 0.10 | I | I | F | Q | N | Prokka only with wrong flags; no AMR tools; ignored multi-level |
