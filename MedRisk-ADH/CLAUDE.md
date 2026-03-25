# CLAUDE.md

## Project
MedRisk-ADH — AI-driven medical underwriting with confidence-calibrated failure mode detection. Proof-of-concept demonstrating plausible-but-wrong (PBW) detection for automated underwriting decisions.

## Commands
- `make install` — install package in dev mode
- `make test` — run all tests (pytest)
- `make lint` — run linter (ruff)
- `make notebooks` — execute all 5 Jupyter notebooks

## Architecture
- `src/medrisk/data/` — schemas, ICD-10 codelist, Charlson CCI, synthetic cohort generator
- `src/medrisk/features/` — ICD-10 encoding, feature matrix construction
- `src/medrisk/models/` — XGBoost classifier, Cox PH survival, CTMC multistate Markov, disease config registry
- `src/medrisk/validation/` — DQS (Data Quality Score), CCM, EPU, PBW failure detection
- `src/medrisk/explain/` — SHAP explainability layer
- `src/medrisk/reporting/` — PDF report generation
- `src/medrisk/evaluation/` — discrimination and calibration metrics

## Conventions
- Python 3.11+, hatchling build
- Type hints, Google-style docstrings, logging not prints
- ruff for linting, pytest for testing

## Subagent Patterns: Testing

Use these patterns when asked to "run tests", "validate the project", or "check everything works".

### Full validation (deploy as subagents)
Phase 1 — run in parallel:
- **Unit tests**: `make test` — expect 231 tests, ~15s. Report any failures with file:line.
- **Lint**: `make lint` — expect clean. Fix violations with `make format` then re-run.

Phase 2 — run in parallel after Phase 1 passes:
- **Integration test**: Run full pipeline in Python:
  `generate_cohort(n_per_market=100)` → `cohort_to_dataframe` → `build_feature_matrix` →
  `RiskClassifier().fit()` → `compute_dqs()` per patient → `batch_detect()`.
  Verify: no exceptions, output shapes match, all 3 recommendation tiers represented.
- **Notebook validation**: `make notebooks` — all 5 must execute without error.
  If a notebook fails, report the cell number and traceback.
- **Slide deck**: `python scripts/generate_slides.py` — must produce
  `data/reports/medrisk_adh_deck.pdf`. Verify file exists, 10 pages, size > 50KB.

### Individual patterns
- Fix failing test: Run `pytest tests/test_<module>.py -v`, read traceback,
  fix source in `src/medrisk/`, re-run to confirm.
- SHAP tests (gap): No tests exist for `src/medrisk/explain/shap_layer.py`.
  If writing tests, follow `tests/test_xgb_classifier.py` pattern.

## Subagent Patterns: Medical Data Research

These agents research external medical data. They produce reports, NOT code changes.
Deploy individually or all four in parallel — they are fully independent.

- **ICD-10 validation**: Verify 56 codes in `src/medrisk/data/icd10.py` CODELIST against
  WHO ICD-10 2019 + ICD-10-GM (DE market). Flag deprecated codes, ICD-10-CM vs GM
  divergences. Output: markdown table of code, status, notes.
- **Epidemiological data**: Compare 28 prevalence rates in `src/medrisk/data/synthetic.py`
  BASELINE_PREVALENCE against GBD 2019, RKI DEGS1, Eurostat. Flag >50% discrepancies.
  Output: table of condition, our rate, published rate, source.
- **Data source scouting**: Research Phase 2 data sources: InGef, GePaRD (BIPS), PKV
  Verband, SNIIRAM (France), CMBD (Spain), CPRD (UK). For each: coverage, time span,
  data elements, access process, timeline, cost estimate.
- **Literature**: Search 2023-2026 for PBW detection in medical AI, confidence calibration
  in underwriting, DQS frameworks, epistemic uncertainty in clinical prediction.
  Output: citation, relevance (1-5), 2-sentence summary.

## Subagent Patterns: Literature Research & Fact-Checking

Deploy all 3 agents in parallel after adding or modifying any disease module,
clinical data, or biomarker definitions. They produce reports, NOT code changes.

### Source hierarchy & methodology

Agents MUST use these tools and source priorities:

**Primary sources (use WebFetch to query directly):**
- PubMed E-utilities (free, no API key): search via
  `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&term=<QUERY>`
  then fetch abstracts via
  `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=<PMID>&rettype=abstract&retmode=text`
  Prefer systematic reviews and meta-analyses: append `AND (systematic+review[pt] OR meta-analysis[pt])`.
- PubMed Central full text: `https://www.ncbi.nlm.nih.gov/pmc/articles/PMC<ID>/`
- LOINC registry: `https://loinc.org/<CODE>` (verify observation codes)
- WHO ATC/DDD Index: `https://atcddd.fhi.no/atc_ddd_index/?code=<CODE>`
- ICD-10 registries: `https://www.icd10data.com/ICD10CM/Codes/` (CM),
  `https://www.icd-code.de/icd/code/<CODE>.html` (GM)
- GBD Results: `https://vizhub.healthdata.org/gbd-results/` (prevalence data)

**Secondary sources (use WebSearch):**
- Cochrane Library, Lancet, NEJM, JAMA, BMJ (via web search)
- Alzheimer's Association Facts & Figures
- RKI DEGS1 / Gesundheitsberichterstattung
- Eurostat health statistics

**Evidence grading** (report alongside each finding):
- Level 1: Cochrane review / meta-analysis of RCTs
- Level 2: Meta-analysis of observational studies
- Level 3: Individual large cohort study (ADNI, NACC, Framingham)
- Level 4: Expert consensus / clinical guidelines (NIA-AA, IWG)
- Level 5: Textbook / association website (alz.org, WHO)

**Minimum verification**: Each clinical claim must have >= 2 independent sources.
Flag any claim with only 1 source or only Level 5 evidence.

### Agent 1: Clinical Fact-Checker

Read `src/medrisk/models/disease_configs.py` and `src/medrisk/data/synthetic.py`.
For EACH clinical number:
1. Search PubMed via E-utilities for systematic reviews / meta-analyses first
2. Fetch abstracts for top 3-5 results, extract the relevant statistic
3. Cross-check with a second source via WebSearch
4. Report: our value, published value(s), PMID(s), evidence level, severity

Check these categories:
- CTMC transition rates (mean sojourn times vs published stage durations)
- Biomarker reference ranges (means, SDs, cutoffs vs published norms)
- Prevalence rates (vs Alzheimer's Association, GBD 2019, RKI)
- Risk factor multipliers (vs meta-analyses — cite pooled OR/RR/HR)
- Medication ATC codes and typical dosing
- ApoE4 carrier frequency and effect size on progression

Output: severity-rated table (CRITICAL / WARNING / OK) with our value,
published value, PMID or DOI, evidence level, suggested fix.

### Agent 2: Medical Code Validator

Read `src/medrisk/data/icd10.py`, `src/medrisk/data/charlson.py`,
`src/medrisk/data/synthetic.py`.

For EACH code, use WebFetch against the authoritative registry:
- ICD-10: fetch from icd10data.com (CM) AND icd-code.de (GM). Verify code
  exists, description matches, flag codes absent from one system.
- LOINC: fetch from loinc.org. Verify it is an observation code (NOT an
  LP-prefixed Part code). Check component, property, system, scale.
- ATC: fetch from WHO ATC/DDD Index. Verify drug name mapping.
- Charlson: verify prefix-based matching covers all registered codes.

Output: code-by-code table with status (CORRECT/WARNING/WRONG),
our description vs official, which systems have it.

### Agent 3: Code Consistency Checker

Read all `src/medrisk/` files and `app/` files.
Check cross-module consistency:
- Category reclassification impacts (grep `get_codes_by_category` calls)
- BASELINE_PREVALENCE keys propagation to `cohort_to_dataframe`, `build_feature_matrix`
- Schema validator `valid_events` alignment with all config `event_types`
- Lab value clamping (score-type labs capped at valid range, no negative values)
- ATC/ICD-10 regex pattern matching against schema validators
- Import patterns in app pages (consistent with existing pages)
- No hardcoded column lists that would miss new features

Output: severity-rated issue list (CRITICAL / WARNING / NOTE) with file:line.

## Subagent Patterns: MBB Presentation Design

Deploy when creating or reviewing pitch decks, PDFs, or PPTX presentations.
Full design system documented in `~/.claude/skills/mbb-slides.md`.

Key rules for the agent prompt:
- **Action titles**: every slide title is a complete sentence stating the takeaway
  (BAD: "Architecture" / GOOD: "Each pipeline stage adds a measurable quality gate")
- **One message per slide**: if a slide makes two points, split it
- **SCR flow**: Situation → Complication → Resolution → Next Steps
- **Data density**: max 5 bullets, every bullet has a number, every chart has a source
- **3-color palette**: navy #0D2339, accent #107ACA, highlight #028901. Red #D00D00 for problems only.
- **Visual hierarchy**: title (28-32pt) → key visual → source line (8pt). No fourth layer.
- **Flowcharts**: max 6 boxes, one direction, 60-70% slide width

Agent should read `scripts/generate_all.py`, apply all rules from the skill file,
rewrite titles as action titles, and rebalance content density.

## Subagent Patterns: Reporting

### Deployment
Phase 1 — run in parallel:
- **PDF deck**: `python scripts/generate_slides.py` → verify `data/reports/medrisk_adh_deck.pdf`
  exists, 10 pages, >50KB. Fix and re-run if it fails.
- **Metrics report**: Generate 5000-patient DE cohort (seed=42), train XGB + Cox PH,
  compute AUC-ROC, Brier score, concordance index. Run DQS + failure detection.
  Output: markdown metrics table with PBW flag rates by market, DQS distribution summary.

Phase 2 — sequential, after Phase 1:
- **Documentation**: Verify README test count, ROADMAP phase status, `docs/failure_modes.md`
  equations match implementation in `src/medrisk/validation/`. Report discrepancies
  before editing.
