# Step 2: Quality Control

- Models evaluated: 28
- Fully correct responses: 21/28
- Average composite score: 0.89

## Dominant Non-Correct Labels

- `tool_selection`: A (3x)
- `parameter_accuracy`: P (5x)
- `output_compatibility`: F (2x)
- `scientific_validity`: Q (4x)
- `executability`: N (2x)

## Model-Level Results

| Family | Model | Composite | Tool | Params | Output | Science | Exec | Notes |
|:------|:------|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| OpenAI | GPT-4o | 0.70 | A | P | P | Q | R | Recommended FastQC (short-read tool) as primary; ignored nanopore context |
| OpenAI | o1-preview | 1.00 | C | C | P | S | R | NanoPlot with correct parameters |
| OpenAI | o1-mini | 0.70 | A | P | P | Q | R | FastQC only; ignored nanopore-specific metrics |
| OpenAI | o1 | 1.00 | C | C | P | S | R | NanoPlot recommended correctly |
| OpenAI | o1-pro | 1.00 | C | C | P | S | R | NanoPlot with comprehensive parameters |
| OpenAI | o3-mini | 0.90 | C | P | P | S | R | NanoPlot correct but incomplete parameters |
| OpenAI | o3 (high reasoning) | 1.00 | C | C | P | S | R | NanoPlot + NanoStat |
| OpenAI | o4-mini | 1.00 | C | C | P | S | R | NanoPlot correct |
| OpenAI | GPT-5 | 1.00 | C | C | P | S | R | NanoPlot + NanoStat |
| OpenAI | ChatGPT Deep Research | 1.00 | C | C | P | S | R | NanoPlot + NanoStat |
| Claude | Sonnet 3.5 | 0.70 | A | P | P | Q | R | FastQC as primary (wrong tool for nanopore) |
| Claude | Sonnet 4 | 1.00 | C | C | P | S | R | NanoPlot comprehensive |
| Claude | Sonnet 4.5 | 1.00 | C | C | P | S | R | NanoPlot + NanoStat |
| Claude | Haiku 4.5 | 1.00 | C | C | P | S | R | NanoPlot correct |
| Claude | Opus 4.5 | 1.00 | C | C | P | S | R | NanoPlot + NanoStat comprehensive |
| Claude | Opus 4.6 | 1.00 | C | C | P | S | R | NanoPlot + NanoStat |
| Claude | Sonnet 4.6 | 1.00 | C | C | P | S | R | NanoPlot + NanoStat |
| Claude | Claude Deep Research | 1.00 | C | C | P | S | R | NanoPlot + NanoStat |
| Gemini | Gemini 2.0 Flash | 0.10 | I | I | F | Q | N | FastQC only; ignored nanopore context entirely; wrong flags |
| Gemini | Gemini 2.5 Pro Preview | 1.00 | C | C | P | S | R | NanoPlot correct |
| Gemini | Gemini 2.5 Flash | 0.90 | C | P | P | S | R | NanoPlot correct but incomplete flags |
| Gemini | Gemini 2.5 Pro | 1.00 | C | C | P | S | R | NanoPlot comprehensive |
| Gemini | Gemini 3 Pro | 1.00 | C | C | P | S | R | NanoPlot + NanoStat |
| Gemini | Gemini 3 Flash | 1.00 | C | C | P | S | R | NanoPlot correct |
| Gemini | Gemini 3.1 Pro | 1.00 | C | C | P | S | R | NanoPlot + NanoStat |
| Google | Gemini Deep Research | 1.00 | C | C | P | S | R | NanoPlot + NanoStat |
| DeepSeek | DeepSeek V3 | 0.00 | I | I | F | I | N | Used wrong flags; generated wildcards in code |
| Zhipu | GLM-5 | 1.00 | C | C | P | S | R | NanoPlot correct |
