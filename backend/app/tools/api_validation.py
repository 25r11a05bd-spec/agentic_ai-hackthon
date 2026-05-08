from __future__ import annotations

from typing import Any

import httpx

from app.schemas.qa_run import WorkflowFinding


SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


async def validate_api(url: str, method: str = "HEAD") -> dict[str, Any]:
    chosen_method = method.upper()
    if chosen_method not in SAFE_METHODS:
        raise ValueError(f"Unsafe validation method: {chosen_method}")

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        response = await client.request(chosen_method, url)
        return {
            "url": url,
            "method": chosen_method,
            "status_code": response.status_code,
            "headers": dict(response.headers),
        }


async def retry_request(url: str, method: str = "HEAD", attempts: int = 3) -> dict[str, Any]:
    last_error: str | None = None
    for _ in range(attempts):
        try:
            return await validate_api(url, method)
        except Exception as exc:  # pragma: no cover
            last_error = str(exc)
    return {"url": url, "method": method, "status_code": None, "error": last_error or "Unknown error"}


def inspect_response(result: dict[str, Any]) -> list[WorkflowFinding]:
    findings: list[WorkflowFinding] = []
    status_code = result.get("status_code")
    if status_code is None:
        findings.append(
            WorkflowFinding(
                category="api_validation",
                severity="high",
                title="API validation failed",
                description=result.get("error", "The endpoint could not be validated."),
                evidence=[result.get("url", "unknown")],
                recommendation="Verify the endpoint, DNS resolution, or firewall policy.",
            )
        )
    elif status_code >= 500:
        findings.append(
            WorkflowFinding(
                category="api_validation",
                severity="high",
                title="API health check returned server error",
                description=f"Validation probe returned HTTP {status_code}.",
                evidence=[result.get("url", "unknown")],
                recommendation="Use a fallback endpoint or add stronger retry/backoff handling.",
            )
        )
    elif status_code >= 400:
        findings.append(
            WorkflowFinding(
                category="api_validation",
                severity="medium",
                title="API health check returned client error",
                description=f"Validation probe returned HTTP {status_code}.",
                evidence=[result.get("url", "unknown")],
                recommendation="Confirm authentication, path correctness, and allowed validation methods.",
            )
        )
    return findings

