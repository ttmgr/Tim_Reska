# Evaluation Summary

## Overview

The current benchmark covers 28 evaluated entries across 7 pipeline stages, yielding 196 scored step-results. The matrix remains consistent with the main finding of the project: local plausibility is not sufficient for end-to-end scientific validity. Quality control and taxonomic classification are now handled well by many modern systems, but assembly, binning, and functional annotation still expose persistent weaknesses in multi-step reasoning and domain-specific parameter choice.

The public prompt files that accompany this benchmark are reconstructed documentation artifacts, not raw transcript exports. Where the evaluated setup made a score-relevant requirement explicit, the prompt documentation records it directly.

## Key Findings

### First fully correct pipeline per family

| Model Family | First Fully Correct Version | Notes |
|:-------------|:----------------------------|:------|
| OpenAI | GPT-5 | First OpenAI entry with a fully correct 7-step pipeline; later matched by ChatGPT Deep Research |
| Claude | Opus 4.5 | First Claude core version to reach full correctness; later matched by Opus 4.6, Sonnet 4.6, and Claude Deep Research |
| Gemini | 3 Pro | First Gemini core version to reach full correctness; later matched by Gemini 3.1 Pro |
| Google | Gemini Deep Research | Singleton interface evaluation; fully correct in the current matrix |
| DeepSeek | None | No fully correct end-to-end pipeline in the current matrix |
| Zhipu | None | No fully correct end-to-end pipeline in the current matrix |

### Hardest step across all evaluated entries

`Binning` has the lowest average composite score in the current matrix (`0.59`). The next most difficult steps are `Assembly` (`0.63`) and `Functional annotation` (`0.62`). All three require stateful compatibility reasoning across multiple prior outputs rather than a single tool recommendation.

### Most common failure mode per step

| Step | Most Common Failure | Models Affected |
|:-----|:-------------------|:----------------|
| 1. Basecalling | Wrong ONT model, wrong Q threshold, or incomplete basecall → trim → filter chain | 17/28; e.g. GPT-4o, o1, o3-mini, Gemini 3 Flash |
| 2. Quality control | FastQC-first answers or incomplete nanopore-specific QC | 7/28; e.g. GPT-4o, o1-mini, Sonnet 3.5 |
| 3. Host depletion | Short-read aligner choice or missing sample-context reasoning | 14/28; e.g. GPT-4o, o1-preview, o1-mini, Gemini 3 Flash |
| 4. Taxonomic classification | Wrong Kraken2 database or missing report/output flags | 13/28; e.g. GPT-4o, o1-preview, o4-mini, Gemini 3 Flash |
| 5. Assembly | Short-read assembler recommendation or omission of 3x Racon polishing | 17/28; e.g. GPT-4o, o1-preview, Sonnet 4, Gemini 2.5 Flash |
| 6. Binning | Overly strict completeness thresholds, broken binning order, or missing ensemble logic | 19/28; e.g. GPT-4o, o1, o4-mini, Gemini 2.5 Pro |
| 7. Functional annotation | Contigs-only annotation, missing `seqkit`, or missing multi-level AMR screening | 19/28; e.g. GPT-4o, o1, Sonnet 4.5, Gemini 3 Flash |

### Error compounding

The compounding pattern is most visible when an upstream answer changes the expected object type for the next stage. A short-read assembly recommendation in step 5 produces the wrong contig assumptions for step 6; a contigs-only annotation plan in step 7 usually reflects the fact that the model never preserved the read-level branch of the pipeline at all. Because the benchmark carries forward prior state into fresh prompts without correcting mistakes, early errors remain visible downstream as chaining failures rather than being masked by later restarts.

## Scoring Heatmap

![Scoring heatmap](../results/figures/scoring_heatmap.png)

The heatmap shows a clear stratification. Older or weaker entries cluster red across assembly, binning, and annotation, while later core models and several interface evaluations converge on full-green profiles. The main transition is not from “cannot write code” to “can write code”; it is from partial tool recall to full workflow compatibility.

## Conclusions

These results support a narrow but important claim: modern LLMs can now produce fully correct nanopore metagenomics pipelines under expert-controlled prompting, but that capability is neither historically stable nor uniformly distributed across model families or interfaces. For scientific users, the benchmark therefore argues against treating fluent code generation as a proxy for analytical correctness. Verification remains necessary at the level of tool choice, parameters, file chaining, and biological interpretation.

## Recommendations

- Use LLMs as drafting and comparison tools, not as unreviewed pipeline authors.
- Inspect assembly, binning, and annotation steps with the highest scrutiny; those stages remain the main failure surface.
- Validate database choice, ONT chemistry assumptions, and file-format transitions explicitly.
- Preserve a human-maintained ground truth when benchmarking domain-specific pipeline generation.
- Re-run the benchmark whenever the evaluated interface or model family changes; the matrix is a dated snapshot, not a permanent ranking.
