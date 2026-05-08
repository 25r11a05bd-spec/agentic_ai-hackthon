# Autonomous Academic Intelligence System (AAIS)

## Frontend ↔ Backend API Contracts

Production-ready API request/response formats for the Agentic AI Automation Platform.

---

# BASE URLS

## Development

```txt
Frontend: http://localhost:3000
Backend:  http://localhost:8000
```

---

## Production

```txt
Frontend: https://your-app.vercel.app
Backend:  https://your-api.railway.app
```

---

# STANDARD API RESPONSE FORMAT

## Success Response

```json
{
  "success": true,
  "message": "Workflow started successfully",
  "data": {},
  "timestamp": "2026-05-08T10:30:00Z"
}
```

---

## Error Response

```json
{
  "success": false,
  "message": "Validation failed",
  "error": {
    "code": "MISSING_FIELDS",
    "details": ["marks"]
  },
  "timestamp": "2026-05-08T10:30:00Z"
}
```

---

# 1. START WORKFLOW

## Endpoint

```http
POST /api/v1/workflows/start
```

## Frontend Request

```json
{
  "workflow_name": "student_risk_analysis",
  "goal": "Analyze risky students and notify parents",
  "student_ids": [
    "STU101",
    "STU102"
  ],
  "options": {
    "send_whatsapp": true,
    "generate_pdf": true,
    "store_memory": true,
    "enable_reflection": true,
    "max_retries": 3
  }
}
```

## Backend Response

```json
{
  "success": true,
  "message": "Workflow execution started",
  "data": {
    "workflow_id": "wf_9ad82",
    "status": "running",
    "current_agent": "planner",
    "estimated_steps": 8,
    "started_at": "2026-05-08T10:30:00Z"
  }
}
```

---

# 2. GET WORKFLOW STATUS

## Endpoint

```http
GET /api/v1/workflows/{workflow_id}
```

## Backend Response

```json
{
  "success": true,
  "data": {
    "workflow_id": "wf_9ad82",
    "status": "running",
    "current_agent": "validator",
    "current_step": "Validating attendance response",
    "progress": 65,
    "retries": 1,
    "started_at": "2026-05-08T10:30:00Z",
    "updated_at": "2026-05-08T10:31:10Z"
  }
}
```

---

# 3. LIVE WORKFLOW STREAM (WEBSOCKET)

## Endpoint

```txt
ws://localhost:8000/ws/workflows
```

## Frontend Connection

```ts
const socket = new WebSocket(
  "ws://localhost:8000/ws/workflows"
)
```

## Live Message Format

```json
{
  "workflow_id": "wf_9ad82",
  "event_type": "agent_update",
  "agent": "executor",
  "step": "Calling marks API",
  "tool": "fetch_marks_api",
  "status": "running",
  "retry_count": 1,
  "timestamp": "2026-05-08T10:31:00Z"
}
```

## Validation Failure Event

```json
{
  "workflow_id": "wf_9ad82",
  "event_type": "validation_failed",
  "agent": "validator",
  "missing_fields": [
    "marks"
  ],
  "reflection_required": true,
  "timestamp": "2026-05-08T10:31:20Z"
}
```

## Reflection Event

```json
{
  "workflow_id": "wf_9ad82",
  "event_type": "reflection",
  "agent": "reflection",
  "reason": "Marks field missing",
  "proposed_fix": "Retry using fallback endpoint",
  "retry_number": 2,
  "timestamp": "2026-05-08T10:31:25Z"
}
```

## Success Event

```json
{
  "workflow_id": "wf_9ad82",
  "event_type": "workflow_completed",
  "status": "success",
  "report_url": "/reports/report_101.pdf",
  "notification_sent": true,
  "memory_saved": true,
  "timestamp": "2026-05-08T10:32:10Z"
}
```

---

# 4. GET LIVE EXECUTION LOGS

## Endpoint

```http
GET /api/v1/workflows/live
```

## Backend Response

```json
{
  "success": true,
  "data": [
    {
      "agent": "planner",
      "message": "Creating execution plan...",
      "status": "success",
      "timestamp": "2026-05-08T10:30:10Z"
    },
    {
      "agent": "executor",
      "message": "Calling attendance API...",
      "status": "running",
      "timestamp": "2026-05-08T10:30:20Z"
    }
  ]
}
```

---

# 5. RETRY WORKFLOW

## Endpoint

```http
POST /api/v1/workflows/retry/{workflow_id}
```

## Frontend Request

```json
{
  "reason": "Manual retry triggered by admin",
  "override_reflection": false
}
```

## Backend Response

```json
{
  "success": true,
  "message": "Workflow retry started",
  "data": {
    "workflow_id": "wf_9ad82",
    "retry_number": 2,
    "status": "running"
  }
}
```

---

# 6. GET WORKFLOW HISTORY

## Endpoint

```http
GET /api/v1/workflows/history
```

## Backend Response

```json
{
  "success": true,
  "data": [
    {
      "workflow_id": "wf_101",
      "workflow_name": "student_risk_analysis",
      "status": "success",
      "retries": 1,
      "duration_seconds": 42,
      "created_at": "2026-05-07T09:00:00Z"
    },
    {
      "workflow_id": "wf_102",
      "workflow_name": "marks_analysis",
      "status": "failed",
      "retries": 3,
      "duration_seconds": 120,
      "created_at": "2026-05-07T12:00:00Z"
    }
  ]
}
```

---

# 7. GET ALL STUDENTS

## Endpoint

```http
GET /api/v1/students
```

## Backend Response

```json
{
  "success": true,
  "data": [
    {
      "student_id": "STU101",
      "name": "Rahul",
      "attendance": 72,
      "marks": 35,
      "risk_score": 82,
      "risk_level": "high"
    },
    {
      "student_id": "STU102",
      "name": "Ananya",
      "attendance": 91,
      "marks": 88,
      "risk_score": 12,
      "risk_level": "low"
    }
  ]
}
```

---

# 8. GET RISKY STUDENTS

## Endpoint

```http
GET /api/v1/students/risky
```

## Backend Response

```json
{
  "success": true,
  "data": {
    "high_risk_count": 12,
    "medium_risk_count": 25,
    "students": [
      {
        "student_id": "STU101",
        "name": "Rahul",
        "attendance": 61,
        "marks": 28,
        "risk_score": 91,
        "recommendation": "Immediate academic counseling"
      }
    ]
  }
}
```

---

# 9. FILE UPLOAD (CSV/PDF)

## Endpoint

```http
POST /api/v1/students/upload
```

## Frontend Request

```ts
const formData = new FormData()

formData.append("file", file)
formData.append("type", "csv")
```

## Backend Response

```json
{
  "success": true,
  "message": "File uploaded successfully",
  "data": {
    "file_id": "file_92",
    "rows_processed": 120,
    "workflow_triggered": true
  }
}
```

---

# 10. SEND WHATSAPP

## Endpoint

```http
POST /api/v1/notifications/whatsapp
```

## Frontend Request

```json
{
  "phone": "+919999999999",
  "message": "High-risk student detected"
}
```

## Backend Response

```json
{
  "success": true,
  "message": "WhatsApp message sent",
  "data": {
    "sid": "SMX939393",
    "status": "queued"
  }
}
```

---

# 11. SEND SMS

## Endpoint

```http
POST /api/v1/notifications/sms
```

## Frontend Request

```json
{
  "phone": "+919999999999",
  "message": "Workflow completed successfully"
}
```

## Backend Response

```json
{
  "success": true,
  "message": "SMS sent successfully",
  "data": {
    "sid": "SM883882",
    "status": "sent"
  }
}
```

---

# 12. GET NOTIFICATION LOGS

## Endpoint

```http
GET /api/v1/notifications/logs
```

## Backend Response

```json
{
  "success": true,
  "data": [
    {
      "type": "whatsapp",
      "recipient": "+919999999999",
      "message": "High-risk student detected",
      "status": "delivered",
      "timestamp": "2026-05-08T10:33:00Z"
    }
  ]
}
```

---

# 13. GET AI INSIGHTS

## Endpoint

```http
GET /api/v1/analytics/insights
```

## Backend Response

```json
{
  "success": true,
  "data": {
    "summary": "Attendance decline detected among 2nd-year students.",
    "recommendations": [
      "Increase mentorship sessions",
      "Schedule parent meetings"
    ],
    "predictions": {
      "dropout_risk": 0.23,
      "improvement_probability": 0.74
    }
  }
}
```

---

# 14. GET WORKFLOW GRAPH DATA

## Endpoint

```http
GET /api/v1/workflows/graph/{workflow_id}
```

## Backend Response

```json
{
  "success": true,
  "data": {
    "nodes": [
      {
        "id": "planner",
        "label": "Planner",
        "status": "completed"
      },
      {
        "id": "executor",
        "label": "Executor",
        "status": "running"
      }
    ],
    "edges": [
      {
        "source": "planner",
        "target": "executor"
      }
    ]
  }
}
```

---

# FRONTEND API SERVICE LAYER

## lib/api.ts

```ts
const API_BASE =
  process.env.NEXT_PUBLIC_API_URL

export async function startWorkflow(data: any) {
  const response = await fetch(
    `${API_BASE}/api/v1/workflows/start`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data)
    }
  )

  return response.json()
}
```

---

# FRONTEND WEBSOCKET STORE

## Zustand Example

```ts
import { create } from "zustand"

interface WorkflowStore {
  logs: any[]
  addLog: (log: any) => void
}

export const useWorkflowStore =
  create<WorkflowStore>((set) => ({
    logs: [],
    addLog: (log) =>
      set((state) => ({
        logs: [...state.logs, log]
      }))
  }))
```

---

# BEST PRACTICE RESPONSE CODES

```txt
200 OK
201 Created
400 Bad Request
401 Unauthorized
404 Not Found
422 Validation Error
500 Internal Server Error
```

---

# IDEAL DEMO FLOW

1. User clicks Analyze Student Risk
2. Frontend calls POST /workflows/start
3. Backend creates LangGraph execution plan
4. Planner selects tools
5. Executor fetches APIs
6. Validator checks responses
7. Reflection retries failures
8. Notifications sent through Twilio
9. Memory stored in ChromaDB
10. Live updates streamed to frontend via WebSockets

---

# GITHUB README SUGGESTION

```md
# Autonomous Academic Intelligence System

Production-grade Agentic AI Automation Platform.

## Features
- LangGraph autonomous workflows
- Planner/Executor/Validator agents
- Reflection & retry loops
- ChromaDB memory
- Twilio WhatsApp alerts
- Live workflow visualization
- AI risk analytics
- Real-time WebSocket streaming

## Stack
- Next.js
- FastAPI
- LangGraph
- CrewAI
- Groq
- Supabase
- ChromaDB
- Twilio
```
