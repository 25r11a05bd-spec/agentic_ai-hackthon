from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


Severity = Literal["info", "low", "medium", "high", "critical"]
QARunStatus = Literal["queued", "running", "approval_required", "success", "failed"]
RunStatus = QARunStatus
ApprovalStatus = Literal["not_required", "pending", "approved", "rejected"]


class WorkflowNode(BaseModel):
    id: str
    label: str
    type: str = "task"
    config: dict[str, Any] = Field(default_factory=dict)
    status: str | None = None


class WorkflowEdge(BaseModel):
    source: str
    target: str
    label: str | None = None


class CanonicalWorkflowSpec(BaseModel):
    nodes: list[WorkflowNode]
    edges: list[WorkflowEdge]
    api_calls: list[str] = Field(default_factory=list)
    validation_rules: list[str] = Field(default_factory=list)
    retry_policy: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    risk_flags: list[str] = Field(default_factory=list)


class PythonAnalysis(BaseModel):
    imports: list[str] = Field(default_factory=list)
    functions: list[str] = Field(default_factory=list)
    classes: list[str] = Field(default_factory=list)
    api_calls: list[str] = Field(default_factory=list)
    validators: list[str] = Field(default_factory=list)
    retry_patterns: list[str] = Field(default_factory=list)
    exception_handlers: list[str] = Field(default_factory=list)
    undefined_symbols: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    ast_summary: str = ""


class WorkflowFinding(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    category: str
    severity: Severity
    title: str
    description: str
    evidence: list[str] = Field(default_factory=list)
    affected_nodes: list[str] = Field(default_factory=list)
    recommendation: str


class QualityScores(BaseModel):
    reliability: int = 0
    validation: int = 0
    hallucination_risk: int = 0
    retry_health: int = 0
    overall: int = 0


class PlaybackEvent(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    run_id: str
    event_type: str
    agent: str
    step: str
    status: str
    tool: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    sequence: int = 0
    timestamp: datetime


class PlaybackSnapshot(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    run_id: str
    current_node: str
    status_map: dict[str, str] = Field(default_factory=dict)
    created_at: datetime


class CollaborationStep(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    run_id: str
    agent: str
    started_at: datetime
    completed_at: datetime | None = None
    tools_used: list[str] = Field(default_factory=list)
    handoff_summary: str = ""
    risk_level: str = "low"
    confidence: float = 0.0
    dependencies: list[str] = Field(default_factory=list)


class FailureExplanation(BaseModel):
    root_cause: str
    evidence: list[str] = Field(default_factory=list)
    affected_nodes: list[str] = Field(default_factory=list)
    user_impact: str
    why_previous_attempt_failed: str
    recommended_fix: str


class RepairStrategy(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    title: str
    strategy_type: str
    rationale: str
    steps: list[str] = Field(default_factory=list)
    memory_similarity: float = 0.0
    prior_success_rate: float = 0.0
    safety_score: float = 1.0
    selected: bool = False
    fixed_code: str | None = None
    explanation: str | None = None
    evidence: list[str] = Field(default_factory=list)


class RunArtifact(BaseModel):
    name: str
    file_type: str
    path: str


class QARunCreate(BaseModel):
    task: str = "Analyze automation workflow quality"
    validation_mode: str = "strict"
    retry_enabled: bool = True
    notifications_enabled: bool = True
    max_retries: int = 3


class QARunRecord(BaseModel):
    id: str
    task: str
    validation_mode: str
    status: RunStatus
    approval_status: ApprovalStatus
    retry_enabled: bool
    notifications_enabled: bool
    max_retries: int
    retries_used: int = 0
    current_agent: str = "planner"
    risk_level: Literal["low", "medium", "high"] = "low"
    created_by: str
    created_at: datetime
    updated_at: datetime
    project_file_name: str
    workflow_file_name: str
    attachments: list[RunArtifact] = Field(default_factory=list)
    scores: QualityScores = Field(default_factory=QualityScores)
    latest_state: dict[str, Any] = Field(default_factory=dict)


class QARunDetail(QARunRecord):
    findings: list[WorkflowFinding] = Field(default_factory=list)
    playback: list[PlaybackEvent] = Field(default_factory=list)
    snapshots: list[PlaybackSnapshot] = Field(default_factory=list)
    failure_explanation: FailureExplanation | None = None
    repair_strategies: list[RepairStrategy] = Field(default_factory=list)
    collaboration: list[CollaborationStep] = Field(default_factory=list)
    report_markdown: str | None = None
    report_pdf_path: str | None = None


class ApprovalDecisionRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    rationale: str


class ApprovalDecision(BaseModel):
    run_id: str
    decision: Literal["approved", "rejected"]
    rationale: str
    decided_by: str
    decided_at: datetime


class RetryRequest(BaseModel):
    reason: str = "Manual retry"


class ApprovalRecord(BaseModel):
    run_id: str
    status: ApprovalStatus
    recommended_action: str
    rationale: str
    updated_at: datetime
    decided_by: str | None = None


class NotificationLog(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    run_id: str
    channel: Literal["whatsapp", "sms"]
    recipient: str
    message: str
    status: str
    provider_sid: str | None = None
    created_at: datetime


class MetricsOverview(BaseModel):
    total_runs: int
    success_rate: float
    average_retries: float
    approval_queue: int
    reliability_trend: list[dict[str, Any]] = Field(default_factory=list)
    risk_breakdown: list[dict[str, Any]] = Field(default_factory=list)
    agent_contribution: list[dict[str, Any]] = Field(default_factory=list)


class QualityReportSummary(BaseModel):
    run_id: str
    status: QARunStatus
    generated_at: datetime
    summary: str
    scores: QualityScores
    finding_counts: dict[str, int] = Field(default_factory=dict)
    top_risks: list[str] = Field(default_factory=list)
