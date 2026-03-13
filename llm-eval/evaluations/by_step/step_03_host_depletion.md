# Step 3: Host Depletion

- Models evaluated: 28
- Fully correct responses: 14/28
- Average composite score: 0.75

## Dominant Non-Correct Labels

- `tool_selection`: I (4x)
- `parameter_accuracy`: P (9x)
- `output_compatibility`: F (5x)
- `scientific_validity`: Q (10x)
- `executability`: N (5x)

## Model-Level Results

| Family | Model | Composite | Tool | Params | Output | Science | Exec | Notes |
|:------|:------|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| OpenAI | GPT-4o | 0.00 | I | I | F | I | N | Used Bowtie2 with wrong flags; treated as mandatory without context |
| OpenAI | o1-preview | 0.70 | A | P | P | Q | R | minimap2 but with wrong preset; ignored air sample context |
| OpenAI | o1-mini | 0.00 | I | I | F | I | N | BWA-MEM (short-read aligner); wrong flags throughout |
| OpenAI | o1 | 0.80 | C | P | P | Q | R | minimap2 correct but wrong preset flag |
| OpenAI | o1-pro | 1.00 | C | C | P | S | R | minimap2; discussed sample context appropriately |
| OpenAI | o3-mini | 0.80 | C | P | P | Q | R | minimap2 correct but ignored sample context |
| OpenAI | o3 (high reasoning) | 1.00 | C | C | P | S | R | minimap2; noted low host contamination in air samples |
| OpenAI | o4-mini | 0.80 | C | P | P | Q | R | minimap2 correct but ignored input context about air samples |
| OpenAI | GPT-5 | 1.00 | C | C | P | S | R | minimap2; correctly noted optional for air samples |
| OpenAI | ChatGPT Deep Research | 1.00 | C | C | P | S | R | minimap2; excellent context |
| Claude | Sonnet 3.5 | 0.20 | A | I | F | Q | N | minimap2 but with wrong preset and wrong flags |
| Claude | Sonnet 4 | 0.80 | C | P | P | Q | R | minimap2 + samtools correct but ignored air sample context |
| Claude | Sonnet 4.5 | 0.80 | C | P | P | Q | R | minimap2 correct but ignored air sample details |
| Claude | Haiku 4.5 | 1.00 | C | C | P | S | R | minimap2 correct |
| Claude | Opus 4.5 | 1.00 | C | C | P | S | R | minimap2; noted optional for environmental air |
| Claude | Opus 4.6 | 1.00 | C | C | P | S | R | minimap2; excellent context discussion |
| Claude | Sonnet 4.6 | 1.00 | C | C | P | S | R | minimap2; excellent sample context |
| Claude | Claude Deep Research | 1.00 | C | C | P | S | R | minimap2; excellent context |
| Gemini | Gemini 2.0 Flash | 0.00 | I | I | F | I | N | BWA-MEM (wrong tool); wrong flags; wrong pipeline order |
| Gemini | Gemini 2.5 Pro Preview | 1.00 | C | C | P | S | R | minimap2 correct |
| Gemini | Gemini 2.5 Flash | 0.60 | A | P | P | Q | M | minimap2 but wrong preset; ignored sample context |
| Gemini | Gemini 2.5 Pro | 1.00 | C | C | P | S | R | minimap2; noted environmental context |
| Gemini | Gemini 3 Pro | 1.00 | C | C | P | S | R | minimap2; excellent sample context awareness |
| Gemini | Gemini 3 Flash | 0.80 | C | P | P | Q | R | minimap2 correct but ignored air sample context |
| Gemini | Gemini 3.1 Pro | 1.00 | C | C | P | S | R | minimap2; excellent reasoning |
| Google | Gemini Deep Research | 1.00 | C | C | P | S | R | minimap2; excellent context |
| DeepSeek | DeepSeek V3 | 0.00 | I | I | F | I | N | Used wrong flags; generated wildcards in code |
| Zhipu | GLM-5 | 0.80 | C | P | P | Q | R | minimap2 correct |
