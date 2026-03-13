# GLM-5

- Family: Zhipu
- Steps scored: 7
- Average composite score: 0.59
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling | 0.70 | C | P | P | Q | M | Dorado correct; minor flag issues |
| 2. quality control | 1.00 | C | C | P | S | R | NanoPlot correct |
| 3. host depletion | 0.80 | C | P | P | Q | R | minimap2 correct |
| 4. taxonomic classification | 0.90 | C | P | P | S | R | Kraken2 + nt |
| 5. assembly | 0.00 | I | I | F | I | N | Failed assembly completely; wrong tool/flags |
| 6. binning | 0.70 | C | P | P | Q | M | metaWRAP + CheckM; acceptable |
| 7. functional annotation | 0.00 | I | I | F | I | N | Failed resistance annotation and virulence screening |
