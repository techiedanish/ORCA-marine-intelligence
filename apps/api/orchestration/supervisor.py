"""
========================================================================================
ORCA: Marine EcOsystem Reasoning with Collaborative Agents (SIH 2026 - PS 26176)
Orchestration: Supervisor Agent
========================================================================================
The single entry point for the conversational endpoint (/api/v1/orca/chat). Coordinates
task execution across the 5 specialized domain agents, tracks a step-by-step
Chain-of-Thought trace for the frontend's ThoughtAccordion, attempts Gemini Flash for
multilingual synthesis, and ALWAYS falls back to a deterministic rule-based planner so
the SIH demo never returns a 500 or an incomplete response.
========================================================================================
"""

import time
from typing import Any, Dict, List, Optional

try:
    from core.citations import CitationTracker
    from data_sources.eez_boundaries import EezBoundaries
    from agents.discovery_agent import MarineDataDiscoveryAgent
    from agents.analytics_agent import OceanAnalyticsAgent
    from agents.weather_agent import WeatherIntelligenceAgent
    from agents.risk_agent import RiskAssessmentAgent
    from agents.geospatial_agent import GeospatialReasoningAgent
    from orchestration.intent import parse_query
    from orchestration.language import detect_language, phrase, LANGUAGE_NAMES
    from orchestration import gemini_engine
    from orchestration.gemini_engine import GeminiUnavailableError
except (ImportError, ValueError):
    from ..core.citations import CitationTracker
    from ..data_sources.eez_boundaries import EezBoundaries
    from ..agents.discovery_agent import MarineDataDiscoveryAgent
    from ..agents.analytics_agent import OceanAnalyticsAgent
    from ..agents.weather_agent import WeatherIntelligenceAgent
    from ..agents.risk_agent import RiskAssessmentAgent
    from ..agents.geospatial_agent import GeospatialReasoningAgent
    from .intent import parse_query
    from .language import detect_language, phrase, LANGUAGE_NAMES
    from . import gemini_engine
    from .gemini_engine import GeminiUnavailableError

_eez = EezBoundaries()

_discovery_agent = MarineDataDiscoveryAgent()
_analytics_agent = OceanAnalyticsAgent()
_weather_agent = WeatherIntelligenceAgent()
_risk_agent = RiskAssessmentAgent()
_geo_agent = GeospatialReasoningAgent()


def _trace_step(agent_name: str, status: str, summary: str, duration_ms: int) -> Dict[str, Any]:
    return {
        "agent": agent_name,
        "status": status,
        "summary": summary,
        "duration_ms": duration_ms,
    }


def _verdict_color_key(color_code: str) -> str:
    return {"GREEN": "GREEN_SAFE", "AMBER": "AMBER_CAUTION", "RED": "RED_DANGER"}.get(color_code, "GREEN_SAFE")


def _build_deterministic_answer(
    intent: str,
    lang: str,
    parsed: Dict[str, Any],
    findings: Dict[str, Any],
    risk: Optional[Dict[str, Any]],
) -> str:
    parts: List[str] = []

    if risk:
        parts.append(phrase(_verdict_color_key(risk["color_code"]), lang))

    if intent == "pfz_discovery" and "discovery" in findings:
        top = findings["discovery"]["findings"].get("top_recommendation")
        if top:
            parts.append(phrase("PFZ_FOUND", lang))
            parts.append(
                f"{top.get('landing_centre', 'Sector')} — SST {top.get('sst_celsius')}°C, "
                f"Chl-a {top.get('chlorophyll_mg_m3')} mg/m³, ~{top.get('distance_from_user_km', top.get('distance_from_coast_km', '?'))} km away."
            )

    if intent == "productivity_explain" and "analytics" in findings:
        parts.append(findings["analytics"]["analysis"]["ecological_explanation"])

    if intent == "border_check" and "geospatial" in findings:
        imbl = findings["geospatial"]["geospatial_audit"]["imbl_check"]
        if imbl["status"] in ("CLEAR_SAFE_DISTANCE",):
            parts.append(phrase("BORDER_SAFE", lang))
        else:
            parts.append(phrase("BORDER_WARNING", lang))
        parts.append(f"Distance to IMBL: {imbl['distance_to_imbl_km']} km ({imbl['side_of_border']}).")

    if not parts:
        parts.append(phrase("GREEN_SAFE", lang))

    return " ".join(parts)


def _build_map_payload(
    parsed: Dict[str, Any],
    findings: Dict[str, Any],
    risk: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    pfz_points = []
    if "discovery" in findings:
        sectors = findings["discovery"]["findings"].get("pfz_sectors", [])
        for s in sectors:
            pfz_points.append(
                {
                    "name": s.get("landing_centre") or s.get("sector_id"),
                    "lat": s.get("latitude"),
                    "lon": s.get("longitude"),
                    "sst_celsius": s.get("sst_celsius"),
                    "chlorophyll_mg_m3": s.get("chlorophyll_mg_m3"),
                    "fapi_score": s.get("fapi_score"),
                }
            )

    mpa_highlight = None
    if "geospatial" in findings:
        mpa = findings["geospatial"]["geospatial_audit"]["mpa_check"]
        if mpa.get("inside_protected_area"):
            mpa_highlight = mpa.get("protected_area_name")

    risk_tint = risk["color_code"] if risk else "GREEN"

    return {
        "center": {"lat": parsed["lat"], "lon": parsed["lon"]},
        "zoom": 7,
        "vessel_marker": {"lat": parsed["lat"], "lon": parsed["lon"]},
        "pfz_points": pfz_points,
        "imbl_line": _eez.get_imbl_coordinates(),
        "mpa_features": _eez.get_mpa_features(),
        "mpa_highlight": mpa_highlight,
        "risk_tint": risk_tint,
    }


async def handle_query(
    user_query: str,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Main Supervisor entry point. Runs the relevant domain agents for the detected
    intent, tracks a Chain-of-Thought trace, and synthesizes a final answer via
    Gemini Flash (with deterministic rule-based fallback on any failure).

    `user_lat`/`user_lon` are the caller's REAL grounded position (browser
    geolocation or an explicit harbour selection from the frontend) — used
    whenever the query text itself doesn't name an explicit position or place.
    """
    lang = detect_language(user_query)
    # NOTE: `gemini_engine.extract_intent_llm` is available as a drop-in upgrade to
    # the deterministic parser below (better handling of novel phrasings once a real
    # GEMINI_API_KEY is configured), but is not called by default so the demo stays
    # fully deterministic and fast without a network round-trip on every keystroke.
    parsed = parse_query(user_query, user_lat=user_lat, user_lon=user_lon)
    intent = parsed["intent"]

    tracker = CitationTracker()
    trace: List[Dict[str, Any]] = []
    findings: Dict[str, Any] = {}

    # --- Geospatial Reasoning Agent: always runs to audit the working position ---
    t0 = time.perf_counter()
    geo_result = await _geo_agent.evaluate_position(parsed["lat"], parsed["lon"], citation_tracker=tracker)
    findings["geospatial"] = geo_result
    trace.append(
        _trace_step(
            "Geospatial Reasoning Agent",
            "COMPLETED",
            f"Audited position ({parsed['lat']}, {parsed['lon']}) against IMBL treaty line and MPA registry.",
            int((time.perf_counter() - t0) * 1000),
        )
    )

    # --- Marine Data Discovery Agent ---
    if intent in ("pfz_discovery", "general"):
        t0 = time.perf_counter()
        disc = await _discovery_agent.execute(
            lat=parsed["lat"], lon=parsed["lon"], species=parsed["species"], citation_tracker=tracker
        )
        findings["discovery"] = disc
        trace.append(
            _trace_step(
                "Marine Data Discovery Agent",
                "COMPLETED",
                f"Scanned INCOIS PFZ sectors" + (f" for {parsed['species']}" if parsed["species"] else "") + ".",
                int((time.perf_counter() - t0) * 1000),
            )
        )
    else:
        trace.append(_trace_step("Marine Data Discovery Agent", "SKIPPED", "Not required for this query intent.", 0))

    # --- Ocean Analytics Agent ---
    if intent in ("productivity_explain", "pfz_discovery", "general"):
        t0 = time.perf_counter()
        analytics = await _analytics_agent.analyze_productivity(
            lat=parsed["lat"], lon=parsed["lon"], target_species=parsed["species"], citation_tracker=tracker
        )
        findings["analytics"] = analytics
        trace.append(
            _trace_step(
                "Ocean Analytics Agent",
                "COMPLETED",
                f"Computed SST thermal gradient and Chlorophyll-a upwelling (FAPI {analytics['analysis']['fapi_score']}).",
                int((time.perf_counter() - t0) * 1000),
            )
        )
    else:
        trace.append(_trace_step("Ocean Analytics Agent", "SKIPPED", "Not required for this query intent.", 0))

    # --- Weather Intelligence Agent: runs whenever safety is implicated (always, for risk fusion) ---
    t0 = time.perf_counter()
    weather = await _weather_agent.evaluate_sea_safety(
        sea_zone=parsed["sea_zone"], lat=parsed["lat"], lon=parsed["lon"], citation_tracker=tracker
    )
    findings["weather"] = weather
    trace.append(
        _trace_step(
            "Weather Intelligence Agent",
            "COMPLETED",
            f"Fused IMD bulletins and OpenWeatherMap telemetry: verdict {weather['findings']['safety_verdict']}.",
            int((time.perf_counter() - t0) * 1000),
        )
    )

    # --- Risk Assessment Agent: always runs to produce the final safety verdict ---
    t0 = time.perf_counter()
    risk = await _risk_agent.evaluate_risk(
        weather_data=weather["findings"],
        geofence_data=geo_result["geospatial_audit"],
        citation_tracker=tracker,
    )
    findings["risk"] = risk
    trace.append(
        _trace_step(
            "Risk Assessment Agent",
            "COMPLETED",
            f"Synthesized multi-factor risk score {risk['risk_score']}/100 -> {risk['color_code']}.",
            int((time.perf_counter() - t0) * 1000),
        )
    )

    # --- Final synthesis: Gemini Flash first, deterministic fallback on ANY failure ---
    engine_used = "deterministic_fallback"
    try:
        answer_text = await gemini_engine.synthesize_answer(user_query, lang, findings, risk)
        engine_used = "gemini_flash"
    except GeminiUnavailableError:
        answer_text = _build_deterministic_answer(intent, lang, parsed, findings, risk)

    map_payload = _build_map_payload(parsed, findings, risk)

    return {
        "query": user_query,
        "intent": intent,
        "detected_language": lang,
        "detected_language_name": LANGUAGE_NAMES.get(lang, "English"),
        "engine_used": engine_used,
        "trace": trace,
        "answer_text": answer_text,
        "coordinate_source": parsed["coordinate_source"],
        "resolved_location": {"lat": parsed["lat"], "lon": parsed["lon"], "location_name": parsed["location_name"]},
        "safety_verdict": {
            "verdict": risk["verdict"],
            "risk_score": risk["risk_score"],
            "color_code": risk["color_code"],
            "reasons": risk["reasons"],
            "alerts": risk["alerts"],
        },
        "citations": tracker.all(),
        "citation_sources": tracker.sources_summary(),
        "map": map_payload,
        "raw_findings": findings,
    }
