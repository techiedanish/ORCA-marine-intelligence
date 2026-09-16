"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { GoogleMap, useLoadScript, Marker, Polyline, Polygon } from "@react-google-maps/api";
import { Layers, KeyRound, AlertTriangle } from "lucide-react";
import type { MapPayload, ColorCode } from "@/lib/types";

const RISK_HEX: Record<ColorCode, string> = {
  GREEN: "#3FBF7F",
  AMBER: "#E8A93B",
  RED: "#E24C4C",
};

// Baked in at BUILD time (this app is statically exported) — see README for how to
// get a free key from Google Cloud Console and where to put it before building.
const GOOGLE_MAPS_API_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "";

const mapContainerStyle: React.CSSProperties = { width: "100%", height: "100%" };

// A standard published Google Maps "night mode" style (dark land/water, muted
// labels) — this replaces the previous CSS-invert-filter hack over OpenStreetMap
// tiles with a properly supported dark theme from the provider itself.
const DARK_MAP_STYLE = [
  { elementType: "geometry", stylers: [{ color: "#0F2131" }] },
  { elementType: "labels.text.stroke", stylers: [{ color: "#0A1622" }] },
  { elementType: "labels.text.fill", stylers: [{ color: "#8FA6B8" }] },
  { featureType: "administrative", elementType: "geometry", stylers: [{ color: "#16324A" }] },
  { featureType: "administrative.country", elementType: "labels.text.fill", stylers: [{ color: "#B7C7D3" }] },
  { featureType: "landscape", elementType: "geometry", stylers: [{ color: "#0F2131" }] },
  { featureType: "poi", stylers: [{ visibility: "off" }] },
  { featureType: "road", elementType: "geometry", stylers: [{ color: "#16324A" }] },
  { featureType: "road", elementType: "labels", stylers: [{ visibility: "off" }] },
  { featureType: "transit", stylers: [{ visibility: "off" }] },
  { featureType: "water", elementType: "geometry", stylers: [{ color: "#0A1622" }] },
  { featureType: "water", elementType: "labels.text.fill", stylers: [{ color: "#4FD1C5" }] },
] as google.maps.MapTypeStyle[];

type LayerKey = "pfz" | "imbl" | "mpa";

interface Props {
  data: MapPayload | null;
}

function MapMessage({ icon: Icon, title, body }: { icon: any; title: string; body: React.ReactNode }) {
  return (
    <div className="h-full w-full flex items-center justify-center p-6">
      <div className="max-w-sm text-center space-y-2">
        <Icon size={22} className="mx-auto text-mist-400" />
        <p className="text-sm text-mist-300">{title}</p>
        <p className="text-xs text-mist-400 leading-relaxed">{body}</p>
      </div>
    </div>
  );
}

export default function MarineMap({ data }: Props) {
  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: GOOGLE_MAPS_API_KEY,
    id: "orca-google-maps-script",
  });

  const [layers, setLayers] = useState<Record<LayerKey, boolean>>({ pfz: true, imbl: true, mpa: true });
  const [panelOpen, setPanelOpen] = useState(false);
  const mapRef = useRef<google.maps.Map | null>(null);

  const center = data?.center ?? { lat: 9.9312, lon: 76.2673 };
  const zoom = data?.zoom ?? 6;
  const riskTint = data?.risk_tint ?? "GREEN";

  const imblPath = useMemo(
    () => (data?.imbl_line || []).map(([lon, lat]) => ({ lat, lng: lon })),
    [data?.imbl_line]
  );

  const toggleLayer = (key: LayerKey) => setLayers((prev) => ({ ...prev, [key]: !prev[key] }));

  const onLoad = useCallback((map: google.maps.Map) => {
    mapRef.current = map;
  }, []);
  const onUnmount = useCallback(() => {
    mapRef.current = null;
  }, []);

  // Move the camera only when the RESOLVED center/zoom actually changes (primitive
  // dependency, not object identity). google.maps.Map#panTo smoothly pans for short
  // moves and jumps directly for long ones — no dramatic zoom-out/zoom-in arc, which
  // is what made the previous Leaflet flyTo() implementation feel erratic on every
  // re-render.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    map.panTo({ lat: center.lat, lng: center.lon });
    map.setZoom(zoom);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [center.lat, center.lon, zoom]);

  const layersPanel = (
    <div className="absolute top-3 right-3 z-20 flex flex-col items-end gap-2">
      <button
        onClick={() => setPanelOpen((v) => !v)}
        className="flex items-center gap-1.5 bg-abyss-900/90 border border-abyss-700 text-mist-300 text-xs px-2.5 py-1.5 rounded-md shadow-panel hover:text-white"
      >
        <Layers size={13} /> Layers
      </button>
      {panelOpen && (
        <div className="bg-abyss-900/95 border border-abyss-700 rounded-md shadow-panel px-3 py-2.5 text-xs w-44 space-y-2">
          {[
            { key: "pfz" as LayerKey, label: "PFZ Sectors" },
            { key: "imbl" as LayerKey, label: "IMBL Boundary" },
            { key: "mpa" as LayerKey, label: "Marine Protected Areas" },
          ].map(({ key, label }) => (
            <label key={key} className="flex items-center gap-2 cursor-pointer text-mist-300">
              <input
                type="checkbox"
                checked={layers[key]}
                onChange={() => toggleLayer(key)}
                className="accent-depth-teal"
              />
              {label}
            </label>
          ))}
        </div>
      )}
    </div>
  );

  const riskBadge = (
    <div className="absolute bottom-3 left-3 z-20 flex items-center gap-2 bg-abyss-900/90 border border-abyss-700 rounded-md px-2.5 py-1.5 text-[11px] font-mono text-mist-300">
      <span className="h-2 w-2 rounded-full" style={{ background: RISK_HEX[riskTint] }} />
      Sea zone risk tint: {riskTint}
    </div>
  );

  const riskGlow = (
    <div
      className="absolute inset-0 pointer-events-none z-10 transition-colors duration-700"
      style={{ boxShadow: `inset 0 0 140px ${RISK_HEX[riskTint]}33` }}
    />
  );

  if (!GOOGLE_MAPS_API_KEY) {
    return (
      <MapMessage
        icon={KeyRound}
        title="Google Maps API key required"
        body={
          <>
            Add a free key to <code className="text-depth-teal">apps/web3/.env.local</code> as{" "}
            <code className="text-depth-teal">NEXT_PUBLIC_GOOGLE_MAPS_API_KEY</code>, then rebuild
            (<code className="text-depth-teal">python run.py --rebuild</code>). Full steps are in the
            project README.
          </>
        }
      />
    );
  }

  if (loadError) {
    return (
      <MapMessage
        icon={AlertTriangle}
        title="Google Maps failed to load"
        body="Check that the API key in apps/web3/.env.local is valid, that the Maps JavaScript API is enabled for it in Google Cloud Console, and that this domain isn't blocked by the key's restrictions."
      />
    );
  }

  if (!isLoaded) {
    return (
      <div className="h-full w-full flex items-center justify-center text-mist-400 text-sm">
        Loading chart…
      </div>
    );
  }

  return (
    <div className="relative h-full w-full">
      {riskGlow}
      {layersPanel}
      {riskBadge}

      <GoogleMap
        mapContainerStyle={mapContainerStyle}
        center={{ lat: center.lat, lng: center.lon }}
        zoom={zoom}
        onLoad={onLoad}
        onUnmount={onUnmount}
        options={{
          styles: DARK_MAP_STYLE,
          disableDefaultUI: false,
          zoomControl: true,
          streetViewControl: false,
          mapTypeControl: false,
          fullscreenControl: false,
          clickableIcons: false,
        }}
      >
        {layers.imbl && imblPath.length > 1 && (
          <Polyline
            path={imblPath}
            options={{
              strokeColor: "#E8A93B",
              strokeWeight: 2.5,
              strokeOpacity: 0.9,
            }}
          />
        )}

        {layers.mpa &&
          (data?.mpa_features || []).map((feat, idx) => {
            if (feat.geometry.type !== "Polygon") return null;
            const ring = feat.geometry.coordinates[0] as number[][];
            const paths = ring.map(([lon, lat]) => ({ lat, lng: lon }));
            const highlighted = data?.mpa_highlight === feat.properties.name;
            return (
              <Polygon
                key={idx}
                paths={paths}
                options={{
                  strokeColor: highlighted ? "#E24C4C" : "#4FD1C5",
                  strokeWeight: 1.5,
                  fillColor: highlighted ? "#E24C4C" : "#4FD1C5",
                  fillOpacity: highlighted ? 0.35 : 0.12,
                }}
              />
            );
          })}

        {layers.pfz &&
          (data?.pfz_points || []).map((p, idx) =>
            p.lat && p.lon ? (
              <Marker
                key={idx}
                position={{ lat: p.lat, lng: p.lon }}
                title={[
                  p.name,
                  p.sst_celsius ? `SST: ${p.sst_celsius}°C` : null,
                  p.chlorophyll_mg_m3 ? `Chl-a: ${p.chlorophyll_mg_m3} mg/m³` : null,
                  p.fapi_score ? `FAPI: ${p.fapi_score}/100` : null,
                ]
                  .filter(Boolean)
                  .join("\n")}
                icon={{
                  path: google.maps.SymbolPath.CIRCLE,
                  scale: 6 + Math.min(6, (p.fapi_score || 50) / 20),
                  fillColor: "#4FD1C5",
                  fillOpacity: 0.65,
                  strokeColor: "#4FD1C5",
                  strokeWeight: 1,
                }}
              />
            ) : null
          )}

        {data?.vessel_marker && (
          <Marker
            position={{ lat: data.vessel_marker.lat, lng: data.vessel_marker.lon }}
            title="Vessel position"
            icon={{
              path: google.maps.SymbolPath.CIRCLE,
              scale: 8,
              fillColor: "#7DD3E8",
              fillOpacity: 1,
              strokeColor: "#05131F",
              strokeWeight: 2,
            }}
          />
        )}
      </GoogleMap>
    </div>
  );
}
