# AI Deployment Readiness Assessment

**A lightweight self-assessment tool for organizations evaluating AI deployment.**

Answer 25 concrete questions across five dimensions and receive an AI maturity score, a benchmark comparison against your industry sector, and prioritised recommendations for closing gaps.

## What it does

The tool guides an organization through a structured self-assessment and produces:

- A **maturity score** (1.0--5.0) across five dimensions drawn from published AI maturity literature.
- A **maturity tier** label: Exploring, Piloting, Scaling, or Optimizing.
- A **sector benchmark comparison** against synthetic industry averages derived from publicly available survey data (McKinsey, Stanford HAI, Gartner).
- Three **prioritised recommendations** targeting the lowest-scoring dimensions.

No data leaves your machine. No API keys required. Pure Python, zero dependencies.

## Quick start

```bash
# Clone and enter the repo
git clone https://github.com/timreska/ai-deployment-readiness.git
cd ai-deployment-readiness

# Run the interactive questionnaire
python -m src.questionnaire

# Or run with pre-filled demo answers
python -m src.questionnaire --demo

# Run tests
pip install pytest
pytest
```

Requires Python 3.10+.

## Dimensions explained

The assessment covers five dimensions that the academic and practitioner literature consistently identifies as prerequisites for successful AI deployment:

1. **Data Infrastructure & Quality** -- Whether the organization has governed, accessible, and version-controlled data assets that can support analytical and ML workloads.

2. **Process Maturity & Documentation** -- Whether core business processes are documented, measured, and structured enough to identify where AI adds value (and where it does not).

3. **Governance & Compliance Readiness** -- Whether policies, review processes, and incident-response procedures exist to deploy AI responsibly and within regulatory constraints.

4. **AI Talent & Skills** -- Whether the organization has the technical depth to build and operate AI systems and the organizational breadth to adopt them.

5. **Executive Sponsorship & Change Management** -- Whether leadership commitment, budget allocation, and internal communication are sufficient to move AI from pilots to production.

## How scoring works

Each of the 25 questions is answered on a 1--5 Likert scale with concrete anchors (e.g., "No data dictionary exists" to "Comprehensive, auto-updated dictionary"). Within each dimension, questions are weighted by their relative importance to overall readiness. The per-dimension score is a weighted average; the overall score is the mean of the five dimension scores.

Maturity tiers:

| Score range | Tier | Interpretation |
|---|---|---|
| 1.0--2.0 | Exploring | AI interest exists but no structured capability |
| 2.0--3.0 | Piloting | Isolated experiments; not yet embedded in operations |
| 3.0--4.0 | Scaling | AI in production for select use cases; governance emerging |
| 4.0--5.0 | Optimizing | AI integrated across the organisation with mature governance |

Sector benchmarks are synthetic approximations reflecting the relative ordering and rough magnitude reported in McKinsey "The State of AI" (2023), Stanford HAI AI Index Report (2024), and the Gartner AI Maturity Model (2023).

## Adapting to your context

This tool is deliberately generic. To adapt it to a specific organization:

- **Adjust question weights** in `src/scorer.py` to reflect which factors matter most in your industry.
- **Add sector benchmarks** in `src/benchmarks.py` using your own survey data or published reports.
- **Extend the question bank** in `src/questionnaire.py` with domain-specific questions (e.g., FDA compliance for pharma, SOC 2 for SaaS).
- **Integrate with your workflow** by importing the scoring functions directly rather than using the CLI.

## License

MIT. See [LICENSE](LICENSE).

---

For comprehensive AI deployment due diligence with governance mapping and implementation roadmaps, engage a specialist firm.

Built by Tim Reska (Helmholtz AI / TU Munich).
