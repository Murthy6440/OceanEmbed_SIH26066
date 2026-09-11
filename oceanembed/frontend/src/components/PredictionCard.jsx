import React from "react";

export default function PredictionCard({ prediction, loading, error, risk }) {
  return (
    <div className="card stat-card">
      <div className="card-head">
        <h2 className="card-title">Predicted Temperature</h2>
      </div>

      {risk && risk.level !== "normal" && (
        <div className={`alarm-banner ${risk.level}`}>
          <span className="alarm-icon">⚠️</span>
          <div>
            <strong>{risk.title}</strong>
            <div>{risk.description}</div>
          </div>
        </div>
      )}

      {loading && <p className="empty-state">Running model…</p>}

      {!loading && error && (
        <p className="error-state">
          Prediction failed: {error} — check the backend is running, then
          click <b>Generate Prediction</b> again.
        </p>
      )}

      {!loading && !error && !prediction && (
        <p className="empty-state">
          Select a location and depth, then click{" "}
          <b>Generate Prediction</b>.
        </p>
      )}

      {!loading && prediction && (
        <>
          <div>
            <span className="stat-value">
              {prediction.predicted_temperature_degC.toFixed(2)}
            </span>
            <span className="stat-unit">°C</span>
          </div>
          <div className="stat-secondary">
            at {prediction.depth.toFixed(0)} m · {prediction.lat.toFixed(2)}
            °N, {prediction.lon.toFixed(2)}°E
          </div>
          <div className="stat-secondary">
            Predicted salinity:{" "}
            <b>{prediction.predicted_salinity_psu.toFixed(2)} psu</b>
          </div>
          <div className="stat-secondary">
            Synthetic reference: {prediction.synthetic_reference_temperature_degC.toFixed(2)}
            °C · Δ{" "}
            {(
              prediction.predicted_temperature_degC -
              prediction.synthetic_reference_temperature_degC
            ).toFixed(2)}
            °C
          </div>
        </>
      )}
    </div>
  );
}
