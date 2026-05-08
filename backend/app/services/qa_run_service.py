from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.api.websocket.manager import PlaybackWebSocketManager
from app.core.config import Settings
from app.core.security import AuthenticatedUser
from app.memory.chroma_service import ChromaMemoryService
from app.repositories.run_repository import FileRunRepository
from app.schemas.qa_run import (
    ApprovalDecision,
    ApprovalDecisionRequest,
    ApprovalRecord,
    CollaborationStep,
    FailureExplanation,
    PlaybackEvent,
    PlaybackSnapshot,
    QARunCreate,
    QARunDetail,
    QARunRecord,
    RepairStrategy,
    RetryRequest,
    RunArtifact,
    WorkflowFinding,
)
from app.services.memory_runtime import rank_repair_strategies, retrieve_memory, save_failure_patterns, store_memory
from app.services.job_queue import JobQueueService
from app.services.notification_service import NotificationService
from app.services.reporting import generate_markdown_report, generate_pdf_report
from app.tools.api_validation import inspect_response, retry_request
from app.tools.python_analysis import analyze_python_code, generate_quality_report
from app.tools.workflow_validation import detect_hallucinations, inspect_workflow, normalize_workflow, validate_json
from app.utils.time import utcnow
from app.workflows.runtime import EXECUTION_NODE_IDS, build_execution_graph


class QARunService:
    def __init__(
        self,
        repository: FileRunRepository,
        memory_service: ChromaMemoryService,
        notification_service: NotificationService,
        websocket_manager: PlaybackWebSocketManager,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._memory_service = memory_service
        self._notification_service = notification_service
        self._websocket_manager = websocket_manager
        self._settings = settings
        self._processing: dict[str, asyncio.Task[None]] = {}

    async def create_run(
        self,
        request: QARunCreate,
        created_by: AuthenticatedUser,
        project_file_name: str,
        project_bytes: bytes,
        workflow_file_name: str,
        workflow_bytes: bytes,
        attachments: list[tuple[str, bytes]] | None = None,
    ) -> QARunRecord:
        run_dir = self._settings.data_dir / "uploads" / f"run_{uuid4().hex[:8]}"
        run_dir.mkdir(parents=True, exist_ok=True)

        project_path = run_dir / project_file_name
        workflow_path = run_dir / workflow_file_name
        project_path.write_bytes(project_bytes)
        workflow_path.write_bytes(workflow_bytes)

        stored_attachments: list[RunArtifact] = []
        for attachment_name, payload in attachments or []:
            attachment_path = run_dir / attachment_name
            attachment_path.write_bytes(payload)
            stored_attachments.append(
                RunArtifact(
                    name=attachment_name,
                    file_type=attachment_path.suffix.lstrip(".") or "bin",
                    path=str(attachment_path),
                )
            )

        run = await self._repository.create_run(
            request=request,
            created_by=created_by.user_id,
            project_file_name=project_file_name,
            workflow_file_name=workflow_file_name,
            attachments=stored_attachments,
        )
        await self._repository.update_run(
            run.id,
            latest_state={
                "upload_dir": str(run_dir),
                "project_path": str(project_path),
                "workflow_path": str(workflow_path),
                "execution_graph": self._serialize_graph(),
                "node_status_map": {node_id: "pending" for node_id in EXECUTION_NODE_IDS},
            },
        )
        return await self._repository.get_run(run.id) or run

    def schedule_run(self, run_id: str) -> None:
        if run_id in self._processing and not self._processing[run_id].done():
            return
        self._processing[run_id] = asyncio.create_task(self.process_run(run_id))

    async def mark_run_dispatched(self, run_id: str, queue_mode: str, detail: str) -> None:
        await self._repository.update_run(
            run_id,
            status="queued",
            latest_state={
                "queue_mode": queue_mode,
                "queue_detail": detail,
            },
        )
        await self._emit(
            run_id,
            "agent_log",
            "queue_dispatcher",
            detail,
            "queued",
            payload={"queue_mode": queue_mode},
        )

    async def process_run(self, run_id: str) -> None:
        run = await self._require_run(run_id)
        await self._repository.update_run(run_id, status="running", current_agent="ingest")
        await self._emit(run_id, "run_started", "ingest", "Run accepted for analysis", "running")

        collaboration: list[CollaborationStep] = []
        node_status_map = dict(run.latest_state.get("node_status_map", {}))

        await self._transition_node(run_id, "ingest", node_status_map)
        project_path = Path(run.latest_state["project_path"])
        workflow_path = Path(run.latest_state["workflow_path"])
        source = project_path.read_text(encoding="utf-8")
        raw_workflow = validate_json(workflow_path.read_text(encoding="utf-8"))
        collaboration.append(self._collaboration_step(run_id, "ingest", ["file_loader"], "Stored uploaded artifacts."))

        await self._transition_node(run_id, "planner", node_status_map)
        python_analysis = analyze_python_code(source)
        workflow = normalize_workflow(raw_workflow)
        await self._emit(
            run_id,
            "agent_log",
            "planner",
            "Normalized workflow and extracted Python symbols",
            "success",
            payload={"ast_summary": python_analysis.ast_summary, "node_count": len(workflow.nodes)},
        )
        collaboration.append(
            self._collaboration_step(
                run_id,
                "planner",
                ["analyze_python_code", "normalize_workflow"],
                python_analysis.ast_summary,
                confidence=0.84,
            )
        )

        await self._transition_node(run_id, "tool_router", node_status_map)
        selected_tools = ["inspect_workflow", "detect_hallucinations"]
        if workflow.api_calls:
            selected_tools.append("validate_api")
        await self._emit(
            run_id,
            "agent_log",
            "tool_router",
            "Selected validation and probe tools",
            "success",
            payload={"tools": selected_tools, "api_calls": workflow.api_calls},
        )
        collaboration.append(
            self._collaboration_step(
                run_id,
                "tool_router",
                selected_tools,
                f"Selected {len(selected_tools)} tools for this run.",
                confidence=0.79,
                dependencies=["planner"],
            )
        )

        await self._transition_node(run_id, "executor", node_status_map)
        findings = inspect_workflow(raw_workflow, workflow)
        findings.extend(
            detect_hallucinations(
                workflow=workflow,
                python_functions=python_analysis.functions,
                python_api_calls=python_analysis.api_calls,
            )
        )
        api_results: list[dict[str, Any]] = []
        for url in workflow.api_calls:
            result = await retry_request(url)
            api_results.append(result)
            findings.extend(inspect_response(result))

        for finding in findings:
            await self._emit(
                run_id,
                "finding_created",
                "executor",
                finding.title,
                finding.severity,
                payload=finding.model_dump(mode="json"),
            )

        collaboration.append(
            self._collaboration_step(
                run_id,
                "executor",
                selected_tools,
                f"Generated {len(findings)} findings from workflow inspection and probes.",
                risk_level="medium" if findings else "low",
                confidence=0.77,
                dependencies=["tool_router"],
            )
        )

        await self._repository.replace_findings(run_id, findings)
        await self._transition_node(run_id, "validator", node_status_map)
        scores = self._score_with_context(findings)
        risk_level = self._risk_level(scores.hallucination_risk, scores.validation)
        quality_summary = generate_quality_report(run_id, "running", scores, findings)
        validation_passed = scores.validation >= self._settings.approval_validation_threshold and scores.hallucination_risk <= self._settings.approval_hallucination_threshold
        await self._repository.update_run(
            run_id,
            scores=scores,
            risk_level=risk_level,
            latest_state={
                "python_analysis": python_analysis.model_dump(mode="json"),
                "canonical_workflow": workflow.model_dump(mode="json"),
                "api_results": api_results,
                "quality_summary": quality_summary.model_dump(mode="json"),
                "node_status_map": node_status_map,
            },
        )
        collaboration.append(
            self._collaboration_step(
                run_id,
                "validator",
                ["score_workflow_quality"],
                f"Validation score {scores.validation}, hallucination risk {scores.hallucination_risk}.",
                risk_level=risk_level,
                confidence=0.81,
                dependencies=["executor"],
            )
        )

        failure_explanation: FailureExplanation | None = None
        repair_strategies: list[RepairStrategy] = []
        approval_needed = False
        status = "success"

        await self._transition_node(run_id, "failure_explainer", node_status_map)
        if findings:
            failure_explanation = self._build_failure_explanation(findings, python_analysis.ast_summary, api_results, run.retries_used)
            await self._repository.save_failure_explanation(run_id, failure_explanation)
            await self._emit(
                run_id,
                "failure_explained",
                "failure_explainer",
                failure_explanation.root_cause,
                "success",
                payload=failure_explanation.model_dump(mode="json"),
            )
            collaboration.append(
                self._collaboration_step(
                    run_id,
                    "failure_explainer",
                    ["generate_failure_explanation"],
                    failure_explanation.root_cause,
                    risk_level=risk_level,
                    confidence=0.76,
                    dependencies=["validator"],
                )
            )

        await self._transition_node(run_id, "reflection", node_status_map)
        if not validation_passed and run.retry_enabled:
            await self._emit(
                run_id,
                "agent_log",
                "reflection",
                "Validation failed, preparing safe self-heal strategies",
                "running",
            )
            collaboration.append(
                self._collaboration_step(
                    run_id,
                    "reflection",
                    ["retrieve_memory", "rank_repair_strategies"],
                    "Prepared a reflection plan for bounded retries.",
                    risk_level=risk_level,
                    confidence=0.7,
                    dependencies=["failure_explainer"],
                )
            )

        await self._transition_node(run_id, "self_heal_router", node_status_map)
        if not validation_passed:
            memory_hits = await retrieve_memory(
                self._memory_service,
                "failure_patterns",
                failure_explanation.root_cause if failure_explanation else "unknown failure",
                limit=self._settings.self_heal_max_strategies,
            )
            repair_strategies = rank_repair_strategies(
                candidates=self._build_repair_strategies(findings, workflow.api_calls),
                retrieved_memories=memory_hits,
                min_similarity=self._settings.self_heal_min_similarity,
                max_strategies=self._settings.self_heal_max_strategies,
            )
            await self._repository.save_repair_strategies(run_id, repair_strategies)
            for strategy in repair_strategies:
                await self._emit(
                    run_id,
                    "self_heal_suggested",
                    "self_heal_router",
                    strategy.title,
                    "success",
                    payload=strategy.model_dump(mode="json"),
                )
            approval_needed = bool(repair_strategies)

        await self._transition_node(run_id, "retry_or_replan", node_status_map)
        if not validation_passed and run.retry_enabled and run.retries_used < run.max_retries:
            retries_used = run.retries_used + 1
            selected = repair_strategies[0] if repair_strategies else None
            if selected:
                selected.selected = True
                approval_needed = True
                await self._repository.save_repair_strategies(run_id, repair_strategies)
                await self._emit(
                    run_id,
                    "self_heal_applied",
                    "retry_or_replan",
                    selected.title,
                    "running",
                    payload=selected.model_dump(mode="json"),
                )
            await self._emit(
                run_id,
                "retry_scheduled",
                "retry_or_replan",
                f"Retry #{retries_used} scheduled with safe execution plan changes",
                "running",
            )
            await self._repository.update_run(
                run_id,
                retries_used=retries_used,
                latest_state={
                    "self_heal_changed_path": bool(selected),
                    "selected_repair_strategy": selected.model_dump(mode="json") if selected else None,
                },
            )
            validation_passed = bool(selected) and all(item.severity not in {"critical", "high"} for item in findings)

        await self._transition_node(run_id, "approval_gate", node_status_map)
        current_run = await self._require_run(run_id)
        if (
            scores.validation < self._settings.approval_validation_threshold
            or scores.hallucination_risk > self._settings.approval_hallucination_threshold
            or current_run.retries_used >= current_run.max_retries
            or approval_needed
        ):
            status = "approval_required"
            approval = ApprovalRecord(
                run_id=run_id,
                status="pending",
                recommended_action="Review self-heal plan and failure explanation before finalization.",
                rationale=self._build_approval_rationale(scores, repair_strategies),
                updated_at=utcnow(),
            )
            await self._repository.save_approval(approval)
            await self._emit(
                run_id,
                "approval_required",
                "approval_gate",
                approval.rationale,
                "pending",
                payload=approval.model_dump(mode="json"),
            )
        elif not validation_passed:
            status = "failed"

        await self._transition_node(run_id, "memory_writer", node_status_map)
        await self._write_memories(run_id, workflow, findings, failure_explanation, repair_strategies)
        await self._emit(run_id, "memory_saved", "memory_writer", "Run memories persisted", "success")
        collaboration.append(
            self._collaboration_step(
                run_id,
                "memory_writer",
                ["store_memory"],
                "Stored workflow and failure memory for later self-heal retrieval.",
                confidence=0.73,
                dependencies=["approval_gate"],
            )
        )

        await self._transition_node(run_id, "notifier", node_status_map)
        if run.notifications_enabled:
            message = f"QA run {run_id} is now {status} with score {scores.overall}/100."
            log = await self._notification_service.send_whatsapp(run_id, message)
            await self._repository.add_notification(log)
            await self._emit(
                run_id,
                "notification_sent",
                "notifier",
                "Dispatching run outcome notification",
                log.status,
                payload=log.model_dump(mode="json"),
            )
            collaboration.append(
                self._collaboration_step(
                    run_id,
                    "notifier",
                    ["send_whatsapp"],
                    f"Sent {log.channel} notification with status {log.status}.",
                    confidence=0.9,
                    dependencies=["memory_writer"],
                )
            )

        await self._transition_node(run_id, "finalizer", node_status_map)
        detail = await self._require_run(run_id)
        refreshed_summary = generate_quality_report(run_id, status, scores, findings)
        markdown = generate_markdown_report(detail, refreshed_summary, failure_explanation)
        pdf_path = generate_pdf_report(markdown, self._settings.data_dir / "reports" / f"{run_id}.pdf")
        await self._repository.save_report(run_id, markdown, pdf_path)
        await self._repository.save_collaboration(run_id, collaboration)
        node_status_map["finalizer"] = "completed"
        await self._repository.update_run(
            run_id,
            status=status,
            approval_status="pending" if status == "approval_required" else "not_required",
            current_agent="finalizer",
            risk_level=risk_level,
            latest_state={"node_status_map": node_status_map},
        )
        await self._emit(
            run_id,
            "run_completed",
            "finalizer",
            f"Run finished with status {status}",
            status,
            payload={"scores": scores.model_dump(mode="json"), "risk_level": risk_level},
        )

    async def retry_run(
        self,
        run_id: str,
        request: RetryRequest,
        user: AuthenticatedUser,
        queue_service: JobQueueService,
    ) -> QARunDetail:
        run = await self._require_run(run_id)
        await self._repository.update_run(
            run_id,
            status="queued",
            current_agent="planner",
            latest_state={"manual_retry_reason": request.reason, "retried_by": user.user_id},
        )
        await self._emit(run_id, "retry_scheduled", "operator", request.reason, "queued")
        queue_result = await queue_service.enqueue_run(run_id)
        if queue_result.dispatched:
            await self.mark_run_dispatched(run_id, queue_result.mode, queue_result.detail)
        else:
            await self.mark_run_dispatched(run_id, queue_result.mode, queue_result.detail)
            self.schedule_run(run_id)
        return await self._require_run(run_id)

    async def decide_approval(
        self,
        run_id: str,
        request: ApprovalDecisionRequest,
        user: AuthenticatedUser,
    ) -> ApprovalDecision:
        decision = ApprovalDecision(
            run_id=run_id,
            decision=request.decision,
            rationale=request.rationale,
            decided_by=user.user_id,
            decided_at=utcnow(),
        )
        approval_status = "approved" if request.decision == "approved" else "rejected"
        new_status = "success" if request.decision == "approved" else "failed"
        await self._repository.save_approval(
            ApprovalRecord(
                run_id=run_id,
                status=approval_status,
                recommended_action="Decision recorded.",
                rationale=request.rationale,
                updated_at=decision.decided_at,
                decided_by=user.user_id,
            )
        )
        await self._repository.update_run(run_id, approval_status=approval_status, status=new_status)
        await self._emit(
            run_id,
            "agent_log",
            "approval_gate",
            f"Approval decision recorded: {request.decision}",
            approval_status,
            payload=decision.model_dump(mode="json"),
        )
        return decision

    async def get_graph(self, run_id: str) -> dict[str, Any]:
        run = await self._require_run(run_id)
        graph = run.latest_state.get("execution_graph") or self._serialize_graph()
        status_map = run.latest_state.get("node_status_map", {})
        for node in graph["nodes"]:
            node["status"] = status_map.get(node["id"], "pending")
        return graph

    async def get_playback(self, run_id: str) -> dict[str, Any]:
        run = await self._require_run(run_id)
        return {
            "events": [item.model_dump(mode="json") for item in run.playback],
            "snapshots": [item.model_dump(mode="json") for item in run.snapshots],
        }

    async def get_report(self, run_id: str) -> dict[str, Any]:
        run = await self._require_run(run_id)
        return {
            "markdown": run.report_markdown,
            "pdf_path": run.report_pdf_path,
            "quality_summary": run.latest_state.get("quality_summary"),
        }

    async def get_failure_explainer(self, run_id: str) -> FailureExplanation | None:
        run = await self._require_run(run_id)
        return run.failure_explanation

    async def get_collaboration(self, run_id: str) -> list[CollaborationStep]:
        run = await self._require_run(run_id)
        return run.collaboration

    async def _require_run(self, run_id: str) -> QARunDetail:
        run = await self._repository.get_run(run_id)
        if not run:
            raise KeyError(run_id)
        return run

    async def _emit(
        self,
        run_id: str,
        event_type: str,
        agent: str,
        step: str,
        status: str,
        tool: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> PlaybackEvent:
        event = PlaybackEvent(
            run_id=run_id,
            event_type=event_type,
            agent=agent,
            step=step,
            status=status,
            tool=tool,
            payload=payload or {},
            timestamp=utcnow(),
        )
        saved = await self._repository.add_event(event)
        await self._websocket_manager.broadcast(run_id, saved.model_dump(mode="json"))
        return saved

    async def _transition_node(self, run_id: str, node_id: str, status_map: dict[str, str]) -> None:
        for existing_node in status_map:
            if status_map[existing_node] == "running":
                status_map[existing_node] = "completed"
        status_map[node_id] = "running"
        snapshot = PlaybackSnapshot(
            run_id=run_id,
            current_node=node_id,
            status_map=status_map.copy(),
            created_at=utcnow(),
        )
        await self._repository.save_snapshot(snapshot)
        await self._repository.update_run(run_id, current_agent=node_id, latest_state={"node_status_map": status_map})
        await self._emit(
            run_id,
            "node_state_changed",
            node_id,
            f"Transitioned to {node_id}",
            "running",
            payload={"current_node": node_id, "status_map": status_map},
        )

    def _collaboration_step(
        self,
        run_id: str,
        agent: str,
        tools_used: list[str],
        summary: str,
        risk_level: str = "low",
        confidence: float = 0.8,
        dependencies: list[str] | None = None,
    ) -> CollaborationStep:
        timestamp = utcnow()
        return CollaborationStep(
            run_id=run_id,
            agent=agent,
            started_at=timestamp,
            completed_at=timestamp,
            tools_used=tools_used,
            handoff_summary=summary,
            risk_level=risk_level,
            confidence=confidence,
            dependencies=dependencies or [],
        )

    def _serialize_graph(self) -> dict[str, Any]:
        nodes, edges = build_execution_graph()
        return {
            "nodes": [node.model_dump(mode="json") for node in nodes],
            "edges": [edge.model_dump(mode="json") for edge in edges],
        }

    def _score_with_context(self, findings: list[WorkflowFinding]):
        from app.tools.workflow_validation import score_workflow_quality

        return score_workflow_quality(findings)

    def _risk_level(self, hallucination_risk: int, validation_score: int) -> str:
        if hallucination_risk > 50 or validation_score < 70:
            return "high"
        if hallucination_risk > 20 or validation_score < 85:
            return "medium"
        return "low"

    def _build_failure_explanation(
        self,
        findings: list[WorkflowFinding],
        ast_summary: str,
        api_results: list[dict[str, Any]],
        retries_used: int,
    ) -> FailureExplanation:
        highest = max(findings, key=lambda item: {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}[item.severity])
        evidence = [ast_summary]
        evidence.extend(highest.evidence)
        evidence.extend(
            f"{result.get('url', 'unknown')} -> {result.get('status_code', result.get('error', 'n/a'))}"
            for result in api_results
        )
        return FailureExplanation(
            root_cause=highest.title,
            evidence=evidence[:8],
            affected_nodes=highest.affected_nodes,
            user_impact="Autonomous validation could not complete cleanly and may require operator review.",
            why_previous_attempt_failed=f"The current run has consumed {retries_used} retries before stabilization.",
            recommended_fix=highest.recommendation,
        )

    def _build_repair_strategies(self, findings: list[WorkflowFinding], api_calls: list[str]) -> list[RepairStrategy]:
        strategies: list[RepairStrategy] = []
        categories = {finding.category for finding in findings}
        if "api_validation" in categories or api_calls:
            strategies.append(
                RepairStrategy(
                    title="Fallback API Probe",
                    strategy_type="endpoint_fallback",
                    rationale="Use a safer health-check probe or alternate provider before final failure.",
                    steps=["Switch to HEAD/GET probe", "Lower timeout", "Use alternate provider if configured"],
                    safety_score=0.95,
                    evidence=api_calls,
                )
            )
        if "validation" in categories:
            strategies.append(
                RepairStrategy(
                    title="Inject Validation Layer",
                    strategy_type="validator_injection",
                    rationale="Insert a generated validator stage into the execution plan without mutating source files.",
                    steps=["Add schema guard", "Re-run validation stage", "Mark path as auto-fixed"],
                    safety_score=0.98,
                )
            )
        if "resilience" in categories:
            strategies.append(
                RepairStrategy(
                    title="Adjust Retry Policy",
                    strategy_type="retry_policy_adjustment",
                    rationale="The workflow lacks explicit backoff or safe retry metadata.",
                    steps=["Set max retries", "Add backoff", "Retry the affected node only"],
                    safety_score=0.9,
                )
            )
        if "hallucination" in categories:
            strategies.append(
                RepairStrategy(
                    title="Planner Replan",
                    strategy_type="planner_replan",
                    rationale="Ungrounded workflow claims require a safer, validated execution plan.",
                    steps=["Remove unsupported node claims", "Re-order tools", "Re-run validator with grounded schema"],
                    safety_score=0.75,
                )
            )
        if not strategies:
            strategies.append(
                RepairStrategy(
                    title="Timeout and Backoff Tuning",
                    strategy_type="timeout_backoff_change",
                    rationale="Apply conservative runtime tuning when the failure pattern is ambiguous.",
                    steps=["Increase timeout", "Add backoff", "Re-run only read-safe operations"],
                    safety_score=0.88,
                )
            )
        return strategies

    def _build_approval_rationale(self, scores, repair_strategies: list[RepairStrategy]) -> str:
        reasons = []
        if scores.validation < self._settings.approval_validation_threshold:
            reasons.append(f"validation score {scores.validation} < {self._settings.approval_validation_threshold}")
        if scores.hallucination_risk > self._settings.approval_hallucination_threshold:
            reasons.append(
                f"hallucination risk {scores.hallucination_risk} > {self._settings.approval_hallucination_threshold}"
            )
        if repair_strategies:
            reasons.append("self-heal changed the interpreted execution path")
        return "; ".join(reasons) or "Manual review required by policy."

    async def _write_memories(
        self,
        run_id: str,
        workflow,
        findings: list[WorkflowFinding],
        explanation: FailureExplanation | None,
        repair_strategies: list[RepairStrategy],
    ) -> None:
        await store_memory(
            self._memory_service,
            "workflow_embeddings",
            f"{run_id}_workflow",
            json.dumps(workflow.model_dump(mode="json")),
            {"run_id": run_id, "node_count": len(workflow.nodes)},
        )
        await save_failure_patterns(self._memory_service, run_id, findings, explanation)
        for strategy in repair_strategies:
            await store_memory(
                self._memory_service,
                "repair_strategy_memories",
                f"{run_id}_{strategy.id}",
                strategy.title,
                {
                    "run_id": run_id,
                    "strategy_type": strategy.strategy_type,
                    "success_rate": strategy.prior_success_rate or 0.75,
                },
            )
