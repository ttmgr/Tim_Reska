# Step 8: Edna Metabarcoding

- Models evaluated: 28
- Fully correct responses: 0/28
- Average composite score: 0.23

## Dominant Non-Correct Labels

- `tool_selection`: I (16x)
- `parameter_accuracy`: I (17x)
- `output_compatibility`: F (25x)
- `scientific_validity`: Q (18x)
- `executability`: N (17x)

## Model-Level Results

| Family | Model | Composite | Tool | Params | Output | Science | Exec | Notes |
|:------|:------|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| OpenAI | GPT-4o | 0.00 | I | I | F | I | N | Recommended Kraken2 for amplicon data; no OBITools4 or VSEARCH |
| OpenAI | o1-preview | 0.00 | I | I | F | I | N | Shotgun metagenomics tools for amplicon data |
| OpenAI | o1-mini | 0.00 | I | I | F | I | N | Shotgun tools for amplicon data |
| OpenAI | o1 | 0.10 | I | I | F | Q | N | Shotgun tools; no amplicon awareness |
| OpenAI | o1-pro | 0.40 | A | P | F | Q | M | Knows VSEARCH; missed OBITools4 and MIDORI2 specifics |
| OpenAI | o3-mini | 0.00 | I | I | F | I | N | Shotgun tools for amplicons |
| OpenAI | o3 (high reasoning) | 0.40 | A | P | F | Q | M | Knew VSEARCH and amplicon concept; missed OBITools4 and MIDORI2 |
| OpenAI | o4-mini | 0.10 | I | I | F | Q | N | No amplicon-specific tools |
| OpenAI | GPT-5 | 0.40 | A | P | F | Q | M | Knew VSEARCH and amplicon paradigm; missed OBITools4 and MIDORI2 |
| OpenAI | ChatGPT Deep Research | 0.70 | A | P | P | Q | R | Found eDNA metabarcoding tools through research; partial OBITools4 knowledge |
| Claude | Sonnet 3.5 | 0.00 | I | I | F | I | N | Shotgun metagenomics tools for amplicons |
| Claude | Sonnet 4 | 0.10 | I | I | F | Q | N | Shotgun tools for amplicons; no OBITools4 |
| Claude | Sonnet 4.5 | 0.10 | I | I | F | Q | N | No amplicon-specific tools |
| Claude | Haiku 4.5 | 0.10 | I | I | F | Q | N | No eDNA metabarcoding tools |
| Claude | Opus 4.5 | 0.40 | A | P | F | Q | M | Knew VSEARCH and OTU concept; missed OBITools4 and MIDORI2 |
| Claude | Opus 4.6 | 0.50 | A | P | F | Q | R | Best non-search model on eDNA; knew VSEARCH; missed OBITools4 |
| Claude | Sonnet 4.6 | 0.40 | A | P | F | Q | M | Knew amplicon paradigm; VSEARCH but missed OBITools4/MIDORI2 |
| Claude | Claude Deep Research | 0.70 | A | P | P | Q | R | Found eDNA metabarcoding tools through search; partial pipeline |
| Gemini | Gemini 2.0 Flash | 0.00 | I | I | F | I | N | Shotgun tools for amplicons; no metabarcoding awareness |
| Gemini | Gemini 2.5 Pro Preview | 0.10 | I | I | F | Q | N | No eDNA metabarcoding tools |
| Gemini | Gemini 2.5 Flash | 0.00 | I | I | F | I | N | No metabarcoding awareness |
| Gemini | Gemini 2.5 Pro | 0.20 | A | I | F | Q | N | Knew amplicon concept; missing OBITools4 and MIDORI2 |
| Gemini | Gemini 3 Pro | 0.40 | A | P | F | Q | M | Knew amplicon paradigm; VSEARCH; missed OBITools4/MIDORI2 |
| Gemini | Gemini 3 Flash | 0.00 | I | I | F | I | N | No metabarcoding tools |
| Gemini | Gemini 3.1 Pro | 0.50 | A | P | F | Q | R | Good amplicon awareness; VSEARCH; missed OBITools4 |
| Google | Gemini Deep Research | 0.70 | A | P | P | Q | R | Found eDNA tools through search; partial OBITools4 |
| DeepSeek | DeepSeek V3 | 0.00 | I | I | F | I | N | Wrong flags; generated wildcards; broken code |
| Zhipu | GLM-5 | 0.00 | I | I | F | I | N | No metabarcoding tools |
