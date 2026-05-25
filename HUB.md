# Tim Reska — Project Hub

**Status:** ACTIVE · Askeras v3.0.0 buildout, site architecture deepening, academy PWA live

Personal portfolio site + the Askeras AI Enablement venture. The published site showcases applied ML, LLM evaluation, outbreak dashboards, and genomics pipelines. The private `company_askeras/` layer generates every Askeras deliverable (100+ generators, 40+ PDF/DOCX/PPTX outputs). Both surfaces share fonts, tokens, and the terracotta design language.

## :oneline

Portfolio of applied ML, LLM evaluation, and AI deployment work — plus the full Askeras AI Enablement venture (Academy curriculum, Due Diligence pipeline, legal/sales generators).

## :status

The published site is stable. Current energy is on the Askeras buildout: v3.0.0 deliverables shipping, academy PWA installable offline, enterprise pitch materials complete, starter packs per-recipient, legal generators production-ready.

From here you can:
- Open the [published site](index.html) for the portfolio landing page
- Open the [Askeras marketing site](askeras-v2/index.html) for the venture's public face
- Run `cd company_askeras && make build` to regenerate all Askeras outputs
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
| Minas CV | `askeras-v2/minas-schwager.html` | Co-Founder CV |
| --- | --- | --- |
| **Askeras generators** (private, `company_askeras/`) | | |
| Build orchestrator | `company_askeras/src/askeras/shared/run_all.py` | Drives 100+ generators via `make build` |
| Brand constants | `company_askeras/src/askeras/brand.py` | Colours, fonts, firm name |
| Makefile | `company_askeras/Makefile` | Build, test, lint, ship, starter-pack |
| Course content | `company_askeras/data/course_content/` | Markdown source for trainer guides |
| Architecture | `company_askeras/docs/architecture.md` | Generator system design |
| PWA shell | `company_askeras/web/pwa/index.html` | iOS-installable study workbook |
| PWA modules | `company_askeras/web/src/` | 12 UMD JS modules (auth, progress, terminal) |
| Supabase functions | `company_askeras/infra/supabase/functions/` | Stripe checkout, seat management |
| Askeras HUB | `company_askeras/docs/HUB.html` | Dedicated Askeras-only dashboard (deeper detail) |
| --- | --- | --- |
| **Askeras deliverables** (private, `company_askeras/outputs/3.0.0/`) | | |
| Curriculum overview | `company_askeras/outputs/3.0.0/Askeras_AI_Academy_Curriculum_Overview.pdf` | 4-tier programme at a glance |
| Student Bible | `company_askeras/outputs/3.0.0/Askeras_Academy_Student_Bible.pdf` | Learner reference |
| Teacher Bible | `company_askeras/outputs/3.0.0/Askeras_Academy_Teacher_Bible.pdf` | Trainer reference |
| Student booklet | `company_askeras/outputs/3.0.0/Askeras_AI_Academy_STUDENT_BOOKLET.pdf` | Compiled student materials |
| Teacher booklet | `company_askeras/outputs/3.0.0/Askeras_AI_Academy_TEACHER_BOOKLET.pdf` | Compiled trainer materials |
| Trainer guides | `company_askeras/outputs/3.0.0/academy/Askeras_AI_Academy_Trainer_Guide_Tier1.pdf` | Also: Tier2, Tier3 |
| Demo playbooks | `company_askeras/outputs/3.0.0/academy/Askeras_AI_Academy_Tier1_Demo_Playbook.pdf` | Also: Tier2, Tier3, Tier4 |
| Interactive study guides | `company_askeras/outputs/3.0.0/academy/study_guides/index.html` | Offline PWA with progress tracking |
| Curriculum packs | `company_askeras/dist/askeras_curriculum_packs/` | Bundled tier/sector PDFs |
| Starter pack template | `company_askeras/outputs/_starter_pack_do_not_touch_if_not_prompted/` | Per-recipient learner zip source |
| Firm credentials | `company_askeras/outputs/3.0.0/Askeras_Firm_Credentials.pdf` | Track record and capabilities |
| Generic pitch | `company_askeras/outputs/3.0.0/Askeras_AI_Enablement_Generic_Pitch.pdf` | Cold outreach one-pager |
| Enterprise pitch | `company_askeras/outputs/3.0.0/sales/Askeras_AI_Enablement_Enterprise.pdf` | Also: Mid-Market |
| Pricing | `company_askeras/outputs/3.0.0/Askeras_Pricing_2026.pdf` | Tier pricing |
| Internal bible | `company_askeras/outputs/3.0.0/Askeras_Operating_Bible_Internal.pdf` | Full operational handbook |
| External bible | `company_askeras/outputs/3.0.0/Askeras_Bible_External.pdf` | Client-facing methodology |
| SME bible (DE) | `company_askeras/outputs/3.0.0/Askeras_Betriebs_Bibel_SME_DE.pdf` | German SME operations manual |
| SOW template | `company_askeras/outputs/3.0.0/legal/Askeras_SOW_Muster_Consulting_2026-05-25.pdf` | Statement of work |
| DPA template | `company_askeras/outputs/3.0.0/legal/Askeras_AVV_Muster_GmbH_2026-05-25.pdf` | Data processing agreement |
| Invoice template | `company_askeras/outputs/3.0.0/legal/Askeras_Rechnung_ASK-2026-001.pdf` | Invoice |
| DD blank templates | `company_askeras/outputs/3.0.0/templates/blank/` | 8 empty DD templates |
| DD biotech examples | `company_askeras/outputs/3.0.0/templates/example_biotech/` | Filled sector examples |
| Compass readout | `company_askeras/outputs/3.0.0/compass/Askeras_Compass_Sample_Firm_2026-05-25.pdf` | Sample diagnostic output |
| Outreach kit | `company_askeras/outreach/` | Email templates, LinkedIn posts, prospect list |
| Howtocode (DE) | `company_askeras/docs/howtocode/howtocode.html` | Coding tutorial for non-coders |
| Howtocode (EN) | `company_askeras/docs/howtocode_en/howtocode_en.html` | English version |

## :concepts

- **PBW** — Plausible But Wrong. The core LLM failure mode identified in the 28-model benchmark. Central to both the LLM eval project and Askeras Academy teaching.
- **Terracotta palette** — Brand design language: `--accent: #C4794A` on `--bg: #FAF9F7`. Used by the portfolio site, Askeras marketing site, and all generated deliverables.
- **Earth + Sky palette** — Scientific figure palette (forest green, water blue, clay, amber, slate). Used by the LLM eval, disease progression, and scientific figures only.
- **Teaser** — A published showcase page that hints at private underlying work (e.g., `academy/index.html` is the public teaser for the private `company_askeras/` Academy generators).
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

- **Tim Reska** — Everything. PhD Helmholtz AI / TU Munich. 8 publications incl. Nature Communications. All code, all content.
- **Minas Schwager** — Co-Founder Askeras (joining). PhD computational biology Helmholtz / TUM. Single-cell multi-omics, LLM deployment in patent law.

## :superseded

- `archive/` — old/unwanted working files (gitignored, never published)
- `company_askeras/archive/brand/` — pre-terracotta Askera-pastel brand materials
- `company_askeras/archive/outputs/` — pre-v3 output snapshots
