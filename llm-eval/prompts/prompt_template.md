# Prompt Documentation Template

Use this file as the structure for public prompt documentation in this repository.

## Required sections

### Metadata

Document the following fields explicitly:

- Step number
- Step name
- Objective
- Context provided to the model
- Constraints imposed on the response

### Provenance note

State whether the prompt text is:

- a verbatim preserved prompt, or
- a reconstruction derived from metadata, the reference pipeline, and scored notes

For the current public `llm-eval` repository, reconstructed prompts should be labeled clearly as reconstructions.

### Prompt text

Write the exact public prompt block shown to readers. If the original verbatim chat prompt is unavailable, provide a concise reconstruction that preserves:

- the biological context
- the expected input object
- the output required for the next pipeline stage
- any critical constraints such as ONT chemistry, database choice, or file-format expectations

### Expected ground truth response

Summarize:

- expected tools
- critical parameters
- expected output format
- any acceptable alternatives that still preserve scientific validity

### Known failure modes observed

List the dominant failure patterns actually observed in the matrix notes. Focus on recurring analytical mistakes rather than one-off phrasing issues.

### Notes

Capture any prompt-specific caveats, such as:

- whether the step was explicit or implicit in the published workflow
- whether scientifically acceptable alternatives exist
- whether this stage is unusually sensitive to upstream state poisoning
