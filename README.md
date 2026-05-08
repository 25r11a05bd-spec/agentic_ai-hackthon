# Autonomous AI QA Platform

Monorepo for an internal AI QA operations platform with authenticated file uploads, autonomous workflow validation, evidence-backed failure explanation, playback, approvals, and memory-driven self-healing.

## Current Structure

- `backend/`: FastAPI control plane, run orchestration services, analysis tools, memory helpers, and tests.
- `frontend/`: Next.js app space for dashboard, runs, approvals, history, and settings surfaces.
- `endpoints.md`: v1 API and WebSocket contract summary.

## V1 Flow

1. Upload `app.py` and `automation.json`.
2. Run the fixed execution graph:
   `ingest -> planner -> tool_router -> executor -> validator -> failure_explainer -> reflection -> self_heal_router -> retry_or_replan -> approval_gate -> memory_writer -> notifier -> finalizer`
3. Persist findings, playback events, snapshots, collaboration traces, approval records, and reports.
4. Surface live progress over REST + WebSocket.

## Status

The backend foundation is now implemented as a runnable FastAPI service around the QA run lifecycle. The frontend application shell and the dedicated Redis worker/service split still need to be built out on top of these contracts.
