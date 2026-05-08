"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import ReactFlow, { Background, Controls, Edge, MarkerType, Node } from "reactflow";
import "reactflow/dist/style.css";

import { StatusPill } from "@/components/status-pill";
import type {
  CollaborationStep,
  FailureExplanation,
  GraphEdge,
  GraphNode,
  PlaybackEvent,
  QARunDetail
} from "@/lib/types";

interface RunDetailWorkspaceProps {
  run: QARunDetail;
  graph: { nodes: GraphNode[]; edges: GraphEdge[] };
  initialEvents: PlaybackEvent[];
  failure: FailureExplanation | null;
  collaboration: CollaborationStep[];
}

const WS_BASE = process.env.NEXT_PUBLIC_WS_BASE_URL ?? "ws://localhost:8000";
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Maps event types / agent names to readable pipeline steps
const PIPELINE_STEPS = [
  { key: "planner",   label: "Planning",          icon: "🧠" },
  { key: "executor",  label: "Executing",          icon: "⚙️" },
  { key: "validator", label: "Validating",         icon: "🔍" },
  { key: "reflection",label: "Error Correction",   icon: "🔧" },
  { key: "finalizer", label: "Generating Report",  icon: "📄" },
];

function getStepStatus(key: string, events: PlaybackEvent[], currentAgent: string) {
  const relevantEvents = events.filter(
    (e) => e.agent === key || e.step?.toLowerCase().includes(key)
  );
  if (relevantEvents.some((e) => e.status === "completed")) return "completed";
  if (relevantEvents.some((e) => e.status === "error")) return "error";
  if (currentAgent === key) return "running";
  const stepIndex = PIPELINE_STEPS.findIndex((s) => s.key === key);
  const currentIndex = PIPELINE_STEPS.findIndex((s) => s.key === currentAgent);
  if (stepIndex < currentIndex) return "completed";
  return "pending";
}

export function RunDetailWorkspace({
  run,
  graph,
  initialEvents,
  failure,
  collaboration
}: RunDetailWorkspaceProps) {
  const router = useRouter();
  const [events, setEvents] = useState<PlaybackEvent[]>(initialEvents);
  const [activeIndex, setActiveIndex] = useState(Math.max(initialEvents.length - 1, 0));
  const [currentRun, setCurrentRun] = useState(run);

  // Auto-poll every 3 s while run is not finished
  useEffect(() => {
    const isTerminal = ["success", "failed"].includes(currentRun.status);
    if (isTerminal) return;
    const interval = setInterval(() => router.refresh(), 3000);
    return () => clearInterval(interval);
  }, [currentRun.status, router]);

  // Keep local state in sync when server refreshes props
  useEffect(() => { setCurrentRun(run); }, [run]);
  useEffect(() => {
    setEvents(initialEvents);
    setActiveIndex(Math.max(initialEvents.length - 1, 0));
  }, [initialEvents]);

  useEffect(() => {
    const socket = new WebSocket(`${WS_BASE}/ws/qa-runs/${run.id}`);
    socket.onmessage = (message) => {
      const payload = JSON.parse(message.data) as PlaybackEvent & { event_type?: string };
      if (!payload.event_type || payload.event_type === "heartbeat") {
        return;
      }
      setEvents((current) => {
        if (current.some((item) => item.id === payload.id)) {
          return current;
        }
        return [...current, payload];
      });
      setActiveIndex((current) => Math.max(current, events.length));
    };
    return () => socket.close();
  }, [run.id, events.length]);

  const activeEvent = events[Math.min(activeIndex, Math.max(events.length - 1, 0))];

  const flowNodes: Node[] = useMemo(() => {
    const highlightedNode =
      typeof activeEvent?.payload?.current_node === "string"
        ? activeEvent.payload.current_node
        : activeEvent?.agent;

    return graph.nodes.map((node, index) => ({
      id: node.id,
      data: { label: node.label },
      position: {
        x: (index % 3) * 240,
        y: Math.floor(index / 3) * 120
      },
      style: {
        borderRadius: 18,
        padding: 12,
        border:
          node.id === highlightedNode
            ? "1px solid rgba(42, 228, 255, 0.9)"
            : "1px solid rgba(132, 197, 255, 0.12)",
        background:
          node.id === highlightedNode
            ? "rgba(42, 228, 255, 0.16)"
            : node.status === "completed"
              ? "rgba(149, 255, 153, 0.12)"
              : "rgba(12, 31, 47, 0.88)",
        color: "#edf5ff",
        minWidth: 180,
        boxShadow: node.id === highlightedNode ? "0 0 0 1px rgba(42, 228, 255, 0.3)" : "none"
      }
    }));
  }, [activeEvent, graph.nodes]);

  const flowEdges: Edge[] = useMemo(() => {
    return graph.edges.map((edge, index) => ({
      id: `${edge.source}-${edge.target}-${index}`,
      source: edge.source,
      target: edge.target,
      type: "smoothstep",
      markerEnd: { type: MarkerType.ArrowClosed, color: "#2ae4ff" },
      style: { stroke: "#2ae4ff", strokeOpacity: 0.4 }
    }));
  }, [graph.edges]);

  return (
    <div className="detail-grid">

      {/* ── Agent Pipeline Steps ── */}
      <section className="panel" style={{ gridColumn: "span 2", marginBottom: 0 }}>
        <div className="section-heading">
          <div>
            <div className="eyebrow">Live Progress</div>
            <h3>Agent Pipeline</h3>
          </div>
          <StatusPill status={currentRun.status} />
        </div>
        <div style={{ display: "flex", gap: 12, marginTop: 16, flexWrap: "wrap" }}>
          {PIPELINE_STEPS.map((step, i) => {
            const status = getStepStatus(step.key, events, currentRun.current_agent);
            const colors: Record<string, string> = {
              completed: "rgba(77,255,128,0.15)",
              running:   "rgba(42,228,255,0.15)",
              error:     "rgba(255,80,80,0.15)",
              pending:   "rgba(132,197,255,0.04)",
            };
            const borders: Record<string, string> = {
              completed: "1px solid rgba(77,255,128,0.5)",
              running:   "1px solid rgba(42,228,255,0.6)",
              error:     "1px solid rgba(255,80,80,0.5)",
              pending:   "1px solid rgba(132,197,255,0.1)",
            };
            return (
              <div key={step.key} style={{
                flex: "1 1 160px",
                padding: "14px 16px",
                borderRadius: 12,
                background: colors[status],
                border: borders[status],
                display: "flex",
                alignItems: "center",
                gap: 10,
                position: "relative",
              }}>
                <span style={{ fontSize: 22 }}>{step.icon}</span>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "#edf5ff" }}>{step.label}</div>
                  <div style={{ fontSize: 11, color: "rgba(132,197,255,0.7)", marginTop: 2 }}>
                    {status === "running" ? "⏳ In Progress..." :
                     status === "completed" ? "✅ Done" :
                     status === "error" ? "❌ Error" : "⏸ Waiting"}
                  </div>
                </div>
                {status === "running" && (
                  <span style={{
                    position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)",
                    width: 8, height: 8, borderRadius: "50%",
                    background: "#2ae4ff",
                    animation: "pulse 1.5s ease-in-out infinite"
                  }} />
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* ── Download Result Card ── */}
      {(currentRun.report_markdown || currentRun.report_pdf_path || currentRun.status === "success") && (
        <section className="panel" style={{ gridColumn: "span 2", background: "rgba(77,255,128,0.06)", border: "1px solid rgba(77,255,128,0.2)" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
            <div>
              <div className="eyebrow">Analysis Complete</div>
              <h3 style={{ marginTop: 4 }}>✅ Your Result is Ready</h3>
              <p className="muted" style={{ marginTop: 4 }}>The AI agent fleet has finished analysing your code.</p>
            </div>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <a
                href={`${API_BASE}/api/v1/qa-runs/${currentRun.id}/download-report`}
                download="result.md"
                className="toolbar-select primary"
                style={{ padding: "10px 20px", textDecoration: "none", fontSize: 14, fontWeight: 600 }}
              >
                ⬇ Download result.md
              </a>
              {currentRun.report_pdf_path && (
                <a
                  href={`${API_BASE}/storage/${currentRun.report_pdf_path}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="toolbar-select"
                  style={{ padding: "10px 20px", textDecoration: "none", fontSize: 14 }}
                >
                  ⬇ Download PDF
                </a>
              )}
            </div>
          </div>
        </section>
      )}

      <div className="detail-column">
        <section className="timeline-panel">
          <div className="section-heading">
            <div>
              <div className="eyebrow">Playback</div>
              <h3>Timeline Replay</h3>
            </div>
            <StatusPill status={run.status} />
          </div>
          <input
            type="range"
            min={0}
            max={Math.max(events.length - 1, 0)}
            value={Math.min(activeIndex, Math.max(events.length - 1, 0))}
            onChange={(event) => setActiveIndex(Number(event.target.value))}
          />
          <div className="timeline-list" style={{ marginTop: 18 }}>
            {events.slice().reverse().map((event) => (
              <button
                key={event.id}
                type="button"
                className="timeline-item"
                style={{ color: "inherit", textAlign: "left", cursor: "pointer" }}
                onClick={() => setActiveIndex(events.findIndex((item) => item.id === event.id))}
              >
                <strong>{event.event_type}</strong>
                <div>{event.step}</div>
                <small className="muted" suppressHydrationWarning>
                  {event.agent} · {new Date(event.timestamp).toLocaleTimeString()}
                </small>
              </button>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="section-heading">
            <div>
              <div className="eyebrow">Runtime Topology</div>
              <h3>Graph Highlight Sync</h3>
            </div>
          </div>
          <div style={{ width: "100%", height: 520 }}>
            <ReactFlow nodes={flowNodes} edges={flowEdges} fitView>
              <Background color="rgba(132, 197, 255, 0.08)" />
              <Controls />
            </ReactFlow>
          </div>
        </section>

        <section className="console-panel">
          <div className="section-heading">
            <div>
              <div className="eyebrow">Live Console</div>
              <h3>Agent Log Stream</h3>
            </div>
          </div>
          <ul className="console-stream">
            {events.map((event) => (
              <li key={event.id}>
                <strong>
                  {event.agent} · {event.event_type}
                </strong>
                <span>{event.step}</span>
                <small className="muted" suppressHydrationWarning>
                  {event.status} · {new Date(event.timestamp).toLocaleString()}
                </small>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <div className="detail-column">
        <section className="panel">
          <div className="section-heading">
            <div>
              <div className="eyebrow">Failure Explainer</div>
              <h3>Grounded Evidence</h3>
            </div>
          </div>
          {failure ? (
            <div className="finding-list">
              <div className="finding-item">
                <strong>Root Cause</strong>
                <div>{failure.root_cause}</div>
              </div>
              <div className="finding-item">
                <strong>User Impact</strong>
                <div>{failure.user_impact}</div>
              </div>
              <div className="finding-item">
                <strong>Why Previous Attempt Failed</strong>
                <div>{failure.why_previous_attempt_failed}</div>
              </div>
              <div className="finding-item">
                <strong>Recommended Fix</strong>
                <div>{failure.recommended_fix}</div>
              </div>
              <div className="finding-item">
                <strong>Evidence</strong>
                <div className="timeline-list">
                  {failure.evidence.map((entry) => (
                    <div key={entry} className="artifact-item">
                      {entry}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="muted">No failure explanation was required for this run.</div>
          )}
        </section>

        <section className="panel">
          <div className="section-heading">
            <div>
              <div className="eyebrow">Findings</div>
              <h3>Validator and Hallucination Flags</h3>
            </div>
          </div>
          <div className="finding-list">
            {run.findings.map((finding) => (
              <div className="finding-item" key={finding.id}>
                <strong>{finding.title}</strong>
                <div>{finding.description}</div>
                <small className="muted">
                  {finding.category} · {finding.severity}
                </small>
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="section-heading">
            <div>
              <div className="eyebrow">Collaboration</div>
              <h3>Agent Handoffs</h3>
            </div>
          </div>
          <div className="lane-list">
            {collaboration.map((step) => (
              <div className="lane-item" key={step.id}>
                <strong>{step.agent}</strong>
                <div>{step.handoff_summary}</div>
                <small className="muted">
                  risk {step.risk_level} · confidence {(step.confidence * 100).toFixed(0)}%
                </small>
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="section-heading">
            <div>
              <div className="eyebrow">Artifacts</div>
              <h3>Uploaded Evidence</h3>
            </div>
          </div>
          <div className="artifact-list">
            {run.attachments.length ? (
              run.attachments.map((artifact) => (
                <div className="artifact-item" key={artifact.path}>
                  <strong>{artifact.name}</strong>
                  <div>{artifact.file_type}</div>
                </div>
              ))
            ) : (
              <div className="artifact-item">No extra evidence attachments were supplied for this run.</div>
            )}
          </div>
        </section>
        <section className="panel" style={{ gridColumn: "span 2" }}>
          <div className="section-heading">
            <div>
              <div className="eyebrow">Analysis Result</div>
              <h3>Executive Analysis Report</h3>
            </div>
          </div>
          {run.report_markdown ? (
            <div
              className="console-stream"
              style={{
                maxHeight: "none",
                background: "rgba(12, 31, 47, 0.4)",
                padding: "20px",
                whiteSpace: "pre-wrap",
                fontFamily: "Inter, sans-serif",
                lineHeight: "1.6",
                color: "#edf5ff"
              }}
            >
              {run.report_markdown}
            </div>
          ) : (
            <div className="muted">The report is being generated by the AI agent fleet...</div>
          )}
        </section>
      </div>
    </div>
  );
}
