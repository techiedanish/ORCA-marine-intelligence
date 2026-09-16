"use client";

import { useState } from "react";
import { Thermometer, Droplets, Gauge, LocateFixed } from "lucide-react";
import { getAnalytics } from "@/lib/api";
import { useLocation } from "@/components/providers/LocationProvider";

export default function AnalyticsPage() {
  const { location } = useLocation();
  const [lat, setLat] = useState(location.lat.toFixed(4));
  const [lon, setLon] = useState(location.lon.toFixed(4));
  const [species, setSpecies] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const useMyLocation = () => {
    setLat(location.lat.toFixed(4));
    setLon(location.lon.toFixed(4));
  };

  const run = async () => {
    setLoading(true);
    try {
      const res = await getAnalytics({ lat, lon, species: species || undefined });
      setResult(res);
    } finally {
      setLoading(false);
    }
  };

  const a = result?.analysis;

  return (
    <div className="h-full overflow-y-auto p-6 max-w-4xl mx-auto space-y-6">
      <header className="flex items-center gap-2">
        <Thermometer size={20} className="text-depth-teal" />
        <h1 className="font-display text-xl">Ocean Analytics</h1>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 bg-abyss-900 border border-abyss-700 rounded-lg p-4">
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
          className="flex items-center justify-center gap-1.5 text-xs text-depth-teal border border-depth-teal/30 rounded-md px-3 py-2 hover:bg-depth-teal/10"
        >
          <LocateFixed size={13} /> Use {location.label}
        </button>
        <input
          value={species}
          onChange={(e) => setSpecies(e.target.value)}
          placeholder="Target species (optional)"
          className="bg-abyss-800 border border-abyss-700 rounded-md px-3 py-2 text-sm"
        />
        <button
          onClick={run}
          disabled={loading}
          className="flex items-center justify-center gap-2 bg-depth-teal text-abyss-950 font-medium rounded-md px-4 py-2 text-sm hover:brightness-110 disabled:opacity-50"
        >
          {loading ? "Analyzing…" : "Analyze"}
        </button>
      </div>

      {a && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-abyss-900 border border-abyss-700 rounded-lg p-4">
              <div className="flex items-center gap-1.5 text-mist-400 text-xs mb-1">
                <Thermometer size={13} /> SST Thermal Front
              </div>
              <p className="text-sm">{a.sst_evaluation}</p>
              <p className="text-[11px] text-mist-400 mt-1 font-mono">{a.thermal_front_gradient}</p>
            </div>
            <div className="bg-abyss-900 border border-abyss-700 rounded-lg p-4">
              <div className="flex items-center gap-1.5 text-mist-400 text-xs mb-1">
                <Droplets size={13} /> Chlorophyll-a Upwelling
              </div>
              <p className="text-sm">{a.chlorophyll_evaluation}</p>
            </div>
            <div className="bg-abyss-900 border border-abyss-700 rounded-lg p-4">
              <div className="flex items-center gap-1.5 text-mist-400 text-xs mb-1">
                <Gauge size={13} /> FAPI Score
              </div>
              <p className="text-2xl font-display text-depth-teal">{a.fapi_score}<span className="text-sm text-mist-400">/100</span></p>
              <p className="text-[11px] text-mist-400 mt-1">{a.productivity_index}</p>
            </div>
          </div>

          <div className="bg-abyss-900 border border-abyss-700 rounded-lg p-4">
            <p className="text-xs text-mist-400 mb-1.5">Ecological explanation</p>
            <p className="text-sm leading-relaxed">{a.ecological_explanation}</p>
          </div>

          <div className="bg-abyss-900 border border-abyss-700 rounded-lg p-4">
            <p className="text-xs text-mist-400 mb-1.5">Historical productivity trend</p>
            <p className="text-sm leading-relaxed">{a.historical_productivity_trend}</p>
          </div>
        </div>
      )}
    </div>
  );
}
