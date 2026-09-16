import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure apps/api is in sys.path
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from core.config import settings
from api.v1.api import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sis-api")

# The statically-exported Next.js frontend (apps/web3 -> `npm run build` with
# `output: "export"`) lands here. Single-port architecture: this ONE FastAPI process
# serves both the UI (at "/") and the API (at settings.API_V1_STR) — no separate
# :3002 dev server, no proxy config, no CORS friction for the judge running the demo.
WEB_STATIC_DIR = CURRENT_DIR.parent / "web3" / "out"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    logger.info(f"Starting {settings.PROJECT_NAME} in [{settings.ENVIRONMENT}] mode...")
    logger.info(f"API endpoints available at {settings.API_V1_STR}")
    if WEB_STATIC_DIR.exists():
        logger.info(f"Serving statically-exported web3 frontend from {WEB_STATIC_DIR} at /")
    else:
        logger.warning(
            f"No built frontend found at {WEB_STATIC_DIR}. "
            "Run `python run.py` from the repo root (it builds web3 automatically), "
            "or `npm run build` inside apps/web3, then restart."
        )
    yield
    # Shutdown sequence
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Smart India Hackathon 2026 (SIH26) SIS Monorepo Backend API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Set up CORS middleware (kept for local `npm run dev` on :3002 against this API
# during frontend-only iteration; irrelevant once served same-origin via StaticFiles)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount V1 API router BEFORE the static frontend mount. Starlette resolves routes in
# registration order, so /api/v1/* always matches the router first; only paths NOT
# claimed by the API router fall through to the static frontend files below.
app.include_router(api_router, prefix=settings.API_V1_STR)


if WEB_STATIC_DIR.exists():
    # Single-port production mode: the built frontend IS the root application.
    app.mount("/", StaticFiles(directory=str(WEB_STATIC_DIR), html=True), name="web3")
else:
    # Backend-only / pre-build fallback so hitting "/" is still informative instead
    # of a bare 404 while you're setting things up.
    @app.get("/", summary="Root API Index (frontend not yet built)")
    async def root():
        return JSONResponse(
            content={
                "message": f"Welcome to {settings.PROJECT_NAME}",
                "status": "online",
                "note": (
                    "The apps/web3 frontend has not been built yet, so this API-only "
                    "index is shown instead of the ORCA copilot UI. Run `python run.py` "
                    "from the repo root, or `npm run build` in apps/web3, then restart."
                ),
                "docs": "/docs",
                "health": f"{settings.API_V1_STR}/health",
                "system_info": f"{settings.API_V1_STR}/system/info",
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=False)

