# Evaluation Framework

## Objective

Assess whether current large language models can produce a correct, end-to-end nanopore metagenomics pipeline through sequential prompting in a way that preserves scientific validity across chained workflow stages.

## Why sequential evaluation is necessary

Standard code benchmarks evaluate isolated units. That misses the main failure surface of bioinformatics pipelines: **compositional correctness**. In a real workflow, each step constrains the next through file formats, assumptions, tool compatibility, and biological context.

A model can therefore fail even when an individual command looks plausible:

- the basecalling output is not compatible with the downstream trimming step
- the wrong Kraken2 database makes later taxonomic summaries misleading
- the assembly choice invalidates binning assumptions
- the annotation stage loses the read-level branch required by the validated pipeline

These are chaining failures, not syntax failures.

## Protocol

### Ground truth

The benchmark is anchored to the validated aerobiome workflow described in:

> Reska T, Pozdniakova S, Urban L. *Air monitoring by nanopore sequencing*. ISME Communications (2024). DOI: [10.1093/ismeco/ycae058](https://doi.org/10.1093/ismeco/ycae058)

The public reference implementation is summarized in [`pipeline_reference.md`](pipeline_reference.md) and cross-linked to the local [`../pipelines/aerobiome/`](../pipelines/aerobiome/) workflow.

### Stateless cumulative prompting

This benchmark does **not** use one continuous conversation thread per model. Instead, it uses a stateless fresh-chat protocol:

1. Individual steps are first evaluated in isolated fresh sessions.
2. Integration prompts are then reconstructed cumulatively from the expected prior output state.
3. The evaluator manually passes forward the output type and biological context required for the next step.
4. Errors are not corrected before the next prompt, allowing upstream mistakes to propagate.

This design isolates a specific scientific question: can a model preserve correctness when prior state must be carried forward explicitly rather than being rediscovered or silently repaired?

### Controls

- **Prompt structure matched across evaluated entries.** Public prompt files document the reconstructed prompt shape for each step.
- **Benchmark-critical constraints preserved.** Score-relevant constraints that were explicit in the benchmark setup are documented in the reconstructed public prompt files.
- **No mid-benchmark correction.** Once an upstream error appears, it is preserved in the carried state.
- **Five-dimensional scoring.** Each step is evaluated for tool selection, parameter accuracy, output compatibility, scientific validity, and executability.

## Scoring Dimensions

| Dimension | What it measures | Why it matters |
|:----------|:-----------------|:---------------|
| Tool Selection | Conceptual workflow choice | Wrong tool selection invalidates the analysis even if the code runs |
| Parameter Accuracy | Domain-specific implementation detail | Correct tool with wrong flags can still produce misleading outputs |
| Output Compatibility | File and pipeline chaining | A pipeline can fail even when every individual command is plausible |
| Scientific Validity | Analytical defensibility | Fluency is not a substitute for domain judgment |
| Executability | Practical utility | Non-running code is unusable regardless of analytical intent |

The detailed rubric is in [`scoring_criteria.md`](scoring_criteria.md).

## Public Artifact Boundaries

This repository contains:

- the validated reference workflow
- reconstructed public prompt documents
- the scored matrix in `results/tables/scoring_matrix.csv`
- generated summaries and figures derived from that matrix

This repository does **not** contain:

- verbatim raw web-interface chat transcripts
- a complete archive of raw model response logs

The `responses/` directory is retained as a scaffold, but it is not a public transcript archive in the current checked-in tree.

The prompt reconstructions are benchmark documentation, not transcript surrogates. When the evaluated setup made a score-relevant requirement explicit, the public prompt files record that requirement. This documentation clarification does not modify the matrix, rankings, or rubric outcomes.

## Access Method

The evaluated outputs were collected through public interfaces rather than API-only execution environments. Results should therefore be interpreted as interface-level benchmark behavior rather than as a claim about any one provider's raw model endpoint under fixed API parameters.

## Limitations

- **Single reference pipeline:** the benchmark covers one validated nanopore metagenomics workflow.
- **Single-domain scope:** the results should not be generalized automatically to other sequencing modalities or analytical domains.
- **Dated snapshot:** the scoring matrix reflects tested behavior at specific dates.
- **Human scoring:** the rubric was applied by a single domain expert.
- **Protocol dependence:** the benchmark measures performance under stateless state-carrying prompts; other prompting regimes may differ.
