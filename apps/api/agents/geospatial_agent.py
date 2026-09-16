"""
========================================================================================
ORCA: Marine EcOsystem Reasoning with Collaborative Agents (SIH 2026 - PS 26176)
Section 3: Geospatial Reasoning Agent
========================================================================================

ROLE IN MULTI-AGENT ORCHESTRATION:
----------------------------------
The Geospatial Reasoning Agent is responsible for all spatial decision-support tasks:
1. Auditing vessel GPS coordinates against international boundary treaties (13-point IMBL).
2. Evaluating containment within Marine Protected Areas (MPAs) under Wildlife Protection laws.
3. Generating collision-free, border-safe navigational corridors with step-by-step headings.
4. Identifying closest emergency refuge harbors for maritime safety.
5. Emitting structured verifiable citations for all spatial claims.
========================================================================================
"""

from typing import Any, Dict, Optional
try:
    from geo.geofence import check_vessel_geofence, find_nearest_landing_centre
    from geo.route_planner import calculate_safe_corridor_route
    from core.citations import CitationTracker
except (ImportError, ValueError):
    from ..geo.geofence import check_vessel_geofence, find_nearest_landing_centre
    from ..geo.route_planner import calculate_safe_corridor_route
    from ..core.citations import CitationTracker


class GeospatialReasoningAgent:
    """
    Specialized Agent 4: Geospatial Reasoning Agent (PS 26176)
    Performs geodesic boundary distance calculations (EEZ / 13-point IMBL treaty line),
    ray-casting Marine Protected Area containment audits, and constraint-aware safe navigational corridor planning.
    """
    async def evaluate_position(
        self,
        lat: float,
        lon: float,
        citation_tracker: Optional[CitationTracker] = None
    ) -> Dict[str, Any]:
        """
        Audits vessel GPS position against international maritime boundaries and ecological reserves.
        """
        audit = check_vessel_geofence(lat, lon)
        imbl_res = audit["imbl_check"]
        mpa_res = audit["mpa_check"]

        if citation_tracker:
            citation_tracker.add(
                claim=(
                    f"Vessel at ({lat}°N, {lon}°E) evaluated: {imbl_res['distance_to_imbl_km']} km to Sri Lanka IMBL "
                    f"[{imbl_res['status']}]; MPA containment: {mpa_res['inside_protected_area']}"
                ),
                source="Marine Regions World EEZ v12 & Bilateral Treaty 1974/1976",
                dataset_name="India Exclusive Economic Zone & International Maritime Boundary Line",
                reference_id="MR-EEZ-IND-2026",
                is_live=True
            )

        return {
            "agent": "Geospatial Reasoning Agent",
            "status": "COMPLETED",
            "geospatial_audit": audit
        }

    async def plan_route(
        self,
        start_lat: float,
        start_lon: float,
        target_lat: float,
        target_lon: float,
        vessel_speed_knots: float = 9.0,
        engine_hp: int = 120,
        citation_tracker: Optional[CitationTracker] = None
    ) -> Dict[str, Any]:
        """
        Calculates a compliant navigational route avoiding IMBL encroachment and MPA core zones.
        """
        route = calculate_safe_corridor_route(
            start_lat=start_lat,
            start_lon=start_lon,
            target_lat=target_lat,
            target_lon=target_lon,
            vessel_speed_knots=vessel_speed_knots,
            engine_hp=engine_hp
        )

        if citation_tracker:
            citation_tracker.add(
                claim=(
                    f"Generated safe navigational corridor ({route['total_route_distance_nm']} NM, "
                    f"{route['estimated_transit_hours']} hrs) maintaining certified buffer from hazardous zones"
                ),
                source="ISRO Bhuvan Coastal Spatial Decision Support System & Marine Regions",
                dataset_name="National Marine Spatial Planning & Navigation Corridors",
                reference_id="BHUVAN-CSDSS-2026",
                is_live=True
            )

        return {
            "agent": "Geospatial Reasoning Agent",
            "status": "COMPLETED",
            "route_plan": route
        }

    async def find_emergency_harbor(
        self,
        lat: float,
        lon: float,
        citation_tracker: Optional[CitationTracker] = None
    ) -> Dict[str, Any]:
        """
        Identifies the closest registered Indian fishing harbor for emergency refuge.
        """
        harbor = find_nearest_landing_centre(lat, lon)

        if citation_tracker:
            citation_tracker.add(
                claim=f"Nearest emergency landing harbor identified as {harbor['name']}, {harbor['state']} ({harbor['distance_km']} km, bearing {harbor['bearing_deg']}°)",
                source="Department of Fisheries & Coastal Aquaculture Authority",
                dataset_name="National Fishery Harbor Directory",
                reference_id="NFHD-2026"
            )

        return {
            "agent": "Geospatial Reasoning Agent",
            "status": "COMPLETED",
            "emergency_harbor": harbor
        }
