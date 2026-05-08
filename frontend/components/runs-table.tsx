"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Download, FileText } from "lucide-react";

import { StatusPill } from "@/components/status-pill";
import type { QARunRecord } from "@/lib/types";

export function RunsTable({ runs }: { runs: QARunRecord[] }) {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");

  const filtered = useMemo(() => {
    return runs.filter((run) => {
      const matchesStatus = status === "all" || run.status === status;
      const haystack = `${run.id} ${run.task} ${run.project_file_name} ${run.workflow_file_name}`.toLowerCase();
      const matchesSearch = haystack.includes(search.toLowerCase());
      return matchesStatus && matchesSearch;
    });
  }, [runs, search, status]);

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <div className="eyebrow">Runs</div>
          <h3>Execution Queue</h3>
        </div>
      </div>

      <div className="filter-row" style={{ gridTemplateColumns: "2fr 1fr" }}>
        <input
          className="toolbar-input"
          placeholder="Search by id, task, or file name"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <select className="toolbar-select" value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="all">All statuses</option>
          <option value="queued">Queued</option>
          <option value="running">Running</option>
          <option value="approval_required">Approval required</option>
          <option value="success">Success</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      <table className="table" style={{ marginTop: 18 }}>
        <thead>
          <tr>
            <th>Run</th>
            <th>Status</th>
            <th>Risk</th>
            <th>Retries</th>
            <th>Scores</th>
            <th>Updated</th>
            <th>Reports</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((run) => (
            <tr key={run.id}>
              <td>
                <Link className="small-link" href={`/runs/${run.id}`}>
                  {run.id}
                </Link>
                <br />
                <small>{run.task}</small>
              </td>
              <td>
                <StatusPill status={run.status} />
              </td>
              <td>{run.risk_level}</td>
              <td>
                {run.retries_used} / {run.max_retries}
              </td>
              <td>
                <strong>{run.scores.overall}</strong>
                <br />
                <small>Validation {run.scores.validation}</small>
              </td>
              <td>
                <span suppressHydrationWarning>
                  {new Date(run.updated_at).toLocaleString()}
                </span>
              </td>
              <td>
                <div style={{ display: "flex", gap: 8 }}>
                  {run.latest_state.report_pdf_path && (
                    <a
                      href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/storage/${run.latest_state.report_pdf_path}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      title="Download PDF"
                      className="muted-link"
                    >
                      <Download size={16} />
                    </a>
                  )}
                  {(run.latest_state.report_md_url || run.latest_state.report_markdown) && (
                    <a
                      href={
                        (run.latest_state.report_md_url as string) ||
                        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/storage/uploads/${run.id}/report.md`
                      }
                      target="_blank"
                      rel="noopener noreferrer"
                      title="Download MD"
                      className="muted-link"
                    >
                      <FileText size={16} />
                    </a>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
