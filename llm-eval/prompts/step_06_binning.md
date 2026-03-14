# Step 6: Binning and MAG Quality Assessment

## Metadata

- **Step Number:** 6
- **Step Name:** Binning and MAG quality assessment
- **Objective:** Group contigs into MAGs and assess completeness and contamination using thresholds appropriate to low-biomass environmental data
- **Context Provided:** Polished assembly plus the need to preserve compatibility with the prior assembly output
- **Constraints:** Must include ensemble binning plus quality-assessment logic, and must reflect the low-biomass thresholding used in the validated workflow

## Provenance Note

The prompt text below is a reconstruction derived from the preserved metadata, the aerobiome reference pipeline, and the scored notes in `results/tables/scoring_matrix.csv`. It is not a verbatim export of the original chat prompt.

## Prompt Text

> Write the binning stage for the assembled nanopore metagenomics contigs. Use an approach appropriate for environmental mixed-community data, include MAG quality assessment, and choose completeness and contamination thresholds that are defensible for low-biomass air samples rather than high-coverage isolate genomes.

## Benchmark-Critical Constraints

- The validated workflow uses metaWRAP ensemble binning rather than a single standalone binning tool.
- Quality assessment is required and is performed with CheckM.
- Low-biomass air samples use permissive MAG thresholds: at least 30% completeness and at most 10% contamination.
- The answer should preserve the expected order of coverage estimation, binning/refinement, and quality assessment so later annotation remains compatible.

## Expected Ground Truth Response

**Binning tool:** metaWRAP with MetaBAT2, MaxBin2, and CONCOCT

**Quality assessment:** CheckM

**Critical parameters:**
- permissive completeness threshold of at least 30%
- contamination threshold of at most 10%
- explicit awareness that low-biomass samples require looser thresholds than typical high-coverage MAG studies

**Output format:** Refined bins plus quality reports

## Known Failure Modes Observed

- Returning a single-tool binning answer rather than an ensemble approach
- Using completeness thresholds such as 50%, 70%, or 90% without low-biomass justification
- Omitting quality assessment entirely
- Breaking the expected order between coverage estimation, binning, and refinement
- Failing to connect the answer to the output state produced by the assembly stage

## Notes

Binning has the lowest average composite score in the current matrix (`0.59`). Coverage estimation, binning order, and threshold choice remain common failure points.
