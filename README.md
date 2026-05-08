# 🛠️ Agenetic AI: The Self-Healing Autonomous QA Engineer

> **Winner-Grade Autonomous Infrastructure for Enterprise-Scale QA Validation.**

Agenetic AI is not just a testing tool—it is an autonomous agentic engine that **Plans, Executes, Validates, and Remediates** software workflows. By combining advanced AST analysis with RAG-driven memory, it discovers bugs, understands root causes, and **self-heals source code** autonomously.

---

## 🚀 The Core Innovation: "Autonomous Remediation"
Traditional QA finds bugs. **Agenetic AI kills them.**
When a workflow fails, the engine enters a **Reflection Phase**:
1.  **RAG Lookup**: Queries **ChromaDB** for past successful patches of similar failures.
2.  **Root Cause Analysis**: Uses **Groq (Llama-3.1-70B)** to reflect on stack traces and AST findings.
3.  **Source Patching**: Generates an atomic code patch, overwrites the target `app.py`, and re-triggers the validation loop until the system is "healed."

---

## 🧠 Advanced Engineering Features
*   **DAG Graph Intelligence**: Pre-execution analysis to detect infinite cycles, unreachable nodes, and unanchored logic in workflow graphs.
*   **Geometric Severity Scoring**: A non-linear risk engine that penalizes architectural risks (security/control flow) more heavily than cosmetic issues.
*   **Route-Isolated Sandboxing**: Uses FastAPI's `TestClient` to perform route-discovery and probe API endpoints in isolation, preventing cascading runtime failures.
*   **Recursive Scope Tracking**: An AST-based analyzer that eliminates false-positive undefined variable alerts by tracking local and global lexical scopes.

---

## 🛠️ The Tech Stack
| Layer | Technology |
| :--- | :--- |
| **Brain** | Groq (Llama-3.1-70B) + Ollama (Llama-3.1-8B) |
| **Memory** | ChromaDB (Vector Search / RAG) |
| **Backend** | FastAPI (Python 3.11) + ARQ (Async Job Queue) |
| **Persistence** | Supabase (PostgreSQL) |
| **Frontend** | Next.js 14 (App Router) + TypeScript + TailwindCSS |
| **Alerts** | Twilio (WhatsApp/SMS) + Real-time WebSockets |
| **Reporting** | ReportLab (HVD PDF Generation) |

---

## 📊 Quality Scoring Engine
We don't do pass/fail. We do **Weighted Quality Matrices**:
*   **Reliability (40%)**: Static Stability + Runtime Health.
*   **Validation (30%)**: Business Logic Coverage.
*   **Grounding (20%)**: Hallucination & Risk Detection.
*   **Resilience (10%)**: Self-Healing Success Rate.

---

**Built with 💜 for Hackathon Excellence.**
