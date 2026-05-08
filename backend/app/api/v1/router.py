from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes.metrics import router as metrics_router
from app.api.v1.routes.notifications import router as notifications_router
from app.api.v1.routes.qa_runs import router as qa_runs_router


router = APIRouter(prefix="/api/v1")
router.include_router(qa_runs_router, tags=["qa-runs"])
router.include_router(metrics_router, tags=["metrics"])
router.include_router(notifications_router, tags=["notifications"])
