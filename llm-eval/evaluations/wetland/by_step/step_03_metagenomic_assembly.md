# Step 3: Metagenomic Assembly

- Models evaluated: 28
- Fully correct responses: 3/28
- Average composite score: 0.61

## Dominant Non-Correct Labels

- `tool_selection`: A (20x)
- `parameter_accuracy`: P (12x)
- `output_compatibility`: F (8x)
- `scientific_validity`: Q (11x)
- `executability`: N (7x)

## Model-Level Results

| Family | Model | Composite | Tool | Params | Output | Science | Exec | Notes |
|:------|:------|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| OpenAI | GPT-4o | 0.00 | I | I | F | I | N | Recommended SPAdes; no dual assembler concept |
| OpenAI | o1-preview | 0.20 | A | I | F | Q | N | MetaFlye correct but no nanoMDBG; wrong read type flag |
| OpenAI | o1-mini | 0.00 | I | I | F | I | N | Short-read assembler; no long-read awareness |
| OpenAI | o1 | 0.70 | A | P | P | Q | R | MetaFlye alone; acceptable but no dual assembler |
| OpenAI | o1-pro | 0.80 | A | P | P | S | R | MetaFlye correct with --meta; no nanoMDBG dual strategy |
| OpenAI | o3-mini | 0.70 | A | P | P | Q | R | MetaFlye alone; acceptable |
| OpenAI | o3 (high reasoning) | 0.80 | A | P | P | S | R | MetaFlye correct; mentioned nanoMDBG as alternative but didn't implement |
| OpenAI | o4-mini | 0.70 | A | P | P | Q | R | MetaFlye alone; acceptable |
| OpenAI | GPT-5 | 0.90 | A | C | P | S | R | MetaFlye excellent; acknowledged alternatives but not nanoMDBG specifically |
| OpenAI | ChatGPT Deep Research | 1.00 | C | C | P | S | R | Found dual assembler strategy through research; metaFlye + nanoMDBG |
| Claude | Sonnet 3.5 | 0.20 | A | I | F | Q | N | MetaFlye but wrong flags; no --meta; no dual assembler |
| Claude | Sonnet 4 | 0.70 | A | P | P | Q | R | MetaFlye alone; acceptable; correct read type flag |
| Claude | Sonnet 4.5 | 0.70 | A | P | P | Q | R | MetaFlye alone; correct flags |
| Claude | Haiku 4.5 | 0.70 | A | P | P | Q | R | MetaFlye alone; correct basic setup |
| Claude | Opus 4.5 | 0.90 | A | C | P | S | R | MetaFlye excellent; noted assembly alternatives but not nanoMDBG |
| Claude | Opus 4.6 | 0.90 | A | C | P | S | R | MetaFlye excellent; acknowledged complementary assemblers |
| Claude | Sonnet 4.6 | 0.90 | A | C | P | S | R | MetaFlye excellent; no nanoMDBG |
| Claude | Claude Deep Research | 1.00 | C | C | P | S | R | Found dual assembler strategy; metaFlye + nanoMDBG |
| Gemini | Gemini 2.0 Flash | 0.00 | I | I | F | I | N | Short-read assembler; no long-read or meta mode |
| Gemini | Gemini 2.5 Pro Preview | 0.70 | A | P | P | Q | R | MetaFlye alone; acceptable setup |
| Gemini | Gemini 2.5 Flash | 0.40 | A | P | F | Q | M | MetaFlye but wrong read flag; no dual assembler |
| Gemini | Gemini 2.5 Pro | 0.80 | A | P | P | S | R | MetaFlye correct; no dual assembler |
| Gemini | Gemini 3 Pro | 0.90 | A | C | P | S | R | MetaFlye excellent; noted alternatives but not nanoMDBG |
| Gemini | Gemini 3 Flash | 0.70 | A | P | P | Q | R | MetaFlye alone; wrong read flag |
| Gemini | Gemini 3.1 Pro | 0.90 | A | C | P | S | R | MetaFlye excellent; acknowledged complementary assemblers |
| Google | Gemini Deep Research | 1.00 | C | C | P | S | R | Found dual assembler strategy through research |
| DeepSeek | DeepSeek V3 | 0.00 | I | I | F | I | N | Wrong flags; generated wildcards; broken code |
| Zhipu | GLM-5 | 0.00 | I | I | F | I | N | Failed assembly; wrong tool/flags |
