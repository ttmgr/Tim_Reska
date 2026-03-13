# Step 4: Taxonomic Classification

- Models evaluated: 28
- Fully correct responses: 15/28
- Average composite score: 0.84

## Dominant Non-Correct Labels

- `tool_selection`: A (3x)
- `parameter_accuracy`: P (9x)
- `output_compatibility`: F (4x)
- `scientific_validity`: Q (7x)
- `executability`: N (3x)

## Model-Level Results

| Family | Model | Composite | Tool | Params | Output | Science | Exec | Notes |
|:------|:------|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| OpenAI | GPT-4o | 0.30 | A | I | F | Q | M | Kraken2 but wrong database and flags; wrong report format |
| OpenAI | o1-preview | 0.80 | C | P | P | Q | R | Kraken2 with Standard database instead of nt |
| OpenAI | o1-mini | 0.20 | A | I | F | Q | N | Kraken2 with wrong confidence threshold and wrong database |
| OpenAI | o1 | 0.90 | C | P | P | S | R | Kraken2 with nt database; missed report format flag |
| OpenAI | o1-pro | 1.00 | C | C | P | S | R | Kraken2 + nt; mentioned downsampling |
| OpenAI | o3-mini | 0.80 | C | P | P | Q | R | Kraken2 + nt but wrong report flags |
| OpenAI | o3 (high reasoning) | 1.00 | C | C | P | S | R | Kraken2 + nt; discussed downsampling strategy |
| OpenAI | o4-mini | 0.90 | C | P | P | S | R | Kraken2 + nt but wrong report flag |
| OpenAI | GPT-5 | 1.00 | C | C | P | S | R | Kraken2 + nt; mentioned DIAMOND as alternative |
| OpenAI | ChatGPT Deep Research | 1.00 | C | C | P | S | R | Kraken2 + nt |
| Claude | Sonnet 3.5 | 0.80 | C | P | P | Q | R | Kraken2 but PlusPF database; wrong report flags |
| Claude | Sonnet 4 | 0.90 | C | P | P | S | R | Kraken2 + nt database but wrong confidence flag |
| Claude | Sonnet 4.5 | 1.00 | C | C | P | S | R | Kraken2 + nt; mentioned downsampling |
| Claude | Haiku 4.5 | 1.00 | C | C | P | S | R | Kraken2 + nt |
| Claude | Opus 4.5 | 1.00 | C | C | P | S | R | Kraken2 + nt; mentioned DIAMOND + CZID alternatives |
| Claude | Opus 4.6 | 1.00 | C | C | P | S | R | Kraken2 + nt; comprehensive alternatives |
| Claude | Sonnet 4.6 | 1.00 | C | C | P | S | R | Kraken2 + nt; comprehensive |
| Claude | Claude Deep Research | 1.00 | C | C | P | S | R | Kraken2 + nt |
| Gemini | Gemini 2.0 Flash | 0.20 | A | I | F | Q | N | Kraken2 but Standard database; wrong flags; no report format |
| Gemini | Gemini 2.5 Pro Preview | 1.00 | C | C | P | S | R | Kraken2 + nt correct |
| Gemini | Gemini 2.5 Flash | 0.80 | C | P | P | Q | R | Kraken2 + nt but wrong report flags |
| Gemini | Gemini 2.5 Pro | 1.00 | C | C | P | S | R | Kraken2 + nt; downsampling mentioned |
| Gemini | Gemini 3 Pro | 1.00 | C | C | P | S | R | Kraken2 + nt; DIAMOND alternative mentioned |
| Gemini | Gemini 3 Flash | 0.90 | C | P | P | S | R | Kraken2 + nt but wrong report flag |
| Gemini | Gemini 3.1 Pro | 1.00 | C | C | P | S | R | Kraken2 + nt; comprehensive |
| Google | Gemini Deep Research | 1.00 | C | C | P | S | R | Kraken2 + nt |
| DeepSeek | DeepSeek V3 | 0.00 | I | I | F | I | N | Used wrong flags; generated wildcards in code |
| Zhipu | GLM-5 | 0.90 | C | P | P | S | R | Kraken2 + nt |
