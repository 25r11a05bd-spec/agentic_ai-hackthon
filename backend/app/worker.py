from __future__ import annotations

from app.api.deps import get_run_service
from app.core.config import get_settings

try:
    from arq.connections import RedisSettings
except ImportError:  # pragma: no cover
    RedisSettings = None


async def process_qa_run_job(ctx: dict, run_id: str) -> None:
    del ctx
    await get_run_service().process_run(run_id)


settings = get_settings()


class WorkerSettings:
    functions = [process_qa_run_job]
    queue_name = settings.queue_name
    max_jobs = settings.worker_concurrency
    job_timeout = settings.worker_job_timeout_seconds
    redis_settings = RedisSettings.from_dsn(settings.redis_url) if RedisSettings and settings.redis_url else None
