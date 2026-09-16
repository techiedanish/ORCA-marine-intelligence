from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter()


@router.get("", summary="Liveness probe")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
