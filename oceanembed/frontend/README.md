# OceanEmbed Frontend — SIH26066 Prototype

React + Vite dashboard for the OceanEmbed FastAPI backend. Connects to every
backend endpoint (`/health`, `/api/locations`, `/api/grid`,
`/api/profile/{id}`, `/api/predict`, `/api/validation`) — nothing in the UI
is hardcoded or faked.

> ⚠️ The whole system (including this UI) is a **demo running on synthetic
> data**. Every screen carries the live disclaimer text returned by the
> backend.

## Stack

- React 18 + Vite 5
- **Leaflet** + **react-leaflet** with **OpenStreetMap** tiles (no paid map API)
- **Plotly.js** (`plotly.js-dist-min` + `react-plotly.js`) for all charts
- Plain CSS (no UI kit) — dark, projector-friendly theme

No paid APIs, no API keys, nothing that requires a network key.

## 1. Run the backend first

```bash
cd oceanembed_backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Confirm it's up: `http://localhost:8000/health`

## 2. Run the frontend

```bash
cd oceanembed_frontend
npm install
cp .env.example .env   # edit VITE_API_BASE_URL if your backend isn't on :8000
npm run dev
```

Open the printed local URL (default `http://localhost:5173`).

## What each piece does

| UI element | Backend call(s) |
|---|---|
| Header status pill | `GET /health` |
| Disclaimer banner | `disclaimer` field from `/health` / `/api/grid` / `/api/profile` / `/api/predict` |
| Map domain + virtual float markers | `GET /api/locations` |
| Map temperature layer at depth 0 | `GET /api/grid` (SST field, colored per cell) |
| Map temperature layer at depth > 0 | `GET /api/grid` once for surface fields, then one `POST /api/predict` per grid cell (with those surface fields as overrides), run with a bounded-concurrency batcher |
| Clicking a virtual float marker | `GET /api/profile/{location_id}` — full 0–1000 m profile |
| Clicking anywhere else on the map | `POST /api/predict` once per standard depth level (0…1000 m), assembled client-side into the same shape as `/api/profile` |
| **Generate Prediction** button | `POST /api/predict` for the exact lat/lon/depth selected |
| Predicted Temperature card | last `/api/predict` response |
| RMSE / Correlation / Bias cards | `GET /api/validation` |
| Model Inputs card | `surface_inputs_used` from the last `/api/predict` response |
| Temperature Profile chart | selected location's profile (predicted only) |
| Predicted vs ARGO-style Reference chart | selected location's profile (predicted + synthetic reference) |
| Predicted vs Observed validation scatter | same profile's predicted vs synthetic-reference pairs, one per depth level, plus a 1:1 line |

## Notes on the depth-aware map layer

`/api/grid` only returns **surface** fields (SST, SSS, SSH, currents, winds).
To show how the *subsurface* temperature field changes with depth, the
frontend re-queries `/api/predict` for every grid cell at the selected depth
(reusing that cell's exact surface fields as overrides, so it's consistent
with what `/api/predict`/`/api/profile` would say for that point). This runs
with limited concurrency and only fires when you release the depth slider,
not on every drag tick. Default grid spacing is 3° (~189 cells) to keep this
responsive and legible on a projector; edit `GRID_RESOLUTION_DEG` in
`src/App.jsx` to change it.

## Project layout

```
src/
  api/client.js          All backend calls + batching helpers
  utils/colorScale.js    Temperature -> color mapping for the map layer
  utils/plotly.js         Shared Plotly component + dark theme layout
  components/            One component per dashboard piece
  App.jsx                 Orchestrates state + data flow
  main.jsx                 Entry point
```
