from fastapi import APIRouter, Query
from pydantic import BaseModel

from core.citations import CitationTracker
from agents.geospatial_agent import GeospatialReasoningAgent
from agents.risk_agent import RiskAssessmentAgent
from agents.weather_agent import WeatherIntelligenceAgent
from data_sources.eez_boundaries import EezBoundaries

router = APIRouter()
_geo_agent = GeospatialReasoningAgent()
_risk_agent = RiskAssessmentAgent()
_weather_agent = WeatherIntelligenceAgent()
_eez = EezBoundaries()


class RoutePlanRequest(BaseModel):
    start_lat: float
    start_lon: float
    target_lat: float
    target_lon: float
    vessel_speed_knots: float = 9.0
    engine_hp: int = 120


@router.get("/audit", summary="Audit a vessel position against IMBL & MPA registry (Risk & Geofencing dashboard)")
async def audit(lat: float = Query(...), lon: float = Query(...), include_risk: bool = Query(True)):
    tracker = CitationTracker()
    geo_result = await _geo_agent.evaluate_position(lat, lon, citation_tracker=tracker)

    response = {**geo_result, "citations": tracker.all()}

    if include_risk:
        weather = await _weather_agent.evaluate_sea_safety(lat=lat, lon=lon, citation_tracker=tracker)
        risk = await _risk_agent.evaluate_risk(
            weather_data=weather["findings"],
            geofence_data=geo_result["geospatial_audit"],
            citation_tracker=tracker,
        )
        response["risk_assessment"] = risk
        response["citations"] = tracker.all()

    return response


@router.post("/route", summary="Plan a border-safe navigational corridor")
async def plan_route(payload: RoutePlanRequest):
    tracker = CitationTracker()
    result = await _geo_agent.plan_route(
        start_lat=payload.start_lat,
        start_lon=payload.start_lon,
        target_lat=payload.target_lat,
        target_lon=payload.target_lon,
        vessel_speed_knots=payload.vessel_speed_knots,
        engine_hp=payload.engine_hp,
        citation_tracker=tracker,
    )
    result["citations"] = tracker.all()
    return result


@router.get("/emergency-harbor", summary="Find nearest emergency refuge harbor")
async def emergency_harbor(lat: float = Query(...), lon: float = Query(...)):
    tracker = CitationTracker()
    result = await _geo_agent.find_emergency_harbor(lat, lon, citation_tracker=tracker)
    result["citations"] = tracker.all()
    return result


@router.get("/boundaries", summary="Raw GeoJSON: IMBL line, EEZ polygon, MPA features")
async def boundaries():
    return _eez.get_geojson()
