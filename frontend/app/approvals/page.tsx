import Link from "next/link";

import { AppShell } from "@/components/app-shell";
import { RunActionPanel } from "@/components/run-action-panel";
import { StatusPill } from "@/components/status-pill";
import { getRuns } from "@/lib/api";
import { requireSession } from "@/lib/session";

export default async function ApprovalsPage() {
  const session = await requireSession(["admin"]);
  const runs = await getRuns();
  const pending = runs.filter(
    (run) => run.approval_status === "pending" || run.status === "approval_required"
  );

  return (
    <AppShell pathname="/approvals">
      <div className="topbar">
        <div className="page-title">
          <h2>Approval Queue</h2>
          <p>
            High-risk or auto-fixed runs land here when scores, retries, or fallback use cross the
            policy threshold.
          </p>
        </div>
      </div>

      <section className="panel">
        <div className="section-heading">
          <div>
            <div className="eyebrow">Pending Decisions</div>
            <h3>Go / No-Go Review</h3>
          </div>
        </div>
        <div className="approval-list">
          {pending.map((run) => (
            <div className="approval-item" key={run.id}>
              <div className="section-heading" style={{ marginBottom: 0 }}>
                <div>
                  <strong>{run.id}</strong>
                  <div className="muted">{run.task}</div>
                </div>
                <StatusPill status={run.status} />
              </div>
              <p>
                Validation {run.scores.validation} · Hallucination risk {run.scores.hallucination_risk}
                {" · "}
                Retries {run.retries_used}/{run.max_retries}
              </p>
              <div style={{ marginBottom: 12 }}>
                <RunActionPanel runId={run.id} role={session.role} status={run.status} />
              </div>
              <Link className="small-link" href={`/runs/${run.id}`}>
                Open playback and failure evidence
              </Link>
            </div>
          ))}
          {!pending.length && (
            <div className="approval-item">No runs are currently waiting for approval.</div>
          )}
        </div>
      </section>
    </AppShell>
  );
}
