from typing import Optional
from fastapi import APIRouter, Query

from core.citations import CitationTracker
from agents.discovery_agent import MarineDataDiscoveryAgent
from agents.analytics_agent import OceanAnalyticsAgent

router = APIRouter()

_discovery_agent = MarineDataDiscoveryAgent()
_analytics_agent = OceanAnalyticsAgent()


@router.get("/discovery", summary="Manual PFZ discovery query (Marine Discovery dashboard)")
async def discovery(
    state: Optional[str] = Query(None, description="Coastal state, e.g. Kerala"),
    species: Optional[str] = Query(None, description="Tuna, Mackerel, Sardine, Pomfret, Hilsa, Prawn"),
    landing_centre: Optional[str] = Query(None),
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
):
    tracker = CitationTracker()
    result = await _discovery_agent.execute(
        state=state, lat=lat, lon=lon, species=species, landing_centre=landing_centre, citation_tracker=tracker
    )
    result["citations"] = tracker.all()
    return result


@router.get("/analytics", summary="Manual SST/Chlorophyll/FAPI analysis (Ocean Analytics dashboard)")
async def analytics(
    lat: float = Query(...),
    lon: float = Query(...),
    region_name: str = Query("Coastal Maritime Sector"),
    species: Optional[str] = Query(None),
):
    tracker = CitationTracker()
    result = await _analytics_agent.analyze_productivity(
        lat=lat, lon=lon, region_name=region_name, target_species=species, citation_tracker=tracker
    )
    result["citations"] = tracker.all()
    return result


@router.get("/species/{species_name}", summary="Species-specific ecological niche advisory")
async def species_advisory(species_name: str):
    tracker = CitationTracker()
    result = await _discovery_agent.incois_client.get_species_advisory(species_name, citation_tracker=tracker)
    result["citations"] = tracker.all()
    return result


@router.get("/landing-centres", summary="Registered fishing harbor directory")
async def landing_centres(state: Optional[str] = Query(None)):
    return {"landing_centres": _discovery_agent.incois_client.get_landing_centres(state=state)}
