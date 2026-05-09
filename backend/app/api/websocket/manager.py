from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class PlaybackWebSocketManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, run_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[run_id].add(websocket)

    async def disconnect(self, run_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            sockets = self._connections.get(run_id)
            if not sockets:
                return
            sockets.discard(websocket)
            if not sockets:
                self._connections.pop(run_id, None)

    async def broadcast(self, run_id: str, payload: dict[str, Any]) -> None:
        async with self._lock:
            sockets = list(self._connections.get(run_id, set()))

        stale: list[WebSocket] = []
        for socket in sockets:
            try:
                await asyncio.wait_for(socket.send_json(payload), timeout=1.0)
            except Exception:
                stale.append(socket)

        for socket in stale:
            await self.disconnect(run_id, socket)
