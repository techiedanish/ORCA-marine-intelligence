from fastapi import APIRouter
from core.config import settings

router = APIRouter()


@router.get("/status", summary="Multi-agent orchestrator status & configuration")
async def orchestrator_status():
    return {
        "orchestrator": "ORCA Supervisor Agent",
        "llm_engine": settings.GEMINI_MODEL,
        "gemini_configured": bool(settings.GEMINI_API_KEY) and not settings.FORCE_DETERMINISTIC_MODE,
        "deterministic_fallback": "ALWAYS_AVAILABLE",
        "supported_languages": ["en", "hi", "ta", "ml", "te", "bn"],
        "domain_agents": [
            {"name": "Marine Data Discovery Agent", "endpoint_prefix": "/api/v1/marine"},
            {"name": "Ocean Analytics Agent", "endpoint_prefix": "/api/v1/marine"},
            {"name": "Weather Intelligence Agent", "endpoint_prefix": "/api/v1/weather"},
            {"name": "Risk Assessment Agent", "endpoint_prefix": "/api/v1/geospatial"},
            {"name": "Geospatial Reasoning Agent", "endpoint_prefix": "/api/v1/geospatial"},
        ],
    }
