from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.api.deps import get_app_settings, get_repository, get_websocket_manager
from app.api.websocket.manager import PlaybackWebSocketManager
from app.core.config import Settings
from app.repositories.run_repository import FileRunRepository


router = APIRouter()


@router.websocket("/ws/qa-runs/{run_id}")
async def qa_run_stream(
    websocket: WebSocket,
    run_id: str,
    manager: PlaybackWebSocketManager = Depends(get_websocket_manager),
    repository: FileRunRepository = Depends(get_repository),
    settings: Settings = Depends(get_app_settings),
) -> None:
    await manager.connect(run_id, websocket)
    run = await repository.get_run(run_id)
    if run:
        for event in run.playback[-25:]:
            await websocket.send_json(event.model_dump(mode="json"))

    try:
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=settings.websocket_heartbeat_seconds)
            except TimeoutError:
                await websocket.send_json({"event_type": "heartbeat", "run_id": run_id})
    except WebSocketDisconnect:
        await manager.disconnect(run_id, websocket)
