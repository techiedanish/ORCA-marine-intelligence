from fastapi import APIRouter
from core.config import settings

router = APIRouter()


@router.get("/info", summary="ORCA system info & agent registry")
async def system_info():
    return {
        "project": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "problem_statement": "SIH 2026 - PS 26176",
        "llm_engine": settings.GEMINI_MODEL,
        "deterministic_fallback_available": True,
        "agents": [
            "Marine Data Discovery Agent",
            "Ocean Analytics Agent",
            "Weather Intelligence Agent",
            "Risk Assessment Agent",
            "Geospatial Reasoning Agent",
        ],
    }
