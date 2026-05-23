# Repository layout

This repo is two things at once, which is why the root looks busy:

1. **A GitHub Pages portfolio site** — the root `index.html` is the hub, and **each top-level kebab-case directory is a self-contained showcase published at `https://ttmgr.github.io/Tim_Reska/<dir>/`** and linked from the homepage.
2. **A monorepo of real project codebases** — some of those directories (`medrisk`, `llm-eval`, `pipelines`) are full projects with their own internal `src/`, `tests/`, etc.

If you're looking for a file: first decide which *showcase/project* it belongs to (top-level dir), then navigate inside — each project owns its own structure.

## Conventions

- **Directory names are kebab-case** (`disease-progression`, `llm-cost-calculator`, `multi-agent-dd`). No `snake_case`, no spaces.
- **Each showcase dir owns its own `index.html`.** Cross-page navigation is generated from `assets/js/nav.js` — add a new showcase there.
- **Renames use `git mv`** to preserve history (`git blame` / `--follow`). The dir name doubles as the public URL, so a rename also means updating the homepage link, `assets/js/nav.js`, and any `.gitignore` rule for that dir.
- **Customer-facing / staging content** lives in `*_data_do_not_touch_if_not_prompted/` holding folders (gitignored) until reviewed and promoted — never edited live in place.

## Published showcases (each = a `/<dir>/` route)

**Applied ML · healthcare**
- `medrisk/` — medical-underwriting platform. **Published as a teaser only** (`index.html`); the platform code, methodology, and data adapters are private (gitignored, sellable IP).
- `disease-progression/` — survival + multistate progression models.
- `disease-network/` — D3.js clinical comorbidity atlas.
- `pkv-ml-explorer/` — PKV ML methods catalog.

**LLM evaluation**
- `llm-eval/` — "Against Plausibility": 28-model evaluation (`evaluations/ responses/ results/ prompts/ methodology/ scripts/`).

**AI deployment strategy**
- `ai-deployment-readiness/` — maturity self-assessment.
- `llm-cost-calculator/` — cost modeling + ROI.

**Outbreak dashboards** *(twin pair — identical shape: `data/*.json` + `js/{app,charts,map}.js` + `index.html`)*
- `ebola/`, `hanta/` (the latter also has a German `de/` page). Their **shared** CSS/JS lives in `assets/css/outbreak.css` and `assets/js/outbreak-common.js`; only per-disease logic stays in each dir's `js/`. Edit shared behaviour in `assets/`, not in one twin.

**Other showcases**
- `agent-skill-pack/`, `nanopore-advisor/`, `academy/`, `multi-agent-dd/`. Some publish only a teaser `index.html`; their build internals are gitignored (see `.gitignore`).

## Non-published

- `pipelines/` — One Health bioinformatics (Snakemake) pipelines (`aerobiome/`, `listeria-adaptive-sampling/`, `wetland-surveillance/`). Tracked code, not linked as a Pages showcase.
- `assets/` — site-wide shared resources: `css/tokens.css` (brand tokens), `css/outbreak.css`, `js/nav.js`, `js/outbreak-common.js`.
- Root files: `index.html` (hub), `README.md`, `LICENSE`, `CITATION.cff`, `favicon.svg`, `.nojekyll`.

## Local-only (gitignored — never published)

- `archive/` — old working files.
- `*_data_do_not_touch_if_not_prompted/` — staging holding folders, reviewed before promotion.
- `company_askeras/`, `askeras-v1/`, `askeras-v2/` — the Askeras venture (own domain / future GmbH); lives here locally but is published from its own repo.
- `medrisk/` (all except `index.html`) — the underwriting platform code, methodology, and data adapters (sellable IP).
- `multi-agent-dd/` build internals (`build_*.py`, `SKILL.md`, `docs/`, `outputs/`, `workings/`, `templates/`) — only the teaser `index.html` is published.
- `llm-coding-radar/` — personal weekly digests of the LLM-coding ecosystem (output of the `/llm-coding-radar` skill); local-only, not a showcase.
