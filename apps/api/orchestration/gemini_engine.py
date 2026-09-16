"""
========================================================================================
ORCA: Marine EcOsystem Reasoning with Collaborative Agents (SIH 2026 - PS 26176)
Orchestration: Google Gemini Flash LLM Engine
========================================================================================
Thin wrapper around `google-generativeai` used for:
  1. Fast multilingual intent parsing / entity extraction (optional enhancement over
     the deterministic regex-based parser in intent.py).
  2. Natural-language synthesis of the final answer in the user's queried language.

FAILURE MODE: ANY exception here (missing key, missing package, network failure,
quota exceeded, malformed response) is caught and surfaced as `None` / raises
GeminiUnavailableError so the Supervisor can transparently fall back to the
deterministic rule-based planner. The demo must NEVER 500.
========================================================================================
"""

import json
from typing import Any, Dict, Optional

try:
    from core.config import settings
except (ImportError, ValueError):
    from ..core.config import settings


class GeminiUnavailableError(Exception):
    """Raised whenever Gemini cannot be used for this request; triggers fallback."""


def _get_model():
    if not settings.GEMINI_API_KEY or settings.FORCE_DETERMINISTIC_MODE:
        raise GeminiUnavailableError("Gemini API key not configured or deterministic mode forced.")
    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise GeminiUnavailableError("google-generativeai package not installed.") from exc

    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel(settings.GEMINI_MODEL)


async def synthesize_answer(
    user_query: str,
    detected_language: str,
    agent_findings: Dict[str, Any],
    verdict: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Asks Gemini Flash to produce a concise, fisherman-friendly natural language
    answer in the detected language, grounded strictly in the structured agent
    findings supplied (never inventing new numbers).
    """
    model = _get_model()

    prompt = f"""You are ORCA, a marine safety and fisheries copilot for Indian fishermen.
Answer the user's question ONLY using the structured data provided below. Do not invent
numbers, coordinates, or facts not present in the data. Respond in the same language as
the user's query (language code: {detected_language}). Keep the answer under 120 words,
plain and actionable for a fisherman at sea.

USER QUERY:
{user_query}

STRUCTURED AGENT FINDINGS (JSON):
{json.dumps(agent_findings, default=str)[:6000]}

SAFETY VERDICT (if applicable):
{json.dumps(verdict, default=str) if verdict else "N/A"}
"""

    try:
        response = model.generate_content(prompt)
        text = getattr(response, "text", None)
        if not text:
            raise GeminiUnavailableError("Empty Gemini response.")
        return text.strip()
    except Exception as exc:
        raise GeminiUnavailableError(f"Gemini generation failed: {exc}") from exc


async def extract_intent_llm(user_query: str) -> Dict[str, Any]:
    """
    Optional LLM-assisted intent/entity extraction. Returns a dict compatible with
    orchestration.intent.parse_query's output shape. Falls back by raising
    GeminiUnavailableError if anything goes wrong.
    """
    model = _get_model()

    prompt = f"""Extract structured intent from this marine fisheries query. Return ONLY
raw JSON (no markdown fences) with keys: intent (one of pfz_discovery, safety_check,
productivity_explain, border_check, general), lat (float or null), lon (float or null),
location_name (string or null), species (string or null), time_horizon (today or
tomorrow), detected_language (ISO 639-1 code).

QUERY: {user_query}
"""
    try:
        response = model.generate_content(prompt)
        text = getattr(response, "text", "").strip()
        text = text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(text)
        return parsed
    except Exception as exc:
        raise GeminiUnavailableError(f"Gemini intent extraction failed: {exc}") from exc
