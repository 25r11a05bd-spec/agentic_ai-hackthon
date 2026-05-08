from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status

from app.api.deps import get_job_queue_service, get_repository, get_run_service
from app.core.security import AuthenticatedUser, get_current_user, require_role
from app.repositories.run_repository import FileRunRepository
from app.schemas.qa_run import ApprovalDecisionRequest, QARunCreate, RetryRequest
from app.services.job_queue import JobQueueService
from app.services.qa_run_service import QARunService


router = APIRouter(prefix="/qa-runs")


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_qa_run(
    background_tasks: BackgroundTasks,
    project_file: UploadFile = File(...),
    workflow_file: UploadFile = File(...),
    attachments: list[UploadFile] | None = File(default=None),
    task: str = Form(default="Analyze automation workflow quality"),
    validation_mode: str = Form(default="strict"),
    retry_enabled: bool = Form(default=True),
    notifications_enabled: bool = Form(default=True),
    max_retries: int = Form(default=3),
    user: AuthenticatedUser = Depends(require_role("admin", "operator")),
    service: QARunService = Depends(get_run_service),
    queue_service: JobQueueService = Depends(get_job_queue_service),
) -> dict:
    request = QARunCreate(
        task=task,
        validation_mode=validation_mode,
        retry_enabled=retry_enabled,
        notifications_enabled=notifications_enabled,
        max_retries=max_retries,
    )
    run = await service.create_run(
        request=request,
        created_by=user,
        project_file_name=project_file.filename or "app.py",
        project_bytes=await project_file.read(),
        workflow_file_name=workflow_file.filename or "automation.json",
        workflow_bytes=await workflow_file.read(),
        attachments=[
            (upload.filename or f"attachment_{index}", await upload.read()) for index, upload in enumerate(attachments or [])
        ],
    )
    queue_result = await queue_service.enqueue_run(run.id)
    if queue_result.dispatched:
        await service.mark_run_dispatched(run.id, queue_result.mode, queue_result.detail)
    else:
        await service.mark_run_dispatched(run.id, queue_result.mode, queue_result.detail)
        background_tasks.add_task(service.process_run, run.id)
    return {"success": True, "data": run.model_dump(mode="json")}


@router.get("")
async def list_qa_runs(
    repository: FileRunRepository = Depends(get_repository),
    user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    del user
    runs = await repository.list_runs()
    return {"success": True, "data": [item.model_dump(mode="json") for item in runs]}


@router.get("/{run_id}")
async def get_qa_run(
    run_id: str,
    repository: FileRunRepository = Depends(get_repository),
    user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    del user
    run = await repository.get_run(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")
    return {"success": True, "data": run.model_dump(mode="json")}


@router.get("/{run_id}/graph")
async def get_qa_run_graph(
    run_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    service: QARunService = Depends(get_run_service),
) -> dict:
    del user
    try:
        graph = await service.get_graph(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.") from exc
    return {"success": True, "data": graph}


@router.get("/{run_id}/playback")
async def get_qa_run_playback(
    run_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    service: QARunService = Depends(get_run_service),
) -> dict:
    del user
    try:
        playback = await service.get_playback(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.") from exc
    return {"success": True, "data": playback}


@router.get("/{run_id}/report")
async def get_qa_run_report(
    run_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    service: QARunService = Depends(get_run_service),
) -> dict:
    del user
    try:
        report = await service.get_report(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.") from exc
    return {"success": True, "data": report}


@router.get("/{run_id}/failure-explainer")
async def get_failure_explainer(
    run_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    service: QARunService = Depends(get_run_service),
) -> dict:
    del user
    try:
        explanation = await service.get_failure_explainer(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.") from exc
    return {"success": True, "data": explanation.model_dump(mode='json') if explanation else None}


@router.get("/{run_id}/collaboration")
async def get_collaboration(
    run_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    service: QARunService = Depends(get_run_service),
) -> dict:
    del user
    try:
        collaboration = await service.get_collaboration(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.") from exc
    return {"success": True, "data": [item.model_dump(mode='json') for item in collaboration]}


@router.post("/{run_id}/retry")
async def retry_qa_run(
    run_id: str,
    request: RetryRequest,
    user: AuthenticatedUser = Depends(require_role("admin", "operator")),
    service: QARunService = Depends(get_run_service),
    queue_service: JobQueueService = Depends(get_job_queue_service),
) -> dict:
    try:
        run = await service.retry_run(run_id, request, user, queue_service)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.") from exc
    return {"success": True, "data": run.model_dump(mode="json")}


@router.post("/{run_id}/approve")
async def approve_qa_run(
    run_id: str,
    request: ApprovalDecisionRequest,
    user: AuthenticatedUser = Depends(require_role("admin")),
    service: QARunService = Depends(get_run_service),
) -> dict:
    try:
        decision = await service.decide_approval(run_id, request, user)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.") from exc
    return {"success": True, "data": decision.model_dump(mode="json")}
