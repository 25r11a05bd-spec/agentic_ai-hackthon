# Autonomous Academic Intelligence System (Backend)

Production-grade autonomous AI workflow engine using LangGraph.

---

# Features

* Planner agent
* Executor agent
* Validator agent
* Reflection agent
* Autonomous retries
* Memory storage
* Twilio notifications
* Real-time WebSockets
* LangGraph orchestration
* ChromaDB vector memory
* Groq + Ollama support

---

# Tech Stack

* FastAPI
* Python 3.12
* LangGraph
* CrewAI
* Groq API
* Ollama
* Supabase PostgreSQL
* ChromaDB
* Twilio API
* Docker

---

# Folder Structure

```txt
backend/
│
├── app/
│   ├── agents/
│   ├── api/
│   ├── workflows/
│   ├── tools/
│   ├── memory/
│   ├── database/
│   ├── services/
│   ├── schemas/
│   └── utils/
│
├── requirements.txt
├── Dockerfile
├── railway.json
└── .env.example
```

---

# Installation

## Clone Repository

```bash
git clone https://github.com/your-username/agentic-ai-platform.git
cd backend
```

---

# Create Virtual Environment

## Windows

```bash
python -m venv venv
venv\Scripts\activate
```

## Linux/Mac

```bash
python3 -m venv venv
source venv/bin/activate
```

---

# Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create:

```txt
.env
```

Add:

```env
GROQ_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434

SUPABASE_URL=
SUPABASE_KEY=
DATABASE_URL=

TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
TWILIO_WHATSAPP_NUMBER=

CHROMA_DB_DIR=./chroma

FRONTEND_URL=http://localhost:3000
```

---

# Run Backend Server

```bash
uvicorn app.main:app --reload
```

Backend runs at:

```txt
http://localhost:8000
```

---

# API Documentation

Swagger Docs:

```txt
http://localhost:8000/docs
```

ReDoc:

```txt
http://localhost:8000/redoc
```

---

# Main Workflow Architecture

```txt
PLAN
 ↓
TOOL SELECTION
 ↓
EXECUTION
 ↓
VALIDATION
 ↓
REFLECTION
 ↓
RETRY
 ↓
SUCCESS
```

---

# API Endpoints

## Workflows

```txt
POST   /api/v1/workflows/start
GET    /api/v1/workflows/{id}
GET    /api/v1/workflows/live
POST   /api/v1/workflows/retry/{id}
GET    /api/v1/workflows/history
```

---

## Students

```txt
GET    /api/v1/students
GET    /api/v1/students/risky
POST   /api/v1/students/upload
```

---

## Notifications

```txt
POST   /api/v1/notifications/whatsapp
POST   /api/v1/notifications/sms
GET    /api/v1/notifications/logs
```

---

# WebSocket Endpoint

```txt
ws://localhost:8000/ws/workflows
```

---

# Docker Support

## Build Docker Image

```bash
docker build -t agentic-ai-backend .
```

## Run Container

```bash
docker run -p 8000:8000 agentic-ai-backend
```

---

# Railway Deployment

## railway.json

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
  }
}
```

---

# Recommended Python Packages

```bash
pip install fastapi uvicorn langgraph crewai chromadb sqlalchemy asyncpg twilio httpx pydantic python-dotenv
```

---

# License

MIT License
