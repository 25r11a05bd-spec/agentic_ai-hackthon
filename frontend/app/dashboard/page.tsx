import { AppShell } from "@/components/app-shell";
import { DashboardCharts } from "@/components/dashboard-charts";
import { StatCard } from "@/components/stat-card";
import { RunsHeader } from "@/components/runs/runs-header";
import { getMetrics, getNotificationLogs, getRuns } from "@/lib/api";
import { requireSession } from "@/lib/session";

export default async function DashboardPage() {
  const session = await requireSession(["admin", "operator", "viewer"]);
  const [metrics, notifications, runs] = await Promise.all([
    getMetrics(),
    getNotificationLogs(),
    getRuns()
  ]);

  return (
    <AppShell pathname="/dashboard">
      <div className="topbar">
        <div className="page-title">
          <h2>Autonomous QA Command Deck</h2>
          <p>
            Track self-healing runs, approval pressure, and agent contribution across the current
            validation fleet.
          </p>
        </div>
        <div className="badge-row">
          <div className="chip">
            <strong>{session.role}</strong> access
          </div>
          <div className="chip">
            <strong>{runs.length}</strong> active records
          </div>
          <div className="chip">
            <strong>{metrics.approval_queue}</strong> approvals pending
          </div>
        </div>
        <RunsHeader hideTitle />
      </div>

      <section className="stat-grid" style={{ marginBottom: 24 }}>
        <StatCard label="Total Runs" value={String(metrics.total_runs)} meta="Historical execution volume" />
        <StatCard
          label="Success Rate"
          value={`${metrics.success_rate}%`}
          meta="Autonomous completions within policy"
        />
        <StatCard
          label="Average Retries"
          value={metrics.average_retries.toFixed(1)}
          meta="Reflection loop pressure"
          tone="warning"
        />
        <StatCard
          label="Approval Queue"
          value={String(metrics.approval_queue)}
          meta="Runs awaiting human decision"
          tone="warning"
        />
      </section>

      <DashboardCharts metrics={metrics} notifications={notifications} />
    </AppShell>
  );
}
