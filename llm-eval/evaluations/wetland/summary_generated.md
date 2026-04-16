# Aggregated Scoring Results

*Auto-generated from `results/tables/scoring_matrix.csv`.*

## Dataset Scope

- Evaluated entries: 28
- Scored step-results: 280
- Pipeline steps: 10

## First Fully Correct Pipeline per Family

- **OpenAI:** None
- **Claude:** None
- **Gemini:** None
- **Google:** None
- **DeepSeek:** None
- **Zhipu:** None

## Steps Ranked by Difficulty

| Rank | Step | Average Composite Score |
|:-----|:-----|------------------------:|
| 1 | 8. edna metabarcoding | 0.23 |
| 2 | 7. rna virome | 0.46 |
| 3 | 5. pathogen identification | 0.54 |
| 4 | 4. polishing annotation | 0.55 |
| 5 | 3. metagenomic assembly | 0.61 |
| 6 | 6. amr virulence plasmid | 0.62 |
| 7 | 10. aiv phylogenetics | 0.66 |
| 8 | 9. aiv consensus | 0.71 |
| 9 | 1. basecalling qc | 0.72 |
| 10 | 2. taxonomic classification | 0.83 |

## Dominant Non-Correct Labels by Step

### Step 1: Basecalling Qc

- `tool_selection`: A (10x)
- `parameter_accuracy`: P (15x)
- `output_compatibility`: F (3x)
- `scientific_validity`: Q (11x)
- `executability`: M (11x)

### Step 2: Taxonomic Classification

- `tool_selection`: A (3x)
- `parameter_accuracy`: P (9x)
- `output_compatibility`: F (4x)
- `scientific_validity`: Q (7x)
- `executability`: N (4x)

### Step 3: Metagenomic Assembly

- `tool_selection`: A (20x)
- `parameter_accuracy`: P (12x)
- `output_compatibility`: F (8x)
- `scientific_validity`: Q (11x)
- `executability`: N (7x)

### Step 4: Polishing Annotation

- `tool_selection`: A (14x)
- `parameter_accuracy`: P (19x)
- `output_compatibility`: F (13x)
- `scientific_validity`: Q (14x)
- `executability`: N (7x)

### Step 5: Pathogen Identification

- `tool_selection`: A (19x)
- `parameter_accuracy`: P (19x)
- `output_compatibility`: F (8x)
- `scientific_validity`: Q (14x)
- `executability`: N (8x)

### Step 6: Amr Virulence Plasmid

- `tool_selection`: A (13x)
- `parameter_accuracy`: P (17x)
- `output_compatibility`: F (6x)
- `scientific_validity`: Q (16x)
- `executability`: M (8x)

### Step 7: Rna Virome

- `tool_selection`: A (22x)
- `parameter_accuracy`: P (22x)
- `output_compatibility`: F (16x)
- `scientific_validity`: Q (14x)
- `executability`: N (8x)

### Step 8: Edna Metabarcoding

- `tool_selection`: I (16x)
- `parameter_accuracy`: I (17x)
- `output_compatibility`: F (25x)
- `scientific_validity`: Q (18x)
- `executability`: N (17x)

### Step 9: Aiv Consensus

- `tool_selection`: A (9x)
- `parameter_accuracy`: P (15x)
- `output_compatibility`: F (4x)
- `scientific_validity`: Q (9x)
- `executability`: M (9x)

### Step 10: Aiv Phylogenetics

- `tool_selection`: A (11x)
- `parameter_accuracy`: P (17x)
- `output_compatibility`: F (5x)
- `scientific_validity`: Q (14x)
- `executability`: M (8x)

## Family Coverage

- **OpenAI (10):** GPT-4o | o1-preview | o1-mini | o1 | o1-pro | o3-mini | o3 (high reasoning) | o4-mini | GPT-5 | ChatGPT Deep Research
- **Claude (8):** Sonnet 3.5 | Sonnet 4 | Sonnet 4.5 | Haiku 4.5 | Opus 4.5 | Opus 4.6 | Sonnet 4.6 | Claude Deep Research
- **Gemini (7):** Gemini 2.0 Flash | Gemini 2.5 Pro Preview | Gemini 2.5 Flash | Gemini 2.5 Pro | Gemini 3 Pro | Gemini 3 Flash | Gemini 3.1 Pro
- **Google (1):** Gemini Deep Research
- **DeepSeek (1):** DeepSeek V3
- **Zhipu (1):** GLM-5
