# Gemini 2.5 Flash

- Family: Gemini
- Steps scored: 7
- Average composite score: 0.53
- Fully correct end-to-end pipeline: No

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling | 0.60 | A | P | P | Q | M | Dorado correct but Chopper with wrong flags; wrong length filter |
| 2. quality control | 0.90 | C | P | P | S | R | NanoPlot correct but incomplete flags |
| 3. host depletion | 0.60 | A | P | P | Q | M | minimap2 but wrong preset; ignored sample context |
| 4. taxonomic classification | 0.80 | C | P | P | Q | R | Kraken2 + nt but wrong report flags |
| 5. assembly | 0.40 | A | P | F | Q | M | MetaFlye but wrong read flag; only 1 round Racon; ignored input |
| 6. binning | 0.20 | A | I | F | Q | N | metaWRAP but wrong flags throughout; 70% completeness; wrong order |
| 7. functional annotation | 0.20 | A | I | F | Q | N | AMRFinderPlus contigs only; wrong flags; ignored multi-level input |
