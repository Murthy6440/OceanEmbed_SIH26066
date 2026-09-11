import React from "react";
import Plot, { baseLayout, baseConfig } from "../utils/plotly.js";

export default function ProfileChart({ profile, loading, error }) {
  return (
    <div className="card chart-card">
      <div className="card-head">
        <h2 className="card-title">Temperature Profile (0–1000 m)</h2>
      </div>

      {loading && <p className="empty-state">Loading profile…</p>}
      {!loading && error && (
        <p className="error-state">Could not load profile: {error}</p>
      )}
      {!loading && !error && !profile && (
        <p className="empty-state">
          Select a location on the map to load its predicted temperature
          profile.
        </p>
      )}

      {!loading && profile && (
        <Plot
          data={[
            {
              x: profile.predicted_temperature_degC,
              y: profile.depth_m,
              type: "scatter",
              mode: "lines+markers",
              name: "Predicted",
              line: { color: "#4fd0ff", width: 2.5 },
              marker: { size: 5, color: "#4fd0ff" },
            },
          ]}
          layout={{
            ...baseLayout,
            xaxis: { ...baseLayout.xaxis, title: "Temperature (°C)" },
            yaxis: {
              ...baseLayout.yaxis,
              title: "Depth (m)",
              autorange: "reversed",
            },
            showlegend: false,
          }}
          config={baseConfig}
          style={{ width: "100%", height: "300px" }}
          useResizeHandler
        />
      )}
      <p className="chart-note">
        {profile?.location?.name || "Selected location"} — predicted
        temperature at each standard depth level.
      </p>
    </div>
  );
}
