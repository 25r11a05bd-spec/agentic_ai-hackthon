from __future__ import annotations

from functools import lru_cache

from app.api.websocket.manager import PlaybackWebSocketManager
from app.core.config import Settings, get_settings
from app.memory.chroma_service import ChromaMemoryService
from app.repositories.run_repository import FileRunRepository
from app.services.notification_service import NotificationService
from app.services.job_queue import JobQueueService
from app.services.qa_run_service import QARunService


@lru_cache(maxsize=1)
def get_repository() -> FileRunRepository:
    settings = get_settings()
    return FileRunRepository(settings.data_dir)


@lru_cache(maxsize=1)
def get_memory_service() -> ChromaMemoryService:
    return ChromaMemoryService(get_settings())


@lru_cache(maxsize=1)
def get_websocket_manager() -> PlaybackWebSocketManager:
    return PlaybackWebSocketManager()


@lru_cache(maxsize=1)
def get_notification_service() -> NotificationService:
    return NotificationService(get_settings())


@lru_cache(maxsize=1)
def get_job_queue_service() -> JobQueueService:
    return JobQueueService(get_settings())


@lru_cache(maxsize=1)
def get_run_service() -> QARunService:
    return QARunService(
        repository=get_repository(),
        memory_service=get_memory_service(),
        notification_service=get_notification_service(),
        websocket_manager=get_websocket_manager(),
        settings=get_settings(),
    )


def get_app_settings() -> Settings:
    return get_settings()
