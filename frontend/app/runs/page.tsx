import { AppShell } from "@/components/app-shell";
import { RunsTable } from "@/components/runs-table";
import { RunsHeader } from "@/components/runs/runs-header";
import { getRuns } from "@/lib/api";
import { requireSession } from "@/lib/session";

export default async function RunsPage() {
  await requireSession(["admin", "operator", "viewer"]);
  const runs = await getRuns();

  return (
    <AppShell pathname="/runs">
      <RunsHeader />
      <RunsTable runs={runs} />
    </AppShell>
  );
}
