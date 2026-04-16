# Step 2: Taxonomic Classification

- Models evaluated: 28
- Fully correct responses: 15/28
- Average composite score: 0.83

## Dominant Non-Correct Labels

- `tool_selection`: A (3x)
- `parameter_accuracy`: P (9x)
- `output_compatibility`: F (4x)
- `scientific_validity`: Q (7x)
- `executability`: N (4x)

## Model-Level Results

| Family | Model | Composite | Tool | Params | Output | Science | Exec | Notes |
|:------|:------|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| OpenAI | GPT-4o | 0.20 | A | I | F | Q | N | Kraken2 but wrong database variant; no read normalization |
| OpenAI | o1-preview | 0.80 | C | P | P | Q | R | Kraken2 with Standard database instead of nt_core; no normalization |
| OpenAI | o1-mini | 0.20 | A | I | F | Q | N | Kraken2 with wrong database and flags; no normalization |
| OpenAI | o1 | 0.90 | C | P | P | S | R | Kraken2 + nt; missed nt_core distinction; mentioned normalization |
| OpenAI | o1-pro | 1.00 | C | C | P | S | R | Kraken2 + nt_core; mentioned normalization |
| OpenAI | o3-mini | 0.80 | C | P | P | Q | R | Kraken2 + nt; wrong report flags; no normalization |
| OpenAI | o3 (high reasoning) | 1.00 | C | C | P | S | R | Kraken2 + nt_core; discussed downsampling |
| OpenAI | o4-mini | 0.90 | C | P | P | S | R | Kraken2 + nt; normalization mentioned |
| OpenAI | GPT-5 | 1.00 | C | C | P | S | R | Kraken2 + nt_core; SeqKit normalization discussed |
| OpenAI | ChatGPT Deep Research | 1.00 | C | C | P | S | R | Kraken2 + nt_core; SeqKit normalization |
| Claude | Sonnet 3.5 | 0.80 | C | P | P | Q | R | Kraken2 but PlusPF database; no normalization |
| Claude | Sonnet 4 | 0.90 | C | P | P | S | R | Kraken2 + nt; wrong confidence flag; no normalization |
| Claude | Sonnet 4.5 | 1.00 | C | C | P | S | R | Kraken2 + nt; mentioned downsampling |
| Claude | Haiku 4.5 | 1.00 | C | C | P | S | R | Kraken2 + nt correct |
| Claude | Opus 4.5 | 1.00 | C | C | P | S | R | Kraken2 + nt_core; mentioned DIAMOND and CZID alternatives |
| Claude | Opus 4.6 | 1.00 | C | C | P | S | R | Kraken2 + nt_core; comprehensive normalization discussion |
| Claude | Sonnet 4.6 | 1.00 | C | C | P | S | R | Kraken2 + nt_core; comprehensive |
| Claude | Claude Deep Research | 1.00 | C | C | P | S | R | Kraken2 + nt_core; SeqKit normalization |
| Gemini | Gemini 2.0 Flash | 0.20 | A | I | F | Q | N | Kraken2 but Standard database; wrong flags; no normalization |
| Gemini | Gemini 2.5 Pro Preview | 1.00 | C | C | P | S | R | Kraken2 + nt correct |
| Gemini | Gemini 2.5 Flash | 0.80 | C | P | P | Q | R | Kraken2 + nt but wrong report flags |
| Gemini | Gemini 2.5 Pro | 1.00 | C | C | P | S | R | Kraken2 + nt_core; normalization mentioned |
| Gemini | Gemini 3 Pro | 1.00 | C | C | P | S | R | Kraken2 + nt_core; DIAMOND alternative mentioned |
| Gemini | Gemini 3 Flash | 0.90 | C | P | P | S | R | Kraken2 + nt; wrong report flag |
| Gemini | Gemini 3.1 Pro | 1.00 | C | C | P | S | R | Kraken2 + nt_core; comprehensive |
| Google | Gemini Deep Research | 1.00 | C | C | P | S | R | Kraken2 + nt_core; SeqKit normalization |
| DeepSeek | DeepSeek V3 | 0.00 | I | I | F | I | N | Wrong flags; generated wildcards; broken code |
| Zhipu | GLM-5 | 0.90 | C | P | P | S | R | Kraken2 + nt reasonable |
