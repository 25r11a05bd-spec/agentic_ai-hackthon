import { AppShell } from "@/components/app-shell";
import { RunActionPanel } from "@/components/run-action-panel";
import { RunDetailWorkspace } from "@/components/run-detail-workspace";
import { StatusPill } from "@/components/status-pill";
import { getCollaboration, getFailureExplainer, getGraph, getPlayback, getRun } from "@/lib/api";
import { requireSession } from "@/lib/session";

export default async function RunDetailPage({
  params
}: {
  params: Promise<{ id: string }>;
}) {
  const session = await requireSession(["admin", "operator", "viewer"]);
  const { id } = await params;
  const [run, graph, playback, failure, collaboration] = await Promise.all([
    getRun(id),
    getGraph(id),
    getPlayback(id),
    getFailureExplainer(id),
    getCollaboration(id)
  ]);

  return (
    <AppShell pathname="/runs">
      <div className="topbar">
        <div className="page-title">
          <h2>{run.id}</h2>
          <p>
            {run.project_file_name} + {run.workflow_file_name} · agent {run.current_agent} · risk{" "}
            {run.risk_level}
          </p>
        </div>
        <div className="badge-row">
          <StatusPill status={run.status} />
          <div className="chip">
            <strong>{run.scores.overall}</strong> overall
          </div>
          <div className="chip">
            <strong>{run.scores.hallucination_risk}</strong> hallucination risk
          </div>
        </div>
      </div>

      <div style={{ marginBottom: 24 }}>
        <RunActionPanel runId={run.id} role={session.role} status={run.status} />
      </div>

      <RunDetailWorkspace
        run={run}
        graph={graph}
        initialEvents={playback.events}
        failure={failure}
        collaboration={collaboration}
      />
    </AppShell>
  );
}
