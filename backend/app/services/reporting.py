from __future__ import annotations

from pathlib import Path

from app.schemas.qa_run import FailureExplanation, PlaybackEvent, QARunDetail, QualityReportSummary, WorkflowFinding

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_CENTER
except ImportError:  # pragma: no cover
    canvas = None
    letter = None
    SimpleDocTemplate = None

def _format_findings(findings: list[WorkflowFinding]) -> str:
    if not findings:
        return "No findings were generated."

    lines = []
    for finding in findings:
        lines.append(f"- **[{finding.severity.upper()}]** {finding.title}: {finding.description}")
    return "\n".join(lines)


def _format_events(events: list[PlaybackEvent]) -> str:
    if not events:
        return "No playback events were recorded."

    lines = []
    for event in events[-15:]:
        lines.append(f"- `{event.timestamp.strftime('%H:%M:%S')}` **{event.agent}**: {event.step} ({event.status})")
    return "\n".join(lines)


def generate_markdown_report(
    run: QARunDetail,
    quality_summary: QualityReportSummary,
    failure_explanation: FailureExplanation | None,
) -> str:
    explanation = "No failure explanation required."
    if failure_explanation:
        explanation = (
            f"### Root Cause Analysis\n{failure_explanation.root_cause}\n\n"
            f"**User Impact:** {failure_explanation.user_impact}\n\n"
            f"**Recommended Fix:** {failure_explanation.recommended_fix}"
        )

    repairs = ""
    if run.repair_strategies:
        repairs = "\n## 🛠️ Proposed Repairs & Autonomous Patches\n"
        for strategy in run.repair_strategies:
            repairs += f"\n### Strategy: {strategy.title}\n"
            repairs += f"**Safety Score:** {strategy.safety_score * 100:.1f}%\n"
            repairs += f"**Reasoning:** {strategy.rationale}\n"
            if strategy.fixed_code:
                repairs += "\n#### Suggested Code Patch:\n"
                repairs += f"```python\n{strategy.fixed_code}\n```\n"

    return (
        f"# QA Run Report: {run.id}\n\n"
        f"## 📊 Executive Quality Summary\n"
        f"**Overall Quality Score:** `{quality_summary.scores.overall}/100` \n"
        f"**Current Status:** `{run.status.upper()}`\n\n"
        f"### 🛡️ Core Metrics Breakdown\n"
        f"- **Reliability Score:** `{quality_summary.scores.reliability}/100` (Static & Runtime Stability)\n"
        f"- **Validation Score:** `{quality_summary.scores.validation}/100` (Business Logic Coverage)\n"
        f"- **Hallucination Risk:** `{quality_summary.scores.hallucination_risk}/100` (Ungrounded Logic Detectors)\n"
        f"- **Resilience Health:** `{quality_summary.scores.retry_health}/100` (Error Handling & Retries)\n\n"
        f"## 🔍 Critical Security & Logic Findings\n\n"
        f"{_format_findings(run.findings)}\n\n"
        f"## 🧠 Autonomous Failure Explainer\n\n"
        f"{explanation}\n\n"
        f"## 📜 Agent Execution Timeline\n\n"
        f"{_format_events(run.playback)}\n"
        f"{repairs}"
    )

import re

def generate_pdf_report(markdown: str, output_path: Path) -> str | None:
    if SimpleDocTemplate is None:  # pragma: no cover
        return None

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )
    styles = getSampleStyleSheet()
    
    # Custom Styled Definitions
    title_style = styles["Title"]
    title_style.fontSize = 24
    title_style.spaceAfter = 20
    
    h1_style = styles["Heading1"]
    h1_style.fontSize = 16
    h1_style.spaceBefore = 12
    h1_style.spaceAfter = 10
    h1_style.textColor = "navy"
    
    h2_style = styles["Heading2"]
    h2_style.fontSize = 12
    h2_style.spaceBefore = 8
    
    body_style = styles["Normal"]
    body_style.fontSize = 10
    body_style.leading = 14
    
    list_style = ParagraphStyle(
        "ListStyle",
        parent=body_style,
        leftIndent=20,
        firstLineIndent=0,
        spaceBefore=4,
        bulletFontName="Helvetica"
    )

    code_style = ParagraphStyle(
        "CodeStyle",
        parent=body_style,
        fontName="Courier",
        fontSize=9,
        leftIndent=15,
        rightIndent=15,
        backColor="#f4f4f4",
        borderPadding=5,
        leading=12
    )

    elements = []

    in_code_block = False
    code_content = []

    for line in markdown.splitlines():
        # Handle Code Block Toggles
        if line.strip().startswith("```"):
            if in_code_block:
                # Close block and render
                elements.append(Paragraph("<br/>".join(code_content), code_style))
                code_content = []
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            # Escape HTML characters in code
            escaped = line.replace("<", "&lt;").replace(">", "&gt;")
            code_content.append(f"<font name='Courier'>{escaped}</font>")
            continue

        line = line.strip()
        if not line:
            elements.append(Spacer(1, 8))
            continue
        
        # Robust Regex for Bold: **text** -> <b>text</b>
        processed_line = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", line)
        # Regex for Inline Code: `text` -> <i>text</i>
        processed_line = re.sub(r"`(.*?)`", r"<i>\1</i>", processed_line)
        
        if line.startswith("# "):
            elements.append(Paragraph(processed_line[2:], title_style))
        elif line.startswith("## "):
            elements.append(Paragraph(processed_line[3:], h1_style))
        elif line.startswith("### "):
            elements.append(Paragraph(processed_line[4:], h2_style))
        elif line.startswith("- "):
            elements.append(Paragraph(processed_line[2:], list_style))
        else:
            elements.append(Paragraph(processed_line, body_style))

    try:
        doc.build(elements)
        return str(output_path)
    except Exception as e:
        print(f"PDF Build Error: {e}")
        return None
