# OceanEmbed — SIH26066 Prototype Backend

> ⚠️ **ALL DATA IN THIS PROTOTYPE IS SYNTHETIC / DEMO DATA.**
> There is no real satellite, Argo float, or in-situ ocean data anywhere in
> this codebase. Every field, prediction, and "accuracy" number is generated
> by simple parametric formulas (`data_generator.py`) chosen to *resemble*
> plausible ocean behaviour (a thermocline shape, monsoon-like winds, smooth
> eddy-like currents) purely so the pipeline has something realistic-looking
> to train and demo against. **Never present anything from this service as a
> real oceanographic forecast or as validated against real observations.**
> Every API response also carries an explicit `disclaimer` field.

This backend demonstrates the end-to-end ML pipeline envisioned by the
SIH26066 problem statement: estimating **subsurface** ocean parameters
(temperature & salinity) from **surface** observations (SST, SSS, SSH/SLA,
surface currents, surface winds) plus depth, using a lightweight neural
network.

## Domain

- Latitude: 5–30°N
- Longitude: 45–105°E (North Indian Ocean box — Arabian Sea + Bay of Bengal)
- Depth: 0–1000 m

## Stack

- Python 3
- FastAPI + Uvicorn
- PyTorch (small feed-forward MLP, 10 → 64 → 64 → 32 → 2)
- NumPy for the synthetic data generator
- No database, no auth, no Docker — kept intentionally minimal for a hackathon prototype

## Project layout

```
data_generator.py   Synthetic ocean field + profile generator (the "fake truth")
model.py             PyTorch model, Scaler, OceanEmbedPredictor (load + predict)
train_model.py       Generates synthetic train/test sets, trains the model,
                      saves weights + scalers + validation metrics to saved_model/
main.py              FastAPI app with all endpoints + CORS
test_api.py          Functional test hitting every endpoint (TestClient)
saved_model/         Created after training: model weights, scalers, metrics JSON
requirements.txt
```

## Setup & run

```bash
pip install -r requirements.txt

# Optional: train explicitly first (otherwise main.py auto-trains on first startup)
python train_model.py

# Start the API
uvicorn main:app --reload --port 8000
```

Interactive API docs: `http://localhost:8000/docs`

## Run the test suite

```bash
python test_api.py
```

This exercises every endpoint (including a 404 and a 422 validation-error
case) using FastAPI's `TestClient` and prints each response.

## Endpoints

| Method | Path                          | Purpose |
|--------|-------------------------------|---------|
| GET    | `/health`                     | Liveness + model-loaded check |
| GET    | `/api/locations`               | List of demo "virtual float" locations |
| GET    | `/api/grid?resolution=2.0`     | Synthetic surface field grid (SST, SSS, SSH, currents, winds) for map display |
| GET    | `/api/profile/{location_id}`   | Full 0–1000 m depth profile (predicted temperature & salinity) for a demo location |
| POST   | `/api/predict`                 | Predict subsurface temperature & salinity at a given lat/lon/depth |
| GET    | `/api/validation`              | RMSE, correlation, bias on a held-out **synthetic** test split |

### `POST /api/predict` body

```json
{
  "lat": 15.0,
  "lon": 70.0,
  "depth": 200.0
}
```

`sst`, `sss`, `ssh`, `u_curr`, `v_curr`, `u_wind`, `v_wind` are optional
overrides — if omitted, they're filled in from the synthetic surface-field
formula for that lat/lon so you can test with just a location + depth.

Response includes both the model's `predicted_*` values and a
`synthetic_reference_*` value (what the underlying synthetic formula says
the "truth" should be at that point) purely so you can sanity-check the
model against the demo ground truth — again, **not real data**.

## Model

- Input features (10): `sst, sss, ssh, u_curr, v_curr, u_wind, v_wind, depth, lat_norm, lon_norm`
- Output (2): `temperature (°C), salinity (psu)`
- Architecture: `Linear(10→64) → ReLU → Dropout → Linear(64→64) → ReLU → Dropout → Linear(64→32) → ReLU → Linear(32→2)`
- Trained on 20,000 synthetic samples, evaluated on 5,000 held-out synthetic samples
- Standardized inputs/outputs (mean/std), scalers persisted as JSON

## Validation metrics (from the last training run, synthetic data only)

| Variable    | RMSE   | Correlation | Bias    |
|-------------|--------|-------------|---------|
| Temperature | ~0.26 °C | ~0.999     | ~+0.01 °C |
| Salinity    | ~0.05 psu | ~0.98     | ~-0.01 psu |

These numbers describe how well the network reproduces the **synthetic
formula**, not real-world skill. Re-running `train_model.py` will regenerate
slightly different numbers (fresh training) but they're always reported live
via `GET /api/validation`, never hardcoded in the frontend.

## CORS

CORS is enabled for all origins (`allow_origins=["*"]`) so a React dev server
(e.g. `http://localhost:3000` or `5173`) can call this API directly during
the hackathon. Tighten this before any real deployment.
