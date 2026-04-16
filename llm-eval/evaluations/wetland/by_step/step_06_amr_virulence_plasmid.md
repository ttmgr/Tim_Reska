# Step 6: Amr Virulence Plasmid

- Models evaluated: 28
- Fully correct responses: 4/28
- Average composite score: 0.62

## Dominant Non-Correct Labels

- `tool_selection`: A (13x)
- `parameter_accuracy`: P (17x)
- `output_compatibility`: F (6x)
- `scientific_validity`: Q (16x)
- `executability`: M (8x)

## Model-Level Results

| Family | Model | Composite | Tool | Params | Output | Science | Exec | Notes |
|:------|:------|----------:|:----:|:------:|:------:|:-------:|:----:|:------|
| OpenAI | GPT-4o | 0.10 | I | I | F | Q | N | Prokka only; no AMRFinderPlus --plus; no virulence screening |
| OpenAI | o1-preview | 0.50 | A | I | P | Q | M | AMRFinderPlus without --plus; no Prodigal; no PlasmidFinder |
| OpenAI | o1-mini | 0.10 | I | I | F | Q | N | Wrong tools; no AMR-specific pipeline |
| OpenAI | o1 | 0.60 | A | P | P | Q | M | AMRFinderPlus without --plus; no Prodigal; no PlasmidFinder |
| OpenAI | o1-pro | 0.90 | C | P | P | S | R | AMRFinderPlus --plus; Prodigal for ORFs; missed PlasmidFinder |
| OpenAI | o3-mini | 0.60 | A | P | P | Q | M | AMRFinderPlus on contigs only; no --plus; no Prodigal |
| OpenAI | o3 (high reasoning) | 0.70 | A | P | P | Q | R | AMRFinderPlus --plus; missed PlasmidFinder and VFDB screening |
| OpenAI | o4-mini | 0.60 | A | P | P | Q | M | AMRFinderPlus without --plus; missed components |
| OpenAI | GPT-5 | 0.90 | C | P | P | S | R | AMRFinderPlus --plus + Prodigal; missed PlasmidFinder |
| OpenAI | ChatGPT Deep Research | 1.00 | C | C | P | S | R | AMRFinderPlus --plus + Prodigal + VFDB + PlasmidFinder |
| Claude | Sonnet 3.5 | 0.10 | I | I | F | Q | N | Prokka only; no AMR tools; no virulence screening |
| Claude | Sonnet 4 | 0.60 | A | P | P | Q | M | AMRFinderPlus on contigs; no --plus; no Prodigal |
| Claude | Sonnet 4.5 | 0.60 | A | P | P | Q | M | AMRFinderPlus on contigs/bins; missed --plus and Prodigal |
| Claude | Haiku 4.5 | 0.70 | A | P | P | Q | R | AMRFinderPlus; CheckM2; missing components |
| Claude | Opus 4.5 | 0.90 | C | P | P | S | R | AMRFinderPlus --plus + Prodigal; missed PlasmidFinder |
| Claude | Opus 4.6 | 1.00 | C | C | P | S | R | AMRFinderPlus --plus + Prodigal + VFDB; noted plasmid mobility |
| Claude | Sonnet 4.6 | 0.90 | C | P | P | S | R | AMRFinderPlus --plus + Prodigal; missed PlasmidFinder |
| Claude | Claude Deep Research | 1.00 | C | C | P | S | R | Complete AMR + virulence + plasmid pipeline |
| Gemini | Gemini 2.0 Flash | 0.00 | I | I | F | I | N | Wrong tools; no AMR pipeline |
| Gemini | Gemini 2.5 Pro Preview | 0.70 | A | P | P | Q | R | AMRFinderPlus; missing components |
| Gemini | Gemini 2.5 Flash | 0.20 | A | I | F | Q | N | AMRFinderPlus contigs only; wrong flags |
| Gemini | Gemini 2.5 Pro | 0.70 | A | P | P | Q | R | AMRFinderPlus; contigs and bins; missed --plus |
| Gemini | Gemini 3 Pro | 0.90 | C | P | P | S | R | AMRFinderPlus --plus + Prodigal; missed PlasmidFinder |
| Gemini | Gemini 3 Flash | 0.60 | A | P | P | Q | M | AMRFinderPlus; missed read-level; wrong flags |
| Gemini | Gemini 3.1 Pro | 0.90 | C | P | P | S | R | AMRFinderPlus --plus + Prodigal; noted VFDB |
| Google | Gemini Deep Research | 1.00 | C | C | P | S | R | Complete AMR + virulence + plasmid pipeline |
| DeepSeek | DeepSeek V3 | 0.00 | I | I | F | I | N | Wrong flags; generated wildcards; broken code |
| Zhipu | GLM-5 | 0.60 | A | P | P | Q | M | Some AMR tools; incomplete |
