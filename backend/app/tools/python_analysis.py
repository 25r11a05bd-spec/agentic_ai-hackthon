from __future__ import annotations

import ast

from app.schemas.qa_run import PythonAnalysis, QualityReportSummary, QualityScores, WorkflowFinding
from app.utils.time import utcnow


HTTP_CLIENT_IMPORTS = {"requests", "httpx", "aiohttp"}


def analyze_python_code(source: str) -> PythonAnalysis:
    tree = ast.parse(source)

    imports: list[str] = []
    functions: list[str] = []
    classes: list[str] = []
    api_calls: list[str] = []
    validators: list[str] = []
    retry_patterns: list[str] = []
    exception_handlers: list[str] = []
    risk_flags: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
            if node.name.startswith(("validate_", "check_", "guard_")):
                validators.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, ast.Try):
            exception_handlers.append("try/except")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            owner = getattr(node.func.value, "id", "")
            if owner in {"requests", "httpx", "client", "session"} and node.func.attr in {
                "get",
                "post",
                "put",
                "patch",
                "delete",
                "head",
                "options",
            }:
                api_calls.append(node.func.attr)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"retry", "sleep"}:
                retry_patterns.append(node.func.id)

    if not validators:
        risk_flags.append("No explicit validation functions were found in app.py.")
    if not retry_patterns:
        risk_flags.append("No retry or backoff helper was found in app.py.")
    if not any(entry.split(".", 1)[0] in HTTP_CLIENT_IMPORTS for entry in imports):
        risk_flags.append("No HTTP client library import was detected; API validation may be indirect.")

    return PythonAnalysis(
        imports=sorted(set(imports)),
        functions=sorted(set(functions)),
        classes=sorted(set(classes)),
        api_calls=sorted(set(api_calls)),
        validators=sorted(set(validators)),
        retry_patterns=sorted(set(retry_patterns)),
        exception_handlers=exception_handlers,
        risk_flags=risk_flags,
        ast_summary=(
            f"Detected {len(functions)} functions, {len(classes)} classes, "
            f"{len(api_calls)} HTTP call sites, and {len(validators)} validator-style functions."
        ),
    )


def generate_quality_report(
    run_id: str,
    status: str,
    scores: QualityScores,
    findings: list[WorkflowFinding],
) -> QualityReportSummary:
    finding_counts: dict[str, int] = {}
    for finding in findings:
        finding_counts[finding.severity] = finding_counts.get(finding.severity, 0) + 1

    top_risks = [finding.title for finding in findings if finding.severity in {"critical", "high"}][:5]
    summary = (
        f"Run {run_id} finished with status `{status}`. "
        f"Overall score: {scores.overall}/100, validation: {scores.validation}/100, "
        f"hallucination risk: {scores.hallucination_risk}/100."
    )

    return QualityReportSummary(
        run_id=run_id,
        status=status,
        generated_at=utcnow(),
        summary=summary,
        scores=scores,
        finding_counts=finding_counts,
        top_risks=top_risks,
    )
