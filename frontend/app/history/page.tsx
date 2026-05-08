import { AppShell } from "@/components/app-shell";
import { getMetrics, getRuns } from "@/lib/api";
import { requireSession } from "@/lib/session";

export default async function HistoryPage() {
  await requireSession(["admin", "operator", "viewer"]);
  const [metrics, runs] = await Promise.all([getMetrics(), getRuns()]);

  return (
    <AppShell pathname="/history">
      <div className="topbar">
        <div className="page-title">
          <h2>Historical Memory</h2>
          <p>
            Review trend movement, high-risk recurrence, and which agent patterns most often lead to
            recovery or approval pauses.
          </p>
        </div>
      </div>

      <div className="history-grid">
        <section className="panel">
          <div className="section-heading">
            <div>
              <div className="eyebrow">Similarity Memory</div>
              <h3>Recent Risk Patterns</h3>
            </div>
          </div>
          <div className="timeline-list">
            {runs.map((run) => (
              <div className="history-item" key={run.id}>
                <strong>{run.id}</strong>
                <div>
                  {run.status} · risk {run.risk_level} · score {run.scores.overall}
                </div>
                <small className="muted">
                  validation {run.scores.validation} · hallucination {run.scores.hallucination_risk}
                </small>
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="section-heading">
            <div>
              <div className="eyebrow">Agent Patterning</div>
              <h3>Contribution Snapshot</h3>
            </div>
          </div>
          <div className="timeline-list">
            {metrics.agent_contribution.map((item) => (
              <div className="history-item" key={item.agent}>
                <strong>{item.agent}</strong>
                <div>{item.share}% contribution share</div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </AppShell>
  );
}
