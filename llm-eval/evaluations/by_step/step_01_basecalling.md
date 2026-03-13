# Step 1: Basecalling

- Models evaluated: 28
- Fully correct responses: 11/28
- Average composite score: 0.69

## Dominant Non-Correct Labels

- `tool_selection`: A (8x)
- `parameter_accuracy`: P (12x)
- `output_compatibility`: F (5x)
- `scientific_validity`: Q (9x)
- `executability`: M (9x)

## Model-Level Results

| Family | Model | Composite | Tool | Params | Output | Science | Exec | Notes |
|:------|:------|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| OpenAI | GPT-4o | 0.00 | I | I | F | I | N | Recommended Guppy with wrong model name; Illumina Q30 threshold; ignored R10.4.1 chemistry |
| OpenAI | o1-preview | 0.60 | A | P | P | Q | M | Recommended Guppy (acceptable) but outdated version and wrong config flags |
| OpenAI | o1-mini | 0.00 | I | I | F | I | N | Recommended Albacore (discontinued); completely wrong pipeline order |
| OpenAI | o1 | 0.60 | A | P | P | Q | M | Dorado correct but wrong model name; missed Porechop step; Q15 threshold |
| OpenAI | o1-pro | 1.00 | C | C | P | S | R | Dorado + Porechop + NanoFilt correct sequence |
| OpenAI | o3-mini | 0.60 | A | P | P | Q | M | Dorado correct but used Chopper with wrong flags; wrong quality threshold |
| OpenAI | o3 (high reasoning) | 0.90 | C | P | P | S | R | Dorado + Porechop + NanoFilt correct but slightly wrong NanoFilt flags |
| OpenAI | o4-mini | 0.60 | A | P | P | Q | M | Dorado + Chopper (acceptable) but wrong quality threshold and flags |
| OpenAI | GPT-5 | 1.00 | C | C | P | S | R | Dorado + Porechop + NanoFilt; correct three-tool sequence |
| OpenAI | ChatGPT Deep Research | 1.00 | C | C | P | S | R | Dorado + Porechop + NanoFilt; fully correct |
| Claude | Sonnet 3.5 | 0.00 | I | I | F | I | N | Guppy with completely wrong config; ignored R10.4.1 input; wrong pipeline order |
| Claude | Sonnet 4 | 0.60 | A | P | P | Q | M | Dorado + Porechop correct tools but wrong NanoFilt flags; Q12 threshold |
| Claude | Sonnet 4.5 | 0.60 | A | P | P | Q | M | Dorado + Porechop correct but wrong NanoFilt parameters |
| Claude | Haiku 4.5 | 0.90 | C | P | P | S | R | Dorado correct; used Chopper; Q10 threshold |
| Claude | Opus 4.5 | 1.00 | C | C | P | S | R | Dorado + Porechop + NanoFilt; fully correct |
| Claude | Opus 4.6 | 1.00 | C | C | P | S | R | Dorado + Porechop + NanoFilt; fully correct |
| Claude | Sonnet 4.6 | 1.00 | C | C | P | S | R | Dorado + Porechop + NanoFilt; fully correct |
| Claude | Claude Deep Research | 1.00 | C | C | P | S | R | Dorado + Porechop + NanoFilt; fully correct |
| Gemini | Gemini 2.0 Flash | 0.00 | I | I | F | I | N | Guppy with completely wrong config; Illumina params; wrong pipeline order |
| Gemini | Gemini 2.5 Pro Preview | 0.90 | C | P | P | S | R | Dorado correct; Chopper instead of Porechop+NanoFilt |
| Gemini | Gemini 2.5 Flash | 0.60 | A | P | P | Q | M | Dorado correct but Chopper with wrong flags; wrong length filter |
| Gemini | Gemini 2.5 Pro | 1.00 | C | C | P | S | R | Dorado + Porechop + NanoFilt correct |
| Gemini | Gemini 3 Pro | 1.00 | C | C | P | S | R | Dorado + Porechop + NanoFilt; fully correct |
| Gemini | Gemini 3 Flash | 0.60 | A | P | P | Q | M | Dorado + Chopper but wrong flags; wrong quality threshold |
| Gemini | Gemini 3.1 Pro | 1.00 | C | C | P | S | R | Dorado + Porechop + NanoFilt; fully correct |
| Google | Gemini Deep Research | 1.00 | C | C | P | S | R | Dorado + Porechop + NanoFilt; fully correct |
| DeepSeek | DeepSeek V3 | 0.00 | I | I | F | I | N | Used wrong flags; wrong tool; generated wildcards in code |
| Zhipu | GLM-5 | 0.70 | C | P | P | Q | M | Dorado correct; minor flag issues |
