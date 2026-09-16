"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { ShieldAlert, MapPin, LocateFixed } from "lucide-react";
import { getGeofenceAudit } from "@/lib/api";
import { RiskGauge } from "@/components/chat/ResponseCards";
import { useLocation } from "@/components/providers/LocationProvider";
import type { MapPayload } from "@/lib/types";

const MarineMap = dynamic(() => import("@/components/map/MarineMap"), { ssr: false });

export default function RiskPage() {
  const { location } = useLocation();
  const [lat, setLat] = useState(location.lat.toFixed(4));
  const [lon, setLon] = useState(location.lon.toFixed(4));
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const useMyLocation = () => {
    setLat(location.lat.toFixed(4));
    setLon(location.lon.toFixed(4));
  };

  const run = async () => {
    setLoading(true);
    try {
      const res = await getGeofenceAudit({ lat, lon, include_risk: true });
      setResult(res);
    } finally {
      setLoading(false);
    }
  };

  const audit = result?.geospatial_audit;
  const risk = result?.risk_assessment;

  const mapData: MapPayload | null = result
    ? {
        center: { lat: parseFloat(lat), lon: parseFloat(lon) },
        zoom: 8,
        vessel_marker: { lat: parseFloat(lat), lon: parseFloat(lon) },
        pfz_points: [],
        imbl_line: [],
        mpa_features: [],
        mpa_highlight: audit?.mpa_check?.protected_area_name ?? null,
        risk_tint: risk?.color_code ?? "GREEN",
      }
    : null;

  return (
    <div className="h-full flex flex-col md:flex-row">
      <div className="md:w-[46%] h-1/2 md:h-full overflow-y-auto p-6 space-y-6 border-b md:border-b-0 md:border-r border-abyss-700">
        <header className="flex items-center gap-2">
          <ShieldAlert size={20} className="text-depth-teal" />
          <h1 className="font-display text-xl">Risk & Geofencing</h1>
        </header>

        <div className="grid grid-cols-2 gap-3 bg-abyss-900 border border-abyss-700 rounded-lg p-4">
          <input
            value={lat}
            onChange={(e) => setLat(e.target.value)}
            placeholder="Latitude"
            className="bg-abyss-800 border border-abyss-700 rounded-md px-3 py-2 text-sm font-mono"
          />
          <input
            value={lon}
            onChange={(e) => setLon(e.target.value)}
            placeholder="Longitude"
            className="bg-abyss-800 border border-abyss-700 rounded-md px-3 py-2 text-sm font-mono"
          />
          <button
            type="button"
            onClick={useMyLocation}
            className="col-span-2 flex items-center justify-center gap-1.5 text-xs text-depth-teal border border-depth-teal/30 rounded-md px-3 py-2 hover:bg-depth-teal/10"
          >
            <LocateFixed size={13} /> Use {location.label}
          </button>
          <button
            onClick={run}
            disabled={loading}
            className="col-span-2 flex items-center justify-center gap-2 bg-depth-teal text-abyss-950 font-medium rounded-md px-4 py-2 text-sm hover:brightness-110 disabled:opacity-50"
          >
            <MapPin size={14} /> {loading ? "Auditing position…" : "Audit Vessel Position"}
          </button>
        </div>

        {audit && (
          <div className="space-y-3">
            <div className="bg-abyss-900 border border-abyss-700 rounded-lg p-4 space-y-1.5">
              <p className="text-xs text-mist-400">International Maritime Boundary Line</p>
              <p className="text-sm font-medium">{audit.imbl_check.status.replaceAll("_", " ")}</p>
              <p className="text-xs font-mono text-mist-300">
                {audit.imbl_check.distance_to_imbl_km} km · {audit.imbl_check.side_of_border.replaceAll("_", " ")}
              </p>
            </div>

            <div className="bg-abyss-900 border border-abyss-700 rounded-lg p-4 space-y-1.5">
              <p className="text-xs text-mist-400">Marine Protected Area Containment</p>
              <p className="text-sm font-medium">
                {audit.mpa_check.inside_protected_area
                  ? `Inside ${audit.mpa_check.protected_area_name}`
                  : "Not inside any MPA"}
              </p>
              {audit.mpa_check.nearest_protected_area && (
                <p className="text-xs font-mono text-mist-300">
                  Nearest: {audit.mpa_check.nearest_protected_area} ({audit.mpa_check.distance_to_nearest_mpa_km} km)
                </p>
              )}
            </div>

            {risk && (
              <div className="bg-abyss-900 border border-abyss-700 rounded-lg p-4">
                <p className="text-xs text-mist-400 mb-1">Fused Risk Assessment</p>
                <p className="text-sm font-medium mb-1">{risk.verdict.replaceAll("_", " ")}</p>
                <RiskGauge score={risk.risk_score} colorCode={risk.color_code} />
                {risk.alerts.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {risk.alerts.map((a: string, i: number) => (
                      <li key={i} className="text-xs text-verdict-red">{a}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="flex-1 h-1/2 md:h-full">
        <MarineMap data={mapData} />
      </div>
    </div>
  );
}
