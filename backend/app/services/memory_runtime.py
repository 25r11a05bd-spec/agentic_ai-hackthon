from __future__ import annotations

from typing import Any

from app.memory.chroma_service import ChromaMemoryService
from app.schemas.qa_run import FailureExplanation, RepairStrategy, WorkflowFinding


async def store_memory(
    memory_service: ChromaMemoryService,
    collection: str,
    identifier: str,
    text: str,
    metadata: dict[str, Any],
) -> None:
    await memory_service.store(collection, identifier, text, metadata)


async def retrieve_memory(
    memory_service: ChromaMemoryService,
    collection: str,
    text: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    return await memory_service.query(collection, text, limit=limit)


async def save_failure_patterns(
    memory_service: ChromaMemoryService,
    run_id: str,
    findings: list[WorkflowFinding],
    explanation: FailureExplanation | None,
) -> None:
    if not findings:
        return

    text = "\n".join(f"{finding.category}:{finding.title}:{finding.description}" for finding in findings)
    metadata = {
        "run_id": run_id,
        "severity": max((finding.severity for finding in findings), default="info"),
        "root_cause": explanation.root_cause if explanation else "unknown",
    }
    await store_memory(memory_service, "failure_patterns", run_id, text, metadata)


def rank_repair_strategies(
    candidates: list[RepairStrategy],
    retrieved_memories: list[dict[str, Any]],
    min_similarity: float,
    max_strategies: int,
) -> list[RepairStrategy]:
    for strategy in candidates:
        strategy.memory_similarity = 0.0
        strategy.prior_success_rate = 0.0
        for memory in retrieved_memories:
            metadata = memory.get("metadata", {})
            similarity = float(memory.get("similarity", 0.0))
            if metadata.get("strategy_type") == strategy.strategy_type and similarity >= strategy.memory_similarity:
                strategy.memory_similarity = similarity
                strategy.prior_success_rate = float(metadata.get("success_rate", similarity))

    ranked = [
        item
        for item in candidates
        if item.safety_score >= 0.6 and (item.memory_similarity >= min_similarity or item.safety_score >= 0.9)
    ]
    ranked.sort(
        key=lambda item: (
            item.selected,
            round((item.memory_similarity * 0.45) + (item.prior_success_rate * 0.35) + (item.safety_score * 0.20), 6),
            item.prior_success_rate,
            item.safety_score,
            item.memory_similarity,
        ),
        reverse=True,
    )
    return ranked[:max_strategies]
