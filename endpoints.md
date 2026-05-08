# Autonomous AI QA Platform API Contracts

## Create Run

`POST /api/v1/qa-runs`

Multipart form fields:

- `project_file`
- `workflow_file`
- `attachments[]` optional
- `task`
- `validation_mode`
- `retry_enabled`
- `notifications_enabled`
- `max_retries`

## Read Models

- `GET /api/v1/qa-runs`
- `GET /api/v1/qa-runs/{id}`
- `GET /api/v1/qa-runs/{id}/graph`
- `GET /api/v1/qa-runs/{id}/playback`
- `GET /api/v1/qa-runs/{id}/report`
- `GET /api/v1/qa-runs/{id}/failure-explainer`
- `GET /api/v1/qa-runs/{id}/collaboration`
- `GET /api/v1/metrics/overview`
- `GET /api/v1/notifications/logs`

## Mutations

- `POST /api/v1/qa-runs/{id}/retry`
- `POST /api/v1/qa-runs/{id}/approve`

## WebSocket

`/ws/qa-runs/{id}`

Primary event types:

- `run_started`
- `agent_log`
- `node_state_changed`
- `finding_created`
- `failure_explained`
- `self_heal_suggested`
- `self_heal_applied`
- `retry_scheduled`
- `approval_required`
- `notification_sent`
- `memory_saved`
- `run_completed`

## Approval Policy

Approval is required when:

- validation score `< 85`
- hallucination risk `> 25`
- configured retries are exhausted
- self-heal changes the interpreted execution path
- a fallback provider or endpoint is used to achieve success
