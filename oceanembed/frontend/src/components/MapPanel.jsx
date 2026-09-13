import React, { useEffect, useMemo, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Rectangle,
  CircleMarker,
  Tooltip,
  useMap,
  useMapEvents,
} from "react-leaflet";
import { tempToColor } from "../utils/colorScale.js";

function MapFocus({ selectedLocation }) {
  const map = useMap();

  useEffect(() => {
    if (!selectedLocation) return;
    map.flyTo([selectedLocation.lat, selectedLocation.lon], 6, {
      animate: true,
      duration: 1.2,
    });
  }, [map, selectedLocation]);

  return null;
}

function ZoomTracker({ onZoomChange }) {
  const map = useMap();

  useEffect(() => {
    const updateZoom = () => onZoomChange(map.getZoom());
    updateZoom();
    map.on("zoomend", updateZoom);
    return () => map.off("zoomend", updateZoom);
  }, [map, onZoomChange]);

  return null;
}

function ClickHandler({ domain, onMapClick }) {
  useMapEvents({
    click(e) {
      const { lat, lng } = e.latlng;
      const [latMin, latMax] = domain.lat_range_degN;
      const [lonMin, lonMax] = domain.lon_range_degE;
      if (lat < latMin || lat > latMax || lng < lonMin || lng > lonMax) return;
      onMapClick(lat, lng);
    },
  });
  return null;
}

export default function MapPanel({
  domain,
  locations,
  selectedLocation,
  gridSurface,
  heatmap,
  onSelectDemoLocation,
  onMapClick,
}) {
  const [latMin, latMax] = domain.lat_range_degN;
  const [lonMin, lonMax] = domain.lon_range_degE;
  const [mapZoom, setMapZoom] = useState(4);
  const bounds = [
    [latMin, lonMin],
    [latMax, lonMax],
  ];
  const center = [(latMin + latMax) / 2, (lonMin + lonMax) / 2];

  const heatmapStride = useMemo(() => {
    if (mapZoom >= 7) return 4;
    if (mapZoom >= 5) return 2;
    return 1;
  }, [mapZoom]);

  const halfRes = useMemo(() => {
    if (!gridSurface || gridSurface.lat.length < 2) return 1.5;
    const baseStep = Math.abs(gridSurface.lat[1] - gridSurface.lat[0]);
    return (baseStep * heatmapStride) / 2;
  }, [gridSurface, heatmapStride]);

  const cells = useMemo(() => {
    if (!gridSurface || !heatmap) return [];
    const out = [];
    const { lat, lon } = gridSurface;
    for (let i = 0; i < lat.length; i += heatmapStride) {
      for (let j = 0; j < lon.length; j += heatmapStride) {
        const value = heatmap[i] ? heatmap[i][j] : null;
        out.push({
          key: `${i}-${j}`,
          bounds: [
            [lat[i] - halfRes, lon[j] - halfRes],
            [lat[i] + halfRes, lon[j] + halfRes],
          ],
          color: tempToColor(value),
        });
      }
    }
    return out;
  }, [gridSurface, heatmap, halfRes, heatmapStride]);

  return (
    <div className="map-wrap">
      <MapContainer
        center={center}
        zoom={4}
        minZoom={3}
        maxZoom={8}
        maxBounds={bounds}
        maxBoundsViscosity={1.0}
        scrollWheelZoom
        preferCanvas
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <ZoomTracker onZoomChange={setMapZoom} />
        <MapFocus selectedLocation={selectedLocation} />
        <ClickHandler domain={domain} onMapClick={onMapClick} />

        {cells.map((c) => (
          <Rectangle
            key={c.key}
            bounds={c.bounds}
            pathOptions={{
              color: c.color,
              weight: 0,
              fillColor: c.color,
              fillOpacity: 0.62,
            }}
            interactive={false}
          />
        ))}

        {locations.map((loc) => {
          const isSelected =
            selectedLocation &&
            selectedLocation.location_id === loc.location_id;
          return (
            <CircleMarker
              key={loc.location_id}
              center={[loc.lat, loc.lon]}
              radius={isSelected ? 9 : 6}
              pathOptions={{
                color: isSelected ? "#ffe6ab" : "#eaf2fa",
                weight: isSelected ? 2.5 : 1.5,
                fillColor: isSelected ? "#4fd0ff" : "#0b5f8a",
                fillOpacity: 0.9,
              }}
              eventHandlers={{
                click: () => onSelectDemoLocation(loc),
              }}
            >
              <Tooltip direction="top" offset={[0, -6]} opacity={0.95}>
                {loc.name}
              </Tooltip>
            </CircleMarker>
          );
        })}

        {selectedLocation && !selectedLocation.location_id && (
          <CircleMarker
            center={[selectedLocation.lat, selectedLocation.lon]}
            radius={8}
            pathOptions={{
              color: "#ffe6ab",
              weight: 2.5,
              fillColor: "#f5b942",
              fillOpacity: 0.9,
            }}
          >
            <Tooltip direction="top" offset={[0, -6]} opacity={0.95} permanent>
              Custom point
            </Tooltip>
          </CircleMarker>
        )}
      </MapContainer>
    </div>
  );
}
