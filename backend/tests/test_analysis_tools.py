from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.core.security import AuthenticatedUser, require_role
from app.schemas.qa_run import QualityScores, RepairStrategy, WorkflowFinding
from app.services.memory_runtime import rank_repair_strategies
from app.tools.python_analysis import analyze_python_code, generate_quality_report
from app.tools.workflow_validation import detect_hallucinations, normalize_workflow, validate_schema


def test_analyze_python_code_extracts_async_functions_and_http_calls() -> None:
    source = """
import httpx

async def validate_payload():
    async with httpx.AsyncClient() as client:
        await client.get("https://example.com")

class Worker:
    pass
"""
    analysis = analyze_python_code(source)
    assert "httpx" in analysis.imports
    assert "validate_payload" in analysis.functions
    assert "Worker" in analysis.classes
    assert "get" in analysis.api_calls
    assert "validate_payload" in analysis.validators


def test_normalize_workflow_supports_steps_format() -> None:
    workflow = normalize_workflow(
        {
            "steps": [
                {"id": "fetch", "name": "Fetch", "type": "api", "endpoint": "https://example.com"},
                {"id": "validate", "name": "Validate", "type": "validator"},
            ]
        }
    )
    assert [node.id for node in workflow.nodes] == ["fetch", "validate"]
    assert workflow.edges[0].source == "fetch"
    assert workflow.validation_rules == ["Validate"]


def test_detect_hallucinations_flags_missing_function_reference() -> None:
    workflow = normalize_workflow(
        {
            "nodes": [{"id": "step_1", "label": "Fetch", "type": "task", "config": {"function": "missing_call"}}],
            "edges": [],
        }
    )
    findings = detect_hallucinations(workflow, python_functions=["real_call"], python_api_calls=[])
    assert any(item.category == "hallucination" for item in findings)
    assert any("missing python symbol" in item.title.lower() for item in findings)


def test_validate_schema_rejects_invalid_nodes_shape() -> None:
    findings = validate_schema({"nodes": "bad-shape"})
    assert any(item.category == "schema" for item in findings)


def test_generate_quality_report_summarizes_findings() -> None:
    findings = [
        WorkflowFinding(
            category="validation",
            severity="high",
            title="Missing validation layer",
            description="No validator present.",
            recommendation="Add one.",
        )
    ]
    report = generate_quality_report(
        "run_1",
        "running",
        QualityScores(overall=70, validation=60, hallucination_risk=20, retry_health=80, reliability=70),
        findings,
    )
    assert report.run_id == "run_1"
    assert report.finding_counts["high"] == 1
    assert report.top_risks == ["Missing validation layer"]


def test_rank_repair_strategies_prefers_safe_matching_memory() -> None:
    strategies = [
        RepairStrategy(title="A", strategy_type="validator_injection", rationale="x", safety_score=0.98),
        RepairStrategy(title="B", strategy_type="planner_replan", rationale="y", safety_score=0.7),
    ]
    ranked = rank_repair_strategies(
        strategies,
        retrieved_memories=[
            {"similarity": 0.91, "metadata": {"strategy_type": "validator_injection", "success_rate": 0.88}},
            {"similarity": 0.95, "metadata": {"strategy_type": "planner_replan", "success_rate": 0.5}},
        ],
        min_similarity=0.8,
        max_strategies=2,
    )
    assert ranked[0].strategy_type == "validator_injection"


@pytest.mark.asyncio
async def test_require_role_blocks_unauthorized_users() -> None:
    dependency = require_role("admin")
    with pytest.raises(HTTPException) as exc:
        await dependency(AuthenticatedUser(user_id="u1", role="viewer", email=None))
    assert exc.value.status_code == 403
