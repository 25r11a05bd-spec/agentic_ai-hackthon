from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.api.deps import (
    get_job_queue_service,
    get_notification_service,
    get_repository,
    get_run_service,
    get_websocket_manager,
)
from app.api.websocket.manager import PlaybackWebSocketManager
from app.core.config import Settings
from app.main import app
from app.memory.chroma_service import ChromaMemoryService
from app.repositories.run_repository import FileRunRepository
from app.services.notification_service import NotificationService
from app.services.job_queue import QueueDispatchResult
from app.services.qa_run_service import QARunService


def _build_service(tmp_path: Path) -> tuple[QARunService, FileRunRepository]:
    settings = Settings(
        data_dir=tmp_path / "storage",
        auth_dev_mode=True,
        frontend_url="http://localhost:3000",
    )
    repository = FileRunRepository(settings.data_dir)
    websocket_manager = PlaybackWebSocketManager()
    notification_service = NotificationService(settings)
    memory_service = ChromaMemoryService(settings)
    service = QARunService(
        repository=repository,
        memory_service=memory_service,
        notification_service=notification_service,
        websocket_manager=websocket_manager,
        settings=settings,
    )
    return service, repository


def _override_dependencies(
    service: QARunService,
    repository: FileRunRepository,
    queue_service: object | None = None,
) -> None:
    app.dependency_overrides[get_run_service] = lambda: service
    app.dependency_overrides[get_repository] = lambda: repository
    app.dependency_overrides[get_websocket_manager] = lambda: service._websocket_manager
    app.dependency_overrides[get_notification_service] = lambda: service._notification_service
    app.dependency_overrides[get_job_queue_service] = lambda: queue_service or _FakeQueueService()


class _FakeQueueService:
    async def enqueue_run(self, run_id: str) -> QueueDispatchResult:
        return QueueDispatchResult(dispatched=False, mode="in_process", detail=f"fallback for {run_id}")


class _QueuedQueueService:
    async def enqueue_run(self, run_id: str) -> QueueDispatchResult:
        return QueueDispatchResult(dispatched=True, mode="redis", detail=f"queued {run_id}")


def _sample_project() -> bytes:
    return (
        b"import httpx\n\n"
        b"async def validate_payload():\n"
        b"    async with httpx.AsyncClient() as client:\n"
        b"        await client.get('https://example.com')\n"
    )


def _sample_workflow() -> bytes:
    return (
        b'{"steps": ['
        b'{"id": "fetch", "name": "Fetch API", "type": "api", "endpoint": "https://example.com"},'
        b'{"id": "validate", "name": "Validate", "type": "validator"}'
        b"]}"
    )


def test_service_process_run_generates_report_and_playback(tmp_path: Path) -> None:
    import asyncio

    service, repository = _build_service(tmp_path)

    async def scenario() -> None:
        from app.core.security import AuthenticatedUser
        from app.schemas.qa_run import QARunCreate

        run = await service.create_run(
            request=QARunCreate(),
            created_by=AuthenticatedUser(user_id="dev", role="admin", email=None),
            project_file_name="app.py",
            project_bytes=_sample_project(),
            workflow_file_name="automation.json",
            workflow_bytes=_sample_workflow(),
        )
        await service.process_run(run.id)
        detail = await repository.get_run(run.id)
        assert detail is not None
        assert detail.report_markdown is not None
        assert len(detail.playback) > 0
        assert len(detail.snapshots) > 0
        assert detail.latest_state["quality_summary"]["run_id"] == run.id

    asyncio.run(scenario())


def test_api_create_run_and_fetch_detail(tmp_path: Path) -> None:
    service, repository = _build_service(tmp_path)
    _override_dependencies(service, repository)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/qa-runs",
            headers={"x-demo-role": "admin", "x-demo-user": "tester"},
            files={
                "project_file": ("app.py", _sample_project(), "text/x-python"),
                "workflow_file": ("automation.json", _sample_workflow(), "application/json"),
            },
            data={
                "task": "Run QA",
                "validation_mode": "strict",
                "retry_enabled": "true",
                "notifications_enabled": "true",
                "max_retries": "2",
            },
        )
        assert response.status_code == 202
        payload = response.json()["data"]
        run_id = payload["id"]

        detail = client.get(f"/api/v1/qa-runs/{run_id}", headers={"x-demo-role": "viewer"}).json()["data"]
        assert detail["id"] == run_id

        playback = client.get(f"/api/v1/qa-runs/{run_id}/playback", headers={"x-demo-role": "viewer"}).json()["data"]
        assert len(playback["events"]) > 0

        graph = client.get(f"/api/v1/qa-runs/{run_id}/graph", headers={"x-demo-role": "viewer"}).json()["data"]
        assert len(graph["nodes"]) == 13

    app.dependency_overrides.clear()


def test_api_approval_flow_and_notifications(tmp_path: Path) -> None:
    service, repository = _build_service(tmp_path)
    _override_dependencies(service, repository)

    with TestClient(app) as client:
        create = client.post(
            "/api/v1/qa-runs",
            headers={"x-demo-role": "admin", "x-demo-user": "tester"},
            files={
                "project_file": ("app.py", _sample_project(), "text/x-python"),
                "workflow_file": ("automation.json", _sample_workflow(), "application/json"),
            },
        )
        run_id = create.json()["data"]["id"]

        approve = client.post(
            f"/api/v1/qa-runs/{run_id}/approve",
            headers={"x-demo-role": "admin", "x-demo-user": "approver"},
            json={"decision": "approved", "rationale": "Looks safe enough for this test."},
        )
        assert approve.status_code == 200
        assert approve.json()["data"]["decision"] == "approved"

        logs = client.get("/api/v1/notifications/logs", headers={"x-demo-role": "viewer"}).json()["data"]
        assert isinstance(logs, list)

    app.dependency_overrides.clear()


def test_api_requires_admin_for_approval(tmp_path: Path) -> None:
    service, repository = _build_service(tmp_path)
    _override_dependencies(service, repository)

    with TestClient(app) as client:
        create = client.post(
            "/api/v1/qa-runs",
            headers={"x-demo-role": "admin", "x-demo-user": "tester"},
            files={
                "project_file": ("app.py", _sample_project(), "text/x-python"),
                "workflow_file": ("automation.json", _sample_workflow(), "application/json"),
            },
        )
        run_id = create.json()["data"]["id"]
        forbidden = client.post(
            f"/api/v1/qa-runs/{run_id}/approve",
            headers={"x-demo-role": "viewer", "x-demo-user": "viewer-user"},
            json={"decision": "approved", "rationale": "Should not work."},
        )
        assert forbidden.status_code == 403

    app.dependency_overrides.clear()


def test_websocket_replays_existing_events(tmp_path: Path) -> None:
    service, repository = _build_service(tmp_path)
    _override_dependencies(service, repository)

    with TestClient(app) as client:
        create = client.post(
            "/api/v1/qa-runs",
            headers={"x-demo-role": "admin", "x-demo-user": "tester"},
            files={
                "project_file": ("app.py", _sample_project(), "text/x-python"),
                "workflow_file": ("automation.json", _sample_workflow(), "application/json"),
            },
        )
        run_id = create.json()["data"]["id"]

        with client.websocket_connect(f"/ws/qa-runs/{run_id}") as websocket:
            first_event = websocket.receive_json()
            assert "event_type" in first_event
            assert first_event["run_id"] == run_id

    app.dependency_overrides.clear()


def test_api_create_run_records_queue_dispatch_when_worker_queue_available(tmp_path: Path) -> None:
    service, repository = _build_service(tmp_path)
    _override_dependencies(service, repository, _QueuedQueueService())

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/qa-runs",
            headers={"x-demo-role": "admin", "x-demo-user": "tester"},
            files={
                "project_file": ("app.py", _sample_project(), "text/x-python"),
                "workflow_file": ("automation.json", _sample_workflow(), "application/json"),
            },
        )
        assert response.status_code == 202
        run_id = response.json()["data"]["id"]
        detail = client.get(f"/api/v1/qa-runs/{run_id}", headers={"x-demo-role": "viewer"}).json()["data"]
        assert detail["status"] == "queued"
        assert detail["latest_state"]["queue_mode"] == "redis"

    app.dependency_overrides.clear()
