"use client";

import { useState } from "react";
import { Search, Compass, Fish, LocateFixed } from "lucide-react";
import { getDiscovery } from "@/lib/api";
import { useLocation } from "@/components/providers/LocationProvider";

const STATES = [
  "Kerala", "Karnataka", "Goa", "Maharashtra", "Gujarat",
  "Tamil Nadu", "Puducherry", "Andhra Pradesh", "Odisha", "West Bengal",
];
const SPECIES = ["Tuna", "Mackerel", "Sardine", "Pomfret", "Hilsa", "Prawn"];

export default function DiscoveryPage() {
  const { location } = useLocation();
  const [state, setState] = useState("");
  const [species, setSpecies] = useState("");
  const [landingCentre, setLandingCentre] = useState("");
  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const useMyLocation = () => {
    setLat(location.lat.toFixed(4));
    setLon(location.lon.toFixed(4));
  };

  const run = async () => {
    setLoading(true);
    try {
      const res = await getDiscovery({
        state: state || undefined,
        species: species || undefined,
        landing_centre: landingCentre || undefined,
        lat: lat || undefined,
        lon: lon || undefined,
      });
      setResult(res);
    } finally {
      setLoading(false);
    }
  };

  const sectors: any[] = result?.findings?.pfz_sectors || [];

  return (
    <div className="h-full overflow-y-auto p-6 max-w-5xl mx-auto space-y-6">
      <header className="flex items-center gap-2">
        <Compass size={20} className="text-depth-teal" />
        <h1 className="font-display text-xl">Marine Data Discovery</h1>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 bg-abyss-900 border border-abyss-700 rounded-lg p-4">
        <select
          value={state}
          onChange={(e) => setState(e.target.value)}
          className="bg-abyss-800 border border-abyss-700 rounded-md px-3 py-2 text-sm"
        >
          <option value="">Any State</option>
          {STATES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>

        <select
          value={species}
          onChange={(e) => setSpecies(e.target.value)}
          className="bg-abyss-800 border border-abyss-700 rounded-md px-3 py-2 text-sm"
        >
          <option value="">Any Species</option>
          {SPECIES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>

        <input
          placeholder="Landing Harbour"
          value={landingCentre}
          onChange={(e) => setLandingCentre(e.target.value)}
          className="bg-abyss-800 border border-abyss-700 rounded-md px-3 py-2 text-sm placeholder:text-mist-400"
        />
        <input
          placeholder="Latitude"
          value={lat}
          onChange={(e) => setLat(e.target.value)}
          className="bg-abyss-800 border border-abyss-700 rounded-md px-3 py-2 text-sm font-mono placeholder:text-mist-400"
        />
        <input
          placeholder="Longitude"
          value={lon}
          onChange={(e) => setLon(e.target.value)}
          className="bg-abyss-800 border border-abyss-700 rounded-md px-3 py-2 text-sm font-mono placeholder:text-mist-400"
        />
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
          className="sm:col-span-2 lg:col-span-6 flex items-center justify-center gap-2 bg-depth-teal text-abyss-950 font-medium rounded-md px-4 py-2 text-sm hover:brightness-110 disabled:opacity-50"
        >
          <Search size={14} /> {loading ? "Searching INCOIS PFZ sectors…" : "Search Potential Fishing Zones"}
        </button>
      </div>

      {result && (
        <div className="space-y-3">
          <p className="text-xs text-mist-400 font-mono">
            Source: {result.findings?.source} · {result.findings?.is_live_feed ? "live" : "snapshot"} ·
            {" "}{result.findings?.total_sectors_found ?? sectors.length} sectors found
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {sectors.map((s, i) => (
              <div key={i} className="bg-abyss-900 border border-abyss-700 rounded-lg p-4 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-sm">{s.landing_centre || s.sector_id}</span>
                  <span className="text-[10px] font-mono text-mist-400 border border-abyss-700 rounded px-1.5 py-0.5">
                    {s.confidence}
                  </span>
                </div>
                <p className="text-xs text-mist-400 font-mono">
                  {s.latitude}°N, {s.longitude}°E
                </p>
                <div className="flex flex-wrap gap-1 pt-1">
                  {(s.species_likely || []).map((sp: string, j: number) => (
                    <span key={j} className="flex items-center gap-1 text-[10px] bg-abyss-800 rounded-full px-2 py-0.5 text-mist-300">
                      <Fish size={10} /> {sp}
                    </span>
                  ))}
                </div>
                <div className="grid grid-cols-3 gap-2 pt-2 text-center">
                  <div>
                    <p className="text-[10px] text-mist-400">SST</p>
                    <p className="text-sm font-mono">{s.sst_celsius}°C</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-mist-400">Chl-a</p>
                    <p className="text-sm font-mono">{s.chlorophyll_mg_m3}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-mist-400">
                      {s.distance_from_user_km !== undefined ? "Dist (km)" : "Coast (km)"}
                    </p>
                    <p className="text-sm font-mono">
                      {s.distance_from_user_km ?? s.distance_from_coast_km ?? "—"}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
