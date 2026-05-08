from __future__ import annotations

import logging
import asyncio
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import router as api_v1_router
from app.api.websocket.routes import router as websocket_router
from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")


@app.on_event("startup")
async def startup_log() -> None:
    from app.api.deps import get_supabase_service
    svc = get_supabase_service()
    if svc.is_enabled:
        logger.warning("✅ SUPABASE ENABLED — all runs will be stored in the cloud.")
    else:
        logger.warning("⚠️  SUPABASE DISABLED — falling back to local file storage.")
        logger.warning(f"    supabase_url={settings.supabase_url!r}")
        logger.warning(f"    supabase_service_role_key set={bool(settings.supabase_service_role_key)}")

# Serve storage directory for downloads
app.mount("/storage", StaticFiles(directory=str(settings.data_dir)), name="storage")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)
app.include_router(websocket_router)

# Debug: Log all routes to verify WebSocket registration
for route in app.routes:
    if hasattr(route, 'path'):
        logger.info(f"🔗 Registered route: {route.path} [{type(route).__name__}]")


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": "backend-api"}
