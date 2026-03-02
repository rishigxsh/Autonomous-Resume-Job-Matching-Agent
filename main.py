"""Application entry point for the Resume–Job Matching Agent.

Run with:
    DEV:  uvicorn main:app --reload
    PROD: uvicorn main:app --host 0.0.0.0 --port 8000
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import router as api_router
from core.config import settings

app = FastAPI(
    title=settings.app_name,
    description=(
        "Compares a candidate resume against a job description and produces "
        "an explainable match score with improvement suggestions."
    ),
    version=settings.version,
    docs_url="/docs" if not settings.is_prod else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health() -> dict:
    """Lightweight liveness check — returns 200 when the server is up."""
    return {"status": "ok", "env": settings.app_env}


# In production, serve the built frontend from /frontend/dist.
_STATIC_DIR = Path(__file__).resolve().parent / "frontend" / "dist"
if settings.is_prod and _STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="static")
