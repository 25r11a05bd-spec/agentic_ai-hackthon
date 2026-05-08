"use client";

import { useMemo, useState } from "react";
import Link from "next/link";

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
              <td>{new Date(run.updated_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
