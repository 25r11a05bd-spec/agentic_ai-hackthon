from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_repository
from app.core.security import AuthenticatedUser, get_current_user
from app.repositories.run_repository import FileRunRepository


router = APIRouter(prefix="/notifications")


@router.get("/logs")
async def get_notification_logs(
    repository: FileRunRepository = Depends(get_repository),
    user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    del user
    logs = await repository.list_notifications()
    return {"success": True, "data": [item.model_dump(mode="json") for item in logs]}
