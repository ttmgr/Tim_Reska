# Nanopore Pipeline Advisor

Static wizard that recommends an Oxford Nanopore kit, basecalling model, and analysis pipeline from a short project questionnaire. Includes rationale, alternatives, and ready-to-run commands. Companion `nanopore-guide.html` is a longer-form reference.

## What this is

A self-contained single-page recommendation tool — no backend, no LLM at runtime. The decision logic is in plain JavaScript (`recommendation-engine.js`); field metadata is in `field-metadata.js`; the UI lives in `app.js`. Data tables under `data/` drive the recommendations.

Aimed at researchers planning a sequencing project who need a defensible starting point (kit + model + pipeline) before committing to a protocol. Pairs with the broader GenomicsForOneHealth pipelines.

## Run locally

```bash
python3 -m http.server   # from repo root, then open http://localhost:8000/nanopore-advisor/
```

Also works with `open index.html` — the page is fully offline-capable once loaded.

## Last refresh

2026-05-23.
