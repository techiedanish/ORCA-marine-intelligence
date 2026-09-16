"""
========================================================================================
ORCA: Marine EcOsystem Reasoning with Collaborative Agents (SIH 2026 - PS 26176)
Section 1: Marine Data Discovery Agent
========================================================================================

ROLE IN MULTI-AGENT ORCHESTRATION:
----------------------------------
The Marine Data Discovery Agent discovers, filters, and prioritizes Potential Fishing Zones:
1. Ingests INCOIS Potential Fishing Zone (PFZ) sectors and ISRO Oceansat-3 OCM composites.
2. Performs spatial proximity ranking relative to vessel coordinates or coastal departure harbors.
3. Applies commercial species filters (Tuna, Mackerel, Sardine, Pomfret, Hilsa, Prawn).
4. Calculates estimated voyage transit hours at standard fishing vessel cruising speeds.
5. Emits verifiable citations for all marine intelligence discoveries.
========================================================================================
"""

from typing import Any, Dict, Optional
try:
    from data_sources.incois_client import IncoisClient
    from core.citations import CitationTracker
except (ImportError, ValueError):
    from ..data_sources.incois_client import IncoisClient
    from ..core.citations import CitationTracker


class MarineDataDiscoveryAgent:
    """
    Specialized Agent 1: Marine Data Discovery Agent (PS 26176)
    Discovers Potential Fishing Zones (PFZ), ocean thermal fronts, and chlorophyll gradients.
    Supports queries by coastal state, landing harbor, species, or GPS coordinates.
    """
    def __init__(self, incois_client: Optional[IncoisClient] = None):
        self.incois_client = incois_client or IncoisClient()

    async def execute(
        self,
        state: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        species: Optional[str] = None,
        landing_centre: Optional[str] = None,
        citation_tracker: Optional[CitationTracker] = None
    ) -> Dict[str, Any]:
        """
        Executes marine data discovery across INCOIS and ISRO Oceansat-3 feeds.
        """
        if lat is not None and lon is not None:
            # Query nearest PFZ relative to user's vessel coordinates
            nearest_res = await self.incois_client.get_nearest_pfz(
                latitude=lat,
                longitude=lon,
                max_results=5,
                citation_tracker=citation_tracker
            )
            sectors = nearest_res.get("nearest_sectors", [])
            top_rec = nearest_res.get("closest_recommendation")
            source_info = "INCOIS Marine Fisheries Advisory Services (Proximity Ranked)"
            is_live = False
            advisory_date = "2026-09-01"
        else:
            # Query general advisory filtered by state/species/landing centre
            result = await self.incois_client.get_pfz_advisory(
                state=state,
                species=species,
                landing_centre=landing_centre,
                citation_tracker=citation_tracker
            )
            sectors = result.get("sectors", [])
            top_rec = sectors[0] if sectors else None
            source_info = result.get("source")
            is_live = result.get("is_live_feed", False)
            advisory_date = result.get("advisory_date")

        return {
            "agent": "Marine Data Discovery Agent",
            "status": "COMPLETED",
            "findings": {
                "source": source_info,
                "is_live_feed": is_live,
                "advisory_date": advisory_date,
                "total_sectors_found": len(sectors),
                "pfz_sectors": sectors,
                "top_recommendation": top_rec,
                "query_context": {
                    "state": state,
                    "species": species,
                    "landing_centre": landing_centre,
                    "origin_coordinates": {"lat": lat, "lon": lon} if lat and lon else None
                }
            }
        }
