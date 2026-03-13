# o1

- Family: OpenAI
- Steps scored: 7
- Average composite score: 0.67
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling | 0.60 | A | P | P | Q | M | Dorado correct but wrong model name; missed Porechop step; Q15 threshold |
| 2. quality control | 1.00 | C | C | P | S | R | NanoPlot recommended correctly |
| 3. host depletion | 0.80 | C | P | P | Q | R | minimap2 correct but wrong preset flag |
| 4. taxonomic classification | 0.90 | C | P | P | S | R | Kraken2 with nt database; missed report format flag |
| 5. assembly | 0.40 | A | P | F | Q | M | MetaFlye correct but only 1 round polish with Medaka; wrong read type flag |
| 6. binning | 0.40 | A | P | F | Q | M | metaWRAP but 50% completeness threshold; wrong flag order; no coverage step |
| 7. functional annotation | 0.60 | A | P | P | Q | M | AMRFinderPlus on contigs only; missed read-level; wrong flags |
