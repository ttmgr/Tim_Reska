# Step 9: Aiv Consensus

- Models evaluated: 28
- Fully correct responses: 9/28
- Average composite score: 0.71

## Dominant Non-Correct Labels

- `tool_selection`: A (9x)
- `parameter_accuracy`: P (15x)
- `output_compatibility`: F (4x)
- `scientific_validity`: Q (9x)
- `executability`: M (9x)

## Model-Level Results

| Family | Model | Composite | Tool | Params | Output | Science | Exec | Notes |
|:------|:------|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| OpenAI | GPT-4o | 0.00 | I | I | F | I | N | Wrong approach; no reference-based mapping strategy |
| OpenAI | o1-preview | 0.60 | A | P | P | Q | M | minimap2 correct but single-pass; incomplete consensus workflow |
| OpenAI | o1-mini | 0.00 | I | I | F | I | N | Wrong analysis approach entirely |
| OpenAI | o1 | 0.60 | A | P | P | Q | M | minimap2 but single-pass; no segment-specific reference selection |
| OpenAI | o1-pro | 0.90 | C | P | P | S | R | minimap2 + BCFtools; discussed segment structure |
| OpenAI | o3-mini | 0.60 | A | P | P | Q | M | minimap2 but incomplete workflow |
| OpenAI | o3 (high reasoning) | 0.90 | C | P | P | S | R | minimap2 + samtools + BCFtools; discussed segment structure |
| OpenAI | o4-mini | 0.60 | A | P | P | Q | M | minimap2 but incomplete |
| OpenAI | GPT-5 | 1.00 | C | C | P | S | R | minimap2 + SAMtools + BCFtools; segment-aware |
| OpenAI | ChatGPT Deep Research | 1.00 | C | C | P | S | R | Complete reference-based AIV consensus workflow |
| Claude | Sonnet 3.5 | 0.60 | A | P | P | Q | M | minimap2 correct but incomplete workflow |
| Claude | Sonnet 4 | 0.60 | A | P | P | Q | M | minimap2 but single-pass |
| Claude | Sonnet 4.5 | 0.90 | C | P | P | S | R | minimap2 + BCFtools; reasonable approach |
| Claude | Haiku 4.5 | 0.90 | C | P | P | S | R | minimap2 + SAMtools + BCFtools |
| Claude | Opus 4.5 | 1.00 | C | C | P | S | R | minimap2 + SAMtools + BCFtools; segment-aware |
| Claude | Opus 4.6 | 1.00 | C | C | P | S | R | Complete reference-based consensus workflow |
| Claude | Sonnet 4.6 | 1.00 | C | C | P | S | R | minimap2 + SAMtools + BCFtools; segment-aware |
| Claude | Claude Deep Research | 1.00 | C | C | P | S | R | Complete AIV consensus workflow |
| Gemini | Gemini 2.0 Flash | 0.00 | I | I | F | I | N | Wrong analysis approach |
| Gemini | Gemini 2.5 Pro Preview | 0.90 | C | P | P | S | R | minimap2 + BCFtools reasonable |
| Gemini | Gemini 2.5 Flash | 0.60 | A | P | P | Q | M | minimap2 but incomplete |
| Gemini | Gemini 2.5 Pro | 0.90 | C | P | P | S | R | minimap2 + BCFtools correct approach |
| Gemini | Gemini 3 Pro | 1.00 | C | C | P | S | R | Complete reference-based consensus |
| Gemini | Gemini 3 Flash | 0.60 | A | P | P | Q | M | minimap2 but incomplete workflow |
| Gemini | Gemini 3.1 Pro | 1.00 | C | C | P | S | R | Complete AIV consensus |
| Google | Gemini Deep Research | 1.00 | C | C | P | S | R | Complete AIV consensus workflow |
| DeepSeek | DeepSeek V3 | 0.00 | I | I | F | I | N | Wrong flags; generated wildcards; broken code |
| Zhipu | GLM-5 | 0.60 | A | P | P | Q | M | minimap2 reasonable |
