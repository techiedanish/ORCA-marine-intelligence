from fastapi import APIRouter
try:
    from .endpoints import health, system, marine, weather, geospatial, orca, chat
except ImportError:
    # pyrefly: ignore [missing-import]
    from api.v1.endpoints import health, system, marine, weather, geospatial, orca, chat

api_router = APIRouter()

# Foundational system routes
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(system.router, prefix="/system", tags=["System"])

# Section 1: Marine Data Discovery & Ocean Analytics
api_router.include_router(marine.router, prefix="/marine", tags=["1. Marine Data Discovery"])

# Section 2: Weather Intelligence & Coastal Warnings
api_router.include_router(weather.router, prefix="/weather", tags=["2. Weather Intelligence"])

# Section 3: Geospatial Reasoning & Geofencing
api_router.include_router(geospatial.router, prefix="/geospatial", tags=["3. Geospatial Reasoning"])

# Section 4: Multi-Agent Orchestrator & Multilingual Grounding
api_router.include_router(orca.router, prefix="/orca", tags=["4. ORCA Multi-Agent Orchestrator"])

# Unified Conversational Copilot Endpoint (consumed by apps/web3 split-screen chat)
api_router.include_router(chat.router, prefix="/chat", tags=["5. Conversational Copilot"])
