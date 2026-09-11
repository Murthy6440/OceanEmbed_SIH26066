import React, { useMemo } from "react";
import {
  MapContainer,
  TileLayer,
  Rectangle,
  CircleMarker,
  Tooltip,
  useMapEvents,
} from "react-leaflet";
import { tempToColor } from "../utils/colorScale.js";

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
  const bounds = [
    [latMin, lonMin],
    [latMax, lonMax],
  ];
  const center = [(latMin + latMax) / 2, (lonMin + lonMax) / 2];

  const halfRes = useMemo(() => {
    if (!gridSurface || gridSurface.lat.length < 2) return 1.5;
    return Math.abs(gridSurface.lat[1] - gridSurface.lat[0]) / 2;
  }, [gridSurface]);

  const cells = useMemo(() => {
    if (!gridSurface || !heatmap) return [];
    const out = [];
    const { lat, lon } = gridSurface;
    for (let i = 0; i < lat.length; i++) {
      for (let j = 0; j < lon.length; j++) {
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
  }, [gridSurface, heatmap, halfRes]);

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
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
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
