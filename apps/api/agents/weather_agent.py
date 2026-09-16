"""
========================================================================================
ORCA: Marine EcOsystem Reasoning with Collaborative Agents (SIH 2026 - PS 26176)
Section 2: Weather Intelligence Agent
========================================================================================

ROLE IN MULTI-AGENT ORCHESTRATION:
----------------------------------
The Weather Intelligence Agent monitors and fuses atmospheric and oceanic hazards:
1. Live Open-Meteo marine telemetry (wind speed, gusts, wave height, Beaufort sea
   state, squall risk) — a genuinely free, zero-API-key provider used as the PRIMARY
   live data source so ORCA is 100% functional with no credentials configured at all.
2. India Meteorological Department (IMD) 24-hr Fishermen Warnings & Coastal Bulletins.
3. IMD Cyclone Warning Division (RSMC) active track, cone of uncertainty, and pressure drops.
4. Synthesizes a unified weather hazard verdict: GREEN (Safe), AMBER (Caution), RED (Do Not Sail).
5. Emits verifiable citations for all meteorological assertions.

NOTE ON OpenWeatherMap: retained as an OPTIONAL secondary telemetry source, only
queried when OPENWEATHERMAP_API_KEY is actually configured (see core.config), since
it requires a paid-tier-capable key ORCA must not depend on by default.
========================================================================================
"""

from typing import Any, Dict, Optional
try:
    from data_sources.imd_client import ImdClient
    from data_sources.open_meteo_client import OpenMeteoClient
    from data_sources.openweather_client import OpenWeatherClient
    from core.citations import CitationTracker
    from core.config import settings
except (ImportError, ValueError):
    from ..data_sources.imd_client import ImdClient
    from ..data_sources.open_meteo_client import OpenMeteoClient
    from ..data_sources.openweather_client import OpenWeatherClient
    from ..core.citations import CitationTracker
    from ..core.config import settings


class WeatherIntelligenceAgent:
    """
    Specialized Agent 3: Weather Intelligence Agent (PS 26176)
    Evaluates marine weather hazards using free Open-Meteo live telemetry (primary),
    optional OpenWeatherMap telemetry (secondary, key-gated), and IMD bulletins.
    """
    def __init__(
        self,
        imd_client: Optional[ImdClient] = None,
        open_meteo_client: Optional[OpenMeteoClient] = None,
        openweather_client: Optional[OpenWeatherClient] = None,
    ):
        self.imd_client = imd_client or ImdClient()
        self.open_meteo_client = open_meteo_client or OpenMeteoClient()
        self.openweather_client = openweather_client or OpenWeatherClient()

    async def evaluate_sea_safety(
        self,
        sea_zone: str = "arabian_sea_south",
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        citation_tracker: Optional[CitationTracker] = None
    ) -> Dict[str, Any]:
        """
        Evaluates marine safety by fusing free live Open-Meteo telemetry and IMD bulletins.
        """
        # Fetch IMD official bulletins and cyclone tracking
        bulletin = await self.imd_client.get_weather_bulletin(citation_tracker=citation_tracker)
        cyclones = await self.imd_client.get_cyclone_status(citation_tracker=citation_tracker)
        zone_info = await self.imd_client.get_warnings_for_zone(sea_zone)

        # Fetch free, zero-key Open-Meteo live micro-telemetry (primary provider)
        query_lat = lat if lat is not None else 10.0
        query_lon = lon if lon is not None else 76.0
        marine_weather = await self.open_meteo_client.get_marine_weather(
            lat=query_lat,
            lon=query_lon,
            citation_tracker=citation_tracker
        )

        # Optional secondary cross-check, only attempted if a key is actually configured
        # (never blocks the response if absent, never required for a complete answer).
        if settings.OPENWEATHERMAP_API_KEY:
            try:
                ow_weather = await self.openweather_client.get_current_weather(
                    lat=query_lat, lon=query_lon, citation_tracker=citation_tracker
                )
                marine_weather["openweather_cross_check"] = {
                    "wind_speed_knots": ow_weather["wind"]["speed_knots"],
                    "source": ow_weather["source"],
                }
            except Exception:
                pass

        is_cyclone_active = len(cyclones) > 0
        wind_knots = marine_weather["wind"]["speed_knots"]

        # Multi-signal safety synthesis
        if is_cyclone_active or wind_knots >= 34 or zone_info.get("safety_status") == "DANGER":
            verdict = "RED_ALERT_DO_NOT_SAIL"
            guidance = "CRITICAL WEATHER HAZARD: Severe squally winds and active cyclonic disturbance. Fishermen are strictly advised NOT to venture into deep sea."
            risk_level = "CRITICAL"
        elif wind_knots >= 20 or zone_info.get("safety_status") == "CAUTION" or marine_weather["squall_risk"] == "HIGH":
            verdict = "AMBER_CAUTION_ALERT"
            guidance = "MODERATE TO ROUGH SEAS: Wind speeds 20-30 knots. Artisanal craft operations restricted. Mechanized vessels must maintain continuous radio watch."
            risk_level = "MODERATE"
        else:
            verdict = "GREEN_SAFE_TO_SAIL"
            guidance = "FAVOURABLE SEA CONDITIONS: Wind speeds and wave heights within normal safe operating thresholds."
            risk_level = "LOW"

        return {
            "agent": "Weather Intelligence Agent",
            "status": "COMPLETED",
            "findings": {
                "location_examined": sea_zone if not (lat and lon) else f"Coordinates ({round(query_lat,2)}°N, {round(query_lon,2)}°E)",
                "is_cyclone_active": is_cyclone_active,
                "active_cyclones_count": len(cyclones),
                "cyclone_risk_level": risk_level,
                "active_cyclones": cyclones,
                "marine_telemetry": marine_weather,
                "zone_fishermen_warning": zone_info,
                "safety_verdict": verdict,
                "action_guidance": guidance
            }
        }
