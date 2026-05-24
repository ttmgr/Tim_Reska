# Multi-Agent Due Diligence — public teaser

Public landing for the Askeras multi-agent DD pipeline: parallel specialist agents, an independent blind validator, and a synthesis step that must honour every critique.

## Teaser only

Only `index.html` is published from this directory. The full DD pipeline — agent prompts, validation harness, report generators, and templates — lives in a private codebase and is gitignored here (`multi-agent-dd/build_*.py`, `SKILL.md`, `docs/`, `outputs/`, `workings/`, `templates/`; see the project `.gitignore`).

The pipeline is in active use under NDA. The published page describes the methodology and one anonymised run's validator-finding counts; no client materials are exposed.

## Run locally

```bash
python3 -m http.server   # from repo root, then open http://localhost:8000/multi-agent-dd/
```

## Last refresh

2026-05-23.
