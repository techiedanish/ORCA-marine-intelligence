"""
========================================================================================
ORCA: Marine EcOsystem Reasoning with Collaborative Agents (SIH 2026 - PS 26176)
API Endpoint: Unified Conversational Copilot (/api/v1/chat)
========================================================================================
Single entry point consumed by the apps/web3 split-screen copilot. Delegates to the
Supervisor Agent, which coordinates all 5 domain agents, tracks the Chain-of-Thought
trace, and guarantees a fully-formed response (Gemini Flash synthesis with an ALWAYS
available deterministic rule-based fallback) so the SIH demo never 500s.
========================================================================================
"""

import logging
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

from orchestration.supervisor import handle_query

logger = logging.getLogger("orca.chat")
router = APIRouter()


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User's natural-language marine safety / fisheries question")
    session_id: str = Field(default="default", description="Optional client session identifier for future memory support")
    user_lat: Optional[float] = Field(default=None, description="User's REAL grounded latitude (browser geolocation or harbour fallback selection) — never hallucinated")
    user_lon: Optional[float] = Field(default=None, description="User's REAL grounded longitude (browser geolocation or harbour fallback selection) — never hallucinated")


@router.post("", summary="Ask ORCA a marine safety / fisheries question")
async def chat(payload: ChatRequest):
    try:
        result = await handle_query(payload.query, user_lat=payload.user_lat, user_lon=payload.user_lon)
        return result
    except Exception as exc:
        # ABSOLUTE last-resort guard: the demo must NEVER return a 500. Even if every
        # agent and the deterministic planner somehow fail, return a graceful, minimal,
        # well-formed payload the frontend can still render.
        logger.exception("Unhandled error in ORCA supervisor; returning safe fallback payload.")
        return {
            "query": payload.query,
            "intent": "general",
            "detected_language": "en",
            "detected_language_name": "English",
            "engine_used": "emergency_fallback",
            "trace": [],
            "answer_text": (
                "ORCA is temporarily unable to complete a full analysis for this query. "
                "Please retry, or check the individual agent dashboards (Marine Discovery, "
                "Ocean Analytics, Weather Intelligence, Risk & Geofencing) for manual lookups."
            ),
            "safety_verdict": None,
            "citations": [],
            "citation_sources": [],
            "map": {"center": {"lat": 9.9312, "lon": 76.2673}, "zoom": 6, "pfz_points": [], "imbl_line": [], "mpa_features": [], "mpa_highlight": None, "risk_tint": "AMBER"},
            "raw_findings": {},
            "error": str(exc),
        }
