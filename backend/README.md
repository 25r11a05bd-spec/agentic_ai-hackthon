# Autonomous AI QA Platform Backend

FastAPI control plane and orchestration layer for authenticated QA runs, playback, approvals, failure explanation, and memory-backed self-healing.

## Implemented Backend Surfaces

- `POST /api/v1/qa-runs`
- `GET /api/v1/qa-runs`
- `GET /api/v1/qa-runs/{id}`
- `GET /api/v1/qa-runs/{id}/graph`
- `GET /api/v1/qa-runs/{id}/playback`
- `GET /api/v1/qa-runs/{id}/report`
- `GET /api/v1/qa-runs/{id}/failure-explainer`
- `GET /api/v1/qa-runs/{id}/collaboration`
- `POST /api/v1/qa-runs/{id}/retry`
- `POST /api/v1/qa-runs/{id}/approve`
- `GET /api/v1/metrics/overview`
- `GET /api/v1/notifications/logs`
- `GET /health`
- `WS /ws/qa-runs/{id}`

## Core Flow

The execution graph is fixed:

```txt
ingest
  -> planner
  -> tool_router
  -> executor
  -> validator
  -> failure_explainer
  -> reflection
  -> self_heal_router
  -> retry_or_replan
  -> approval_gate
  -> memory_writer
  -> notifier
  -> finalizer
```

## Local Run

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Notes

- Clerk auth is supported through bearer-token verification, with `AUTH_DEV_MODE=true` enabling local role simulation.
- ChromaDB writes fall back to local JSON memory when a Chroma server is unavailable.
- Notifications are safely simulated when Twilio credentials are absent.
- The current implementation runs in-process after upload; the dedicated Redis worker split is the next backend evolution.
