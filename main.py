"""Application entry point for the Resume–Job Matching Agent.

Run with:
    uvicorn main:app --reload

FastAPI is used because it provides automatic request validation via Pydantic
(which our data contracts already use), built-in OpenAPI docs, and async
support — all with minimal boilerplate.

AI/LLM logic, scoring, and parsing will be wired in during later phases.
This module is responsible only for creating the FastAPI instance, mounting
routers, and exposing infrastructure endpoints like /health.
"""

from fastapi import FastAPI

from api.routes import router as api_router
from core.config import settings

app = FastAPI(
    title=settings.app_name,
    description=(
        "Compares a candidate resume against a job description and produces "
        "an explainable match score with improvement suggestions."
    ),
    version=settings.version,
)

app.include_router(api_router)


@app.get("/health")
async def health() -> dict:
    """Lightweight liveness check — returns 200 when the server is up."""
    return {"status": "ok"}
