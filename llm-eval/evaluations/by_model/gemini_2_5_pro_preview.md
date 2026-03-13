# Gemini 2.5 Pro Preview

- Family: Gemini
- Steps scored: 7
- Average composite score: 0.89
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling | 0.90 | C | P | P | S | R | Dorado correct; Chopper instead of Porechop+NanoFilt |
| 2. quality control | 1.00 | C | C | P | S | R | NanoPlot correct |
| 3. host depletion | 1.00 | C | C | P | S | R | minimap2 correct |
| 4. taxonomic classification | 1.00 | C | C | P | S | R | Kraken2 + nt correct |
| 5. assembly | 0.80 | C | P | P | S | M | MetaFlye + Medaka (acceptable); 1 round only |
| 6. binning | 0.80 | C | P | P | Q | R | metaWRAP + CheckM; 50% completeness |
| 7. functional annotation | 0.70 | A | P | P | Q | R | AMRFinderPlus on contigs only; missed ABRicate |
