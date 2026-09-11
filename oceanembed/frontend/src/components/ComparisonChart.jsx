import React from "react";
import Plot, { baseLayout, baseConfig } from "../utils/plotly.js";

export default function ComparisonChart({ profile, loading, error }) {
  return (
    <div className="card chart-card">
      <div className="card-head">
        <h2 className="card-title">Predicted vs ARGO-style Reference</h2>
      </div>

      {loading && <p className="empty-state">Loading comparison…</p>}
      {!loading && error && (
        <p className="error-state">Could not load comparison: {error}</p>
      )}
      {!loading && !error && !profile && (
        <p className="empty-state">
          Select a location to compare the predicted profile against the
          demo reference profile.
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
              marker: { size: 5 },
            },
            {
              x: profile.synthetic_reference_temperature_degC,
              y: profile.depth_m,
              type: "scatter",
              mode: "lines+markers",
              name: "Reference (demo)",
              line: { color: "#f5b942", width: 2, dash: "dot" },
              marker: { size: 5, symbol: "diamond" },
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
            showlegend: true,
          }}
          config={baseConfig}
          style={{ width: "100%", height: "300px" }}
          useResizeHandler
        />
      )}
      <p className="chart-note">
        "Reference" stands in for an ARGO float observation — here it is the
        demo backend's synthetic ground truth, not a real observation.
      </p>
    </div>
  );
}
