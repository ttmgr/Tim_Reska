# Gemini 3 Pro

- Family: Gemini
- Steps scored: 7
- Average composite score: 1.00
- Fully correct end-to-end pipeline: Yes

## Step-Level Results

| Step | Composite | Tool | Params | Output | Science | Exec | Notes |
|:-----|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| 1. basecalling | 1.00 | C | C | P | S | R | Dorado + Porechop + NanoFilt; fully correct |
| 2. quality control | 1.00 | C | C | P | S | R | NanoPlot + NanoStat |
| 3. host depletion | 1.00 | C | C | P | S | R | minimap2; excellent sample context awareness |
| 4. taxonomic classification | 1.00 | C | C | P | S | R | Kraken2 + nt; DIAMOND alternative mentioned |
| 5. assembly | 1.00 | C | C | P | S | R | MetaFlye + 3x Racon; pooling noted |
| 6. binning | 1.00 | C | C | P | S | R | metaWRAP + CheckM; 30% completeness for low-biomass |
| 7. functional annotation | 1.00 | C | C | P | S | R | AMRFinderPlus + ABRicate + seqkit; all three levels |
