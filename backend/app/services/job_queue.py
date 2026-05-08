from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings

try:
    from arq import create_pool
    from arq.connections import RedisSettings
except ImportError:  # pragma: no cover
    create_pool = None
    RedisSettings = None


@dataclass(slots=True)
class QueueDispatchResult:
    dispatched: bool
    mode: str
    detail: str


class JobQueueService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def enqueue_run(self, run_id: str) -> QueueDispatchResult:
        if not self._settings.redis_url or create_pool is None or RedisSettings is None:
            return QueueDispatchResult(
                dispatched=False,
                mode="in_process",
                detail="Redis queue unavailable; falling back to in-process execution.",
            )

        try:
            pool = await create_pool(RedisSettings.from_dsn(self._settings.redis_url))
            try:
                job = await pool.enqueue_job("process_qa_run_job", run_id, _queue_name=self._settings.queue_name)
            finally:
                await pool.close()
        except Exception as exc:  # pragma: no cover
            return QueueDispatchResult(
                dispatched=False,
                mode="in_process",
                detail=f"Queue dispatch failed: {exc}",
            )

        return QueueDispatchResult(
            dispatched=job is not None,
            mode="redis" if job is not None else "in_process",
            detail="Run dispatched to Redis worker." if job is not None else "Queue accepted no job; using fallback.",
        )
