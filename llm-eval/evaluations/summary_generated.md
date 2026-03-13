# Aggregated Scoring Results

*Auto-generated from `results/tables/scoring_matrix.csv`.*

## Dataset Scope

- Evaluated entries: 28
- Scored step-results: 196
- Pipeline steps: 7

## First Fully Correct Pipeline per Family

- **OpenAI:** GPT-5
- **Claude:** Opus 4.5
- **Gemini:** Gemini 3 Pro
- **Google:** Gemini Deep Research
- **DeepSeek:** None
- **Zhipu:** None

## Steps Ranked by Difficulty

| Rank | Step | Average Composite Score |
|:-----|:-----|------------------------:|
| 1 | 6. binning | 0.59 |
| 2 | 7. functional annotation | 0.62 |
| 3 | 5. assembly | 0.62 |
| 4 | 1. basecalling | 0.69 |
| 5 | 3. host depletion | 0.75 |
| 6 | 4. taxonomic classification | 0.84 |
| 7 | 2. quality control | 0.89 |

## Dominant Non-Correct Labels by Step

### Step 1: Basecalling

- `tool_selection`: A (8x)
- `parameter_accuracy`: P (12x)
- `output_compatibility`: F (5x)
- `scientific_validity`: Q (9x)
- `executability`: M (9x)

### Step 2: Quality Control

- `tool_selection`: A (3x)
- `parameter_accuracy`: P (5x)
- `output_compatibility`: F (2x)
- `scientific_validity`: Q (4x)
- `executability`: N (2x)

### Step 3: Host Depletion

- `tool_selection`: I (4x)
- `parameter_accuracy`: P (9x)
- `output_compatibility`: F (5x)
- `scientific_validity`: Q (10x)
- `executability`: N (5x)

### Step 4: Taxonomic Classification

- `tool_selection`: A (3x)
- `parameter_accuracy`: P (9x)
- `output_compatibility`: F (4x)
- `scientific_validity`: Q (7x)
- `executability`: N (3x)

### Step 5: Assembly

- `tool_selection`: A (6x)
- `parameter_accuracy`: P (10x)
- `output_compatibility`: F (11x)
- `scientific_validity`: Q (9x)
- `executability`: M (10x)

### Step 6: Binning

- `tool_selection`: A (10x)
- `parameter_accuracy`: P (13x)
- `output_compatibility`: F (13x)
- `scientific_validity`: Q (12x)
- `executability`: N (7x)

### Step 7: Functional Annotation

- `tool_selection`: A (10x)
- `parameter_accuracy`: P (11x)
- `output_compatibility`: F (7x)
- `scientific_validity`: Q (16x)
- `executability`: N (7x)

## Family Coverage

- **OpenAI (10):** GPT-4o | o1-preview | o1-mini | o1 | o1-pro | o3-mini | o3 (high reasoning) | o4-mini | GPT-5 | ChatGPT Deep Research
- **Claude (8):** Sonnet 3.5 | Sonnet 4 | Sonnet 4.5 | Haiku 4.5 | Opus 4.5 | Opus 4.6 | Sonnet 4.6 | Claude Deep Research
- **Gemini (7):** Gemini 2.0 Flash | Gemini 2.5 Pro Preview | Gemini 2.5 Flash | Gemini 2.5 Pro | Gemini 3 Pro | Gemini 3 Flash | Gemini 3.1 Pro
- **Google (1):** Gemini Deep Research
- **DeepSeek (1):** DeepSeek V3
- **Zhipu (1):** GLM-5
