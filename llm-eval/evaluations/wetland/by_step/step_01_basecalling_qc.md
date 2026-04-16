# Step 1: Basecalling Qc

- Models evaluated: 28
- Fully correct responses: 10/28
- Average composite score: 0.72

## Dominant Non-Correct Labels

- `tool_selection`: A (10x)
- `parameter_accuracy`: P (15x)
- `output_compatibility`: F (3x)
- `scientific_validity`: Q (11x)
- `executability`: M (11x)

## Model-Level Results

| Family | Model | Composite | Tool | Params | Output | Science | Exec | Notes |
|:------|:------|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| OpenAI | GPT-4o | 0.60 | A | P | P | Q | M | Dorado correct but HAC mode; single QC threshold for all tracks |
| OpenAI | o1-preview | 0.60 | A | P | P | Q | M | Dorado acceptable but wrong mode; single QC threshold |
| OpenAI | o1-mini | 0.00 | I | I | F | I | N | Wrong basecaller; wrong pipeline order; ignored SUP requirement |
| OpenAI | o1 | 0.60 | A | P | P | Q | M | Dorado correct but HAC not SUP; single QC threshold |
| OpenAI | o1-pro | 0.90 | C | P | P | S | R | Dorado SUP correct; Porechop + NanoFilt but single QC threshold |
| OpenAI | o3-mini | 0.60 | A | P | P | Q | M | Dorado correct but wrong mode; Chopper instead of Porechop+NanoFilt |
| OpenAI | o3 (high reasoning) | 0.90 | C | P | P | S | R | Dorado SUP correct; slightly wrong NanoFilt track-specific params |
| OpenAI | o4-mini | 0.60 | A | P | P | Q | M | Dorado + Chopper; wrong quality threshold for tracks |
| OpenAI | GPT-5 | 1.00 | C | C | P | S | R | Dorado SUP + Porechop + NanoFilt; mentioned track-specific QC |
| OpenAI | ChatGPT Deep Research | 1.00 | C | C | P | S | R | Dorado SUP correct; track-specific QC from publication search |
| Claude | Sonnet 3.5 | 0.60 | A | P | P | Q | M | Dorado but wrong mode; ignored track-specific QC |
| Claude | Sonnet 4 | 0.60 | A | P | P | Q | M | Dorado + Porechop correct; wrong NanoFilt threshold; no track split |
| Claude | Sonnet 4.5 | 0.60 | A | P | P | Q | M | Dorado + Porechop correct; wrong NanoFilt parameters |
| Claude | Haiku 4.5 | 0.90 | C | P | P | S | R | Dorado SUP correct; Chopper acceptable; Q10 threshold |
| Claude | Opus 4.5 | 1.00 | C | C | P | S | R | Dorado SUP + Porechop + NanoFilt; track-specific QC noted |
| Claude | Opus 4.6 | 1.00 | C | C | P | S | R | Dorado SUP + Porechop + NanoFilt; track-specific QC discussed |
| Claude | Sonnet 4.6 | 1.00 | C | C | P | S | R | Dorado SUP + Porechop + NanoFilt; track-specific QC |
| Claude | Claude Deep Research | 1.00 | C | C | P | S | R | Dorado SUP correct; track-specific QC from research |
| Gemini | Gemini 2.0 Flash | 0.00 | I | I | F | I | N | Wrong basecaller; Illumina parameters; wrong pipeline order |
| Gemini | Gemini 2.5 Pro Preview | 0.90 | C | P | P | S | R | Dorado correct; Chopper acceptable; missed track-specific QC |
| Gemini | Gemini 2.5 Flash | 0.60 | A | P | P | Q | M | Dorado correct; Chopper with wrong flags; wrong thresholds |
| Gemini | Gemini 2.5 Pro | 1.00 | C | C | P | S | R | Dorado + Porechop + NanoFilt correct; noted track QC |
| Gemini | Gemini 3 Pro | 1.00 | C | C | P | S | R | Dorado SUP + Porechop + NanoFilt; track-specific QC |
| Gemini | Gemini 3 Flash | 0.60 | A | P | P | Q | M | Dorado + Chopper; wrong quality threshold; no track split |
| Gemini | Gemini 3.1 Pro | 1.00 | C | C | P | S | R | Dorado SUP + Porechop + NanoFilt; track-specific QC |
| Google | Gemini Deep Research | 1.00 | C | C | P | S | R | Dorado SUP + track-specific QC from publication search |
| DeepSeek | DeepSeek V3 | 0.00 | I | I | F | I | N | Wrong flags; generated wildcards; broken code |
| Zhipu | GLM-5 | 0.70 | C | P | P | Q | M | Dorado correct; minor flag issues |
