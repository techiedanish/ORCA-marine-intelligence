"use client";

import { useState } from "react";
import { CloudLightning, Wind, AlertTriangle, Waves, LocateFixed } from "lucide-react";
import { getSeaSafety } from "@/lib/api";
import { useLocation } from "@/components/providers/LocationProvider";

const ZONES = [
  { value: "arabian_sea_south", label: "Arabian Sea (South) — Kerala/Karnataka" },
  { value: "arabian_sea_north", label: "Arabian Sea (North) — Gujarat/Maharashtra" },
  { value: "bay_of_bengal_south", label: "Bay of Bengal (South) — Tamil Nadu" },
  { value: "bay_of_bengal_north", label: "Bay of Bengal (North) — Andhra/Odisha" },
  { value: "west_bengal_coast", label: "West Bengal Coast" },
];

const VERDICT_COLOR: Record<string, string> = {
  GREEN_SAFE_TO_SAIL: "text-verdict-green",
  AMBER_CAUTION_ALERT: "text-verdict-amber",
  RED_ALERT_DO_NOT_SAIL: "text-verdict-red",
};

export default function WeatherPage() {
  const { location } = useLocation();
  const [zone, setZone] = useState(ZONES[0].value);
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
      const res = await getSeaSafety({ sea_zone: zone, lat, lon });
      setResult(res);
    } finally {
      setLoading(false);
    }
  };

  const f = result?.findings;
  const mt = f?.marine_telemetry;

  return (
    <div className="h-full overflow-y-auto p-6 max-w-4xl mx-auto space-y-6">
      <header className="flex items-center gap-2">
        <CloudLightning size={20} className="text-depth-teal" />
        <h1 className="font-display text-xl">Weather Intelligence</h1>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 bg-abyss-900 border border-abyss-700 rounded-lg p-4">
        <select
          value={zone}
          onChange={(e) => setZone(e.target.value)}
          className="sm:col-span-2 bg-abyss-800 border border-abyss-700 rounded-md px-3 py-2 text-sm"
        >
          {ZONES.map((z) => (
            <option key={z.value} value={z.value}>{z.label}</option>
          ))}
        </select>
        <button
          type="button"
          onClick={useMyLocation}
          className="flex items-center justify-center gap-1.5 text-xs text-depth-teal border border-depth-teal/30 rounded-md px-3 py-2 hover:bg-depth-teal/10"
        >
          <LocateFixed size={13} /> Use {location.label}
        </button>
        <button
          onClick={run}
          disabled={loading}
          className="bg-depth-teal text-abyss-950 font-medium rounded-md px-4 py-2 text-sm hover:brightness-110 disabled:opacity-50"
        >
          {loading ? "Fetching bulletins…" : "Check Sea Zone"}
        </button>
        <p className="sm:col-span-4 text-[10px] font-mono text-mist-400">
          Live point query: {lat}°N, {lon}°E — edit the fields above or use your grounded location.
        </p>
      </div>

      {f && (
        <div className="space-y-4">
          <div className={`text-lg font-display ${VERDICT_COLOR[f.safety_verdict] || "text-white"}`}>
            {f.safety_verdict?.replaceAll("_", " ")}
          </div>
          <p className="text-sm text-mist-300">{f.action_guidance}</p>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <div className="bg-abyss-900 border border-abyss-700 rounded-lg p-4">
              <div className="flex items-center gap-1.5 text-mist-400 text-xs mb-1">
                <Wind size={13} /> Wind (Open-Meteo, free)
              </div>
              <p className="text-2xl font-mono">{mt?.wind?.speed_knots} <span className="text-sm text-mist-400">kts</span></p>
              <p className="text-xs text-mist-400 mt-1">{mt?.wind?.direction_cardinal} · gusts {mt?.wind?.gust_knots} kts</p>
            </div>
            <div className="bg-abyss-900 border border-abyss-700 rounded-lg p-4">
              <div className="flex items-center gap-1.5 text-mist-400 text-xs mb-1">
                <Waves size={13} /> Swell / Wave Height
              </div>
              <p className="text-2xl font-mono">{mt?.wave_height_m ?? "—"} <span className="text-sm text-mist-400">m</span></p>
              <p className="text-xs text-mist-400 mt-1">{mt?.sea_state?.description}</p>
            </div>
            <div className="bg-abyss-900 border border-abyss-700 rounded-lg p-4">
              <p className="text-xs text-mist-400 mb-1">Beaufort Scale</p>
              <p className="text-lg">Scale {mt?.sea_state?.scale}</p>
              <p className="text-xs text-mist-400 mt-1 font-mono">{mt?.sea_state?.wave_height_m}m (typical)</p>
            </div>
            <div className="bg-abyss-900 border border-abyss-700 rounded-lg p-4">
              <p className="text-xs text-mist-400 mb-1">Squall Risk</p>
              <p className="text-lg">{mt?.squall_risk}</p>
              <p className="text-xs text-mist-400 mt-1 font-mono">Pressure {mt?.pressure_hpa} hPa</p>
            </div>
          </div>

          <p className="text-[10px] font-mono text-mist-400">
            {mt?.source} · {mt?.is_live_feed ? "live reading" : "grounded estimate (Open-Meteo unreachable)"}
          </p>

          <div className="bg-abyss-900 border border-abyss-700 rounded-lg p-4">
            <p className="text-xs text-mist-400 mb-1.5">IMD 24-hr Fishermen Warning — {f.zone_fishermen_warning?.zone}</p>
            <p className="text-sm">{f.zone_fishermen_warning?.warning_message}</p>
          </div>

          {f.is_cyclone_active && (
            <div className="bg-verdict-red/10 border border-verdict-red/30 rounded-lg p-4 flex items-start gap-2">
              <AlertTriangle size={16} className="text-verdict-red shrink-0 mt-0.5" />
              <p className="text-sm text-verdict-red">
                {f.active_cyclones_count} active cyclone(s) tracked by IMD RSMC Cyclone Warning Division.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
