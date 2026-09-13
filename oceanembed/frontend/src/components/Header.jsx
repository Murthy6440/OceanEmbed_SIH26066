import React from "react";

export default function Header({ backendStatus, apiBase }) {
  const label =
    backendStatus === "online"
      ? "Backend online"
      : backendStatus === "offline"
      ? "Backend unreachable"
      : "Checking backend…";

  return (
    <header className="app-header">
      <div className="brand">
        <div className="brand-mark">🌊</div>
        <div>
          <h1 className="brand-title">OceanEmbed</h1>
          <p className="brand-subtitle">
            SIH26066 · Predicting subsurface ocean variables from surface observations
          </p>
        </div>
      </div>
      <div className="status-cluster">
        <span className="status-pill">
          <span className={`status-dot ${backendStatus}`} />
          {label}
        </span>
        <span>{apiBase}</span>
      </div>
    </header>
  );
}
