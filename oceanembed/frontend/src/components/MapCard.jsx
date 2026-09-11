import React from "react";
import MapPanel from "./MapPanel.jsx";
import { SCALE_MIN, SCALE_MAX } from "../utils/colorScale.js";

export default function MapCard({
  domain,
  locations,
  selectedLocation,
  gridSurface,
  heatmap,
  heatmapLoading,
  resolutionDeg,
  onSelectDemoLocation,
  onMapClick,
  depth,
  onDepthChange,
  onDepthCommit,
  onGeneratePrediction,
  onDemoAlert,
  predictionLoading,
  backendOnline,
}) {
  const [depthMin, depthMax] = domain.depth_range_m;

  return (
    <div className="card map-card">
      <div className="map-card-head">
        <div>
          <h2 className="card-title" style={{ marginBottom: 2 }}>
            North Indian Ocean — Temperature Field
          </h2>
          <p className="card-subtitle" style={{ margin: 0 }}>
            {domain.lat_range_degN[0]}–{domain.lat_range_degN[1]}°N,{" "}
            {domain.lon_range_degE[0]}–{domain.lon_range_degE[1]}°E · grid
            spacing {resolutionDeg}°
          </p>
        </div>
      </div>

      <div className="map-wrap-outer" style={{ position: "relative" }}>
        {heatmapLoading && (
          <div className="map-overlay-loading">
            Recomputing subsurface layer at {depth} m…
          </div>
        )}
        <MapPanel
          domain={domain}
          locations={locations}
          selectedLocation={selectedLocation}
          gridSurface={gridSurface}
          heatmap={heatmap}
          onSelectDemoLocation={onSelectDemoLocation}
          onMapClick={onMapClick}
        />
      </div>

      <div className="legend">
        <span>{SCALE_MIN}°C</span>
        <span className="legend-bar" />
        <span>{SCALE_MAX}°C</span>
      </div>

      <div className="controls">
        <div className="control-row">
          <div className="control-block">
            <span className="control-label">Demo virtual float</span>
            <select
              value={selectedLocation?.location_id || ""}
              onChange={(e) => {
                const loc = locations.find(
                  (l) => l.location_id === e.target.value
                );
                if (loc) onSelectDemoLocation(loc);
              }}
            >
              <option value="" disabled>
                Select a location…
              </option>
              {locations.map((loc) => (
                <option key={loc.location_id} value={loc.location_id}>
                  {loc.name} ({loc.lat.toFixed(1)}°N, {loc.lon.toFixed(1)}°E)
                </option>
              ))}
            </select>
          </div>

          <div className="control-block">
            <span className="control-label">
              Depth <span className="depth-value">{depth} m</span>
            </span>
            <input
              type="range"
              min={depthMin}
              max={depthMax}
              step={10}
              value={depth}
              onChange={(e) => onDepthChange(Number(e.target.value))}
              onMouseUp={onDepthCommit}
              onTouchEnd={onDepthCommit}
              onKeyUp={onDepthCommit}
            />
          </div>
        </div>

        <div className="control-row">
          <div className="selected-point">
            {selectedLocation ? (
              <>
                Selected: <b>{selectedLocation.name}</b> ·{" "}
                {selectedLocation.lat.toFixed(2)}°N,{" "}
                {selectedLocation.lon.toFixed(2)}°E
              </>
            ) : (
              "Click the map, or pick a virtual float, to select a location."
            )}
          </div>
        </div>

        <button
          className="btn btn-block"
          onClick={onGeneratePrediction}
          disabled={!selectedLocation || predictionLoading || !backendOnline}
        >
          {predictionLoading
            ? "Predicting…"
            : `Generate Prediction @ ${depth} m`}
        </button>

        <button
          className="btn btn-block"
          onClick={onDemoAlert}
          style={{ background: "linear-gradient(135deg, #ef5a5a, #b73030)" }}
        >
          Demo Disaster Alert
        </button>

        <span className="hint">
          Map click selects any point in the domain and loads its full
          0–1000 m profile. The depth slider recolors the map layer; the
          button runs a single point prediction for the cards below.
        </span>
      </div>
    </div>
  );
}
