# LLM Cost Calculator

**Model the economics of LLM deployment before you commit.**

A Python library and CLI for estimating the total cost of deploying LLM-powered workflows in production. Takes a workload specification (model, tokens per request, daily volume) and returns cost projections with Monte Carlo sensitivity analysis and ROI calculation against manual baselines.

Built by Tim Reska ([Helmholtz AI / Pioneer Campus / TU Munich](https://www.helmholtz.ai/))

---

## What it does

- **Cost estimation** for API-hosted and self-hosted LLMs across providers
- **Multi-model comparison** to find the best price/performance point
- **Monte Carlo sensitivity analysis** varying volume, token length, and pricing
- **ROI calculator** comparing manual process costs to LLM-augmented workflows
- **Report generation** in Markdown and plain text

## Quick start

```bash
# Clone and install
git clone https://github.com/timreska/llm-cost-calculator.git
cd llm-cost-calculator
pip install -e ".[dev]"

# Estimate cost for a single model
python -m src.calculator \
    --model mistral-large-latest \
    --input-tokens 500 \
    --output-tokens 200 \
    --requests-per-day 1000

# Compare multiple models
python -m src.calculator \
    --compare mistral-large-latest,gpt-4o,claude-sonnet-4 \
    --input-tokens 500 \
    --output-tokens 200 \
    --requests-per-day 1000

# Run sensitivity analysis
python -m src.sensitivity \
    --model mistral-large-latest \
    --input-tokens 500 \
    --output-tokens 200 \
    --requests-per-day 1000

# Calculate ROI vs manual process
python -m src.roi \
    --model mistral-large-latest \
    --input-tokens 500 \
    --output-tokens 200 \
    --manual-cost 5.00 \
    --tasks-per-month 30000

# Run tests
pytest
```

## Supported models

### Mistral AI
| Model | Input ($/1M tokens) | Output ($/1M tokens) |
|-------|--------------------:|---------------------:|
| Mistral Small | $0.10 | $0.30 |
| Mistral Medium | $2.70 | $8.10 |
| Mistral Large | $2.00 | $6.00 |
| Codestral | $0.30 | $0.90 |

### OpenAI
| Model | Input ($/1M tokens) | Output ($/1M tokens) |
|-------|--------------------:|---------------------:|
| GPT-4o | $2.50 | $10.00 |
| GPT-4o Mini | $0.15 | $0.60 |
| o3 | $10.00 | $40.00 |

### Anthropic
| Model | Input ($/1M tokens) | Output ($/1M tokens) |
|-------|--------------------:|---------------------:|
| Claude Sonnet 4 | $3.00 | $15.00 |
| Claude Haiku 3.5 | $0.80 | $4.00 |

### Google
| Model | Input ($/1M tokens) | Output ($/1M tokens) |
|-------|--------------------:|---------------------:|
| Gemini 2.5 Pro | $1.25 | $10.00 |
| Gemini 2.5 Flash | $0.15 | $0.60 |

### Self-Hosted
| Model | GPU Cost/hr | Throughput |
|-------|------------:|-----------:|
| Llama 3.1 70B (A100) | $2.00 | ~500 tok/s |
| Mistral 7B (A10G) | $1.00 | ~800 tok/s |

All pricing sourced from public API documentation. Self-hosted estimates assume single-GPU inference with 20% orchestration overhead.

## Cost model explained

### API-hosted models

```
monthly_cost = (monthly_input_tokens / 1M * input_price)
             + (monthly_output_tokens / 1M * output_price)

where:
    monthly_input_tokens  = requests_per_day * days_per_month * avg_input_tokens
    monthly_output_tokens = requests_per_day * days_per_month * avg_output_tokens
```

### Self-hosted models

```
gpu_hours  = total_tokens / tokens_per_second / 3600
base_cost  = gpu_hours * gpu_cost_per_hour
total_cost = base_cost * (1 + overhead_fraction)
```

The overhead fraction (default 20%) accounts for orchestration, monitoring, load balancing, and idle GPU time.

## Sensitivity analysis

Monte Carlo simulation (default 1,000 runs) samples from uniform distributions around each parameter:

| Parameter | Default variation |
|-----------|------------------:|
| Request volume | +/- 50% |
| Token length | +/- 30% |
| Price changes | +/- 20% |

Reports P10, P50, and P90 cost projections. P90 represents the pessimistic scenario you should budget for; P10 is the optimistic case.

## ROI calculator

Compares the fully loaded cost of a manual process against an LLM-augmented workflow:

```
manual_cost       = cost_per_task * tasks_per_month
augmented_cost    = llm_api_cost + (review_fraction * tasks * review_cost_per_item)
monthly_savings   = manual_cost - augmented_cost
annual_roi        = (annual_savings / annual_augmented_cost) * 100
payback_months    = first_month_augmented_cost / monthly_savings
```

The `human_review_fraction` parameter captures the reality that most LLM deployments require some human-in-the-loop review. Set it to 0 for fully automated workflows.

## Adding custom models

Edit `configs/pricing_2026.yml` to add new models:

```yaml
providers:
  your-provider:
    display_name: Your Provider
    models:
      your-model-id:
        display_name: Your Model Name
        input_per_1m: 1.0
        output_per_1m: 3.0
        type: api
```

For self-hosted models, specify GPU economics instead:

```yaml
      your-self-hosted-model:
        display_name: Your Model (GPU Type)
        type: self_hosted
        gpu_cost_per_hour: 2.0
        tokens_per_second: 500
        overhead_fraction: 0.20
```

## Project structure

```
llm-cost-calculator/
├── src/
│   ├── __init__.py          # Package metadata
│   ├── pricing.py           # YAML pricing database loader
│   ├── calculator.py        # Cost estimation engine + CLI
│   ├── sensitivity.py       # Monte Carlo sensitivity analysis + CLI
│   ├── roi.py               # ROI calculator + CLI
│   └── report.py            # Markdown and text report generation
├── configs/
│   └── pricing_2026.yml     # Model pricing data
├── tests/
│   ├── test_calculator.py   # Cost calculation tests
│   ├── test_sensitivity.py  # Monte Carlo tests
│   └── test_roi.py          # ROI calculation tests
├── pyproject.toml
├── LICENSE                  # MIT
└── README.md
```

## Dependencies

- Python 3.10+
- PyYAML
- NumPy

No heavy frameworks. Install with `pip install -e ".[dev]"` for development (adds pytest).

## License

MIT License. Copyright (c) 2026 Tim Reska.
