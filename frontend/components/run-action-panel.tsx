"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import type { AppRole } from "@/lib/session";
import type { QARunStatus } from "@/lib/types";

interface RunActionPanelProps {
  runId: string;
  role: AppRole;
  status: QARunStatus | string;
}

export function RunActionPanel({ runId, role, status }: RunActionPanelProps) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [message, setMessage] = useState<string | null>(null);

  const canApprove = role === "admin" && status === "approval_required";
  const canRetry = role === "admin" || role === "operator";

  const send = (path: string, payload: Record<string, string>) => {
    startTransition(async () => {
      setMessage(null);
      const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const result = (await response.json()) as { success?: boolean; detail?: string };
      if (!response.ok) {
        setMessage(result.detail ?? "Action failed.");
        return;
      }
      setMessage("Action completed.");
      router.refresh();
    });
  };

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <div className="eyebrow">Operator Actions</div>
          <h3>Approval and Retry Controls</h3>
        </div>
      </div>
      <div className="timeline-list">
        <button
          className="toolbar-select"
          disabled={!canRetry || isPending}
          onClick={() =>
            send(`/api/qa-runs/${runId}/retry`, {
              reason: "Manual retry triggered from frontend control panel."
            })
          }
          type="button"
        >
          {isPending ? "Working..." : "Retry Run"}
        </button>
        <button
          className="toolbar-select"
          disabled={!canApprove || isPending}
          onClick={() =>
            send(`/api/qa-runs/${runId}/approve`, {
              decision: "approved",
              rationale: "Approved from frontend control panel."
            })
          }
          type="button"
        >
          Approve Run
        </button>
        <button
          className="toolbar-select"
          disabled={!canApprove || isPending}
          onClick={() =>
            send(`/api/qa-runs/${runId}/approve`, {
              decision: "rejected",
              rationale: "Rejected from frontend control panel."
            })
          }
          type="button"
        >
          Reject Run
        </button>
        <div className="muted">
          Role: <strong>{role}</strong>
        </div>
        {message ? <div className="muted">{message}</div> : null}
      </div>
    </section>
  );
}
