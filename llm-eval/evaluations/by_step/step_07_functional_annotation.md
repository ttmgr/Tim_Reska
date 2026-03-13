# Step 7: Functional Annotation

- Models evaluated: 28
- Fully correct responses: 9/28
- Average composite score: 0.62

## Dominant Non-Correct Labels

- `tool_selection`: A (10x)
- `parameter_accuracy`: P (11x)
- `output_compatibility`: F (7x)
- `scientific_validity`: Q (16x)
- `executability`: N (7x)

## Model-Level Results

| Family | Model | Composite | Tool | Params | Output | Science | Exec | Notes |
|:------|:------|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| OpenAI | GPT-4o | 0.10 | I | I | F | Q | N | Prokka only with wrong flags; no AMR tools; single level only |
| OpenAI | o1-preview | 0.50 | A | I | P | Q | M | Prokka + ABRicate but missed AMRFinderPlus; wrong pipeline order |
| OpenAI | o1-mini | 0.10 | I | I | F | Q | N | Prokka with wrong flags; no AMR tools; wrong pipeline order |
| OpenAI | o1 | 0.60 | A | P | P | Q | M | AMRFinderPlus on contigs only; missed read-level; wrong flags |
| OpenAI | o1-pro | 0.80 | C | P | P | Q | R | AMRFinderPlus + ABRicate on contigs and bins; missed reads |
| OpenAI | o3-mini | 0.60 | A | P | P | Q | M | AMRFinderPlus on contigs only; wrong flags; missed ABRicate |
| OpenAI | o3 (high reasoning) | 0.70 | A | P | P | Q | R | AMRFinderPlus + ABRicate; contigs and bins only; missed reads |
| OpenAI | o4-mini | 0.60 | A | P | P | Q | M | AMRFinderPlus on contigs and bins; missed read-level; wrong flags |
| OpenAI | GPT-5 | 1.00 | C | C | P | S | R | AMRFinderPlus + ABRicate + seqkit; all three levels |
| OpenAI | ChatGPT Deep Research | 1.00 | C | C | P | S | R | AMRFinderPlus + ABRicate + seqkit; all three levels |
| Claude | Sonnet 3.5 | 0.10 | I | I | F | Q | N | Prokka only with wrong flags; no AMR tools; ignored multi-level |
| Claude | Sonnet 4 | 0.60 | A | P | P | Q | M | AMRFinderPlus + ABRicate on contigs only; wrong pipeline order |
| Claude | Sonnet 4.5 | 0.60 | A | P | P | Q | M | AMRFinderPlus + ABRicate contigs/bins; missed read-level |
| Claude | Haiku 4.5 | 0.80 | C | P | P | Q | R | AMRFinderPlus + ABRicate; contigs only |
| Claude | Opus 4.5 | 1.00 | C | C | P | S | R | AMRFinderPlus + ABRicate + seqkit; all three levels |
| Claude | Opus 4.6 | 1.00 | C | C | P | S | R | AMRFinderPlus + ABRicate + seqkit; all three levels |
| Claude | Sonnet 4.6 | 1.00 | C | C | P | S | R | AMRFinderPlus + ABRicate + seqkit; all three levels |
| Claude | Claude Deep Research | 1.00 | C | C | P | S | R | AMRFinderPlus + ABRicate + seqkit; all three levels |
| Gemini | Gemini 2.0 Flash | 0.00 | I | I | F | I | N | Prokka only with wrong flags; no AMR tools; wrong pipeline order |
| Gemini | Gemini 2.5 Pro Preview | 0.70 | A | P | P | Q | R | AMRFinderPlus on contigs only; missed ABRicate |
| Gemini | Gemini 2.5 Flash | 0.20 | A | I | F | Q | N | AMRFinderPlus contigs only; wrong flags; ignored multi-level input |
| Gemini | Gemini 2.5 Pro | 0.80 | C | P | P | Q | R | AMRFinderPlus + ABRicate; contigs and bins only |
| Gemini | Gemini 3 Pro | 1.00 | C | C | P | S | R | AMRFinderPlus + ABRicate + seqkit; all three levels |
| Gemini | Gemini 3 Flash | 0.60 | A | P | P | Q | M | AMRFinderPlus + ABRicate; missed read-level; wrong flags |
| Gemini | Gemini 3.1 Pro | 1.00 | C | C | P | S | R | AMRFinderPlus + ABRicate + seqkit; all three levels |
| Google | Gemini Deep Research | 1.00 | C | C | P | S | R | AMRFinderPlus + ABRicate + seqkit; all three levels |
| DeepSeek | DeepSeek V3 | 0.00 | I | I | F | I | N | Used wrong flags; generated wildcards in code |
| Zhipu | GLM-5 | 0.00 | I | I | F | I | N | Failed resistance annotation and virulence screening |
