"""FastAPI entry point (Phase 4 foundation).

- GET /api/health: LLM configuration status and a live BTS API connectivity check.
- Serves the built React app (frontend/dist) from the same origin when it exists (D-034).
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.data import bts_api
from app.settings import get_settings

app = FastAPI(title="Airport Investment Intelligence Agent")


@app.get("/api/health")
def health() -> dict:
    settings = get_settings()
    bts = bts_api.check_connectivity(settings)
    return {
        "status": "ok",
        "llm_configured": settings.llm_configured,
        "llm_model": settings.llm_model,
        "bts_api": bts,
    }


_dist = get_settings().frontend_dist
if _dist.is_dir():
    app.mount("/", StaticFiles(directory=_dist, html=True), name="spa")
