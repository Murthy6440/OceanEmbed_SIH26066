import React, { useMemo } from "react";
import Plot, { baseLayout, baseConfig } from "../utils/plotly.js";

export default function ValidationScatter({ profile, loading, error }) {
  const diag = useMemo(() => {
    if (!profile) return null;
    const all = [
      ...profile.predicted_temperature_degC,
      ...profile.synthetic_reference_temperature_degC,
    ];
    const min = Math.min(...all) - 0.5;
    const max = Math.max(...all) + 0.5;
    return [min, max];
  }, [profile]);

  return (
    <div className="card chart-card">
      <div className="card-head">
        <h2 className="card-title">Predicted vs Observed — Validation</h2>
      </div>

      {loading && <p className="empty-state">Loading validation scatter…</p>}
      {!loading && error && (
        <p className="error-state">Could not load validation scatter: {error}</p>
      )}
      {!loading && !error && !profile && (
        <p className="empty-state">
          Select a location to see predicted-vs-reference agreement across
          its depth profile.
        </p>
      )}

      {!loading && profile && diag && (
        <Plot
          data={[
            {
              x: diag,
              y: diag,
              type: "scatter",
              mode: "lines",
              name: "1:1 line",
              line: { color: "#9db2c6", width: 1.5, dash: "dash" },
              hoverinfo: "skip",
            },
            {
              x: profile.synthetic_reference_temperature_degC,
              y: profile.predicted_temperature_degC,
              type: "scatter",
              mode: "markers",
              name: "Depth levels",
              marker: {
                size: 8,
                color: profile.depth_m,
                colorscale: "Viridis",
                showscale: true,
                colorbar: { title: "m", thickness: 10, len: 0.7 },
              },
              text: profile.depth_m.map((d) => `${d} m`),
              hovertemplate: "ref %{x:.2f}°C · pred %{y:.2f}°C · %{text}<extra></extra>",
            },
          ]}
          layout={{
            ...baseLayout,
            xaxis: { ...baseLayout.xaxis, title: "Reference temp (°C)" },
            yaxis: { ...baseLayout.yaxis, title: "Predicted temp (°C)" },
            showlegend: false,
          }}
          config={baseConfig}
          style={{ width: "100%", height: "300px" }}
          useResizeHandler
        />
      )}
      <p className="chart-note">
        Points from the {profile?.depth_m?.length || 0} depth levels at{" "}
        {profile?.location?.name || "the selected location"}. Global RMSE /
        correlation / bias (all held-out samples) are in the metric cards
        above.
      </p>
    </div>
  );
}
