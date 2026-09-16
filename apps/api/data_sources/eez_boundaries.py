import json
from pathlib import Path
from typing import Any, Dict, List, Optional

BOUNDARIES_PATH = Path(__file__).resolve().parent.parent / "data" / "eez" / "india_eez.json"
LANDING_CENTRES_PATH = Path(__file__).resolve().parent.parent / "data" / "coastal_landing_centres.json"


class EezBoundaries:
    """
    Provides maritime boundary polygons, line strings, and coastal harbor catalogs:
    - India EEZ (Exclusive Economic Zone)
    - India - Sri Lanka International Maritime Boundary Line (Official 13 Points)
    - Marine Protected Areas (Gulf of Mannar, Gahirmatha, Sundarbans, Malvan)
    - 40+ Indian Coastal Fishing Harbors
    """
    def __init__(self):
        self._geojson = None
        self._landing_centres = []
        self._load()

    def _load(self):
        if BOUNDARIES_PATH.exists():
            with open(BOUNDARIES_PATH, "r", encoding="utf-8") as f:
                self._geojson = json.load(f)
        else:
            self._geojson = {"type": "FeatureCollection", "features": []}

        if LANDING_CENTRES_PATH.exists():
            with open(LANDING_CENTRES_PATH, "r", encoding="utf-8") as f:
                self._landing_centres = json.load(f)
        else:
            self._landing_centres = []

    def get_geojson(self) -> Dict[str, Any]:
        return self._geojson

    def get_imbl_coordinates(self) -> List[List[float]]:
        """Returns [[lon, lat], ...] for the 13 bilateral treaty IMBL points."""
        for feature in self._geojson.get("features", []):
            if feature.get("properties", {}).get("type") == "IMBL_LINE":
                return feature["geometry"]["coordinates"]
        return []

    def get_mpa_features(self) -> List[Dict[str, Any]]:
        """Returns all Marine Protected Area GeoJSON feature objects."""
        return [f for f in self._geojson.get("features", []) if f.get("properties", {}).get("type") == "MPA"]

    def get_eez_polygon(self) -> List[List[float]]:
        """Returns outer polygon ring [[lon, lat], ...] for the Indian EEZ."""
        for feature in self._geojson.get("features", []):
            if feature.get("properties", {}).get("type") == "EEZ_BOUNDARY":
                return feature["geometry"]["coordinates"][0]
        return []

    def get_landing_centres(self, state: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns coastal fishing harbors, optionally filtered by state."""
        if state:
            return [lc for lc in self._landing_centres if lc.get("state", "").lower() == state.lower()]
        return self._landing_centres

    def find_landing_centre_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Finds landing center by exact or partial name."""
        name_clean = name.strip().lower()
        for lc in self._landing_centres:
            if name_clean in lc["name"].lower() or lc["name"].lower() in name_clean:
                return lc
        return None
