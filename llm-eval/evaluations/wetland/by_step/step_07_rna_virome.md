# Step 7: Rna Virome

- Models evaluated: 28
- Fully correct responses: 0/28
- Average composite score: 0.46

## Dominant Non-Correct Labels

- `tool_selection`: A (22x)
- `parameter_accuracy`: P (22x)
- `output_compatibility`: F (16x)
- `scientific_validity`: Q (14x)
- `executability`: N (8x)

## Model-Level Results

| Family | Model | Composite | Tool | Params | Output | Science | Exec | Notes |
|:------|:------|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| OpenAI | GPT-4o | 0.00 | I | I | F | I | N | Applied DNA shotgun tools to RNA virome data |
| OpenAI | o1-preview | 0.30 | A | P | F | Q | N | Used metaFlye for virome; wrong classification approach |
| OpenAI | o1-mini | 0.00 | I | I | F | I | N | DNA tools applied to RNA virome |
| OpenAI | o1 | 0.40 | A | P | F | Q | M | Wrong assembly tool for virome; nucleotide-level classification |
| OpenAI | o1-pro | 0.70 | A | P | P | Q | R | Reasonable virome approach but wrong assembly tool |
| OpenAI | o3-mini | 0.40 | A | P | F | Q | M | Wrong assembly tool for virome |
| OpenAI | o3 (high reasoning) | 0.70 | A | P | P | Q | R | Reasonable virome approach; used DIAMOND but wrong database |
| OpenAI | o4-mini | 0.40 | A | P | F | Q | M | Wrong assembly approach for virome |
| OpenAI | GPT-5 | 0.70 | A | P | P | Q | R | Virome assembly but not nanoMDBG specifically; DIAMOND NR correct |
| OpenAI | ChatGPT Deep Research | 0.80 | A | P | P | S | R | nanoMDBG for virome found via search; correct classification approach |
| Claude | Sonnet 3.5 | 0.00 | I | I | F | I | N | Applied DNA tools to RNA virome data |
| Claude | Sonnet 4 | 0.40 | A | P | F | Q | M | Wrong assembly tool for virome; nucleotide classification |
| Claude | Sonnet 4.5 | 0.40 | A | P | F | Q | M | Wrong assembly tool; DIAMOND but wrong database |
| Claude | Haiku 4.5 | 0.40 | A | P | F | Q | M | Wrong virome assembly approach |
| Claude | Opus 4.5 | 0.80 | A | P | P | S | R | Reasonable virome approach; DIAMOND NR but wrong assembler |
| Claude | Opus 4.6 | 0.80 | A | P | P | S | R | Virome assembly with DIAMOND NR; correct classification concept |
| Claude | Sonnet 4.6 | 0.80 | A | P | P | S | R | Reasonable virome approach; correct DIAMOND NR classification |
| Claude | Claude Deep Research | 0.80 | A | P | P | S | R | nanoMDBG for virome; DIAMOND NR classification |
| Gemini | Gemini 2.0 Flash | 0.00 | I | I | F | I | N | Completely wrong approach for RNA virome |
| Gemini | Gemini 2.5 Pro Preview | 0.40 | A | P | F | Q | M | Wrong assembly for virome; partial classification |
| Gemini | Gemini 2.5 Flash | 0.30 | A | P | F | Q | N | Wrong virome approach; broken output |
| Gemini | Gemini 2.5 Pro | 0.70 | A | P | P | Q | R | Reasonable virome; wrong assembly tool |
| Gemini | Gemini 3 Pro | 0.80 | A | P | P | S | R | Virome assembly; correct DIAMOND NR classification |
| Gemini | Gemini 3 Flash | 0.40 | A | P | F | Q | M | Wrong virome assembly approach |
| Gemini | Gemini 3.1 Pro | 0.80 | A | P | P | S | R | Virome with DIAMOND NR; correct concept |
| Google | Gemini Deep Research | 0.80 | A | P | P | S | R | nanoMDBG for virome; DIAMOND NR correct |
| DeepSeek | DeepSeek V3 | 0.00 | I | I | F | I | N | Wrong flags; generated wildcards; broken code |
| Zhipu | GLM-5 | 0.00 | I | I | F | I | N | Wrong virome approach |
