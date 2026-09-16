"""
========================================================================================
ORCA: Marine EcOsystem Reasoning with Collaborative Agents (SIH 2026 - PS 26176)
Geo: Geofencing Engine (IMBL Boundary + MPA Containment + Harbor Lookup)
========================================================================================
Pure-python geodesic helpers (no heavyweight GIS dependency required) used by the
Geospatial Reasoning Agent to audit vessel positions against:
  1. The official 13-point India-Sri Lanka International Maritime Boundary Line (IMBL)
  2. Marine Protected Area (MPA) polygons (Gulf of Mannar, Gahirmatha, Sundarbans, Malvan)
  3. The national directory of registered fishing landing centres / harbors
========================================================================================
"""

import math
from typing import Any, Dict, List, Optional, Tuple

try:
    from data_sources.eez_boundaries import EezBoundaries
except (ImportError, ValueError):
    from ..data_sources.eez_boundaries import EezBoundaries

_eez = EezBoundaries()

EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lon points in kilometers."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial compass bearing (0-360) from point 1 to point 2."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_lambda = math.radians(lon2 - lon1)
    x = math.sin(d_lambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(d_lambda)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def _point_to_segment_km(p: Tuple[float, float], a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """
    Approximate shortest distance (km) from point p=(lat,lon) to the great-circle
    segment a-b, using an equirectangular local projection (accurate enough at the
    ~5-10km scale relevant to coastal/EEZ boundary auditing).
    """
    lat0 = math.radians((a[0] + b[0]) / 2.0)
    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * math.cos(lat0)

    def to_xy(pt):
        return (pt[1] * km_per_deg_lon, pt[0] * km_per_deg_lat)  # (x=lon, y=lat) in km

    px, py = to_xy(p)
    ax, ay = to_xy(a)
    bx, by = to_xy(b)

    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)

    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    proj_x, proj_y = ax + t * dx, ay + t * dy
    return math.hypot(px - proj_x, py - proj_y)


def distance_to_polyline_km(lat: float, lon: float, coords_lonlat: List[List[float]]) -> float:
    """Minimum distance (km) from (lat,lon) to a polyline given as [[lon,lat], ...]."""
    if not coords_lonlat or len(coords_lonlat) < 2:
        return 9999.0
    pts = [(c[1], c[0]) for c in coords_lonlat]  # -> (lat, lon)
    p = (lat, lon)
    return min(_point_to_segment_km(p, pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def point_in_polygon(lat: float, lon: float, polygon_lonlat: List[List[float]]) -> bool:
    """Standard ray-casting point-in-polygon test. polygon_lonlat is [[lon,lat], ...]."""
    if not polygon_lonlat or len(polygon_lonlat) < 3:
        return False
    inside = False
    n = len(polygon_lonlat)
    x, y = lon, lat
    j = n - 1
    for i in range(n):
        xi, yi = polygon_lonlat[i][0], polygon_lonlat[i][1]
        xj, yj = polygon_lonlat[j][0], polygon_lonlat[j][1]
        intersect = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / ((yj - yi) if (yj - yi) != 0 else 1e-12) + xi
        )
        if intersect:
            inside = not inside
        j = i
    return inside


def _side_of_line(lat: float, lon: float, coords_lonlat: List[List[float]]) -> str:
    """
    Determines which side of the IMBL a point falls on using the sign of the cross
    product against the nearest segment. Returns 'INDIAN_WATERS' or 'FOREIGN_WATERS'.
    India's EEZ lies to the west/north-west of the treaty line for this sector.
    """
    if len(coords_lonlat) < 2:
        return "INDIAN_WATERS"
    # Use the two nearest consecutive points to establish a local line direction
    pts = [(c[1], c[0]) for c in coords_lonlat]
    best_i, best_d = 0, float("inf")
    for i in range(len(pts) - 1):
        d = _point_to_segment_km((lat, lon), pts[i], pts[i + 1])
        if d < best_d:
            best_d, best_i = d, i
    a, b = pts[best_i], pts[best_i + 1]
    cross = (b[1] - a[1]) * (lat - a[0]) - (b[0] - a[0]) * (lon - a[1])
    return "INDIAN_WATERS" if cross <= 0 else "FOREIGN_WATERS"


def check_vessel_geofence(lat: float, lon: float) -> Dict[str, Any]:
    """
    Audits a vessel position against the 13-point IMBL treaty line and all registered
    Marine Protected Areas. Returns a structured audit with distance, side-of-border,
    and containment status.
    """
    imbl_coords = _eez.get_imbl_coordinates()
    dist_km = distance_to_polyline_km(lat, lon, imbl_coords) if imbl_coords else 9999.0

    # The side-of-line (INDIAN_WATERS vs FOREIGN_WATERS) test is only meaningful when
    # the vessel is actually near the treaty line's local sector (Palk Bay / Gulf of
    # Mannar). Far away (e.g. off Visakhapatnam or Gujarat), the nearest-segment cross
    # product is not a meaningful signal and must NOT be reported as a border breach.
    NEAR_BOUNDARY_THRESHOLD_KM = 50.0
    side = _side_of_line(lat, lon, imbl_coords) if imbl_coords and dist_km <= NEAR_BOUNDARY_THRESHOLD_KM else "INDIAN_WATERS"

    if dist_km > NEAR_BOUNDARY_THRESHOLD_KM:
        imbl_status = "CLEAR_SAFE_DISTANCE"
    elif side == "FOREIGN_WATERS":
        imbl_status = "BORDER_BREACH_DETECTED"
    elif dist_km < 2.0:
        imbl_status = "CRITICAL_VIOLATION_IMMINENT"
    elif dist_km < 5.0:
        imbl_status = "WARNING_APPROACHING_BORDER"
    else:
        imbl_status = "CLEAR_SAFE_DISTANCE"

    imbl_check = {
        "distance_to_imbl_km": round(dist_km, 2),
        "side_of_border": side,
        "status": imbl_status,
    }

    mpa_features = _eez.get_mpa_features()
    inside_mpa = None
    nearest_mpa_name = None
    nearest_mpa_dist = float("inf")
    for feat in mpa_features:
        geom = feat.get("geometry", {})
        name = feat.get("properties", {}).get("name", "Unnamed MPA")
        rings = []
        if geom.get("type") == "Polygon":
            rings = geom.get("coordinates", [])
        elif geom.get("type") == "MultiPolygon":
            for poly in geom.get("coordinates", []):
                rings.extend(poly)
        for ring in rings:
            if point_in_polygon(lat, lon, ring):
                inside_mpa = name
            # distance to centroid for "nearest MPA" reporting
            if ring:
                c_lat = sum(pt[1] for pt in ring) / len(ring)
                c_lon = sum(pt[0] for pt in ring) / len(ring)
                d = haversine_km(lat, lon, c_lat, c_lon)
                if d < nearest_mpa_dist:
                    nearest_mpa_dist = d
                    nearest_mpa_name = name

    mpa_check = {
        "inside_protected_area": inside_mpa is not None,
        "protected_area_name": inside_mpa,
        "nearest_protected_area": nearest_mpa_name,
        "distance_to_nearest_mpa_km": round(nearest_mpa_dist, 2) if nearest_mpa_dist != float("inf") else None,
    }

    return {
        "vessel_position": {"lat": lat, "lon": lon},
        "imbl_check": imbl_check,
        "mpa_check": mpa_check,
    }


def find_nearest_landing_centre(lat: float, lon: float) -> Dict[str, Any]:
    """Finds the closest registered fishing harbor/landing centre for emergency refuge."""
    centres = _eez.get_landing_centres()
    if not centres:
        return {
            "name": "Unknown Harbor",
            "state": "N/A",
            "distance_km": None,
            "bearing_deg": None,
        }

    best = None
    best_dist = float("inf")
    for c in centres:
        d = haversine_km(lat, lon, c["latitude"], c["longitude"])
        if d < best_dist:
            best_dist = d
            best = c

    brg = bearing_deg(lat, lon, best["latitude"], best["longitude"])
    return {
        "name": best["name"],
        "state": best.get("state", "N/A"),
        "latitude": best["latitude"],
        "longitude": best["longitude"],
        "distance_km": round(best_dist, 2),
        "bearing_deg": round(brg, 1),
    }
