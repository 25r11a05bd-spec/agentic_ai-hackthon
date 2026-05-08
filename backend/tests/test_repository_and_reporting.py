from __future__ import annotations

import asyncio
from pathlib import Path

from app.memory.chroma_service import ChromaMemoryService
from app.repositories.run_repository import FileRunRepository
from app.schemas.qa_run import FailureExplanation, PlaybackEvent, QARunCreate, QualityScores, RunArtifact
from app.services.memory_runtime import retrieve_memory, save_failure_patterns, store_memory
from app.services.reporting import generate_markdown_report
from app.tools.python_analysis import generate_quality_report
from app.utils.time import utcnow
from app.core.config import Settings


def test_repository_creates_and_reads_run(tmp_path: Path) -> None:
    repository = FileRunRepository(tmp_path / "storage")

    async def scenario() -> None:
        run = await repository.create_run(
            request=QARunCreate(),
            created_by="dev",
            project_file_name="app.py",
            workflow_file_name="automation.json",
            attachments=[RunArtifact(name="evidence.csv", file_type="csv", path="tmp/evidence.csv")],
        )
        detail = await repository.get_run(run.id)
        assert detail is not None
        assert detail.id == run.id
        assert detail.attachments[0].name == "evidence.csv"

    asyncio.run(scenario())


def test_repository_metrics_track_runs(tmp_path: Path) -> None:
    repository = FileRunRepository(tmp_path / "storage")

    async def scenario() -> None:
        run = await repository.create_run(
            request=QARunCreate(),
            created_by="dev",
            project_file_name="app.py",
            workflow_file_name="automation.json",
            attachments=[],
        )
        await repository.update_run(run.id, status="success", scores=QualityScores(overall=90, validation=92, reliability=91, retry_health=90, hallucination_risk=10))
        metrics = await repository.get_metrics()
        assert metrics.total_runs == 1
        assert metrics.success_rate == 100.0

    asyncio.run(scenario())


def test_reporting_generates_markdown(tmp_path: Path) -> None:
    repository = FileRunRepository(tmp_path / "storage")

    async def scenario() -> None:
        run = await repository.create_run(
            request=QARunCreate(),
            created_by="dev",
            project_file_name="app.py",
            workflow_file_name="automation.json",
            attachments=[],
        )
        await repository.add_event(
            PlaybackEvent(
                run_id=run.id,
                event_type="agent_log",
                agent="planner",
                step="Planning",
                status="success",
                timestamp=utcnow(),
            )
        )
        await repository.save_failure_explanation(
            run.id,
            FailureExplanation(
                root_cause="Missing validation layer",
                evidence=["No validator node found"],
                affected_nodes=["fetch"],
                user_impact="Risky execution path",
                why_previous_attempt_failed="No guards were present",
                recommended_fix="Add validator",
            ),
        )
        detail = await repository.get_run(run.id)
        assert detail is not None
        summary = generate_quality_report(
            run.id,
            "failed",
            QualityScores(overall=50, validation=40, reliability=48, retry_health=60, hallucination_risk=30),
            detail.findings,
        )
        markdown = generate_markdown_report(detail, summary, detail.failure_explanation)
        assert "# QA Run" in markdown
        assert "Failure Explainer" in markdown

    asyncio.run(scenario())


def test_memory_roundtrip_works_with_fallback_store(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "storage")
    memory = ChromaMemoryService(settings)

    async def scenario() -> None:
        await store_memory(
            memory,
            "failure_patterns",
            "run_1",
            "validator missing after API step",
            {"run_id": "run_1", "strategy_type": "validator_injection", "success_rate": 0.9},
        )
        results = await retrieve_memory(memory, "failure_patterns", "validator missing", limit=3)
        assert len(results) >= 1
        assert results[0]["metadata"]["run_id"] == "run_1"

        await save_failure_patterns(
            memory,
            "run_2",
            [],
            None,
        )

    asyncio.run(scenario())
