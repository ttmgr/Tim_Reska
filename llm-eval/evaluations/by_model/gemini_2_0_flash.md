# Gemini 2.0 Flash

- Family: Gemini
- Steps scored: 7
- Average composite score: 0.04
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling | 0.00 | I | I | F | I | N | Guppy with completely wrong config; Illumina params; wrong pipeline order |
| 2. quality control | 0.10 | I | I | F | Q | N | FastQC only; ignored nanopore context entirely; wrong flags |
| 3. host depletion | 0.00 | I | I | F | I | N | BWA-MEM (wrong tool); wrong flags; wrong pipeline order |
| 4. taxonomic classification | 0.20 | A | I | F | Q | N | Kraken2 but Standard database; wrong flags; no report format |
| 5. assembly | 0.00 | I | I | F | I | N | SPAdes meta mode (wrong tool); no polishing; ignored input details |
| 6. binning | 0.00 | I | I | F | I | N | MetaBAT2 with wrong input format; no quality check; wrong order |
| 7. functional annotation | 0.00 | I | I | F | I | N | Prokka only with wrong flags; no AMR tools; wrong pipeline order |
