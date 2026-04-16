# Step 10: Aiv Phylogenetics

- Models evaluated: 28
- Fully correct responses: 6/28
- Average composite score: 0.66

## Dominant Non-Correct Labels

- `tool_selection`: A (11x)
- `parameter_accuracy`: P (17x)
- `output_compatibility`: F (5x)
- `scientific_validity`: Q (14x)
- `executability`: M (8x)

## Model-Level Results

| Family | Model | Composite | Tool | Params | Output | Science | Exec | Notes |
|:------|:------|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| OpenAI | GPT-4o | 0.10 | I | I | F | Q | N | No phylogenetic analysis; basic BLAST only |
| OpenAI | o1-preview | 0.60 | A | P | P | Q | M | MAFFT + basic tree but wrong model selection; no bootstrapping |
| OpenAI | o1-mini | 0.10 | I | I | F | Q | N | No proper phylogenetic analysis |
| OpenAI | o1 | 0.60 | A | P | P | Q | M | MAFFT + tree but fixed model; single bootstrap metric |
| OpenAI | o1-pro | 0.90 | C | P | P | S | R | MAFFT + IQ-TREE2; missed ModelFinder Plus specifics |
| OpenAI | o3-mini | 0.60 | A | P | P | Q | M | Basic phylogenetics; wrong parameters |
| OpenAI | o3 (high reasoning) | 0.90 | C | P | P | S | R | MAFFT + IQ-TREE2; partially correct parameters |
| OpenAI | o4-mini | 0.60 | A | P | P | Q | M | Basic tree; wrong parameters |
| OpenAI | GPT-5 | 1.00 | C | C | P | S | R | MAFFT + IQ-TREE2 with ModelFinder; both support metrics |
| OpenAI | ChatGPT Deep Research | 1.00 | C | C | P | S | R | MAFFT + IQ-TREE2 with MFP; both bootstrap metrics |
| Claude | Sonnet 3.5 | 0.60 | A | P | P | Q | M | Basic MAFFT + tree; wrong parameters |
| Claude | Sonnet 4 | 0.60 | A | P | P | Q | M | MAFFT + tree; partially correct |
| Claude | Sonnet 4.5 | 0.70 | A | P | P | Q | R | MAFFT + IQ-TREE2; partially correct parameters |
| Claude | Haiku 4.5 | 0.70 | A | P | P | Q | R | MAFFT + tree; acceptable approach |
| Claude | Opus 4.5 | 0.90 | C | P | P | S | R | MAFFT + IQ-TREE2; mentioned ModelFinder |
| Claude | Opus 4.6 | 1.00 | C | C | P | S | R | MAFFT + IQ-TREE2 with MFP; both bootstrap metrics |
| Claude | Sonnet 4.6 | 0.90 | C | P | P | S | R | MAFFT + IQ-TREE2; partially correct MFP usage |
| Claude | Claude Deep Research | 1.00 | C | C | P | S | R | MAFFT + IQ-TREE2 with MFP and dual bootstrapping |
| Gemini | Gemini 2.0 Flash | 0.10 | I | I | F | Q | N | No phylogenetic analysis; wrong tools |
| Gemini | Gemini 2.5 Pro Preview | 0.70 | A | P | P | Q | R | MAFFT + IQ-TREE2; partially correct |
| Gemini | Gemini 2.5 Flash | 0.60 | A | P | P | Q | M | Basic tree; wrong parameters |
| Gemini | Gemini 2.5 Pro | 0.90 | C | P | P | S | R | MAFFT + IQ-TREE2; acceptable parameters |
| Gemini | Gemini 3 Pro | 0.90 | C | P | P | S | R | MAFFT + IQ-TREE2; mostly correct parameters |
| Gemini | Gemini 3 Flash | 0.60 | A | P | P | Q | M | Basic phylogenetics; incomplete parameters |
| Gemini | Gemini 3.1 Pro | 1.00 | C | C | P | S | R | MAFFT + IQ-TREE2 with MFP; dual bootstrapping |
| Google | Gemini Deep Research | 1.00 | C | C | P | S | R | MAFFT + IQ-TREE2 with MFP and dual bootstrapping |
| DeepSeek | DeepSeek V3 | 0.00 | I | I | F | I | N | Wrong flags; generated wildcards; broken code |
| Zhipu | GLM-5 | 0.00 | I | I | F | I | N | No phylogenetic analysis |
