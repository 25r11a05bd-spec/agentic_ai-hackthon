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
    repairs = ""
    if run.repair_strategies:
        repairs = "\n\n### 🛠️ Autonomous Repair Strategies\n"
        for strategy in run.repair_strategies:
            repairs += f"\n#### Strategy: {strategy.title}\n"
            repairs += f"- **Safety Score:** {strategy.safety_score * 100:.1f}%\n"
            repairs += f"- **Rationale:** {strategy.rationale}\n"
            if strategy.fixed_code:
                repairs += "\n**Suggested Code Patch:**\n"
                # Use quadruple backticks or alternate wrapping to avoid collisions with triple backticks in code
                repairs += f"```python\n{strategy.fixed_code.strip()}\n```\n"

    explanation = "No failure explanation required."
    if failure_explanation:
        explanation = (
            f"### Root Cause Analysis\n{failure_explanation.root_cause}\n\n"
            f"**User Impact:** {failure_explanation.user_impact}\n\n"
            f"**Recommended Fix:** {failure_explanation.recommended_fix}"
            f"{repairs}"
        )
    elif repairs:
        explanation = f"While the run passed basic validation, the following improvements were autonomously identified:\n{repairs}"

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
    h1_style.fontSize = 18
    h1_style.spaceBefore = 20
    h1_style.spaceAfter = 12
    h1_style.textColor = "#1e293b" # Slate 800
    
    h2_style = styles["Heading2"]
    h2_style.fontSize = 15
    h2_style.spaceBefore = 15
    h2_style.spaceAfter = 8
    h2_style.textColor = "#334155" # Slate 700
    
    h3_style = ParagraphStyle(
        "Heading3",
        parent=styles["Heading3"],
        fontSize=13,
        spaceBefore=12,
        spaceAfter=6,
        textColor="#475569", # Slate 600
        fontName="Helvetica-Bold"
    )

    h4_style = ParagraphStyle(
        "Heading4",
        parent=styles["Heading3"],
        fontSize=11,
        spaceBefore=10,
        spaceAfter=4,
        textColor="#64748b", # Slate 500
        fontName="Helvetica-Bold"
    )

    body_style = styles["Normal"]
    body_style.fontSize = 10
    body_style.leading = 14
    body_style.textColor = "#334155"
    
    list_style = ParagraphStyle(
        "ListStyle",
        parent=body_style,
        leftIndent=20,
        firstLineIndent=0,
        spaceBefore=6,
        bulletFontName="Helvetica"
    )

    code_style = ParagraphStyle(
        "CodeStyle",
        parent=body_style,
        fontName="Courier",
        fontSize=9,
        leftIndent=15,
        rightIndent=15,
        backColor="#f8fafc", # Slate 50
        borderColor="#e2e8f0", # Slate 200
        borderWidth=0.5,
        borderPadding=10,
        leading=12,
        spaceBefore=10,
        spaceAfter=10
    )

    elements = []

    in_code_block = False
    code_content = []

    for line in markdown.splitlines():
        # Handle Code Block Toggles
        if line.strip().startswith("```"):
            if in_code_block:
                # Close block and render
                content = "<br/>".join(code_content)
                elements.append(Paragraph(content, code_style))
                code_content = []
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            # Preserve indentation but allow wrapping:
            # Replace leading spaces with &nbsp; and subsequent spaces with regular spaces
            stripped = line.lstrip(" ")
            indent_count = len(line) - len(stripped)
            indent = "&nbsp;" * indent_count
            escaped = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            code_content.append(f"<code>{indent}{escaped}</code>")
            continue

        line_strip = line.strip()
        if not line_strip:
            elements.append(Spacer(1, 10))
            continue
        
        # Robust Regex for Bold: **text** -> <b>text</b>
        processed_line = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", line_strip)
        # Regex for Inline Code: `text` -> <font name='Courier' color='#0f172a'>\1</font>
        processed_line = re.sub(r"`(.*?)`", r"<font name='Courier' color='#0f172a'>\1</font>", processed_line)
        
        if line_strip.startswith("# "):
            elements.append(Paragraph(processed_line[2:], title_style))
        elif line_strip.startswith("## "):
            elements.append(Paragraph(processed_line[3:], h1_style))
        elif line_strip.startswith("### "):
            elements.append(Paragraph(processed_line[4:], h2_style))
        elif line_strip.startswith("#### "):
            elements.append(Paragraph(processed_line[5:], h3_style))
        elif line_strip.startswith("##### "):
            elements.append(Paragraph(processed_line[6:], h4_style))
        elif line_strip.startswith("- "):
            elements.append(Paragraph(processed_line[2:], list_style))
        else:
            elements.append(Paragraph(processed_line, body_style))

    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor("#94a3b8") # Slate 400
        canvas.drawCentredString(letter[0]/2, 30, "Generated by Autonomous QA Platform | Confidential AI Analysis")
        canvas.restoreState()

    try:
        doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
        return str(output_path)
    except Exception as e:
        print(f"PDF Build Error: {e}")
        return None
