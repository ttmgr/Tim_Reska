# Haiku 4.5

- Family: Claude
- Steps scored: 7
- Average composite score: 0.89
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling | 0.90 | C | P | P | S | R | Dorado correct; used Chopper; Q10 threshold |
| 2. quality control | 1.00 | C | C | P | S | R | NanoPlot correct |
| 3. host depletion | 1.00 | C | C | P | S | R | minimap2 correct |
| 4. taxonomic classification | 1.00 | C | C | P | S | R | Kraken2 + nt |
| 5. assembly | 0.80 | C | P | P | S | M | MetaFlye + 2 rounds Racon |
| 6. binning | 0.70 | A | P | P | Q | R | MetaBAT2 + SemiBin2; CheckM2; 50% completeness |
| 7. functional annotation | 0.80 | C | P | P | Q | R | AMRFinderPlus + ABRicate; contigs only |
