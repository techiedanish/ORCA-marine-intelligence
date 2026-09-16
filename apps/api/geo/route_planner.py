"""
========================================================================================
ORCA: Marine EcOsystem Reasoning with Collaborative Agents (SIH 2026 - PS 26176)
Geo: Border-Safe Navigational Corridor Planner
========================================================================================
Generates a great-circle route between a start and target position, subdividing it
into waypoints and nudging any waypoint that drifts within the IMBL buffer or an MPA
core zone back onto a compliant heading. This keeps the demo deterministic and fast
without requiring a full A*/visibility-graph solver.
========================================================================================
"""

import math
from typing import Any, Dict, List

try:
    from geo.geofence import haversine_km, bearing_deg, check_vessel_geofence
except (ImportError, ValueError):
    from .geofence import haversine_km, bearing_deg, check_vessel_geofence

SAFE_BUFFER_KM = 5.0
WAYPOINT_COUNT = 8


def _interpolate(lat1, lon1, lat2, lon2, fraction: float):
    """Linear (planar-approx) interpolation; adequate at coastal-route distances."""
    return (
        lat1 + (lat2 - lat1) * fraction,
        lon1 + (lon2 - lon1) * fraction,
    )


def calculate_safe_corridor_route(
    start_lat: float,
    start_lon: float,
    target_lat: float,
    target_lon: float,
    vessel_speed_knots: float = 9.0,
    engine_hp: int = 120,
) -> Dict[str, Any]:
    total_km = haversine_km(start_lat, start_lon, target_lat, target_lon)
    total_nm = round(total_km * 0.539957, 2)
    initial_bearing = round(bearing_deg(start_lat, start_lon, target_lat, target_lon), 1)

    waypoints: List[Dict[str, Any]] = []
    rerouted_count = 0

    for i in range(WAYPOINT_COUNT + 1):
        frac = i / WAYPOINT_COUNT
        lat, lon = _interpolate(start_lat, start_lon, target_lat, target_lon, frac)

        audit = check_vessel_geofence(lat, lon)
        imbl = audit["imbl_check"]
        mpa = audit["mpa_check"]

        compliant = True
        note = "On planned corridor track"

        if imbl["status"] in ("BORDER_BREACH_DETECTED", "CRITICAL_VIOLATION_IMMINENT", "WARNING_APPROACHING_BORDER"):
            # Nudge the waypoint westward (into Indian waters) by the safe buffer distance
            nudge_deg = SAFE_BUFFER_KM / 111.0
            lon -= nudge_deg
            compliant = False
            rerouted_count += 1
            note = f"Corridor adjusted {SAFE_BUFFER_KM}km west to clear IMBL buffer (was {imbl['distance_to_imbl_km']}km)"

        if mpa["inside_protected_area"]:
            nudge_deg = SAFE_BUFFER_KM / 111.0
            lat += nudge_deg
            compliant = False
            rerouted_count += 1
            note = f"Corridor adjusted to avoid {mpa['protected_area_name']} core zone"

        waypoints.append(
            {
                "sequence": i + 1,
                "lat": round(lat, 5),
                "lon": round(lon, 5),
                "compliant": compliant,
                "note": note,
                "heading_deg": round(bearing_deg(lat, lon, target_lat, target_lon), 1) if i < WAYPOINT_COUNT else None,
            }
        )

    transit_hours = round((total_nm / vessel_speed_knots) if vessel_speed_knots > 0 else 0, 2)
    fuel_estimate_litres = round(transit_hours * engine_hp * 0.18, 1)  # rough consumption heuristic

    return {
        "start": {"lat": start_lat, "lon": start_lon},
        "target": {"lat": target_lat, "lon": target_lon},
        "initial_heading_deg": initial_bearing,
        "total_route_distance_nm": total_nm,
        "total_route_distance_km": round(total_km, 2),
        "estimated_transit_hours": transit_hours,
        "vessel_speed_knots": vessel_speed_knots,
        "engine_hp": engine_hp,
        "estimated_fuel_litres": fuel_estimate_litres,
        "waypoints_rerouted_for_safety": rerouted_count,
        "waypoints": waypoints,
        "route_geojson": {
            "type": "Feature",
            "properties": {"name": "ORCA Safe Navigational Corridor"},
            "geometry": {
                "type": "LineString",
                "coordinates": [[wp["lon"], wp["lat"]] for wp in waypoints],
            },
        },
    }
