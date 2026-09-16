"""
========================================================================================
ORCA: Marine EcOsystem Reasoning with Collaborative Agents (SIH 2026 - PS 26176)
Orchestration: Rule-Based Intent & Entity Extraction (Deterministic Planner)
========================================================================================
Used whenever Gemini Flash is unavailable (no API key, network failure, quota hit) so
the SIH demo ALWAYS answers the five key hackathon questions with full agent traces,
citations, and map GeoJSON. Also used to pre-extract entities even when Gemini IS
available, since coordinates/species/location names benefit from deterministic
extraction rather than LLM guessing.
========================================================================================
"""

import re
from typing import Any, Dict, Optional

# Known coastal locations -> approximate offshore query coordinates (lat, lon)
KNOWN_LOCATIONS = {
    "kochi": (9.9312, 76.2673),
    "cochin": (9.9312, 76.2673),
    "visakhapatnam": (17.6868, 83.2185),
    "vizag": (17.6868, 83.2185),
    "chennai": (13.0827, 80.2707),
    "mumbai": (18.9220, 72.8347),
    "goa": (15.4989, 73.8278),
    "mangalore": (12.9141, 74.8560),
    "kakinada": (16.9891, 82.2475),
    "rameswaram": (9.2876, 79.3129),
    "tuticorin": (8.7642, 78.1348),
    "thoothukudi": (8.7642, 78.1348),
    "veraval": (20.9159, 70.3629),
    "porbandar": (21.6417, 69.6293),
    "paradip": (20.3167, 86.6167),
    "digha": (21.6274, 87.5088),
    "puducherry": (11.9139, 79.8300),
    "ratnagiri": (16.9902, 73.3120),
}

SPECIES_KEYWORDS = ["tuna", "mackerel", "sardine", "pomfret", "hilsa", "prawn"]

SEA_ZONE_BY_COAST = {
    "kerala": "arabian_sea_south",
    "karnataka": "arabian_sea_south",
    "goa": "arabian_sea_south",
    "maharashtra": "arabian_sea_north",
    "gujarat": "arabian_sea_north",
    "tamil nadu": "bay_of_bengal_south",
    "puducherry": "bay_of_bengal_south",
    "andhra pradesh": "bay_of_bengal_north",
    "odisha": "bay_of_bengal_north",
    "west bengal": "west_bengal_coast",
}

COORD_PATTERN = re.compile(
    r"(-?\d+(?:\.\d+)?)\s*[°]?\s*([NnSs])?\s*[,\s]+\s*(-?\d+(?:\.\d+)?)\s*[°]?\s*([EeWw])?"
)


def extract_coordinates(text: str) -> Optional[Dict[str, float]]:
    """Extracts the first lat/lon pair found in free text, e.g. '9.15°N, 79.45°E'."""
    match = COORD_PATTERN.search(text)
    if not match:
        return None
    lat = float(match.group(1))
    lat_hemi = (match.group(2) or "N").upper()
    lon = float(match.group(3))
    lon_hemi = (match.group(4) or "E").upper()
    if lat_hemi == "S":
        lat = -lat
    if lon_hemi == "W":
        lon = -lon
    # Sanity bound so we don't misfire on unrelated numbers in the query
    if -90 <= lat <= 90 and -180 <= lon <= 180:
        return {"lat": lat, "lon": lon}
    return None


def extract_location_name(text: str) -> Optional[str]:
    lowered = text.lower()
    for name in KNOWN_LOCATIONS:
        if name in lowered:
            return name
    return None


def extract_species(text: str) -> Optional[str]:
    lowered = text.lower()
    for sp in SPECIES_KEYWORDS:
        if sp in lowered:
            return sp
    return None


def extract_time_horizon(text: str) -> str:
    lowered = text.lower()
    if "tomorrow" in lowered or "कल" in lowered:
        return "tomorrow"
    if "today" in lowered or "now" in lowered or "आज" in lowered:
        return "today"
    return "today"


def classify_intent(text: str) -> str:
    """
    Returns one of: 'pfz_discovery', 'safety_check', 'productivity_explain',
    'border_check', 'general'.
    """
    lowered = text.lower()

    border_hints = ["border", "imbl", "boundary", "sri lanka", "vessel at", "coordinates"]
    safety_hints = ["safe", "venture", "sail", "danger", "risk", "should i go", "weather", "cyclone", "storm"]
    pfz_hints = ["pfz", "fishing zone", "where can i fish", "nearest zone", "fish near", "potential fishing"]
    productivity_hints = ["why", "productivity", "aggregat", "thermal front", "chlorophyll", "upwelling"]

    has_coords = extract_coordinates(text) is not None

    if any(h in lowered for h in border_hints) or (has_coords and "safe" not in lowered and "fish" not in lowered):
        return "border_check"
    if any(h in lowered for h in productivity_hints):
        return "productivity_explain"
    if any(h in lowered for h in pfz_hints) or (extract_species(text) and "safe" not in lowered):
        return "pfz_discovery"
    if any(h in lowered for h in safety_hints):
        return "safety_check"
    return "general"


def resolve_query_coordinates(
    text: str,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Best-effort resolution of a working (lat, lon) for the query, in priority order:
      1. Explicit coordinates typed in the query text (e.g. "9.15°N, 79.45°E") — the
         user is deliberately asking about a specific, named position.
      2. A recognized place name mentioned in the query text (e.g. "near Visakhapatnam")
         — the user is asking about somewhere other than where they currently are.
      3. The user's REAL grounded position (browser geolocation, or their selected
         harbour fallback) passed in from the frontend — never hallucinated.
      4. A sane last-resort default (off Kochi) only if nothing else is available.
    """
    coords = extract_coordinates(text)
    if coords:
        return {"lat": coords["lat"], "lon": coords["lon"], "location_name": None, "source": "explicit_coordinates"}

    loc_name = extract_location_name(text)
    if loc_name:
        lat, lon = KNOWN_LOCATIONS[loc_name]
        return {"lat": lat, "lon": lon, "location_name": loc_name.title(), "source": "known_location"}

    if user_lat is not None and user_lon is not None:
        return {"lat": user_lat, "lon": user_lon, "location_name": None, "source": "user_grounded_location"}

    default_lat, default_lon = KNOWN_LOCATIONS["kochi"]
    return {"lat": default_lat, "lon": default_lon, "location_name": "Kochi (default)", "source": "default"}


def parse_query(
    text: str,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
) -> Dict[str, Any]:
    intent = classify_intent(text)
    coords = resolve_query_coordinates(text, user_lat=user_lat, user_lon=user_lon)
    species = extract_species(text)
    time_horizon = extract_time_horizon(text)

    state_hint = None
    for state in SEA_ZONE_BY_COAST:
        if state in text.lower():
            state_hint = state
            break

    return {
        "intent": intent,
        "lat": coords["lat"],
        "lon": coords["lon"],
        "location_name": coords["location_name"],
        "coordinate_source": coords["source"],
        "species": species,
        "time_horizon": time_horizon,
        "state_hint": state_hint,
        "sea_zone": SEA_ZONE_BY_COAST.get(state_hint, "arabian_sea_south"),
    }
