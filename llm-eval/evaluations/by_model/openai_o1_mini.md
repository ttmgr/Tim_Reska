# o1-mini

- Family: OpenAI
- Steps scored: 7
- Average composite score: 0.14
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling | 0.00 | I | I | F | I | N | Recommended Albacore (discontinued); completely wrong pipeline order |
| 2. quality control | 0.70 | A | P | P | Q | R | FastQC only; ignored nanopore-specific metrics |
| 3. host depletion | 0.00 | I | I | F | I | N | BWA-MEM (short-read aligner); wrong flags throughout |
| 4. taxonomic classification | 0.20 | A | I | F | Q | N | Kraken2 with wrong confidence threshold and wrong database |
| 5. assembly | 0.00 | I | I | F | I | N | MEGAHIT (short-read assembler); ignored long-read input entirely |
| 6. binning | 0.00 | I | I | F | I | N | MaxBin2 alone with wrong input format; no quality assessment at all |
| 7. functional annotation | 0.10 | I | I | F | Q | N | Prokka with wrong flags; no AMR tools; wrong pipeline order |
