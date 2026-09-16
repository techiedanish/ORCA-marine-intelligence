"use client";

import { useState } from "react";
import { MapPin, LocateFixed, ChevronDown } from "lucide-react";
import clsx from "clsx";
import { useLocation } from "@/components/providers/LocationProvider";

export default function LocationBadge() {
  const { location, harbours, selectHarbour, requestGeolocation, geoPermissionState } = useLocation();
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className={clsx(
          "flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-md border transition-colors",
          location.source === "geolocation"
            ? "border-depth-teal/40 text-depth-teal"
            : "border-abyss-700 text-mist-300 hover:text-white"
        )}
        title="Every distance/border calculation uses this position. Never simulated."
      >
        <MapPin size={13} />
        <span className="hidden sm:inline">{location.label}</span>
        <ChevronDown size={12} className={clsx("transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <div className="absolute right-0 mt-1.5 w-56 bg-abyss-900 border border-abyss-700 rounded-md shadow-panel z-20 py-1.5">
          <button
            onClick={() => {
              requestGeolocation();
              setOpen(false);
            }}
            className="w-full flex items-center gap-2 text-left px-3 py-2 text-xs text-depth-teal hover:bg-abyss-700"
          >
            <LocateFixed size={13} />
            Use my real location
          </button>

          {geoPermissionState === "denied" && (
            <p className="px-3 py-1 text-[10px] text-mist-400 leading-snug">
              Location permission was denied — pick a coastal base below instead.
            </p>
          )}
          {geoPermissionState === "unsupported" && (
            <p className="px-3 py-1 text-[10px] text-mist-400 leading-snug">
              Your browser doesn't support geolocation — pick a coastal base below.
            </p>
          )}

          <div className="border-t border-abyss-700 my-1" />
          <p className="px-3 py-1 text-[10px] uppercase tracking-wide text-mist-400">Coastal base</p>
          {harbours.map((h) => (
            <button
              key={h.key}
              onClick={() => {
                selectHarbour(h);
                setOpen(false);
              }}
              className={clsx(
                "w-full text-left px-3 py-1.5 text-xs hover:bg-abyss-700",
                location.label === h.label ? "text-depth-teal" : "text-mist-300"
              )}
            >
              {h.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
