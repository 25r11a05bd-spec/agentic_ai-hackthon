from __future__ import annotations

import json
from typing import Any

from app.schemas.qa_run import CanonicalWorkflowSpec, QualityScores, WorkflowEdge, WorkflowFinding, WorkflowNode


APPROVED_TOOL_TYPES = {"task", "api", "http", "request", "validator", "approval", "memory", "notify"}


def validate_json(payload: str) -> dict[str, Any]:
    return json.loads(payload)


def validate_schema(raw_workflow: dict[str, Any]) -> list[WorkflowFinding]:
    findings: list[WorkflowFinding] = []

    if "nodes" in raw_workflow:
        if not isinstance(raw_workflow["nodes"], list):
            findings.append(
                WorkflowFinding(
                    category="schema",
                    severity="high",
                    title="Workflow nodes must be a list",
                    description="The `nodes` field exists but is not an array.",
                    evidence=[f"Received type: {type(raw_workflow['nodes']).__name__}"],
                    recommendation="Provide `nodes` as an array of workflow node objects.",
                )
            )
        if "edges" not in raw_workflow:
            findings.append(
                WorkflowFinding(
                    category="schema",
                    severity="high",
                    title="Workflow edges are missing",
                    description="A node/edge workflow was uploaded without `edges`.",
                    recommendation="Add an `edges` array to describe control flow transitions.",
                )
            )
    elif "steps" in raw_workflow:
        if not isinstance(raw_workflow["steps"], list):
            findings.append(
                WorkflowFinding(
                    category="schema",
                    severity="high",
                    title="Workflow steps must be a list",
                    description="The `steps` field exists but is not an array.",
                    evidence=[f"Received type: {type(raw_workflow['steps']).__name__}"],
                    recommendation="Provide `steps` as an ordered array of step objects.",
                )
            )
    else:
        findings.append(
            WorkflowFinding(
                category="schema",
                severity="high",
                title="Unsupported workflow format",
                description="Expected either a `nodes`/`edges` graph or a `steps` array.",
                evidence=[f"Top-level keys: {', '.join(sorted(raw_workflow.keys())) or 'none'}"],
                recommendation="Upload an `automation.json` file using one of the supported formats.",
            )
        )

    nodes = raw_workflow.get("nodes", [])
    if isinstance(nodes, list):
        for index, node in enumerate(nodes):
            if not isinstance(node, dict):
                findings.append(
                    WorkflowFinding(
                        category="schema",
                        severity="high",
                        title="Workflow node entry must be an object",
                        description="Every `nodes[]` item should be a JSON object.",
                        evidence=[f"Invalid entry at index {index}: {type(node).__name__}"],
                        recommendation="Replace malformed node entries with node objects containing id, label, type, and config.",
                    )
                )
                continue

            node_type = str(node.get("type", "task"))
            if node_type not in APPROVED_TOOL_TYPES:
                findings.append(
                    WorkflowFinding(
                        category="schema",
                        severity="medium",
                        title="Workflow node type is not in the approved registry",
                        description=f"Node `{node.get('id', 'unknown')}` declares unsupported type `{node_type}`.",
                        evidence=[f"Approved types: {', '.join(sorted(APPROVED_TOOL_TYPES))}"],
                        affected_nodes=[str(node.get("id", "unknown"))],
                        recommendation="Use an approved node type or register the tool explicitly before execution.",
                    )
                )

    return findings


def normalize_workflow(raw_workflow: dict[str, Any]) -> CanonicalWorkflowSpec:
    if "nodes" in raw_workflow and "edges" in raw_workflow:
        nodes = [
            WorkflowNode(
                id=str(node.get("id")),
                label=node.get("label", node.get("name", str(node.get("id")))),
                type=node.get("type", "task"),
                config=node.get("config", {}),
            )
            for node in raw_workflow["nodes"]
        ]
        edges = [
            WorkflowEdge(
                source=str(edge.get("source")),
                target=str(edge.get("target")),
                label=edge.get("label"),
            )
            for edge in raw_workflow["edges"]
        ]
    else:
        steps = raw_workflow.get("steps", [])
        nodes = []
        edges = []
        for index, step in enumerate(steps):
            node_id = str(step.get("id", f"step_{index + 1}"))
            nodes.append(
                WorkflowNode(
                    id=node_id,
                    label=step.get("name", node_id),
                    type=step.get("type", "task"),
                    config=step,
                )
            )
            if index > 0:
                edges.append(WorkflowEdge(source=nodes[index - 1].id, target=node_id))

    api_calls = [
        node.config.get("endpoint")
        for node in nodes
        if node.type in {"api", "http", "request"} and node.config.get("endpoint")
    ]
    validation_rules = [node.label for node in nodes if "validate" in node.label.lower() or node.type == "validator"]
    retry_policy = raw_workflow.get("retry_policy", {})
    risk_flags = []

    if not validation_rules:
        risk_flags.append("Workflow lacks an explicit validator or guard node.")
    if not retry_policy:
        risk_flags.append("Workflow does not declare retry_policy metadata.")

    return CanonicalWorkflowSpec(
        nodes=nodes,
        edges=edges,
        api_calls=api_calls,
        validation_rules=validation_rules,
        retry_policy=retry_policy,
        metadata=raw_workflow.get("metadata", {}),
        risk_flags=risk_flags,
    )


def check_missing_fields(raw_workflow: dict[str, Any]) -> list[WorkflowFinding]:
    findings: list[WorkflowFinding] = []
    required_fields = ["nodes", "edges"]
    if "steps" in raw_workflow:
        required_fields = ["steps"]

    for field_name in required_fields:
        if field_name not in raw_workflow:
            findings.append(
                WorkflowFinding(
                    category="schema",
                    severity="high",
                    title=f"Missing required field: {field_name}",
                    description=f"The uploaded automation.json is missing the top-level `{field_name}` field.",
                    evidence=[f"Top-level keys: {', '.join(sorted(raw_workflow.keys()))}"],
                    recommendation=f"Add `{field_name}` to align with the supported workflow format.",
                )
            )
    return findings


def detect_hallucinations(
    workflow: CanonicalWorkflowSpec,
    python_functions: list[str],
    python_api_calls: list[str],
    approved_tool_registry: set[str] | None = None,
    known_schema_fields: set[str] | None = None,
) -> list[WorkflowFinding]:
    findings: list[WorkflowFinding] = []
    known_symbols = {item.lower() for item in python_functions}
    known_transport = {item.lower() for item in python_api_calls}
    approved_tool_registry = {item.lower() for item in (approved_tool_registry or APPROVED_TOOL_TYPES)}
    known_schema_fields = {item.lower() for item in (known_schema_fields or {"id", "label", "type", "config"})}

    for node in workflow.nodes:
        declared_function = str(node.config.get("function", "")).lower()
        if declared_function and declared_function not in known_symbols:
            findings.append(
                WorkflowFinding(
                    category="hallucination",
                    severity="high",
                    title="Workflow references a missing Python symbol",
                    description=f"`{declared_function}` is referenced in automation.json but not found in app.py.",
                    evidence=[f"Known functions: {', '.join(python_functions) or 'none'}"],
                    affected_nodes=[node.id],
                    recommendation="Update automation.json to reference a real function or add the missing implementation.",
                )
            )

        declared_method = str(node.config.get("method", "")).lower()
        if declared_method and declared_method not in {"get", "post", "put", "patch", "delete", "head", "options"}:
            findings.append(
                WorkflowFinding(
                    category="hallucination",
                    severity="medium",
                    title="Workflow declares an unsupported HTTP method",
                    description=f"Node `{node.label}` declares `{declared_method}`, which is not a valid HTTP method.",
                    evidence=[f"Known call types in code: {', '.join(python_api_calls) or 'none'}"],
                    affected_nodes=[node.id],
                    recommendation="Replace the method with a valid HTTP verb and ensure the executor supports it.",
                )
            )

        if node.type.lower() not in approved_tool_registry:
            findings.append(
                WorkflowFinding(
                    category="hallucination",
                    severity="medium",
                    title="Workflow uses an unregistered tool type",
                    description=f"Node `{node.label}` declares `{node.type}`, which is not in the approved tool registry.",
                    evidence=[f"Approved tool types: {', '.join(sorted(approved_tool_registry)) or 'none'}"],
                    affected_nodes=[node.id],
                    recommendation="Use an approved tool type or register the new executor capability before running.",
                )
            )

        unknown_config_keys = sorted(
            key for key in node.config.keys() if key.lower() not in known_schema_fields and key.lower() != "function"
        )
        if unknown_config_keys:
            findings.append(
                WorkflowFinding(
                    category="hallucination",
                    severity="low",
                    title="Workflow node includes ungrounded config fields",
                    description=f"Node `{node.label}` contains config fields not present in the known schema.",
                    evidence=[f"Unknown fields: {', '.join(unknown_config_keys)}"],
                    affected_nodes=[node.id],
                    recommendation="Confirm the fields are supported by the runtime or remove speculative config keys.",
                )
            )

        if node.type in {"api", "http", "request"} and not known_transport:
            findings.append(
                WorkflowFinding(
                    category="hallucination",
                    severity="medium",
                    title="Workflow claims API activity but app.py has no obvious HTTP call sites",
                    description="The workflow expects an API step, but the Python source does not expose an obvious HTTP transport.",
                    evidence=["No HTTP call sites were found in app.py."],
                    affected_nodes=[node.id],
                    recommendation="Verify the executor implementation or annotate the workflow with the true transport layer.",
                )
            )

    return findings


def inspect_workflow(raw_workflow: dict[str, Any], workflow: CanonicalWorkflowSpec) -> list[WorkflowFinding]:
    findings = [*check_missing_fields(raw_workflow), *validate_schema(raw_workflow)]
    outbound_nodes = {edge.source for edge in workflow.edges}

    for node in workflow.nodes:
        if node.type in {"api", "http", "request"} and node.id not in outbound_nodes:
            findings.append(
                WorkflowFinding(
                    category="control_flow",
                    severity="high",
                    title="Unsafe terminal API node",
                    description=f"Node `{node.label}` performs an external call and ends without a validation branch.",
                    evidence=["No downstream edge from the API node was found."],
                    affected_nodes=[node.id],
                    recommendation="Add a validation or guard node immediately after the API call.",
                )
            )

    if not workflow.validation_rules:
        findings.append(
            WorkflowFinding(
                category="validation",
                severity="high",
                title="Missing validation layer",
                description="The workflow has no explicit validation node or rule after execution steps.",
                recommendation="Insert a validator node or schema validation rule before success/finalization.",
            )
        )

    if not workflow.retry_policy:
        findings.append(
            WorkflowFinding(
                category="resilience",
                severity="medium",
                title="Retry policy is missing",
                description="The workflow does not declare retry attempts, delays, or backoff strategy.",
                recommendation="Define retry_policy with max_retries, delay_seconds, and backoff mode.",
            )
        )

    return findings


def score_workflow_quality(findings: list[WorkflowFinding]) -> QualityScores:
    penalties = {"critical": 25, "high": 15, "medium": 8, "low": 4, "info": 1}
    total_penalty = sum(penalties[item.severity] for item in findings)
    validation_penalty = sum(penalties[item.severity] for item in findings if item.category == "validation")
    hallucination_penalty = sum(penalties[item.severity] for item in findings if item.category == "hallucination")
    resilience_penalty = sum(penalties[item.severity] for item in findings if item.category == "resilience")

    overall = max(0, 100 - total_penalty)
    validation = max(0, 100 - validation_penalty)
    hallucination_risk = min(100, hallucination_penalty * 2)
    retry_health = max(0, 100 - resilience_penalty)
    reliability = max(0, round((overall + validation + retry_health) / 3))

    return QualityScores(
        reliability=reliability,
        validation=validation,
        hallucination_risk=hallucination_risk,
        retry_health=retry_health,
        overall=overall,
    )
