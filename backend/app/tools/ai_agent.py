import os
import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import httpx

from app.schemas.qa_run import WorkflowFinding, FailureExplanation, RepairStrategy, QualityScores

def _extract_nested_json(data: Any, required_keys: list[str]) -> dict[str, Any]:
    """
    Recursively searches for a dictionary that contains most or all of the required keys.
    """
    if isinstance(data, dict):
        # Flexible match: if it has at least one of the primary keys, consider it a candidate
        if any(k in data for k in required_keys):
            return data
        for v in data.values():
            found = _extract_nested_json(v, required_keys)
            if found:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _extract_nested_json(item, required_keys)
            if found:
                return found
    return {}

def _map_to_schema(data: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    """
    Renames keys in a dictionary based on a mapping of common AI aliases.
    """
    new_data = data.copy()
    for alias, target in mapping.items():
        if alias in new_data and target not in new_data:
            new_data[target] = new_data.pop(alias)
    return new_data

class AIPatch(BaseModel):
    explanation: str
    patch: str
    confidence: float
    is_safe: bool

from app.core.config import get_settings

settings = get_settings()

async def generate_ai_reflection(
    code: str, 
    findings: List[WorkflowFinding], 
    runtime_logs: str = ""
) -> Optional[FailureExplanation]:
    """
    Uses LLM to generate a root cause analysis and explanation.
    """
    api_key = settings.groq_api_key
    model = settings.groq_model
    base_url = "https://api.groq.com/openai/v1/chat/completions"

    print(f"🤖 [AI-Reflection] Starting... Key present: {bool(api_key)}, Model: {model}")

    if not api_key:
        print("⚠️ [AI-Reflection] Skipping AI reflection: GROQ_API_KEY is missing.")
        return None

    findings_text = "\n".join([f"- {f.severity.upper()}: {f.title} ({f.description})" for f in findings])
    
    prompt = f"""
    You are an Autonomous AI QA Engineer.
    Analyze the following Python code and the detected findings to explain the root cause of failure.
    
    SOURCE CODE:
    ```python
    {code[:2000]}
    ```
    
    FINDINGS:
    {findings_text}
    
    RUNTIME LOGS:
    {runtime_logs}
    
    Return your response in JSON format:
    {{
        "root_cause": "A concise explanation of why it failed",
        "evidence": ["specific line numbers or variable names"],
        "affected_nodes": ["names of impacted functions"],
        "user_impact": "What happens if this goes to production?",
        "why_previous_attempt_failed": "Technical reason for the crash",
        "recommended_fix": "High-level fix strategy"
    }}
    """

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                base_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"}
                }
            )
            data = resp.json()
            content = json.loads(data["choices"][0]["message"]["content"])

            # Use recursive extractor for robustness
            content = _extract_nested_json(content, ["root_cause", "evidence"]) or content
            
            # Map common aliases
            content = _map_to_schema(content, {
                "explanation": "root_cause",
                "analysis": "root_cause",
                "impact": "user_impact",
                "fix": "recommended_fix"
            })

            return FailureExplanation(**content)
    except Exception as e:
        print(f"AI Reflection Error: {e}")
        return None

async def generate_repair_strategies(
    code: str, 
    findings: List[WorkflowFinding],
    past_memories: List[str] = []
) -> List[RepairStrategy]:
    """
    Generates actionable code patches using LLM, informed by past memories.
    """
    api_key = settings.groq_api_key
    if not api_key:
        return []

    memories_text = "\n".join([f"- {m}" for m in past_memories]) if past_memories else "No past memories for this failure pattern."

    prompt = f"""
    You are an AI Self-Healing System.
    Generate 2-3 specific code repair strategies for these findings.
    
    CRITICAL PRIORITIES:
    1. If there is an 'Application Initialization Failure' or import crash (e.g. missing SECRET_TOKEN), you MUST prioritize fixing the Python code by injecting safe fallbacks like `os.getenv("SECRET_TOKEN", "")`.
    2. Fix actual Python syntax errors, division by zero, or type errors BEFORE suggesting workflow-level retry optimizations.
    3. Always output the COMPLETE `fixed_code` so the engine can apply it directly.
    
    SOURCE CODE:
    ```python
    {code[:2000]}
    ```

    LEARNED PATTERNS (FROM PAST SUCCESSFUL FIXES):
    {memories_text}
    
    Return a JSON object with a "strategies" key containing an array:
    {{
      "strategies": [
        {{
          "title": "Short title",
          "strategy_type": "patch",
          "rationale": "Why this works",
          "steps": ["Step 1"],
          "safety_score": 0.95,
          "fixed_code": "The ENTIRE fixed app.py code as a string",
          "explanation": "What was changed"
        }}
      ]
    }}
    """

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": settings.groq_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"}
                }
            )
            data = resp.json()
            if "choices" not in data:
                print(f"❌ [AI-Repair] Groq Error: {data.get('error', 'Unknown Error')}")
                return []
            content = json.loads(data["choices"][0]["message"]["content"])
            items = content.get("strategies", [])
            
            strategies = []
            for item in items:
                # Ensure fixed_code is present, fallback to full code if missing
                if not item.get("fixed_code"):
                    item["fixed_code"] = code
                strategies.append(RepairStrategy(**item))
            return strategies
    except Exception as e:
        if 'resp' in locals() and hasattr(resp, 'json'):
            try:
                err_data = resp.json()
                print(f"❌ [AI-Repair] Groq API Error: {err_data.get('error', e)}")
            except:
                print(f"❌ [AI-Repair] Error: {e}")
        else:
            print(f"❌ [AI-Repair] Error: {e}")
        return []

class PlanStep(BaseModel):
    agent: str
    action: str
    expected_outcome: str

class ExecutionPlan(BaseModel):
    rationale: str
    steps: list[PlanStep]

async def generate_plan(task: str, code: str) -> ExecutionPlan:
    """
    Uses Groq to generate an initial execution strategy for the QA run.
    """
    api_key = settings.groq_api_key
    model = settings.groq_model
    
    print(f"🤖 [AI-Planner] Starting... Key present: {bool(api_key)}, Model: {model}")

    if not api_key:
        print("⚠️ [AI-Planner] Skipping AI planning: GROQ_API_KEY is missing. Using heuristic fallback.")
        # Fallback to a default plan if no API key
        return ExecutionPlan(
            rationale="No AI key detected. Falling back to standard heuristic plan.",
            steps=[
                PlanStep(agent="ingest", action="Parse source", expected_outcome="AST tree ready"),
                PlanStep(agent="planner", action="Static analysis", expected_outcome="Risk profile generated")
            ]
        )

    prompt = f"""
    You are an AI QA Strategist.
    Analyze this task and code to create a strategy.
    
    TASK: {task}
    SOURCE CODE (Snippet):
    {code[:1000]} 

    Return ONLY a JSON object with the following structure. DO NOT include any other text or keys.
    {{
        "rationale": "...",
        "steps": [
            {{
                "agent": "...",
                "action": "...",
                "expected_outcome": "..."
            }}
        ]
    }}
    """

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"}
                }
            )
            data = resp.json()
            if "choices" not in data:
                print(f"❌ [AI-Planner] Groq Error: {data.get('error', 'Unknown')}")
                raise ValueError(f"Groq API Error: {data.get('error', 'Unknown')}")
                
            raw_content = data["choices"][0]["message"]["content"]
            print(f"🤖 [AI-Planner] Raw Response: {raw_content[:200]}...")
            content = json.loads(raw_content)
            
            # Use recursive extractor for robustness
            content = _extract_nested_json(content, ["rationale", "steps"]) or content
            
            # Map common aliases for Planner
            content = _map_to_schema(content, {
                "strategy": "rationale",
                "analysis": "rationale",
                "plan": "steps",
                "execution_plan": "steps",
                "actions": "steps"
            })

            # Ensure steps is a list of objects, not strings
            if "steps" in content and isinstance(content["steps"], list):
                processed_steps = []
                for s in content["steps"]:
                    if isinstance(s, str):
                        processed_steps.append({"agent": "planner", "action": s, "expected_outcome": "Unknown"})
                    else:
                        processed_steps.append(s)
                content["steps"] = processed_steps

            return ExecutionPlan(**content)
    except Exception as e:
        print(f"AI Planning Error (Using Fast Fallback): {e}")
        return ExecutionPlan(
            rationale="Fast Heuristic Analysis",
            steps=[PlanStep(agent="ingest", action="Scan symbols", expected_outcome="Ready")]
        )

class AIQualityAnalysis(BaseModel):
    summary: str
    scores: QualityScores
    top_risks: list[str]
    recommendation: str

async def generate_ai_quality_analysis(
    run_id: str,
    code: str,
    findings: List[WorkflowFinding],
    static_scores: QualityScores
) -> Optional[AIQualityAnalysis]:
    """
    Uses LLM to provide a final qualitative judgment and adjusted scoring.
    """
    api_key = settings.groq_api_key
    if not api_key:
        return None

    findings_text = "\n".join([f"- {f.severity.upper()}: {f.title} ({f.description})" for f in findings])
    
    prompt = f"""
    You are an AI QA Auditor.
    Evaluate this QA Run and provide a final quality judgment.
    
    RUN ID: {run_id}
    SOURCE CODE:
    ```python
    {code[:1500]}
    ```
    
    FINDINGS:
    {findings_text}
    
    STATIC SCORES:
    {json.dumps(static_scores.model_dump(), indent=2)}
    
    Provide an adjusted score and a professional summary.
    Return JSON:
    {{
        "summary": "Professional executive summary of the code quality",
        "scores": {{
            "reliability": 0-100,
            "validation": 0-100,
            "hallucination_risk": 0-100,
            "retry_health": 0-100,
            "overall": 0-100
        }},
        "top_risks": ["risk 1", "risk 2"],
        "recommendation": "Primary next step for the developer"
    }}
    """

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": settings.groq_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"}
                }
            )
            data = resp.json()
            content = json.loads(data["choices"][0]["message"]["content"])
            return AIQualityAnalysis(**content)
    except Exception as e:
        print(f"AI Quality Analysis Error: {e}")
        return None
