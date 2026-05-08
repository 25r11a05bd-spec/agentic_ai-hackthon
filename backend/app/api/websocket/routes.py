from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.api.deps import get_app_settings, get_repository, get_websocket_manager
from app.api.websocket.manager import PlaybackWebSocketManager
from app.core.config import Settings
from app.repositories.run_repository import FileRunRepository

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/test")
async def test_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_text("WebSocket test successful")
    await websocket.close()


@router.websocket("/ws/qa-runs/{run_id}")
async def qa_run_stream(
    websocket: WebSocket,
    run_id: str,
) -> None:
    from app.api.deps import get_websocket_manager, get_repository, get_app_settings
    
    logger.info(f"[WebSocket] Handler invoked for run_id: {run_id}")
    logger.info(f"[WebSocket] Headers: {dict(websocket.headers)}")
    
    try:
        # Accept the WebSocket connection FIRST before any other operations
        await websocket.accept()
        logger.info(f"[WebSocket] Connection accepted for run_id: {run_id}")
        
        manager = get_websocket_manager()
        repository = get_repository()
        settings = get_app_settings()
        
        await manager.connect(run_id, websocket)
        
        run = await repository.get_run(run_id)
        logger.info(f"[WebSocket] Got run data for run_id: {run_id}, found: {run is not None}")
        
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
            logger.info(f"[WebSocket] Client disconnected for run_id: {run_id}")
            await manager.disconnect(run_id, websocket)
    except Exception as e:
        logger.error(f"[WebSocket] Error in qa_run_stream for run_id {run_id}: {e}", exc_info=True)
        raise
