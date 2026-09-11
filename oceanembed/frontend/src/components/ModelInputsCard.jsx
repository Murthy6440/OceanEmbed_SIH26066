import React from "react";

const ROWS = [
  ["sst", "Sea surface temperature", "°C"],
  ["sss", "Sea surface salinity", "psu"],
  ["ssh", "Sea surface height (SLA)", "m"],
  ["u_curr", "Surface current U", "m/s"],
  ["v_curr", "Surface current V", "m/s"],
  ["u_wind", "Surface wind U", "m/s"],
  ["v_wind", "Surface wind V", "m/s"],
];

export default function ModelInputsCard({ prediction }) {
  return (
    <div className="card">
      <div className="card-head">
        <h2 className="card-title">Model Inputs</h2>
      </div>

      {!prediction && (
        <p className="empty-state">
          Inputs used for the last prediction will appear here.
        </p>
      )}

      {prediction && (
        <table className="inputs-table">
          <tbody>
            {ROWS.map(([key, label, unit]) => (
              <tr key={key}>
                <td>{label}</td>
                <td>
                  {prediction.surface_inputs_used[key].toFixed(3)} {unit}
                </td>
              </tr>
            ))}
            <tr>
              <td>Depth</td>
              <td>{prediction.depth.toFixed(1)} m</td>
            </tr>
            <tr>
              <td>Latitude</td>
              <td>{prediction.lat.toFixed(3)}°N</td>
            </tr>
            <tr>
              <td>Longitude</td>
              <td>{prediction.lon.toFixed(3)}°E</td>
            </tr>
          </tbody>
        </table>
      )}
    </div>
  );
}
