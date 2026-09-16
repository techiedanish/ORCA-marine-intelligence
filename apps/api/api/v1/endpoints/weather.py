from typing import Optional
from fastapi import APIRouter, Query

from core.citations import CitationTracker
from agents.weather_agent import WeatherIntelligenceAgent

router = APIRouter()
_weather_agent = WeatherIntelligenceAgent()


@router.get("/sea-safety", summary="Fused IMD + Open-Meteo (free, no key) sea safety verdict (Weather Intelligence dashboard)")
async def sea_safety(
    sea_zone: str = Query("arabian_sea_south"),
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
):
    tracker = CitationTracker()
    result = await _weather_agent.evaluate_sea_safety(sea_zone=sea_zone, lat=lat, lon=lon, citation_tracker=tracker)
    result["citations"] = tracker.all()
    return result


@router.get("/forecast", summary="24-hour marine forecast intervals (free Open-Meteo, no key required)")
async def forecast(lat: float = Query(...), lon: float = Query(...)):
    tracker = CitationTracker()
    result = await _weather_agent.open_meteo_client.get_forecast(lat=lat, lon=lon, citation_tracker=tracker)
    result["citations"] = tracker.all()
    return result


@router.get("/cyclones", summary="Active IMD RSMC cyclone tracks")
async def cyclones():
    tracker = CitationTracker()
    result = await _weather_agent.imd_client.get_cyclone_status(citation_tracker=tracker)
    return {"active_cyclones": result, "citations": tracker.all()}
