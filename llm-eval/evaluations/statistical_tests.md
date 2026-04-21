# Statistical Comparisons of LLM Performance

Two complementary test families are reported for each comparison × pipeline scope.

---

## A — Non-Parametric Tests (model-level means)

**Unit:** each model is reduced to one composite mean score per scope.  
**Omnibus:** Kruskal-Wallis H.  
**Post-hoc:** Dunn's test (Holm correction, only when KW p < 0.05).  
**Effect size:** Cliff's δ (negligible < 0.147 ≤ small < 0.33 ≤ medium < 0.474 ≤ large).  
**CI:** bootstrap 95%, 1 000 iterations.

> **Small-n caveat:** sub-tier groups have n = 3–4 models. Tests are indicative only for those comparisons.


### Company (OpenAI vs Anthropic vs Google)

#### Pooled

| Group | n | Mean ± SD | 95% CI |
|-------|---|-----------|--------|
| OpenAI | 10 | 0.604 ± 0.308 | [0.404, 0.765] |
| Anthropic | 8 | 0.760 ± 0.227 | [0.598, 0.887] |
| Google | 8 | 0.690 ± 0.317 | [0.465, 0.864] |

**Kruskal-Wallis:** H = 1.341, p = 0.5114 (not significant)

| Pair | Cliff's δ | Magnitude | MWU p | Dunn p (Holm) | Sig |
|------|-----------|-----------|-------|---------------|-----|
| OpenAI vs Anthropic | -0.338 | medium | 0.2468 | — | ns |
| OpenAI vs Google | -0.175 | small | 0.5632 | — | ns |
| Anthropic vs Google | +0.094 | negligible | 0.7920 | — | ns |

#### Aerobiome

| Group | n | Mean ± SD | 95% CI |
|-------|---|-----------|--------|
| OpenAI | 10 | 0.674 ± 0.315 | [0.469, 0.841] |
| Anthropic | 8 | 0.821 ± 0.253 | [0.637, 0.957] |
| Google | 8 | 0.766 ± 0.337 | [0.521, 0.945] |

**Kruskal-Wallis:** H = 1.945, p = 0.3782 (not significant)

| Pair | Cliff's δ | Magnitude | MWU p | Dunn p (Holm) | Sig |
|------|-----------|-----------|-------|---------------|-----|
| OpenAI vs Anthropic | -0.388 | medium | 0.1744 | — | ns |
| OpenAI vs Google | -0.225 | small | 0.4449 | — | ns |
| Anthropic vs Google | +0.109 | negligible | 0.7420 | — | ns |

#### Wetland

| Group | n | Mean ± SD | 95% CI |
|-------|---|-----------|--------|
| OpenAI | 10 | 0.554 ± 0.305 | [0.360, 0.715] |
| Anthropic | 8 | 0.718 ± 0.212 | [0.571, 0.838] |
| Google | 8 | 0.637 ± 0.304 | [0.426, 0.806] |

**Kruskal-Wallis:** H = 1.355, p = 0.5079 (not significant)

| Pair | Cliff's δ | Magnitude | MWU p | Dunn p (Holm) | Sig |
|------|-----------|-----------|-------|---------------|-----|
| OpenAI vs Anthropic | -0.350 | medium | 0.2289 | — | ns |
| OpenAI vs Google | -0.138 | negligible | 0.6564 | — | ns |
| Anthropic vs Google | +0.125 | negligible | 0.7120 | — | ns |


### Flash / Small Tier (ChatGPT-all vs Sonnet vs Gemini Flash)

#### Pooled

| Group | n | Mean ± SD | 95% CI |
|-------|---|-----------|--------|
| ChatGPT (all) | 10 | 0.604 ± 0.308 | [0.404, 0.765] |
| Sonnet | 4 | 0.625 ± 0.252 | [0.399, 0.838] |
| Gemini Flash | 3 | 0.369 ± 0.299 | [0.035, 0.612] |

**Kruskal-Wallis:** H = 1.925, p = 0.3820 (not significant)

| Pair | Cliff's δ | Magnitude | MWU p | Dunn p (Holm) | Sig |
|------|-----------|-----------|-------|---------------|-----|
| ChatGPT (all) vs Sonnet | -0.025 | negligible | 1.0000 | — | ns |
| ChatGPT (all) vs Gemini Flash | +0.533 | large | 0.2168 | — | ns |
| Sonnet vs Gemini Flash | +0.500 | large | 0.4000 | — | ns |

#### Aerobiome

| Group | n | Mean ± SD | 95% CI |
|-------|---|-----------|--------|
| ChatGPT (all) | 10 | 0.674 ± 0.315 | [0.469, 0.841] |
| Sonnet | 4 | 0.671 ± 0.294 | [0.396, 0.918] |
| Gemini Flash | 3 | 0.429 ± 0.347 | [0.043, 0.714] |

**Kruskal-Wallis:** H = 1.794, p = 0.4078 (not significant)

| Pair | Cliff's δ | Magnitude | MWU p | Dunn p (Holm) | Sig |
|------|-----------|-----------|-------|---------------|-----|
| ChatGPT (all) vs Sonnet | -0.075 | negligible | 0.8869 | — | ns |
| ChatGPT (all) vs Gemini Flash | +0.500 | large | 0.2354 | — | ns |
| Sonnet vs Gemini Flash | +0.500 | large | 0.4000 | — | ns |

#### Wetland

| Group | n | Mean ± SD | 95% CI |
|-------|---|-----------|--------|
| ChatGPT (all) | 10 | 0.554 ± 0.305 | [0.360, 0.715] |
| Sonnet | 4 | 0.593 ± 0.224 | [0.400, 0.782] |
| Gemini Flash | 3 | 0.327 ± 0.265 | [0.030, 0.540] |

**Kruskal-Wallis:** H = 2.517, p = 0.2840 (not significant)

| Pair | Cliff's δ | Magnitude | MWU p | Dunn p (Holm) | Sig |
|------|-----------|-----------|-------|---------------|-----|
| ChatGPT (all) vs Sonnet | -0.050 | negligible | 0.9435 | — | ns |
| ChatGPT (all) vs Gemini Flash | +0.567 | large | 0.1757 | — | ns |
| Sonnet vs Gemini Flash | +0.667 | large | 0.2286 | — | ns |


### Pro / Large Tier (ChatGPT-all vs Claude-all vs Gemini Pro)

#### Pooled

| Group | n | Mean ± SD | 95% CI |
|-------|---|-----------|--------|
| ChatGPT (all) | 10 | 0.604 ± 0.308 | [0.404, 0.765] |
| Claude (all) | 8 | 0.760 ± 0.227 | [0.598, 0.887] |
| Gemini Pro | 4 | 0.863 ± 0.076 | [0.803, 0.924] |

**Kruskal-Wallis:** H = 2.745, p = 0.2534 (not significant)

| Pair | Cliff's δ | Magnitude | MWU p | Dunn p (Holm) | Sig |
|------|-----------|-----------|-------|---------------|-----|
| ChatGPT (all) vs Claude (all) | -0.338 | medium | 0.2468 | — | ns |
| ChatGPT (all) vs Gemini Pro | -0.525 | large | 0.1568 | — | ns |
| Claude (all) vs Gemini Pro | -0.156 | small | 0.7318 | — | ns |

#### Aerobiome

| Group | n | Mean ± SD | 95% CI |
|-------|---|-----------|--------|
| ChatGPT (all) | 10 | 0.674 ± 0.315 | [0.469, 0.841] |
| Claude (all) | 8 | 0.821 ± 0.253 | [0.637, 0.957] |
| Gemini Pro | 4 | 0.961 ± 0.054 | [0.914, 1.000] |

**Kruskal-Wallis:** H = 4.000, p = 0.1353 (not significant)

| Pair | Cliff's δ | Magnitude | MWU p | Dunn p (Holm) | Sig |
|------|-----------|-----------|-------|---------------|-----|
| ChatGPT (all) vs Claude (all) | -0.388 | medium | 0.1744 | — | ns |
| ChatGPT (all) vs Gemini Pro | -0.625 | large | 0.0858 | — | ns |
| Claude (all) vs Gemini Pro | -0.219 | small | 0.5858 | — | ns |

#### Wetland

| Group | n | Mean ± SD | 95% CI |
|-------|---|-----------|--------|
| ChatGPT (all) | 10 | 0.554 ± 0.305 | [0.360, 0.715] |
| Claude (all) | 8 | 0.718 ± 0.212 | [0.571, 0.838] |
| Gemini Pro | 4 | 0.795 ± 0.093 | [0.720, 0.870] |

**Kruskal-Wallis:** H = 2.574, p = 0.2760 (not significant)

| Pair | Cliff's δ | Magnitude | MWU p | Dunn p (Holm) | Sig |
|------|-----------|-----------|-------|---------------|-----|
| ChatGPT (all) vs Claude (all) | -0.350 | medium | 0.2289 | — | ns |
| ChatGPT (all) vs Gemini Pro | -0.475 | large | 0.2026 | — | ns |
| Claude (all) vs Gemini Pro | -0.156 | small | 0.7318 | — | ns |

---

## B — Linear Mixed Effects Model (step-level, better powered)

**Model:** `composite ~ group + (1 | model)` — step-level scores as observations; model identity as random intercept to absorb within-model correlation.  
**Omnibus:** likelihood-ratio test (LRT) comparing full vs intercept-only model (both fitted with ML, not REML).  
**Pairwise:** binary LMM per pair (one group coded as indicator), Holm correction.  
**Coefficient (coef):** estimated mean difference (group B − group A) in composite score.

> The LMM uses all step-level observations (~17 per model) and is more powerful than KW for the company comparison (n ≈ 10/8/8 models). For Flash-tier (n = 10/4/3) and Pro-tier (n = 10/8/4), power gains are smaller because between-group inference still scales with the number of models, not steps.


### Company (OpenAI vs Anthropic vs Google)

#### Pooled

**LRT:** χ²(2) = 1.461, p = 0.4817 (not significant)  _(N = 442 step-scores, 26 models)_

| Pair | n models (A/B) | coef | SE | z | LMM p | Holm p | Sig |
|------|---------------|------|----|---|-------|--------|-----|
| OpenAI vs Anthropic | 10 / 8 | +0.157 | 0.123 | +1.27 | 0.2037 | 0.6111 | ns |
| OpenAI vs Google | 10 / 8 | +0.087 | 0.140 | +0.62 | 0.5333 | 1.0000 | ns |
| Anthropic vs Google | 8 / 8 | -0.070 | 0.129 | -0.54 | 0.5877 | 1.0000 | ns |

#### Aerobiome

**LRT:** χ²(2) = 1.189, p = 0.5517 (not significant)  _(N = 182 step-scores, 26 models)_

| Pair | n models (A/B) | coef | SE | z | LMM p | Holm p | Sig |
|------|---------------|------|----|---|-------|--------|-----|
| OpenAI vs Anthropic | 10 / 8 | +0.147 | 0.129 | +1.14 | 0.2558 | 0.7673 | ns |
| OpenAI vs Google | 10 / 8 | +0.092 | 0.145 | +0.63 | 0.5275 | 1.0000 | ns |
| Anthropic vs Google | 8 / 8 | -0.055 | 0.140 | -0.40 | 0.6917 | 1.0000 | ns |

#### Wetland

**LRT:** χ²(2) = 1.673, p = 0.4332 (not significant)  _(N = 260 step-scores, 26 models)_

| Pair | n models (A/B) | coef | SE | z | LMM p | Holm p | Sig |
|------|---------------|------|----|---|-------|--------|-----|
| OpenAI vs Anthropic | 10 / 8 | +0.163 | 0.120 | +1.36 | 0.1728 | 0.5184 | ns |
| OpenAI vs Google | 10 / 8 | +0.083 | 0.136 | +0.61 | 0.5399 | 1.0000 | ns |
| Anthropic vs Google | 8 / 8 | -0.080 | 0.122 | -0.65 | 0.5137 | 1.0000 | ns |


### Flash / Small Tier (ChatGPT-all vs Sonnet vs Gemini Flash)

#### Pooled

**LRT:** χ²(2) = 1.900, p = 0.3867 (not significant)  _(N = 289 step-scores, 17 models)_

| Pair | n models (A/B) | coef | SE | z | LMM p | Holm p | Sig |
|------|---------------|------|----|---|-------|--------|-----|
| ChatGPT (all) vs Sonnet | 10 / 4 | +0.021 | 0.162 | +0.13 | 0.8944 | 0.8944 | ns |
| ChatGPT (all) vs Gemini Flash | 10 / 3 | -0.235 | 0.186 | -1.27 | 0.2058 | 0.4315 | ns |
| Sonnet vs Gemini Flash | 4 / 3 | -0.256 | 0.175 | -1.46 | 0.1438 | 0.4315 | ns |

#### Aerobiome

**LRT:** χ²(2) = 1.720, p = 0.4231 (not significant)  _(N = 119 step-scores, 17 models)_

| Pair | n models (A/B) | coef | SE | z | LMM p | Holm p | Sig |
|------|---------------|------|----|---|-------|--------|-----|
| ChatGPT (all) vs Sonnet | 10 / 4 | -0.003 | 0.170 | -0.02 | 0.9866 | 0.9866 | ns |
| ChatGPT (all) vs Gemini Flash | 10 / 3 | -0.246 | 0.194 | -1.27 | 0.2058 | 0.6175 | ns |
| Sonnet vs Gemini Flash | 4 / 3 | -0.243 | 0.204 | -1.19 | 0.2343 | 0.6175 | ns |

#### Wetland

**LRT:** χ²(2) = 2.051, p = 0.3587 (not significant)  _(N = 170 step-scores, 17 models)_

| Pair | n models (A/B) | coef | SE | z | LMM p | Holm p | Sig |
|------|---------------|------|----|---|-------|--------|-----|
| ChatGPT (all) vs Sonnet | 10 / 4 | +0.039 | 0.157 | +0.25 | 0.8064 | 0.8064 | ns |
| ChatGPT (all) vs Gemini Flash | 10 / 3 | -0.227 | 0.181 | -1.26 | 0.2080 | 0.4159 | ns |
| Sonnet vs Gemini Flash | 4 / 3 | -0.266 | 0.156 | -1.71 | 0.0875 | 0.2624 | ns |


### Pro / Large Tier (ChatGPT-all vs Claude-all vs Gemini Pro)

#### Pooled

**LRT:** χ²(2) = 3.720, p = 0.1557 (not significant)  _(N = 374 step-scores, 22 models)_

| Pair | n models (A/B) | coef | SE | z | LMM p | Holm p | Sig |
|------|---------------|------|----|---|-------|--------|-----|
| ChatGPT (all) vs Claude (all) | 10 / 8 | +0.157 | 0.123 | +1.27 | 0.2037 | 0.4074 | ns |
| ChatGPT (all) vs Gemini Pro | 10 / 4 | +0.260 | 0.148 | +1.76 | 0.0788 | 0.2364 | ns |
| Claude (all) vs Gemini Pro | 8 / 4 | +0.103 | 0.109 | +0.95 | 0.3440 | 0.4074 | ns |

#### Aerobiome

**LRT:** χ²(2) = 3.822, p = 0.1479 (not significant)  _(N = 154 step-scores, 22 models)_

| Pair | n models (A/B) | coef | SE | z | LMM p | Holm p | Sig |
|------|---------------|------|----|---|-------|--------|-----|
| ChatGPT (all) vs Claude (all) | 10 / 8 | +0.147 | 0.129 | +1.14 | 0.2558 | 0.4892 | ns |
| ChatGPT (all) vs Gemini Pro | 10 / 4 | +0.286 | 0.150 | +1.91 | 0.0562 | 0.1686 | ns |
| Claude (all) vs Gemini Pro | 8 / 4 | +0.139 | 0.120 | +1.16 | 0.2446 | 0.4892 | ns |

#### Wetland

**LRT:** χ²(2) = 3.638, p = 0.1622 (not significant)  _(N = 220 step-scores, 22 models)_

| Pair | n models (A/B) | coef | SE | z | LMM p | Holm p | Sig |
|------|---------------|------|----|---|-------|--------|-----|
| ChatGPT (all) vs Claude (all) | 10 / 8 | +0.163 | 0.120 | +1.36 | 0.1728 | 0.3456 | ns |
| ChatGPT (all) vs Gemini Pro | 10 / 4 | +0.241 | 0.147 | +1.64 | 0.1009 | 0.3027 | ns |
| Claude (all) vs Gemini Pro | 8 / 4 | +0.078 | 0.103 | +0.75 | 0.4516 | 0.4516 | ns |


---

## C — Flagship Model Comparison

**Models:** GPT-5 (OpenAI) · Opus 4.6 (Anthropic) · Gemini 3.1 Pro (Google)  
**Unit:** step-level composite scores (n = 17 pooled / 7 aerobiome / 10 wetland per model).  
**Tests:** Kruskal-Wallis + Dunn post-hoc (Holm, when significant) + pairwise MWU + Cliff's δ.

> **Correlation caveat:** with only one model per group, steps within a model are not
> independent (same model applied to consecutive pipeline stages). p-values are
> therefore indicative of the direction and size of differences, not formal hypothesis
> tests. Interpret Cliff's δ as the primary measure of practical significance.

### Pooled

| Model | n steps | Mean ± SD |
|-------|---------|-----------|
| GPT-5 | 17 | 0.918 ± 0.159 |
| Opus 4.6 | 17 | 0.935 ± 0.132 |
| Gemini 3.1 Pro | 17 | 0.929 ± 0.131 |

**Kruskal-Wallis:** H = 0.141, p = 0.9319 (not significant)

| Pair | Cliff's δ | Magnitude | MWU p | Dunn p (Holm) | Sig |
|------|-----------|-----------|-------|---------------|-----|
| GPT-5 vs Opus 4.6 | -0.059 | negligible | 0.7396 | — | ns |
| GPT-5 vs Gemini 3.1 Pro | -0.010 | negligible | 0.9677 | — | ns |
| Opus 4.6 vs Gemini 3.1 Pro | +0.048 | negligible | 0.7869 | — | ns |

### Aerobiome

| Model | n steps | Mean ± SD |
|-------|---------|-----------|
| GPT-5 | 7 | 1.000 ± 0.000 |
| Opus 4.6 | 7 | 1.000 ± 0.000 |
| Gemini 3.1 Pro | 7 | 1.000 ± 0.000 |

**Kruskal-Wallis:** all three models scored identically across every step (all scores tied — p = 1)

| Pair | Cliff's δ | Magnitude | MWU p | Dunn p (Holm) | Sig |
|------|-----------|-----------|-------|---------------|-----|
| GPT-5 vs Opus 4.6 | +0.000 | negligible | 1.0000 | — | ns |
| GPT-5 vs Gemini 3.1 Pro | +0.000 | negligible | 1.0000 | — | ns |
| Opus 4.6 vs Gemini 3.1 Pro | +0.000 | negligible | 1.0000 | — | ns |

### Wetland

| Model | n steps | Mean ± SD |
|-------|---------|-----------|
| GPT-5 | 10 | 0.860 ± 0.190 |
| Opus 4.6 | 10 | 0.890 ± 0.160 |
| Gemini 3.1 Pro | 10 | 0.880 ± 0.155 |

**Kruskal-Wallis:** H = 0.171, p = 0.9182 (not significant)

| Pair | Cliff's δ | Magnitude | MWU p | Dunn p (Holm) | Sig |
|------|-----------|-----------|-------|---------------|-----|
| GPT-5 vs Opus 4.6 | -0.100 | negligible | 0.7187 | — | ns |
| GPT-5 vs Gemini 3.1 Pro | -0.030 | negligible | 0.9368 | — | ns |
| Opus 4.6 vs Gemini 3.1 Pro | +0.070 | negligible | 0.8097 | — | ns |

