from __future__ import annotations

from pathlib import Path

from app.schemas.qa_run import FailureExplanation, PlaybackEvent, QARunDetail, QualityReportSummary, WorkflowFinding

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except ImportError:  # pragma: no cover
    canvas = None
    letter = None


def _format_findings(findings: list[WorkflowFinding]) -> str:
    if not findings:
        return "No findings were generated."

    lines = []
    for finding in findings:
        lines.append(f"- [{finding.severity}] {finding.title}: {finding.description}")
    return "\n".join(lines)


def _format_events(events: list[PlaybackEvent]) -> str:
    if not events:
        return "No playback events were recorded."

    lines = []
    for event in events[-10:]:
        lines.append(f"- {event.timestamp.isoformat()} {event.agent}: {event.step} ({event.status})")
    return "\n".join(lines)


def generate_markdown_report(
    run: QARunDetail,
    quality_summary: QualityReportSummary,
    failure_explanation: FailureExplanation | None,
) -> str:
    explanation = "No failure explanation required."
    if failure_explanation:
        explanation = (
            f"Root cause: {failure_explanation.root_cause}\n\n"
            f"User impact: {failure_explanation.user_impact}\n\n"
            f"Recommended fix: {failure_explanation.recommended_fix}"
        )

    return (
        f"# QA Run {run.id}\n\n"
        f"Status: `{run.status}`\n\n"
        f"Task: {run.task}\n\n"
        f"Overall score: **{run.scores.overall}/100**\n\n"
        f"## Summary\n\n{quality_summary.summary}\n\n"
        f"## Findings\n\n{_format_findings(run.findings)}\n\n"
        f"## Failure Explainer\n\n{explanation}\n\n"
        f"## Playback Highlights\n\n{_format_events(run.playback)}\n"
    )


def generate_pdf_report(markdown: str, output_path: Path) -> str | None:
    if canvas is None or letter is None:  # pragma: no cover
        return None

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter
    y = height - 50

    for raw_line in markdown.splitlines():
        line = raw_line[:110]
        pdf.drawString(40, y, line)
        y -= 14
        if y < 50:
            pdf.showPage()
            y = height - 50

    pdf.save()
    return str(output_path)
