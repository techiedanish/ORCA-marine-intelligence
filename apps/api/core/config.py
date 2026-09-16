"""
========================================================================================
ORCA: Marine EcOsystem Reasoning with Collaborative Agents (SIH 2026 - PS 26176)
Core Configuration
========================================================================================
Centralized environment-driven settings for the ORCA backend. All values have safe
defaults so the demo NEVER crashes even with a completely empty `.env` file.
========================================================================================
"""

import os
from typing import List


def _split_csv(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "ORCA - Marine EcOsystem Reasoning with Collaborative Agents")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")

    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    BACKEND_CORS_ORIGINS: List[str] = _split_csv(
        os.getenv(
            "BACKEND_CORS_ORIGINS",
            "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://127.0.0.1:3000",
        )
    )

    # --- External data provider credentials (all optional; deterministic fallback covers absence) ---
    OPENWEATHERMAP_API_KEY: str = os.getenv("OPENWEATHERMAP_API_KEY", "")
    OPENWEATHERMAP_BASE_URL: str = os.getenv("OPENWEATHERMAP_BASE_URL", "https://api.openweathermap.org/data/2.5")

    IMD_BASE_URL: str = os.getenv("IMD_BASE_URL", "https://api.imd.gov.in")
    INCOIS_BASE_URL: str = os.getenv("INCOIS_BASE_URL", "https://incois.gov.in/MarineFisheries")

    # --- LLM Engine (Google Gemini Flash) ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # Toggle to force the deterministic rule-based planner even if a Gemini key is present
    FORCE_DETERMINISTIC_MODE: bool = os.getenv("FORCE_DETERMINISTIC_MODE", "false").lower() == "true"


settings = Settings()
