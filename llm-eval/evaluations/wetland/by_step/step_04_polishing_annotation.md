# Step 4: Polishing Annotation

- Models evaluated: 28
- Fully correct responses: 3/28
- Average composite score: 0.55

## Dominant Non-Correct Labels

- `tool_selection`: A (14x)
- `parameter_accuracy`: P (19x)
- `output_compatibility`: F (13x)
- `scientific_validity`: Q (14x)
- `executability`: N (7x)

## Model-Level Results

| Family | Model | Composite | Tool | Params | Output | Science | Exec | Notes |
|:------|:------|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| OpenAI | GPT-4o | 0.00 | I | I | F | I | N | No polishing; ignored assembler-specific requirements |
| OpenAI | o1-preview | 0.30 | A | P | F | Q | N | Medaka polishing but not assembler-specific; no Prokka |
| OpenAI | o1-mini | 0.00 | I | I | F | I | N | No polishing; wrong annotation approach |
| OpenAI | o1 | 0.40 | A | P | F | Q | M | Some polishing but not assembler-specific; no Prokka |
| OpenAI | o1-pro | 0.70 | A | P | P | Q | R | 3x Racon + Medaka for metaFlye; no assembler-specific differentiation |
| OpenAI | o3-mini | 0.40 | A | P | F | Q | M | Single polishing approach; no annotation |
| OpenAI | o3 (high reasoning) | 0.70 | A | P | P | Q | R | Good polishing but not fully assembler-specific |
| OpenAI | o4-mini | 0.40 | A | P | F | Q | M | Some polishing; not assembler-specific |
| OpenAI | GPT-5 | 0.90 | C | P | P | S | R | Good assembler-aware polishing; Prokka annotation |
| OpenAI | ChatGPT Deep Research | 1.00 | C | C | P | S | R | Assembler-specific polishing from publication details |
| Claude | Sonnet 3.5 | 0.20 | A | I | F | Q | N | Medaka only; wrong polishing strategy; no Prokka |
| Claude | Sonnet 4 | 0.40 | A | P | F | Q | M | Racon polishing but wrong rounds; not assembler-specific |
| Claude | Sonnet 4.5 | 0.70 | A | P | P | Q | R | 2x Racon + Medaka; not assembler-specific |
| Claude | Haiku 4.5 | 0.70 | A | P | P | Q | R | 2 rounds Racon; not assembler-specific |
| Claude | Opus 4.5 | 0.90 | C | P | P | S | R | 3x Racon + Medaka for metaFlye; noted polishing requirements |
| Claude | Opus 4.6 | 0.90 | C | P | P | S | R | Assembler-aware polishing; Prokka annotation included |
| Claude | Sonnet 4.6 | 0.90 | C | P | P | S | R | Good polishing; Prokka included |
| Claude | Claude Deep Research | 1.00 | C | C | P | S | R | Assembler-specific polishing from research |
| Gemini | Gemini 2.0 Flash | 0.00 | I | I | F | I | N | No polishing; wrong annotation approach entirely |
| Gemini | Gemini 2.5 Pro Preview | 0.70 | A | P | P | Q | R | Medaka polishing; 1 round only; no Prokka |
| Gemini | Gemini 2.5 Flash | 0.40 | A | P | F | Q | M | Racon but wrong rounds; not assembler-specific |
| Gemini | Gemini 2.5 Pro | 0.70 | A | P | P | Q | R | 3x Racon + Medaka; not assembler-specific |
| Gemini | Gemini 3 Pro | 0.90 | C | P | P | S | R | Good polishing strategy; Prokka annotation |
| Gemini | Gemini 3 Flash | 0.40 | A | P | F | Q | M | 2x Racon; not assembler-specific |
| Gemini | Gemini 3.1 Pro | 0.90 | C | P | P | S | R | Assembler-aware polishing; Prokka |
| Google | Gemini Deep Research | 1.00 | C | C | P | S | R | Assembler-specific polishing from publication |
| DeepSeek | DeepSeek V3 | 0.00 | I | I | F | I | N | Wrong flags; generated wildcards; broken code |
| Zhipu | GLM-5 | 0.00 | I | I | F | I | N | No polishing; wrong approach |
