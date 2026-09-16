"""
========================================================================================
ORCA: Marine EcOsystem Reasoning with Collaborative Agents (SIH 2026 - PS 26176)
Section 4: Risk Assessment Agent
========================================================================================

ROLE IN MULTI-AGENT ORCHESTRATION:
----------------------------------
The Risk Assessment Agent is the safety arbitrator for the entire platform:
1. Synthesizes atmospheric hazards (OpenWeatherMap wind gusts, squall index).
2. Integrates official government disaster warnings (IMD Cyclone Warning Division).
3. Evaluates sovereign border proximity (13-point treaty IMBL line) and Marine Protected Areas.
4. Computes a multi-factor numerical Risk Index (0 to 100).
5. Outputs a definitive decision: GREEN (Safe to Operate), AMBER (Caution), RED (Do Not Sail).
========================================================================================
"""

from typing import Any, Dict, List, Optional
try:
    from core.citations import CitationTracker
except (ImportError, ValueError):
    from ..core.citations import CitationTracker


class RiskAssessmentAgent:
    """
    Specialized Agent 5: Risk Assessment Agent (PS 26176)
    Synthesizes meteorological hazards (OpenWeather + IMD), boundary geofences (Marine Regions),
    and ocean factors into a unified multi-factor safety decision.
    """
    async def evaluate_risk(
        self,
        weather_data: Dict[str, Any],
        geofence_data: Optional[Dict[str, Any]] = None,
        citation_tracker: Optional[CitationTracker] = None
    ) -> Dict[str, Any]:
        risk_score = 0
        reasons: List[str] = []
        alerts: List[str] = []

        # 1. Weather risk factor
        w_status = weather_data.get("safety_verdict") or weather_data.get("overall_verdict", "SAFE")
        ow_telemetry = weather_data.get("marine_telemetry", {})
        wind_knots = ow_telemetry.get("wind", {}).get("speed_knots", 10.0)
        squall_risk = ow_telemetry.get("squall_risk", "LOW")

        if w_status in ["RED_ALERT_DO_NOT_SAIL", "DANGER_CYCLONIC", "DANGER"] or weather_data.get("is_cyclone_active"):
            risk_score += 75
            reasons.append("Active cyclonic disturbance / high wind advisory reported in maritime zone")
            alerts.append("RED ALERT: Total suspension of fishing operations advised by coast guard")
        elif w_status in ["AMBER_CAUTION_ALERT", "CAUTION"] or squall_risk == "HIGH" or wind_knots >= 22:
            risk_score += 35
            reasons.append(f"Moderate-to-high winds ({wind_knots} knots) and active squall conditions")
            alerts.append("YELLOW ALERT: Venture into sea with high caution; small crafts restricted")

        # 2. Geofence risk factor
        if geofence_data:
            imbl = geofence_data.get("imbl_check", {})
            imbl_status = imbl.get("status", "")
            imbl_dist = imbl.get("distance_to_imbl_km", 999.0)

            if imbl_status == "BORDER_BREACH_DETECTED":
                risk_score += 95
                reasons.append(f"CRITICAL: Vessel has breached Indian EEZ and is {imbl_dist} km inside foreign waters")
                alerts.append("EMERGENCY BORDER BREACH: Execute immediate 180° turn to avoid naval interception")
            elif imbl_status == "CRITICAL_VIOLATION_IMMINENT" or imbl_dist < 2.0:
                risk_score += 85
                reasons.append(f"Vessel is only {imbl_dist} km from International Maritime Boundary Line")
                alerts.append("CRITICAL GEOFENCE: Proximity to international boundary line poses imminent risk of detention")
            elif imbl_status == "WARNING_APPROACHING_BORDER" or imbl_dist < 5.0:
                risk_score += 25
                reasons.append(f"Vessel operating in border buffer zone ({imbl_dist} km to IMBL)")
                alerts.append("CAUTION GEOFENCE: Maintain westward navigation clearance")

            mpa = geofence_data.get("mpa_check", {})
            if mpa.get("inside_protected_area"):
                risk_score += 30
                reasons.append(f"Vessel inside {mpa.get('protected_area_name')} core marine sanctuary")
                alerts.append("REGULATORY ALERT: Motorized bottom-trawling prohibited in Marine National Park")

        # Final verdict classification
        if risk_score >= 60:
            final_verdict = "HAZARDOUS_DO_NOT_SAIL"
            color_code = "RED"
        elif risk_score >= 25:
            final_verdict = "CAUTION_RESTRICTED_OPERATIONS"
            color_code = "AMBER"
        else:
            final_verdict = "SAFE_TO_OPERATE"
            color_code = "GREEN"
            reasons.append("Favourable sea state, moderate winds, and safe clearance from maritime borders.")

        if citation_tracker:
            citation_tracker.add(
                claim=f"Calculated multi-factor risk score {risk_score}/100 with final verdict: {final_verdict}",
                source="ORCA Multi-Factor Risk Assessment Engine",
                dataset_name="OpenWeatherMap + IMD Weather + Marine Regions Geofence Fusion",
                reference_id="ORCA-RISK-2026"
            )

        return {
            "agent": "Risk Assessment Agent",
            "status": "COMPLETED",
            "verdict": final_verdict,
            "risk_score": risk_score,
            "color_code": color_code,
            "reasons": reasons,
            "alerts": alerts
        }
