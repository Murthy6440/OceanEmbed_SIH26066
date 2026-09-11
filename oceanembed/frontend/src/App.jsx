import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  API_BASE,
  DEFAULT_DOMAIN,
  buildCustomProfile,
  computeHeatmapAtDepth,
  getGrid,
  getHealth,
  getLocations,
  getProfile,
  getValidation,
  predictPoint,
} from "./api/client.js";
import {
  evaluateDisasterRisk,
  triggerDisasterAlarm,
} from "./utils/disasterRisk.js";

import Header from "./components/Header.jsx";
import MapCard from "./components/MapCard.jsx";
import PredictionCard from "./components/PredictionCard.jsx";
import MetricCards from "./components/MetricCards.jsx";
import ModelInputsCard from "./components/ModelInputsCard.jsx";
import ProfileChart from "./components/ProfileChart.jsx";
import ComparisonChart from "./components/ComparisonChart.jsx";
import ValidationScatter from "./components/ValidationScatter.jsx";

const GRID_RESOLUTION_DEG = 3.0;
// Starts at the surface (0 m) so the initial map layer matches /api/grid's
// SST field exactly, with no extra batch-predict calls needed on first load.
// Moving the depth slider is what demonstrates the subsurface estimation.
const DEFAULT_DEPTH = 0;

export default function App() {
  const [backendStatus, setBackendStatus] = useState("checking");

  const [domain, setDomain] = useState(DEFAULT_DOMAIN);
  const [locations, setLocations] = useState([]);

  const [gridSurface, setGridSurface] = useState(null);
  const [heatmap, setHeatmap] = useState(null);
  const [heatmapLoading, setHeatmapLoading] = useState(false);

  const [depth, setDepth] = useState(DEFAULT_DEPTH);

  const [selectedLocation, setSelectedLocation] = useState(null);
  const [profile, setProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState(null);

  const [prediction, setPrediction] = useState(null);
  const [predictionLoading, setPredictionLoading] = useState(false);
  const [predictionError, setPredictionError] = useState(null);
  const [risk, setRisk] = useState(null);

  const [validation, setValidation] = useState(null);
  const [validationLoading, setValidationLoading] = useState(true);
  const [validationError, setValidationError] = useState(null);

  // Guards against out-of-order async responses (e.g. rapid location clicks).
  const profileRequestId = useRef(0);
  const heatmapRequestId = useRef(0);

  useEffect(() => {
    if (!prediction) {
      setRisk(null);
      return;
    }

    const nextRisk = evaluateDisasterRisk(
      prediction.predicted_temperature_degC,
      prediction.depth
    );
    setRisk(nextRisk);
  }, [prediction]);

  useEffect(() => {
    if (!risk || risk.level === "normal") return;
    triggerDisasterAlarm(risk.level);
  }, [risk]);

  // --------------------------------------------------------------- bootstrap
  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const health = await getHealth();
        if (cancelled) return;
        setBackendStatus("online");
      } catch {
        if (!cancelled) setBackendStatus("offline");
      }
    })();

    (async () => {
      try {
        const loc = await getLocations();
        if (cancelled) return;
        setLocations(loc.locations || []);
        if (loc.domain) setDomain(loc.domain);
      } catch {
        /* handled by backendStatus / banner */
      }
    })();

    (async () => {
      try {
        const grid = await getGrid(GRID_RESOLUTION_DEG);
        if (cancelled) return;
        setGridSurface(grid);
        setHeatmap(grid.fields.sst.map((row) => row.slice()));
      } catch {
        /* map simply stays without a temperature layer */
      }
    })();

    (async () => {
      try {
        const v = await getValidation();
        if (cancelled) return;
        setValidation(v);
        setValidationError(null);
      } catch (err) {
        if (!cancelled) {
          setValidation(null);
          setValidationError(err.message || "Could not load validation metrics.");
        }
      } finally {
        if (!cancelled) setValidationLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  // Auto-select the first demo location once both locations & grid are ready,
  // so the dashboard isn't empty on first load.
  useEffect(() => {
    if (!selectedLocation && locations.length > 0) {
      handleSelectDemoLocation(locations[0]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locations]);

  // ----------------------------------------------------------- heatmap logic
  const refreshHeatmap = useCallback(
    async (targetDepth) => {
      if (!gridSurface) return;
      const reqId = ++heatmapRequestId.current;
      setHeatmapLoading(true);
      try {
        const grid = await computeHeatmapAtDepth(gridSurface, targetDepth, {
          concurrency: 16,
        });
        if (reqId === heatmapRequestId.current) setHeatmap(grid);
      } finally {
        if (reqId === heatmapRequestId.current) setHeatmapLoading(false);
      }
    },
    [gridSurface]
  );

  const handleDepthCommit = useCallback(() => {
    refreshHeatmap(depth);
  }, [depth, refreshHeatmap]);

  // --------------------------------------------------------- location logic
  async function loadProfileForDemoLocation(loc) {
    const reqId = ++profileRequestId.current;
    setProfileLoading(true);
    setProfile(null);
    setProfileError(null);
    try {
      const p = await getProfile(loc.location_id);
      if (reqId !== profileRequestId.current) return;
      setProfile({
        location: p.location,
        surface_fields: p.surface_fields,
        depth_m: p.depth_m,
        predicted_temperature_degC: p.predicted_temperature_degC,
        predicted_salinity_psu: p.predicted_salinity_psu,
        synthetic_reference_temperature_degC: p.synthetic_reference_temperature_degC,
        synthetic_reference_salinity_psu: p.synthetic_reference_salinity_psu,
      });
    } catch (err) {
      if (reqId === profileRequestId.current) {
        setProfile(null);
        setProfileError(err.message || "Could not load the temperature profile.");
      }
    } finally {
      if (reqId === profileRequestId.current) setProfileLoading(false);
    }
  }

  async function loadProfileForCustomPoint(lat, lon) {
    const reqId = ++profileRequestId.current;
    setProfileLoading(true);
    setProfile(null);
    setProfileError(null);
    try {
      const p = await buildCustomProfile(lat, lon, { concurrency: 8 });
      if (reqId !== profileRequestId.current) return;
      setProfile(p);
    } catch (err) {
      if (reqId === profileRequestId.current) {
        setProfile(null);
        setProfileError(err.message || "Could not load the temperature profile.");
      }
    } finally {
      if (reqId === profileRequestId.current) setProfileLoading(false);
    }
  }

  function handleSelectDemoLocation(loc) {
    setSelectedLocation(loc);
    setPrediction(null);
    setPredictionError(null);
    loadProfileForDemoLocation(loc);
  }

  function handleMapClick(lat, lon) {
    const custom = { location_id: null, name: "Custom Point", lat, lon };
    setSelectedLocation(custom);
    setPrediction(null);
    setPredictionError(null);
    loadProfileForCustomPoint(lat, lon);
  }

  // ----------------------------------------------------- generate prediction
  async function handleGeneratePrediction() {
    if (!selectedLocation) return;
    setPredictionLoading(true);
    setPredictionError(null);
    try {
      const result = await predictPoint({
        lat: selectedLocation.lat,
        lon: selectedLocation.lon,
        depth,
      });
      setPrediction(result);
    } catch (err) {
      // Keep any previous prediction visible; button remains usable to retry.
      setPredictionError(err.message || "Prediction request failed.");
    } finally {
      setPredictionLoading(false);
    }
  }

  function handleDemoAlert() {
    const demoRisk = evaluateDisasterRisk(35, 1000);
    triggerDisasterAlarm(demoRisk.level);
    setRisk(demoRisk);
    setPrediction({
      predicted_temperature_degC: 35,
      predicted_salinity_psu: 34.5,
      synthetic_reference_temperature_degC: 12,
      synthetic_reference_salinity_psu: 35.2,
      depth: 1000,
      lat: selectedLocation?.lat ?? 15.0,
      lon: selectedLocation?.lon ?? 70.0,
      surface_inputs_used: {
        sst: 30,
        sss: 34.5,
        ssh: 0.2,
        u_curr: 0.1,
        v_curr: -0.2,
        u_wind: 5.0,
        v_wind: 3.0,
      },
    });
  }

  return (
    <div className="app">
      <Header backendStatus={backendStatus} apiBase={API_BASE} />

      {backendStatus === "offline" && (
        <p className="hint" style={{ marginTop: 10 }}>
          Could not reach the OceanEmbed backend at <b>{API_BASE}</b>. Start
          it with <code>uvicorn main:app --reload --port 8000</code> from{" "}
          <code>oceanembed_backend/</code>, then reload this page.
        </p>
      )}

      <div className="dashboard-grid">
        <MapCard
          domain={domain}
          locations={locations}
          selectedLocation={selectedLocation}
          gridSurface={gridSurface}
          heatmap={heatmap}
          heatmapLoading={heatmapLoading}
          resolutionDeg={GRID_RESOLUTION_DEG}
          onSelectDemoLocation={handleSelectDemoLocation}
          onMapClick={handleMapClick}
          depth={depth}
          onDepthChange={setDepth}
          onDepthCommit={handleDepthCommit}
          onGeneratePrediction={handleGeneratePrediction}
          onDemoAlert={handleDemoAlert}
          predictionLoading={predictionLoading}
          backendOnline={backendStatus === "online"}
        />

        <div className="right-column">
          <PredictionCard
            prediction={prediction}
            loading={predictionLoading}
            error={predictionError}
            risk={risk}
          />
          <MetricCards
            validation={validation}
            loading={validationLoading}
            error={validationError}
          />
          <ModelInputsCard prediction={prediction} />
        </div>
      </div>

      <div className="charts-row">
        <ProfileChart profile={profile} loading={profileLoading} error={profileError} />
        <ComparisonChart profile={profile} loading={profileLoading} error={profileError} />
        <ValidationScatter profile={profile} loading={profileLoading} error={profileError} />
      </div>

    </div>
  );
}
