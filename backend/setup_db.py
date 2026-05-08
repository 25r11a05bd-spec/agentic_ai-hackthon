import os
import time
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Load environment variables
load_dotenv()

DB_URL = os.getenv("SUPABASE_DB_URL")

SQL_SCHEMA = """
-- 0. Drop existing tables to force schema refresh
DROP TABLE IF EXISTS public.notification_logs;
DROP TABLE IF EXISTS public.repair_strategies;
DROP TABLE IF EXISTS public.approvals;
DROP TABLE IF EXISTS public.collaboration;
DROP TABLE IF EXISTS public.failure_explanations;
DROP TABLE IF EXISTS public.playback_events;
DROP TABLE IF EXISTS public.snapshots;
DROP TABLE IF EXISTS public.findings;
DROP TABLE IF EXISTS public.qa_runs;

-- 1. QA Runs Table
CREATE TABLE IF NOT EXISTS public.qa_runs (
    id TEXT PRIMARY KEY,
    task TEXT NOT NULL,
    validation_mode TEXT NOT NULL,
    status TEXT NOT NULL,
    approval_status TEXT NOT NULL,
    current_agent TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    project_file_name TEXT,
    workflow_file_name TEXT,
    latest_state JSONB DEFAULT '{}',
    scores JSONB DEFAULT '{}',
    created_by TEXT,
    retries_used INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    retry_enabled BOOLEAN DEFAULT TRUE,
    notifications_enabled BOOLEAN DEFAULT TRUE
);

-- 2. Findings Table
CREATE TABLE IF NOT EXISTS public.findings (
    id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES public.qa_runs(id) ON DELETE CASCADE,
    severity TEXT DEFAULT 'medium',
    category TEXT,
    title TEXT,
    description TEXT,
    evidence JSONB DEFAULT '[]',
    affected_nodes JSONB DEFAULT '[]',
    recommendation TEXT,
    status TEXT DEFAULT 'open',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Snapshots Table
CREATE TABLE IF NOT EXISTS public.snapshots (
    id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES public.qa_runs(id) ON DELETE CASCADE,
    current_node TEXT,
    status_map JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Playback Events Table
CREATE TABLE IF NOT EXISTS public.playback_events (
    id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES public.qa_runs(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    agent TEXT NOT NULL,
    step TEXT NOT NULL,
    status TEXT NOT NULL,
    payload JSONB DEFAULT '{}',
    sequence INTEGER NOT NULL,
    tool TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Failure Explanations
CREATE TABLE IF NOT EXISTS public.failure_explanations (
    run_id TEXT PRIMARY KEY REFERENCES public.qa_runs(id) ON DELETE CASCADE,
    root_cause TEXT,
    evidence JSONB DEFAULT '[]',
    affected_nodes JSONB DEFAULT '[]',
    user_impact TEXT,
    why_previous_attempt_failed TEXT,
    recommended_fix TEXT
);

-- 6. Collaboration
CREATE TABLE IF NOT EXISTS public.collaboration (
    id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES public.qa_runs(id) ON DELETE CASCADE,
    agent TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    tools_used JSONB DEFAULT '[]',
    handoff_summary TEXT,
    risk_level TEXT,
    confidence FLOAT,
    dependencies JSONB DEFAULT '[]'
);

-- 7. Approvals
CREATE TABLE IF NOT EXISTS public.approvals (
    run_id TEXT PRIMARY KEY REFERENCES public.qa_runs(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending',
    recommended_action TEXT,
    rationale TEXT,
    updated_at TIMESTAMPTZ,
    decided_by TEXT
);

-- 8. Repair Strategies
CREATE TABLE IF NOT EXISTS public.repair_strategies (
    id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES public.qa_runs(id) ON DELETE CASCADE,
    title TEXT,
    strategy_type TEXT,
    rationale TEXT,
    steps JSONB DEFAULT '[]',
    memory_similarity FLOAT,
    prior_success_rate FLOAT,
    safety_score FLOAT,
    selected BOOLEAN DEFAULT FALSE,
    fixed_code TEXT,
    explanation TEXT,
    evidence JSONB DEFAULT '[]'
);

-- 9. Notification Logs
CREATE TABLE IF NOT EXISTS public.notification_logs (
    id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES public.qa_runs(id) ON DELETE CASCADE,
    channel TEXT NOT NULL,
    recipient TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT NOT NULL,
    provider_sid TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Refresh schema cache
NOTIFY pgrst, 'reload schema';
"""

from urllib.parse import urlparse, unquote

def setup_database():
    if not DB_URL:
        print("❌ Error: SUPABASE_DB_URL not found in .env")
        return

    print(f"🚀 Connecting to Supabase Database...")
    try:
        # Manual parsing because urlparse fails on square brackets in passwords
        # Format: postgresql://user:password@host:port/dbname
        
        # 1. Remove prefix
        core = DB_URL.replace("postgresql://", "")
        
        # 2. Split userinfo and hostinfo
        userinfo, hostinfo = core.rsplit("@", 1)
        user, password = userinfo.split(":", 1)
        
        # 3. Split host, port, and db
        host_and_port, dbname = hostinfo.split("/", 1)
        host, port = host_and_port.split(":", 1)

        # Unquote the password to handle % characters
        password = unquote(password)

        # Connect using the parsed components
        conn = psycopg2.connect(
            database=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        print("🛠️  Applying schema and fixing columns...")
        cur.execute(SQL_SCHEMA)
        
        print("✅ Database setup complete!")
        print("✨ All tables created and columns verified.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print("\n💡 TIP: Your password in .env might have special characters.")
        print("Try wrapping your password in your .env file with double quotes if it isn't already.")
        print("Example: SUPABASE_DB_URL=\"postgresql://postgres:password@host:5432/postgres\"")

if __name__ == "__main__":
    setup_database()
