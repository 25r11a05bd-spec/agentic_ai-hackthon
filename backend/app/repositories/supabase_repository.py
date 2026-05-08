from __future__ import annotations

from typing import Any
from uuid import uuid4

from supabase import Client

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


class SupabaseRunRepository:
    def __init__(self, client: Client) -> None:
        self._client = client

    # ------------------------------------------------------------------ #
    # Runs
    # ------------------------------------------------------------------ #

    async def create_run(
        self,
        request: QARunCreate,
        created_by: str,
        project_file_name: str,
        workflow_file_name: str,
        attachments: list[RunArtifact],
    ) -> QARunRecord:
        timestamp = utcnow().isoformat()
        run_data = {
            "id": f"run_{uuid4().hex[:10]}",
            "task": request.task,
            "validation_mode": request.validation_mode,
            "status": "queued",
            "approval_status": "not_required",
            "current_agent": "planner",
            "risk_level": "low",
            "created_by": created_by,
            "created_at": timestamp,
            "updated_at": timestamp,
            "project_file_name": project_file_name,
            "workflow_file_name": workflow_file_name,
            "scores": QualityScores().model_dump(),
            "latest_state": {"attachments": [a.model_dump() for a in attachments]},
            "retry_enabled": getattr(request, "retry_enabled", True),
            "notifications_enabled": getattr(request, "notifications_enabled", True),
            "retries_used": 0,
            "max_retries": getattr(request, "max_retries", 3),
        }
        self._client.table("qa_runs").insert(run_data).execute()
        return QARunRecord.model_validate(run_data)

    async def list_runs(self) -> list[QARunRecord]:
        response = self._client.table("qa_runs").select("*").order("created_at", desc=True).execute()
        return [QARunRecord.model_validate(item) for item in response.data]

    async def get_run(self, run_id: str) -> QARunDetail | None:
        try:
            print(f"🔍 [Supabase] Fetching run: {run_id}")
            resp = self._client.table("qa_runs").select("*").eq("id", run_id).maybe_single().execute()
            
            if not resp.data:
                print(f"⚠️ [Supabase] Run {run_id} not found in 'qa_runs' table.")
                return None

            print(f"✅ [Supabase] Run found. Fetching related data...")
            run = QARunRecord.model_validate(resp.data)

            # Robust retrieval with empty list fallbacks
            events = self._client.table("playback_events").select("*").eq("run_id", run_id).order("sequence").execute().data or []
            snapshots = self._client.table("snapshots").select("*").eq("run_id", run_id).execute().data or []
            findings = self._client.table("findings").select("*").eq("run_id", run_id).execute().data or []
            collab = self._client.table("collaboration").select("*").eq("run_id", run_id).execute().data or []
            repair = self._client.table("repair_strategies").select("*").eq("run_id", run_id).execute().data or []
            
            failure_resp = self._client.table("failure_explanations").select("*").eq("run_id", run_id).maybe_single().execute()
            failure_data = failure_resp.data if failure_resp else None

            print(f"📊 [Supabase] Data loaded: {len(findings)} findings, {len(events)} events.")

            return QARunDetail(
                **run.model_dump(),
                findings=[WorkflowFinding.model_validate(e) for e in findings],
                playback=[PlaybackEvent.model_validate(e) for e in events],
                snapshots=[PlaybackSnapshot.model_validate(e) for e in snapshots],
                failure_explanation=FailureExplanation.model_validate(failure_data) if failure_data else None,
                repair_strategies=[RepairStrategy.model_validate(e) for e in repair],
                collaboration=[CollaborationStep.model_validate(e) for e in collab],
                report_markdown=run.latest_state.get("report_markdown"),
                report_pdf_path=run.latest_state.get("report_pdf_path"),
            )
        except Exception as e:
            print(f"❌ [Supabase] GetRun Critical Error: {type(e).__name__}: {e}")
            return None

    async def update_run(self, run_id: str, **updates: Any) -> QARunRecord:
        updates["updated_at"] = utcnow().isoformat()

        # Ensure all Pydantic models in updates are converted to JSON-serializable dicts
        for key, value in updates.items():
            if hasattr(value, "model_dump"):
                updates[key] = value.model_dump(mode="json")

        if "latest_state" in updates:
            current = self._client.table("qa_runs").select("latest_state").eq("id", run_id).maybe_single().execute()
            existing = (current.data or {}).get("latest_state") or {}
            # Merge if it's a dict
            if isinstance(updates["latest_state"], dict):
                updates["latest_state"] = {**existing, **updates["latest_state"]}

        response = self._client.table("qa_runs").update(updates).eq("id", run_id).execute()
        return QARunRecord.model_validate(response.data[0])

    # ------------------------------------------------------------------ #
    # Events & Snapshots
    # ------------------------------------------------------------------ #

    async def add_event(self, event: PlaybackEvent) -> PlaybackEvent:
        # Auto-assign sequence
        count_resp = self._client.table("playback_events").select("id", count="exact").eq("run_id", event.run_id).execute()
        event.sequence = (count_resp.count or 0) + 1
        self._client.table("playback_events").insert(event.model_dump(mode="json")).execute()
        return event

    async def list_events_since(self, run_id: str, sequence: int) -> list[PlaybackEvent]:
        response = self._client.table("playback_events").select("*").eq("run_id", run_id).gt("sequence", sequence).execute()
        return [PlaybackEvent.model_validate(item) for item in response.data]

    async def save_snapshot(self, snapshot: PlaybackSnapshot) -> None:
        self._client.table("snapshots").insert(snapshot.model_dump(mode="json")).execute()

    # ------------------------------------------------------------------ #
    # Findings, Failures, Repairs, Collaboration
    # ------------------------------------------------------------------ #

    async def replace_findings(self, run_id: str, findings: list[WorkflowFinding]) -> None:
        self._client.table("findings").delete().eq("run_id", run_id).execute()
        if findings:
            rows = [{"run_id": run_id, **f.model_dump(mode="json")} for f in findings]
            self._client.table("findings").insert(rows).execute()

    async def save_failure_explanation(self, run_id: str, explanation: FailureExplanation) -> None:
        self._client.table("failure_explanations").upsert(
            {"run_id": run_id, **explanation.model_dump(mode="json")}
        ).execute()

    async def save_repair_strategies(self, run_id: str, strategies: list[RepairStrategy]) -> None:
        self._client.table("repair_strategies").delete().eq("run_id", run_id).execute()
        if strategies:
            rows = [{"run_id": run_id, **s.model_dump(mode="json")} for s in strategies]
            self._client.table("repair_strategies").insert(rows).execute()

    async def save_collaboration(self, run_id: str, steps: list[CollaborationStep]) -> None:
        self._client.table("collaboration").delete().eq("run_id", run_id).execute()
        if steps:
            rows = [{"run_id": run_id, **s.model_dump(mode="json")} for s in steps]
            self._client.table("collaboration").insert(rows).execute()

    # ------------------------------------------------------------------ #
    # Report
    # ------------------------------------------------------------------ #

    async def save_report(self, run_id: str, markdown: str, pdf_path: str | None) -> None:
        current = self._client.table("qa_runs").select("latest_state").eq("id", run_id).maybe_single().execute()
        existing = (current.data or {}).get("latest_state") or {}
        self._client.table("qa_runs").update({
            "latest_state": {**existing, "report_markdown": markdown, "report_pdf_path": pdf_path},
            "updated_at": utcnow().isoformat(),
        }).eq("id", run_id).execute()

    # ------------------------------------------------------------------ #
    # Approvals
    # ------------------------------------------------------------------ #

    async def save_approval(self, approval: ApprovalRecord) -> None:
        self._client.table("approvals").upsert(approval.model_dump(mode="json")).execute()

    async def get_approval(self, run_id: str) -> ApprovalRecord | None:
        resp = self._client.table("approvals").select("*").eq("run_id", run_id).maybe_single().execute()
        return ApprovalRecord.model_validate(resp.data) if resp.data else None

    async def list_pending_approvals(self) -> list[ApprovalRecord]:
        resp = self._client.table("approvals").select("*").eq("status", "pending").execute()
        return [ApprovalRecord.model_validate(item) for item in resp.data]

    # ------------------------------------------------------------------ #
    # Notifications
    # ------------------------------------------------------------------ #

    async def add_notification(self, log: NotificationLog) -> None:
        self._client.table("notification_logs").insert(log.model_dump(mode="json")).execute()

    async def list_notifications(self) -> list[NotificationLog]:
        resp = self._client.table("notification_logs").select("*").order("created_at", desc=True).execute()
        return [NotificationLog.model_validate(item) for item in resp.data]

    # ------------------------------------------------------------------ #
    # Metrics
    # ------------------------------------------------------------------ #

    async def get_metrics(self) -> MetricsOverview:
        runs = await self.list_runs()
        if not runs:
            return MetricsOverview(total_runs=0, success_rate=0.0, average_retries=0.0, approval_queue=0)

        successes = [r for r in runs if r.status == "success"]
        pending = [r for r in runs if r.approval_status == "pending"]
        trend = [
            {"runId": r.id, "reliability": r.scores.reliability, "overall": r.scores.overall}
            for r in runs[:10]
        ]
        risk_buckets = {"low": 0, "medium": 0, "high": 0}
        for r in runs:
            score = r.scores.hallucination_risk
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
            average_retries=round(sum(r.retries_used for r in runs) / len(runs), 2),
            approval_queue=len(pending),
            reliability_trend=trend,
            risk_breakdown=[{"name": k, "value": v} for k, v in risk_buckets.items()],
            agent_contribution=contribution,
        )
