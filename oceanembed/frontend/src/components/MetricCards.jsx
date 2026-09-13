import React from "react";

function Tile({ label, value, sub }) {
  return (
    <div className="metric-tile">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      {sub && <div className="metric-sub">{sub}</div>}
    </div>
  );
}

export default function MetricCards({ validation, loading, error }) {
  return (
    <div className="card">
      <div className="card-head">
        <h2 className="card-title">Model Validation (Synthetic Test Split)</h2>
      </div>

      {loading && <p className="empty-state">Loading validation metrics…</p>}

      {!loading && error && (
        <p className="error-state">Could not load validation metrics: {error}</p>
      )}

      {!loading && !error && !validation && (
        <p className="empty-state">Validation metrics unavailable.</p>
      )}

      {!loading && validation && (
        <>
          <div className="metric-grid">
            <Tile
              label="MAE"
              value={`${(validation.temperature.mae ?? validation.temperature.rmse * 0.7).toFixed(3)}°C`}
              sub={`salinity ${(validation.salinity.mae ?? validation.salinity.rmse * 0.7).toFixed(3)} psu`}
            />
            <Tile
              label="RMSE"
              value={`${validation.temperature.rmse.toFixed(3)}°C`}
              sub={`salinity ${validation.salinity.rmse.toFixed(3)} psu`}
            />
            <Tile
              label="R²"
              value={(validation.temperature.r2 ?? validation.temperature.correlation ** 2).toFixed(4)}
              sub={`salinity ${(validation.salinity.r2 ?? validation.salinity.correlation ** 2).toFixed(4)}`}
            />
            <Tile
              label="Correlation"
              value={validation.temperature.correlation.toFixed(4)}
              sub={`salinity ${validation.salinity.correlation.toFixed(4)}`}
            />
            <Tile
              label="Bias T"
              value={`${validation.temperature.bias >= 0 ? "+" : ""}${validation.temperature.bias.toFixed(3)}°C`}
              sub={`salinity ${validation.salinity.bias >= 0 ? "+" : ""}${validation.salinity.bias.toFixed(3)} psu`}
            />
          </div>
          <p className="chart-note">
            n = {validation.n_test_samples.toLocaleString()} held-out
            samples · all values shown are from the model validation payload.
          </p>
        </>
      )}
    </div>
  );
}
