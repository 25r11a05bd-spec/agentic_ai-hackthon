import asyncio
import sys
import tempfile
import json
from pathlib import Path
from typing import Any, Dict, List

from app.schemas.qa_run import WorkflowFinding

HARNESS_TEMPLATE = """
import sys
import json
import traceback
from pathlib import Path

def run_harness():
    results = {{"init_success": False, "routes": []}}
    try:
        # Import the user code
        import app as user_app
        results["init_success"] = True
        
        # Look for FastAPI app
        app_instance = None
        for attr in dir(user_app):
            val = getattr(user_app, attr)
            if hasattr(val, "routes"):
                app_instance = val
                break
        
        if app_instance:
            from fastapi.testclient import TestClient
            client = TestClient(app_instance)
            for route in app_instance.routes:
                if hasattr(route, "path") and hasattr(route, "methods"):
                    method = list(route.methods)[0] if route.methods else "GET"
                    try:
                        resp = client.request(method, route.path)
                        results["routes"].append({{
                            "path": route.path,
                            "method": method,
                            "status_code": resp.status_code,
                            "success": resp.status_code < 500
                        }})
                    except Exception as e:
                        results["routes"].append({{
                            "path": route.path,
                            "method": method,
                            "success": False,
                            "error": str(e),
                            "traceback": traceback.format_exc()
                        }})
    except Exception as e:
        results["init_error"] = str(e)
        results["traceback"] = traceback.format_exc()
    
    print("---HARNESS_RESULTS---")
    print(json.dumps(results))

if __name__ == "__main__":
    run_harness()
"""

async def run_in_sandbox(code: str, timeout: float = 10.0) -> Dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        dir_path = Path(tmp_dir)
        # Create the user app
        (dir_path / "app.py").write_text(code, encoding="utf-8")
        # Create the harness
        (dir_path / "harness.py").write_text(HARNESS_TEMPLATE, encoding="utf-8")
        
        process = await asyncio.create_subprocess_exec(
            sys.executable, "harness.py",
            cwd=tmp_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()
            return {"success": False, "error": "Execution Timeout"}

        stdout_str = stdout.decode().strip()
        if "---HARNESS_RESULTS---" in stdout_str:
            json_str = stdout_str.split("---HARNESS_RESULTS---")[-1].strip()
            return json.loads(json_str)
        
        return {
            "success": False,
            "init_success": False,
            "init_error": stderr.decode() or "Failed to parse harness output",
            "stdout": stdout_str
        }

def analyze_sandbox_result(result: Dict[str, Any]) -> List[WorkflowFinding]:
    findings = []
    
    if not result.get("init_success", False):
        findings.append(WorkflowFinding(
            category="runtime_execution",
            severity="critical",
            title="Application Initialization Failure",
            description=f"The app crashed during import. This usually means top-level dependencies or env vars are missing.\n\nError: {result.get('init_error')}",
            evidence=[result.get("traceback", "")],
            recommendation="Fix top-level crashes so the agent can perform route-isolated testing."
        ))
        return findings

    for route in result.get("routes", []):
        if not route["success"]:
            findings.append(WorkflowFinding(
                category="runtime_execution",
                severity="high",
                title=f"Endpoint Crash: {route['method']} {route['path']}",
                description=f"Route {route['path']} failed during isolated testing.",
                evidence=[route.get("traceback", route.get("error", "Unknown error"))],
                recommendation="Fix the logic inside this route's handler function."
            ))

    return findings
