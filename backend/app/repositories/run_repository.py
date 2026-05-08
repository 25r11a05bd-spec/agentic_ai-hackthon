from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.schemas.qa_run import (
    ApprovalRecord,
    CollaborationStep,
    FailureExplanation,
    MetricsOverview,
    NotificationLog,
    PlaybackEvent,
    PlaybackSnapshot,
    QARunCreate,
    QARunDetail,
    QARunRecord,
    QualityScores,
    RepairStrategy,
    RunArtifact,
    WorkflowFinding,
)
from app.utils.time import utcnow


class FileRunRepository:
    def __init__(self, root: Path) -> None:
        self._lock = asyncio.Lock()
        self._state_dir = root / "state"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._state_dir / "repository.json"
        if not self._db_path.exists():
            self._write(
                {
                    "runs": {},
                    "events": {},
                    "snapshots": {},
                    "findings": {},
                    "failure_explanations": {},
                    "repair_strategies": {},
                    "collaboration": {},
                    "approvals": {},
                    "notifications": [],
                }
            )

    def _read(self) -> dict[str, Any]:
        return json.loads(self._db_path.read_text(encoding="utf-8"))

    def _write(self, payload: dict[str, Any]) -> None:
        self._db_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    async def create_run(
        self,
        request: QARunCreate,
        created_by: str,
        project_file_name: str,
        workflow_file_name: str,
        attachments: list[RunArtifact],
    ) -> QARunRecord:
        async with self._lock:
            db = self._read()
            timestamp = utcnow()
            run = QARunRecord(
                id=f"run_{uuid4().hex[:10]}",
                task=request.task,
                validation_mode=request.validation_mode,
                status="queued",
                approval_status="not_required",
                retry_enabled=request.retry_enabled,
                notifications_enabled=request.notifications_enabled,
                max_retries=request.max_retries,
                created_by=created_by,
                created_at=timestamp,
                updated_at=timestamp,
                project_file_name=project_file_name,
                workflow_file_name=workflow_file_name,
                attachments=attachments,
                scores=QualityScores(),
                latest_state={},
            )
            db["runs"][run.id] = run.model_dump(mode="json")
            self._write(db)
            return run

    async def list_runs(self) -> list[QARunRecord]:
        async with self._lock:
            db = self._read()
            runs = [QARunRecord.model_validate(item) for item in db["runs"].values()]
            return sorted(runs, key=lambda item: item.created_at, reverse=True)

    async def get_run(self, run_id: str) -> QARunDetail | None:
        async with self._lock:
            db = self._read()
            item = db["runs"].get(run_id)
            if not item:
                return None
            run = QARunRecord.model_validate(item)
            return QARunDetail(
                **run.model_dump(),
                findings=[WorkflowFinding.model_validate(entry) for entry in db["findings"].get(run_id, [])],
                playback=[PlaybackEvent.model_validate(entry) for entry in db["events"].get(run_id, [])],
                snapshots=[PlaybackSnapshot.model_validate(entry) for entry in db["snapshots"].get(run_id, [])],
                failure_explanation=FailureExplanation.model_validate(db["failure_explanations"][run_id])
                if run_id in db["failure_explanations"]
                else None,
                repair_strategies=[
                    RepairStrategy.model_validate(entry) for entry in db["repair_strategies"].get(run_id, [])
                ],
                collaboration=[
                    CollaborationStep.model_validate(entry) for entry in db["collaboration"].get(run_id, [])
                ],
                report_markdown=run.latest_state.get("report_markdown"),
                report_pdf_path=run.latest_state.get("report_pdf_path"),
            )

    async def update_run(self, run_id: str, **updates: Any) -> QARunRecord:
        async with self._lock:
            db = self._read()
            current = QARunRecord.model_validate(db["runs"][run_id])
            merged_state = {**current.latest_state, **updates.pop("latest_state", {})}
            updated = current.model_copy(
                update={
                    **updates,
                    "latest_state": merged_state,
                    "updated_at": utcnow(),
                }
            )
            db["runs"][run_id] = updated.model_dump(mode="json")
            self._write(db)
            return updated

    async def add_event(self, event: PlaybackEvent) -> PlaybackEvent:
        async with self._lock:
            db = self._read()
            existing = db["events"].setdefault(event.run_id, [])
            event.sequence = len(existing) + 1
            existing.append(event.model_dump(mode="json"))
            self._write(db)
            return event

    async def list_events_since(self, run_id: str, sequence: int) -> list[PlaybackEvent]:
        async with self._lock:
            db = self._read()
            return [
                PlaybackEvent.model_validate(entry)
                for entry in db["events"].get(run_id, [])
                if entry.get("sequence", 0) > sequence
            ]

    async def save_snapshot(self, snapshot: PlaybackSnapshot) -> None:
        async with self._lock:
            db = self._read()
            db["snapshots"].setdefault(snapshot.run_id, []).append(snapshot.model_dump(mode="json"))
            self._write(db)

    async def replace_findings(self, run_id: str, findings: list[WorkflowFinding]) -> None:
        async with self._lock:
            db = self._read()
            db["findings"][run_id] = [entry.model_dump(mode="json") for entry in findings]
            self._write(db)

    async def save_failure_explanation(self, run_id: str, explanation: FailureExplanation) -> None:
        async with self._lock:
            db = self._read()
            db["failure_explanations"][run_id] = explanation.model_dump(mode="json")
            self._write(db)

    async def save_repair_strategies(self, run_id: str, strategies: list[RepairStrategy]) -> None:
        async with self._lock:
            db = self._read()
            db["repair_strategies"][run_id] = [entry.model_dump(mode="json") for entry in strategies]
            self._write(db)

    async def save_collaboration(self, run_id: str, steps: list[CollaborationStep]) -> None:
        async with self._lock:
            db = self._read()
            db["collaboration"][run_id] = [entry.model_dump(mode="json") for entry in steps]
            self._write(db)

    async def save_report(self, run_id: str, markdown: str, pdf_path: str | None) -> None:
        detail = await self.get_run(run_id)
        if not detail:
            return
        await self.update_run(
            run_id,
            latest_state={
                **detail.latest_state,
                "report_markdown": markdown,
                "report_pdf_path": pdf_path,
            },
        )

    async def save_approval(self, approval: ApprovalRecord) -> None:
        async with self._lock:
            db = self._read()
            db["approvals"][approval.run_id] = approval.model_dump(mode="json")
            self._write(db)

    async def get_approval(self, run_id: str) -> ApprovalRecord | None:
        async with self._lock:
            db = self._read()
            value = db["approvals"].get(run_id)
            return ApprovalRecord.model_validate(value) if value else None

    async def list_pending_approvals(self) -> list[ApprovalRecord]:
        async with self._lock:
            db = self._read()
            approvals = [ApprovalRecord.model_validate(item) for item in db["approvals"].values()]
            return [item for item in approvals if item.status == "pending"]

    async def add_notification(self, log: NotificationLog) -> None:
        async with self._lock:
            db = self._read()
            db["notifications"].append(log.model_dump(mode="json"))
            self._write(db)

    async def list_notifications(self) -> list[NotificationLog]:
        async with self._lock:
            db = self._read()
            return [NotificationLog.model_validate(item) for item in db["notifications"]]

    async def get_metrics(self) -> MetricsOverview:
        runs = await self.list_runs()
        if not runs:
            return MetricsOverview(total_runs=0, success_rate=0.0, average_retries=0.0, approval_queue=0)

        successes = [run for run in runs if run.status == "success"]
        pending_approvals = [run for run in runs if run.approval_status == "pending"]
        trend = [
            {"runId": run.id, "reliability": run.scores.reliability, "overall": run.scores.overall}
            for run in runs[:10]
        ]

        risk_buckets = {"low": 0, "medium": 0, "high": 0}
        for run in runs:
            score = run.scores.hallucination_risk
            if score <= 20:
                risk_buckets["low"] += 1
            elif score <= 50:
                risk_buckets["medium"] += 1
            else:
                risk_buckets["high"] += 1

        contribution = [
            {"agent": "planner", "share": 18},
            {"agent": "executor", "share": 24},
            {"agent": "validator", "share": 20},
            {"agent": "reflection", "share": 16},
            {"agent": "memory", "share": 10},
            {"agent": "notifier", "share": 12},
        ]

        return MetricsOverview(
            total_runs=len(runs),
            success_rate=round((len(successes) / len(runs)) * 100, 2),
            average_retries=round(sum(run.retries_used for run in runs) / len(runs), 2),
            approval_queue=len(pending_approvals),
            reliability_trend=trend,
            risk_breakdown=[{"name": key, "value": value} for key, value in risk_buckets.items()],
            agent_contribution=contribution,
        )

