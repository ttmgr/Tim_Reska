# Step 5: Assembly

- Models evaluated: 28
- Fully correct responses: 11/28
- Average composite score: 0.62

## Dominant Non-Correct Labels

- `tool_selection`: A (6x)
- `parameter_accuracy`: P (10x)
- `output_compatibility`: F (11x)
- `scientific_validity`: Q (9x)
- `executability`: M (10x)

## Model-Level Results

| Family | Model | Composite | Tool | Params | Output | Science | Exec | Notes |
|:------|:------|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| OpenAI | GPT-4o | 0.00 | I | I | F | I | N | Recommended SPAdes (short-read assembler); no polishing; ignored long-read input |
| OpenAI | o1-preview | 0.20 | A | I | F | Q | N | MetaFlye correct but no polishing step at all; wrong read type flag |
| OpenAI | o1-mini | 0.00 | I | I | F | I | N | MEGAHIT (short-read assembler); ignored long-read input entirely |
| OpenAI | o1 | 0.40 | A | P | F | Q | M | MetaFlye correct but only 1 round polish with Medaka; wrong read type flag |
| OpenAI | o1-pro | 1.00 | C | C | P | S | R | MetaFlye + 3x Racon polishing |
| OpenAI | o3-mini | 0.40 | A | P | F | Q | M | MetaFlye correct but only 1 round Medaka; wrong read flag |
| OpenAI | o3 (high reasoning) | 0.80 | C | P | P | S | M | MetaFlye + 2x Racon (not 3x); correct read flag |
| OpenAI | o4-mini | 0.70 | C | P | P | Q | M | MetaFlye + 2x Racon; wrong read type flag |
| OpenAI | GPT-5 | 1.00 | C | C | P | S | R | MetaFlye + 3x Racon + mentioned pooling for urban samples |
| OpenAI | ChatGPT Deep Research | 1.00 | C | C | P | S | R | MetaFlye + 3x Racon |
| Claude | Sonnet 3.5 | 0.20 | A | I | F | Q | N | MetaFlye but Medaka polishing with wrong flags; no --meta flag |
| Claude | Sonnet 4 | 0.40 | A | P | F | Q | M | MetaFlye + Racon but wrong number of rounds; wrong read flag |
| Claude | Sonnet 4.5 | 0.70 | C | P | P | Q | M | MetaFlye + 2x Racon (not 3x); correct read flag |
| Claude | Haiku 4.5 | 0.80 | C | P | P | S | M | MetaFlye + 2 rounds Racon |
| Claude | Opus 4.5 | 1.00 | C | C | P | S | R | MetaFlye + 3x Racon; noted pooling strategy |
| Claude | Opus 4.6 | 1.00 | C | C | P | S | R | MetaFlye + 3x Racon; correct |
| Claude | Sonnet 4.6 | 1.00 | C | C | P | S | R | MetaFlye + 3x Racon; correct |
| Claude | Claude Deep Research | 1.00 | C | C | P | S | R | MetaFlye + 3x Racon |
| Gemini | Gemini 2.0 Flash | 0.00 | I | I | F | I | N | SPAdes meta mode (wrong tool); no polishing; ignored input details |
| Gemini | Gemini 2.5 Pro Preview | 0.80 | C | P | P | S | M | MetaFlye + Medaka (acceptable); 1 round only |
| Gemini | Gemini 2.5 Flash | 0.40 | A | P | F | Q | M | MetaFlye but wrong read flag; only 1 round Racon; ignored input |
| Gemini | Gemini 2.5 Pro | 1.00 | C | C | P | S | R | MetaFlye + 3x Racon correct |
| Gemini | Gemini 3 Pro | 1.00 | C | C | P | S | R | MetaFlye + 3x Racon; pooling noted |
| Gemini | Gemini 3 Flash | 0.70 | C | P | P | Q | M | MetaFlye + 2x Racon; wrong read flag |
| Gemini | Gemini 3.1 Pro | 1.00 | C | C | P | S | R | MetaFlye + 3x Racon; correct |
| Google | Gemini Deep Research | 1.00 | C | C | P | S | R | MetaFlye + 3x Racon |
| DeepSeek | DeepSeek V3 | 0.00 | I | I | F | I | N | Used wrong flags; generated wildcards in code |
| Zhipu | GLM-5 | 0.00 | I | I | F | I | N | Failed assembly completely; wrong tool/flags |
