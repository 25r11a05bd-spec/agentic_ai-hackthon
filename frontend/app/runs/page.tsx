import { AppShell } from "@/components/app-shell";
import { RunsTable } from "@/components/runs-table";
import { getRuns } from "@/lib/api";
import { requireSession } from "@/lib/session";

export default async function RunsPage() {
  await requireSession(["admin", "operator", "viewer"]);
  const runs = await getRuns();

  return (
    <AppShell pathname="/runs">
      <div className="topbar">
        <div className="page-title">
          <h2>Run Inventory</h2>
          <p>
            Search execution records by status, task, and file identity, then drill into playback
            for the exact retry and approval story.
          </p>
        </div>
      </div>

      <RunsTable runs={runs} />
    </AppShell>
  );
}
