# Gemini 2.5 Pro

- Family: Gemini
- Steps scored: 7
- Average composite score: 0.96
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling | 1.00 | C | C | P | S | R | Dorado + Porechop + NanoFilt correct |
| 2. quality control | 1.00 | C | C | P | S | R | NanoPlot comprehensive |
| 3. host depletion | 1.00 | C | C | P | S | R | minimap2; noted environmental context |
| 4. taxonomic classification | 1.00 | C | C | P | S | R | Kraken2 + nt; downsampling mentioned |
| 5. assembly | 1.00 | C | C | P | S | R | MetaFlye + 3x Racon correct |
| 6. binning | 0.90 | C | P | P | S | R | metaWRAP + CheckM; 50% completeness |
| 7. functional annotation | 0.80 | C | P | P | Q | R | AMRFinderPlus + ABRicate; contigs and bins only |
