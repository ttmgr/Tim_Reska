# Ebola 2026 Outbreak Tracker

Unofficial surveillance dashboard for the 2026 Ituri Province Bundibugyo ebolavirus outbreak (DRC + Uganda, PHEIC declared 17 May 2026).

## What this shows

Live case counts, geographic map (Leaflet), timeline, and regional breakdown. Data is curated from WHO / CDC / ECDC situation reports — see `data/*.json` for the raw inputs and provenance.

## Shared infrastructure

This is one half of the outbreak-dashboard twin pair (`ebola` and `hanta`). Both pages share:

- `../assets/css/outbreak.css` — layout, pills, stat grid, map styling.
- `../assets/js/outbreak-common.js` — chart factories, map helpers, pill/stat renderers.

Edit shared behaviour in `assets/`, not per-twin. Only per-disease data and chart wiring live in `js/`.

## Run locally

```bash
python3 -m http.server   # from repo root, then open http://localhost:8000/ebola/
```

The page also works opened directly (`open index.html`), but the Leaflet tiles will not load over `file://`.

## Last refresh

2026-06-07.
