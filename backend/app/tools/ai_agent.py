import os
import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import httpx

from app.schemas.qa_run import WorkflowFinding, FailureExplanation, RepairStrategy

class AIPatch(BaseModel):
    explanation: str
    patch: str
    confidence: float
    is_safe: bool

async def generate_ai_reflection(
    code: str, 
    findings: List[WorkflowFinding], 
    runtime_logs: str = ""
) -> Optional[FailureExplanation]:
    """
    Uses LLM to generate a root cause analysis and explanation.
    """
    # Using Groq or Ollama based on environment
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    base_url = "https://api.groq.com/openai/v1/chat/completions"

    if not api_key:
        return None

    findings_text = "\n".join([f"- {f.severity.upper()}: {f.title} ({f.description})" for f in findings])
    
    prompt = f"""
    You are an Autonomous AI QA Engineer.
    Analyze the following Python code and the detected findings to explain the root cause of failure.
    
    SOURCE CODE:
    ```python
    {code}
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
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return []

    memories_text = "\n".join([f"- {m}" for m in past_memories]) if past_memories else "No past memories for this failure pattern."

    prompt = f"""
    You are an AI Self-Healing System.
    Generate 2-3 specific code repair strategies for these findings.
    
    SOURCE CODE:
    ```python
    {code}
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
                    "model": "llama-3.1-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"}
                }
            )
            data = resp.json()
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
        print(f"AI Repair Error: {e}")
        return []
