# Step 6: Binning

- Models evaluated: 28
- Fully correct responses: 9/28
- Average composite score: 0.59

## Dominant Non-Correct Labels

- `tool_selection`: A (10x)
- `parameter_accuracy`: P (13x)
- `output_compatibility`: F (13x)
- `scientific_validity`: Q (12x)
- `executability`: N (7x)

## Model-Level Results

| Family | Model | Composite | Tool | Params | Output | Science | Exec | Notes |
|:------|:------|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| OpenAI | GPT-4o | 0.00 | I | I | F | I | N | MetaBAT2 alone with wrong input format; 90% completeness threshold; ignored low-biomass context |
| OpenAI | o1-preview | 0.30 | A | P | F | Q | N | MetaBAT2 alone with wrong flags; 70% completeness; no coverage mapping |
| OpenAI | o1-mini | 0.00 | I | I | F | I | N | MaxBin2 alone with wrong input format; no quality assessment at all |
| OpenAI | o1 | 0.40 | A | P | F | Q | M | metaWRAP but 50% completeness threshold; wrong flag order; no coverage step |
| OpenAI | o1-pro | 0.90 | C | P | P | S | R | metaWRAP + CheckM; used 50% completeness |
| OpenAI | o3-mini | 0.40 | A | P | F | Q | M | metaWRAP but wrong flags; 60% completeness; ignored low-biomass |
| OpenAI | o3 (high reasoning) | 0.70 | A | P | P | Q | R | metaWRAP + CheckM but 50% completeness; ignored low-biomass |
| OpenAI | o4-mini | 0.40 | A | P | F | Q | M | metaWRAP + CheckM but 60% completeness; wrong pipeline order for binning |
| OpenAI | GPT-5 | 1.00 | C | C | P | S | R | metaWRAP + CheckM; 30% completeness for low-biomass |
| OpenAI | ChatGPT Deep Research | 1.00 | C | C | P | S | R | metaWRAP + CheckM; 30% completeness |
| Claude | Sonnet 3.5 | 0.00 | I | I | F | I | N | MetaBAT2 with wrong input; 90% completeness; no quality assessment |
| Claude | Sonnet 4 | 0.40 | A | P | F | Q | M | metaWRAP + CheckM but 70% completeness; wrong flag order |
| Claude | Sonnet 4.5 | 0.40 | A | P | F | Q | M | metaWRAP + CheckM but 50% completeness; wrong flag syntax |
| Claude | Haiku 4.5 | 0.70 | A | P | P | Q | R | MetaBAT2 + SemiBin2; CheckM2; 50% completeness |
| Claude | Opus 4.5 | 1.00 | C | C | P | S | R | metaWRAP ensemble + CheckM; 30% completeness |
| Claude | Opus 4.6 | 1.00 | C | C | P | S | R | metaWRAP + CheckM; 30% completeness |
| Claude | Sonnet 4.6 | 1.00 | C | C | P | S | R | metaWRAP + CheckM; 30% completeness |
| Claude | Claude Deep Research | 1.00 | C | C | P | S | R | metaWRAP + CheckM; 30% completeness |
| Gemini | Gemini 2.0 Flash | 0.00 | I | I | F | I | N | MetaBAT2 with wrong input format; no quality check; wrong order |
| Gemini | Gemini 2.5 Pro Preview | 0.80 | C | P | P | Q | R | metaWRAP + CheckM; 50% completeness |
| Gemini | Gemini 2.5 Flash | 0.20 | A | I | F | Q | N | metaWRAP but wrong flags throughout; 70% completeness; wrong order |
| Gemini | Gemini 2.5 Pro | 0.90 | C | P | P | S | R | metaWRAP + CheckM; 50% completeness |
| Gemini | Gemini 3 Pro | 1.00 | C | C | P | S | R | metaWRAP + CheckM; 30% completeness for low-biomass |
| Gemini | Gemini 3 Flash | 0.40 | A | P | F | Q | M | metaWRAP + CheckM but 60% completeness; wrong binning order |
| Gemini | Gemini 3.1 Pro | 1.00 | C | C | P | S | R | metaWRAP + CheckM; 30% completeness |
| Google | Gemini Deep Research | 1.00 | C | C | P | S | R | metaWRAP + CheckM; 30% completeness |
| DeepSeek | DeepSeek V3 | 0.00 | I | I | F | I | N | Used wrong flags; generated wildcards in code |
| Zhipu | GLM-5 | 0.70 | C | P | P | Q | M | metaWRAP + CheckM; acceptable |
