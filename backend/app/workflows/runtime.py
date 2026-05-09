from __future__ import annotations

from app.schemas.qa_run import WorkflowEdge, WorkflowNode


EXECUTION_NODE_IDS = [
    "ingest",
    "planner",
    "tool_router",
    "executor",
    "validator",
    "failure_explainer",
    "reflection",
    "memory_retriever",
    "self_heal_router",
    "retry_or_replan",
    "approval_gate",
    "memory_writer",
    "notifier",
    "finalizer",
]


def build_execution_graph() -> tuple[list[WorkflowNode], list[WorkflowEdge]]:
    nodes = [WorkflowNode(id=node_id, label=node_id.replace("_", " ").title(), type="task") for node_id in EXECUTION_NODE_IDS]
    edges = [
        WorkflowEdge(source=EXECUTION_NODE_IDS[index], target=EXECUTION_NODE_IDS[index + 1])
        for index in range(len(EXECUTION_NODE_IDS) - 1)
    ]
    return nodes, edges
