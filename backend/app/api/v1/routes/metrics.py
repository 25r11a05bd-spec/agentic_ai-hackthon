from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_repository
from app.core.security import AuthenticatedUser, get_current_user
from app.repositories.run_repository import FileRunRepository


router = APIRouter(prefix="/metrics")


@router.get("/overview")
async def get_metrics_overview(
    repository: FileRunRepository = Depends(get_repository),
    user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    del user
    metrics = await repository.get_metrics()
    return {"success": True, "data": metrics.model_dump(mode="json")}
