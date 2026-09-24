import React from "react";
import Plot, { baseConfig } from "../utils/plotly.js";

export default function DepthSurfaceChart({ gridSurface, heatmap, loading }) {
  if (!gridSurface || !heatmap || gridSurface.lat.length === 0 || gridSurface.lon.length === 0) {
    return (
      <div className="card chart-card">
        <div className="card-head">
          <h2 className="card-title">3D Temperature Surface</h2>
        </div>
        <p className="empty-state">Load the grid to view the 3D temperature surface.</p>
      </div>
    );
  }

  const lat = gridSurface.lat;
  const lon = gridSurface.lon;
  const z = heatmap.map((row) => row.slice());

  return (
    <div className="card chart-card">
      <div className="card-head">
        <h2 className="card-title">3D Temperature Surface</h2>
      </div>

      {loading ? (
        <p className="empty-state">Loading 3D surface…</p>
      ) : (
        <Plot
          data={[
            {
              type: "surface",
              x: lon,
              y: lat,
              z,
              colorscale: [
                [0, "#123d5b"],
                [0.2, "#214f74"],
                [0.5, "#4fd0ff"],
                [0.7, "#ffd166"],
                [1, "#ff7b54"],
              ],
              showscale: true,
              colorbar: {
                title: "°C",
                tickfont: { color: "#eaf2fa" },
                titlefont: { color: "#eaf2fa" },
              },
              hovertemplate: "Lat: %{y:.2f}°N<br>Lon: %{x:.2f}°E<br>Temp: %{z:.2f}°C<extra></extra>",
            },
          ]}
          layout={{
            paper_bgcolor: "transparent",
            plot_bgcolor: "transparent",
            font: { color: "#eaf2fa", size: 11.5 },
            margin: { l: 0, r: 0, t: 0, b: 0 },
            scene: {
              xaxis: {
                title: "Longitude (°E)",
                backgroundcolor: "rgba(10, 15, 20, 0.75)",
                gridcolor: "#24405a",
                zerolinecolor: "#24405a",
                linecolor: "#24405a",
                tickfont: { color: "#eaf2fa" },
                titlefont: { color: "#eaf2fa" },
              },
              yaxis: {
                title: "Latitude (°N)",
                backgroundcolor: "rgba(10, 15, 20, 0.75)",
                gridcolor: "#24405a",
                zerolinecolor: "#24405a",
                linecolor: "#24405a",
                tickfont: { color: "#eaf2fa" },
                titlefont: { color: "#eaf2fa" },
              },
              zaxis: {
                title: "Temperature (°C)",
                backgroundcolor: "rgba(10, 15, 20, 0.75)",
                gridcolor: "#24405a",
                zerolinecolor: "#24405a",
                linecolor: "#24405a",
                tickfont: { color: "#eaf2fa" },
                titlefont: { color: "#eaf2fa" },
              },
              camera: { eye: { x: 1.45, y: 1.45, z: 1.2 } },
            },
          }}
          config={baseConfig}
          style={{ width: "100%", height: "300px" }}
          useResizeHandler
        />
      )}
    </div>
  );
}
