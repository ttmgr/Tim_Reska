# Tim Reska — Project Hub

**Status:** ACTIVE · Honesty pass shipped (solo founder, claims scrubbed); going to market

Personal portfolio site. Showcases applied ML, LLM evaluation, outbreak dashboards, and genomics pipelines, plus the public marketing pages for the Askeras AI Enablement venture (`askeras-v2/`, local working source — not yet published). The Askeras business codebase and deliverable generators now live in a separate private repo (`~/Documents/New_project/askeras`, `ttmgr/RESKA-AI-ENABLEMENT`); they share fonts, tokens, and the terracotta design language with this site.

## :oneline

Portfolio of applied ML, LLM evaluation, and AI deployment work, plus the public marketing pages for the Askeras AI Enablement venture.

## :next

Publish the curated Askeras marketing pages once the Impressum address is in place; until then they stay in `askeras-v2/` (gitignored working source).

## :status

The published site is stable and was scrubbed for accuracy (2026-06-02): every unverifiable "in active use under NDA" / pilot-partner / co-founder claim removed, repositioned as **solo founder** (Dr. rer. nat., 7 publications), and the three "Consulting — NDA" cards reframed as self-built projects. The Askeras business codebase and v3.0.0 deliverables were split out into the separate private repo `~/Documents/New_project/askeras` (`ttmgr/RESKA-AI-ENABLEMENT`); this repo keeps only the site and the `askeras-v2/` marketing pages. Posture: selective practice — inbound/referral only, no cold-outreach sprint.

From here you can:
- Open the [published site](index.html) for the portfolio landing page
- Open the [Askeras marketing site](askeras-v2/index.html) for the venture's public face (local working source)
- Run `python3 scripts/build_hub.py` to refresh this dashboard
- Run `python3 scripts/build_index.py && python3 scripts/build_visualization.py` to refresh the code graph

## :canonical

| Artifact | Path | What it is |
|----------|------|------------|
| **Site landing** | | |
| Portfolio homepage | `index.html` | Published personal site entry point |
| Site structure | `STRUCTURE.md` | Human-oriented repo narrative |
| Shared CSS tokens | `assets/css/tokens.css` | Brand variables for all published showcases |
| Self-hosted fonts | `assets/css/fonts.css`, `assets/fonts/` | Inter, Source Serif 4, JetBrains Mono (DSGVO-safe) |
| Navigation manifest | `assets/js/nav-manifest.js` | Drives cross-showcase nav bar |
| Node manifest | `docs/index_nodes.yaml` | Curated code-graph source of truth |
| --- | --- | --- |
| **LLM evaluation** | | |
| LLM eval site | `llm-eval/index.html` | "Against Plausibility" — 28-model evaluation |
| Methodology | `llm-eval/methodology/` | Two pipelines, scoring, statistical methods |
| Results data | `llm-eval/results/` | 476 scored step-results across 28 models |
| --- | --- | --- |
| **Applied ML / Healthcare** | | |
| Disease Network | `disease-network/index.html` | D3.js comorbidity atlas (German UI) |
| Disease Progression | `disease-progression/index.html` | Survival and multistate models (Cox PH, CTMC, DeepSurv) |
| MedRisk teaser | `medrisk/index.html` | Medical underwriting platform (public teaser only) |
| PKV ML Explorer | `pkv-ml-explorer/index.html` | ML methods catalog for private health insurance |
| --- | --- | --- |
| **AI deployment strategy** | | |
| AI Deployment Readiness | `ai-deployment-readiness/index.html` | 25-question maturity self-assessment |
| LLM Cost Calculator | `llm-cost-calculator/index.html` | Pricing DB, Monte Carlo sensitivity, ROI modeling |
| Agentic Systems | `agentic_systems/AGENTIC_FRONTIER_PRIMER.html` | Agentic AI primer |
| AI News Radar | `ai-news-radar/index.html` | LLM coding ecosystem, distilled weekly |
| --- | --- | --- |
| **Outbreak dashboards** | | |
| Ebola tracker | `ebola/index.html` | 2026 Ebola outbreak dashboard |
| Hanta tracker | `hanta/index.html` | 2026 Hantavirus tracker (EN + DE) |
| Shared outbreak CSS/JS | `assets/css/outbreak.css`, `assets/js/outbreak-common.js` | Twin dashboards share these |
| --- | --- | --- |
| **Other showcases** | | |
| Academy teaser | `academy/index.html` | Published Askeras AI Academy one-pager |
| Academy sample lesson | `academy/sample-lesson/index.html` | Sanitised Tier 1 lesson |
| Agent Skill Pack | `agent-skill-pack/index.html` | One Health Genomics agent skills |
| Multi-Agent DD | `multi-agent-dd/index.html` | Due Diligence pipeline teaser |
| Nanopore Advisor | `nanopore-advisor/index.html` | Protocol/parameter recommendation wizard |
| Genomics pipelines | `pipelines/` | Aerobiome, Listeria, Wetland surveillance (Snakemake) |
| --- | --- | --- |
| **Askeras marketing site** (private, `askeras-v2/`) | | |
| Corporate homepage | `askeras-v2/index.html` | "Where AI fits. Where it doesn't." |
| Services | `askeras-v2/services.html` | Five-tier offer ladder |
| Methodology | `askeras-v2/methodology.html` | Eight deliverable templates |
| Reality Check | `askeras-v2/reality-check.html` | 2-week AI reality check product |
| Academy | `askeras-v2/academy.html` | Academy marketing page |
| KMU (DE) | `askeras-v2/kmu.html` | German SME variant |
| Credentials | `askeras-v2/credentials.html` | Full track record |
| Shared chrome | `askeras-v2/chrome.css` | Shared brand CSS for all 11 pages |
| Tim CV | `askeras-v2/tim-reska.html` | Founder CV |
| --- | --- | --- |
| **Askeras business codebase** (separate private repo) | | |
| Generators, deliverables, docs | `~/Documents/New_project/askeras` (`ttmgr/RESKA-AI-ENABLEMENT`) | All 50+ generators, the versioned `outputs/<semver>/` deliverable tree, Academy/DD/legal/sales modules, PWA, Supabase functions. Split out of this repo on 2026-06-09 — run `make build` there, not here. |

## :concepts

- **PBW** — Plausible But Wrong. The core LLM failure mode identified in the 28-model benchmark. Central to both the LLM eval project and Askeras Academy teaching.
- **Terracotta palette** — Brand design language: `--accent: #C4794A` on `--bg: #FAF9F7`. Used by the portfolio site, Askeras marketing site, and all generated deliverables.
- **Earth + Sky palette** — Scientific figure palette (forest green, water blue, clay, amber, slate). Used by the LLM eval, disease progression, and scientific figures only.
- **Teaser** — A published showcase page that hints at private underlying work (e.g., `academy/index.html` is the public teaser for the private Askeras Academy generators in the separate business repo).
- **DD** — AI Deployment Due Diligence. Askeras diagnostic arm: 4-6 week assessment producing capability fit matrix, wave plan, governance gap analysis.
- **Academy** — Askeras AI competence programme. Four tiers (T1 = 4 weeks, T2 = 3 months, T3 = 6 months, T4 = 12 months). Six sector variants.
- **Bible** — Comprehensive operating manual. Internal (full ops), External (client-facing), SME/DE (German SME variant), Student, Teacher.
- **Compass Call** — Free 30-minute diagnostic. Output is a one-page Compass Readout PDF.
- **Reality Check** — 2-week paid Askeras engagement. Tests an AI use case against real data; produces a go/no-go report.
- **Starter Pack** — Personalised learner zip built via `make starter-pack FRIEND=name`. Contains orientation, howtocode, interactive PWA lessons, toolkit cards.
- **Study Guides** — Interactive offline-first HTML/PWA versions of the Academy curriculum. Progress tracking via localStorage, optional Supabase sync.
- **Twins** — `ebola` and `hanta` dashboards share the same architecture and `assets/` CSS/JS. Edit shared behaviour in `assets/`, not per-twin.
- **chrome.css** — Shared brand CSS extracted from the 11 Askeras marketing pages to eliminate duplication. Nav, tokens, cards, footer, responsive rules.

## :collaborators

- **Tim Reska** — Everything. Dr. rer. nat., Helmholtz AI / TU Munich. 7 publications incl. Nature Communications. All code, all content. Solo founder of Askeras.

## :superseded

- `archive/` — old/unwanted working files (gitignored, never published)
- `company_askeras/` — the Askeras business codebase that used to live here; split out to `~/Documents/New_project/askeras` (`ttmgr/RESKA-AI-ENABLEMENT`) on 2026-06-09
