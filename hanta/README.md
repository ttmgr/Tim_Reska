# Hantavirus 2026 Outbreak Tracker

Unofficial surveillance dashboard for the 2026 Andes-virus cluster linked to MV Hondius, plus global hantavirus surveillance. Also available in German under `de/`.

## What this shows

Live case counts, geographic map (Leaflet), MV Hondius ship-cluster narrative, timeline, and regional breakdown. Data is curated from WHO / CDC / ECDC situation reports — see `data/*.json` for the raw inputs and provenance.

## Shared infrastructure

This is one half of the outbreak-dashboard twin pair (`ebola` and `hanta`). Both pages share:

- `../assets/css/outbreak.css` — layout, pills, stat grid, map styling.
- `../assets/js/outbreak-common.js` — chart factories, map helpers, pill/stat renderers.

Edit shared behaviour in `assets/`, not per-twin. Only per-disease data and chart wiring live in `js/`. The German page is a sibling under `de/` with its own translated `index.html`.

## Run locally

```bash
python3 -m http.server   # from repo root, then open http://localhost:8000/hanta/
```

The page also works opened directly (`open index.html`), but the Leaflet tiles will not load over `file://`.

## Last refresh

2026-05-23.
