# Gemini 3 Flash

- Family: Gemini
- Steps scored: 7
- Average composite score: 0.71
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling | 0.60 | A | P | P | Q | M | Dorado + Chopper but wrong flags; wrong quality threshold |
| 2. quality control | 1.00 | C | C | P | S | R | NanoPlot correct |
| 3. host depletion | 0.80 | C | P | P | Q | R | minimap2 correct but ignored air sample context |
| 4. taxonomic classification | 0.90 | C | P | P | S | R | Kraken2 + nt but wrong report flag |
| 5. assembly | 0.70 | C | P | P | Q | M | MetaFlye + 2x Racon; wrong read flag |
| 6. binning | 0.40 | A | P | F | Q | M | metaWRAP + CheckM but 60% completeness; wrong binning order |
| 7. functional annotation | 0.60 | A | P | P | Q | M | AMRFinderPlus + ABRicate; missed read-level; wrong flags |
