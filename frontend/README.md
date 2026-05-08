# Autonomous AI QA Platform Frontend

Planned Next.js 15 operations console for QA runs, playback, approvals, history, and settings.

## Target Surfaces

- `Dashboard`: KPI cards, trend charts, pie charts, alert feed.
- `Runs`: searchable list with status, retry, and risk filters.
- `Runs/[id]`: live console, playback timeline, execution graph, findings, failure explainer, self-heal history, artifacts.
- `Approvals`: review queue for high-risk or auto-fixed runs.
- `History`: similar failures and successful fix patterns.
- `Settings`: provider, thresholds, role-gated policy controls.

## Required Client Integrations

- Clerk auth with `admin`, `operator`, and `viewer` role-aware UI.
- REST consumption of `/api/v1/qa-runs*`, `/metrics/overview`, and `/notifications/logs`.
- WebSocket playback via `/ws/qa-runs/{id}`.
- Recharts pie/donut charts for categorical insight.
- React Flow for runtime topology and playback synchronization.

## Status

The frontend app shell has not been scaffolded yet in this repo. The backend contracts and env example are now aligned for that build-out.
