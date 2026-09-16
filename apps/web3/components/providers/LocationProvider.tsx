"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { HARBOURS, DEFAULT_HARBOUR, type Harbour } from "@/lib/harbours";

export type LocationSource = "geolocation" | "harbour" | "pending" | "denied";

export interface GroundedLocation {
  lat: number;
  lon: number;
  label: string;
  source: LocationSource;
}

interface LocationContextValue {
  location: GroundedLocation;
  requestGeolocation: () => void;
  selectHarbour: (harbour: Harbour) => void;
  harbours: Harbour[];
  geoPermissionState: "unsupported" | "prompt" | "granted" | "denied" | "checking";
}

const STORAGE_KEY = "orca.grounded_location.v1";

const LocationContext = createContext<LocationContextValue | null>(null);

function loadStored(): GroundedLocation | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as GroundedLocation) : null;
  } catch {
    return null;
  }
}

function persist(loc: GroundedLocation) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(loc));
  } catch {
    /* storage unavailable — non-fatal, grounding still works for this session */
  }
}

/**
 * Provides a REAL grounded (lat, lon) for the whole app — either the user's actual
 * browser geolocation, or an explicit harbour they picked. Never fabricates a
 * position: until one of those two things happens, `source` stays "pending" and
 * callers should treat the coordinates as a provisional default only (Kochi), not
 * as evidence of the user's real location.
 */
export function LocationProvider({ children }: { children: React.ReactNode }) {
  const [location, setLocation] = useState<GroundedLocation>({
    ...DEFAULT_HARBOUR,
    label: DEFAULT_HARBOUR.label,
    source: "pending",
  });
  const [geoPermissionState, setGeoPermissionState] =
    useState<LocationContextValue["geoPermissionState"]>("checking");

  const requestGeolocation = useCallback(() => {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      setGeoPermissionState("unsupported");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const grounded: GroundedLocation = {
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
          label: "My current location",
          source: "geolocation",
        };
        setLocation(grounded);
        setGeoPermissionState("granted");
        persist(grounded);
      },
      () => {
        setGeoPermissionState("denied");
        // Leave whatever harbour/default is already selected in place — we do NOT
        // invent a position when permission is denied.
      },
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 5 * 60 * 1000 }
    );
  }, []);

  const selectHarbour = useCallback((harbour: Harbour) => {
    const grounded: GroundedLocation = {
      lat: harbour.lat,
      lon: harbour.lon,
      label: harbour.label,
      source: "harbour",
    };
    setLocation(grounded);
    persist(grounded);
  }, []);

  useEffect(() => {
    const stored = loadStored();
    if (stored) {
      setLocation(stored);
      setGeoPermissionState(stored.source === "geolocation" ? "granted" : "prompt");
      return;
    }
    // First-ever load: proactively prompt for geolocation once, per the spec.
    requestGeolocation();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <LocationContext.Provider
      value={{ location, requestGeolocation, selectHarbour, harbours: HARBOURS, geoPermissionState }}
    >
      {children}
    </LocationContext.Provider>
  );
}

export function useLocation() {
  const ctx = useContext(LocationContext);
  if (!ctx) throw new Error("useLocation must be used within a LocationProvider");
  return ctx;
}
