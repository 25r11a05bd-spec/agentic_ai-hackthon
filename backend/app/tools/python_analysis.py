import ast
import builtins
from typing import Set

from app.schemas.qa_run import PythonAnalysis, QualityReportSummary, QualityScores, WorkflowFinding
from app.utils.time import utcnow

HTTP_CLIENT_IMPORTS = {"requests", "httpx", "aiohttp"}
UNSAFE_CALLS = {"exec", "eval", "os.system", "subprocess.run", "subprocess.Popen"}

class SecurityVisitor(ast.NodeVisitor):
    def __init__(self):
        # Pass 1: Track all defined symbols (built-ins + assignments + imports)
        self.defined_names: Set[str] = set(dir(builtins))
        self.defined_names.update({"app", "FastAPI", "self", "cls", "args", "kwargs", "MEMORY"})
        self.used_names: Set[str] = set()
        self.findings: list[str] = []
        self.api_calls: list[str] = []
        self.validators: list[str] = []
        self.functions: list[str] = []
        self.classes: list[str] = []
        self.imports: list[str] = []

    def _add_target(self, node):
        """Recursively add assignment targets to defined names."""
        if isinstance(node, ast.Name):
            self.defined_names.add(node.id)
        elif isinstance(node, (ast.Tuple, ast.List)):
            for elt in node.elts:
                self._add_target(elt)
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                self.defined_names.add(node.value.id)

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
            self.defined_names.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.append(node.module)
            for alias in node.names:
                self.defined_names.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.functions.append(node.name)
        self.defined_names.add(node.name)
        # Add arguments
        for arg in node.args.args:
            self.defined_names.add(arg.arg)
        if node.args.vararg: self.defined_names.add(node.args.vararg.arg)
        if node.args.kwarg: self.defined_names.add(node.args.kwarg.arg)
        
        # Pre-scan function body for any assignments to avoid false-positives
        for sub_node in ast.walk(node):
            if isinstance(sub_node, (ast.Assign, ast.AnnAssign)):
                targets = sub_node.targets if hasattr(sub_node, "targets") else [sub_node.target]
                for t in targets: self._add_target(t)
            elif isinstance(sub_node, (ast.For, ast.AsyncFor)):
                self._add_target(sub_node.target)
            elif isinstance(sub_node, (ast.With, ast.AsyncWith)):
                for item in sub_node.items:
                    if item.optional_vars: self._add_target(item.optional_vars)
        
        if node.name.startswith(("validate_", "check_", "guard_")):
            self.validators.append(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_Assign(self, node):
        for t in node.targets: self._add_target(t)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_Call(self, node):
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = f"{getattr(node.func.value, 'id', '')}.{node.func.attr}"

        if func_name in UNSAFE_CALLS:
            self.findings.append(f"CRITICAL SECURITY RISK: Unsafe call detected: {func_name}")

        if func_name == "open" and node.args:
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Name):
                self.findings.append(f"HIGH SECURITY RISK: Potential Path Traversal in 'open()' with dynamic variable '{first_arg.id}'")

        if isinstance(node.func, ast.Attribute):
            owner = getattr(node.func.value, "id", "")
            if owner in {"requests", "httpx", "client", "session"} and node.func.attr in {"get", "post", "put", "delete"}:
                self.api_calls.append(node.func.attr)

        self.generic_visit(node)

def analyze_python_code(source: str) -> PythonAnalysis:
    print("🔍 [StaticAnalysis] Starting Python source analysis...")
    try:
        # Initial pass to define all names
        tree = ast.parse(source)
        print("✅ [StaticAnalysis] AST parsed successfully. Starting symbol scan...")
        visitor = SecurityVisitor()
        
        # Double-scan the whole tree first for globals and functions
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if hasattr(node, "targets") else [node.target]
                for t in targets: visitor._add_target(t)
            elif isinstance(node, ast.ClassDef):
                visitor.defined_names.add(node.name)
            elif isinstance(node, (ast.For, ast.With)):
                # Handle top-level loops/withs
                pass 

        visitor.visit(tree)
    except SyntaxError as e:
        return PythonAnalysis(risk_flags=[f"Syntax Error: {e.msg} at line {e.lineno}"], ast_summary="Failed to parse Python code.")

    # Detect Undefined Symbols
    undefined = visitor.used_names - visitor.defined_names
    for name in undefined:
        if not name.startswith("__") and name.isidentifier():
            visitor.findings.append(f"Undefined variable or function reference: '{name}'")

    return PythonAnalysis(
        imports=sorted(set(visitor.imports)),
        functions=sorted(set(visitor.functions)),
        classes=sorted(set(visitor.classes)),
        api_calls=sorted(set(visitor.api_calls)),
        validators=sorted(set(visitor.validators)),
        risk_flags=visitor.findings,
        ast_summary=(
            f"Detected {len(visitor.functions)} functions, {len(visitor.classes)} classes, "
            f"and {len(visitor.findings)} critical code risks."
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

async def generate_ai_code_review(source: str) -> str:
    """
    Optional qualitative review using Groq.
    """
    from app.core.config import get_settings
    import httpx
    import json
    
    settings = get_settings()
    api_key = settings.groq_api_key
    if not api_key:
        return "AI Review skipped: No API Key."

    prompt = f"Review this Python code for logic errors and suggest improvements:\n\n{source[:2000]}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": settings.groq_model,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"AI Review Error: {e}"
