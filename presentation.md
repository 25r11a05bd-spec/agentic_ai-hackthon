# 🚀 Agenetic AI: The Autonomous QA Control Room

## 🎙️ The Elevator Pitch
"We’ve built a **Playback-First Validation Control Room** that replaces traditional manual testing with a fleet of autonomous AI QA Engineers. It doesn't just find bugs; it understands them, runs them in a safe sandbox, and implements **Self-Healing Patches** to fix codebases autonomously."

---

## 🏗️ The Tech Stack (Our Secret Sauce)

### 1. **Groq (The Brain)**
*   **Use**: Powers our Agent Fleet (Llama 3.3).
*   **Performance**: Makes ~5 specialized AI calls per QA run cycle.
*   **Why**: Ultra-fast inference (token generation) allows our agents to "think," "plan," and "patch" in milliseconds, making the autonomous loop feel instantaneous.

### 2. **Supabase (The Core)**
*   **Use**: Real-time database and secure artifact storage.
*   **Why**: Handles persistence for every QA run and stores source code artifacts. It keeps the UI perfectly synced with the backend worker via real-time listeners.

### 3. **ChromaDB (The Memory)**
*   **Use**: Vector database for "Long-Term Failure Memory."
*   **Why**: Every time a bug is found or a fix is successful, it's stored here. The system "remembers" past failures and ranks remediation strategies based on historical success rates.

### 4. **ARQ & Redis (The Distributed Engine)**
*   **Use**: Production-grade Job Queue.
*   **Why**: Decouples API requests from heavy AI execution. This ensures the platform remains responsive while background workers coordinate complex agentic graphs across multiple threads.

### 5. **Next.js & WebSockets (The Window)**
*   **Use**: Futuristic, Glassmorphic UI.
*   **Why**: Provides a real-time dashboard that streams "live thoughts" and execution logs directly from the AI agents as they traverse the QA graph.

---

## 🔄 The 5-Step Autonomous Workflow

### 1. **Ingest & Plan**
The AI Strategist analyzes the task and code architecture to build a custom execution plan. It doesn't use a template; it tailors the plan to the specific source code structure.

### 2. **Hybrid Static Analysis (AST)**
We use **Abstract Syntax Trees (AST)** to detect "Code Smells," security risks (SQLi, SSRF), and logic flaws. We verify undefined symbols and unsafe calls before execution even begins.

### 3. **Isolated Sandbox Execution**
We spin up a **Real, Isolated Environment** to execute the code. We capture real crashes, stdout/stderr, and runtime behavior to provide "Grounded" evidence for every finding.

### 4. **Grounded AI Validation**
The AI Validator takes sandbox results and static findings to calculate a **Quality Score (0-100)**. It cross-references runtime evidence to ensure zero hallucinations in the report.

### 5. **Autonomous Self-Healing Loop**
If quality scores fall below threshold, the **Repair Agent** applies a specific code patch. The system then **automatically re-runs the entire pipeline** to verify the fix works before proposing it to the user.

---

## 🌟 Key Features for Judges

*   **Closed-Loop Verification**: Our AI doesn't just "guess" a fix; it applies it in the sandbox and reruns the tests to prove the fix is valid.
*   **Hallucination Guard**: Every AI claim is backed by actual runtime logs or AST node evidence.
*   **Premium Executive Reporting**: Generates high-fidelity PDF reports with "Slate" aesthetics, featuring deep root-cause analysis and verifiable code patches.
*   **Human-in-the-Loop**: An **Approval Gate** ensures humans have the final say before any AI-generated patch is committed to the main branch.

---

## 💡 The "Why Now?"
As development speed increases, manual QA has become the primary bottleneck. **Agenetic AI** turns QA from a slow "human bottleneck" into a fast, autonomous, and self-improving engine.

**"We don't just find bugs. We automate the entire lifecycle of trust."**
