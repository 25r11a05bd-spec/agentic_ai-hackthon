import type {
  CollaborationStep,
  FailureExplanation,
  GraphEdge,
  GraphNode,
  MetricsOverview,
  NotificationLog,
  PlaybackEvent,
  PlaybackSnapshot,
  QARunDetail,
  QARunRecord
} from "@/lib/types";

const now = new Date().toISOString();

export const mockRuns: QARunRecord[] = [
  {
    id: "run_demo_001",
    task: "Analyze automation workflow quality",
    validation_mode: "strict",
    status: "approval_required",
    approval_status: "pending",
    retry_enabled: true,
    notifications_enabled: true,
    max_retries: 3,
    retries_used: 1,
    current_agent: "approval_gate",
    risk_level: "high",
    created_by: "dev-operator",
    created_at: now,
    updated_at: now,
    project_file_name: "app.py",
    workflow_file_name: "automation.json",
    attachments: [],
    scores: {
      reliability: 72,
      validation: 68,
      hallucination_risk: 31,
      retry_health: 74,
      overall: 69
    },
    latest_state: {}
  }
];

const mockGraphNodeIds = [
  "ingest",
  "planner",
  "tool_router",
  "executor",
  "validator",
  "failure_explainer",
  "reflection",
  "self_heal_router",
  "retry_or_replan",
  "approval_gate",
  "memory_writer",
  "notifier",
  "finalizer"
] as const;

export const mockGraph = {
  nodes: [...mockGraphNodeIds].map(
    (id): GraphNode => ({
      id,
      label: id.replace(/_/g, " "),
      type: "task",
      status: ["ingest", "planner", "tool_router", "executor", "validator"].includes(id)
        ? "completed"
        : id === "approval_gate"
          ? "running"
          : "pending"
    })
  ),
  edges: mockGraphNodeIds.slice(1).map(
    (target, index): GraphEdge => ({
      source: mockGraphNodeIds[index],
      target
    })
  )
};

export const mockEvents: PlaybackEvent[] = [
  {
    id: "evt_1",
    run_id: "run_demo_001",
    event_type: "run_started",
    agent: "ingest",
    step: "Upload accepted and persisted",
    status: "running",
    payload: {},
    sequence: 1,
    timestamp: now
  },
  {
    id: "evt_2",
    run_id: "run_demo_001",
    event_type: "finding_created",
    agent: "executor",
    step: "Workflow node includes ungrounded config fields",
    status: "medium",
    payload: {},
    sequence: 2,
    timestamp: now
  },
  {
    id: "evt_3",
    run_id: "run_demo_001",
    event_type: "approval_required",
    agent: "approval_gate",
    step: "validation score 68 < 85; hallucination risk 31 > 25",
    status: "pending",
    payload: {},
    sequence: 3,
    timestamp: now
  }
];

export const mockSnapshots: PlaybackSnapshot[] = [
  {
    id: "snap_1",
    run_id: "run_demo_001",
    current_node: "approval_gate",
    status_map: {
      ingest: "completed",
      planner: "completed",
      tool_router: "completed",
      executor: "completed",
      validator: "completed",
      approval_gate: "running"
    },
    created_at: now
  }
];

export const mockFailure: FailureExplanation = {
  root_cause: "Missing validation layer",
  evidence: [
    "Detected 1 functions, 0 classes, 1 HTTP call sites, and 1 validator-style functions.",
    "No downstream edge from the API node was found."
  ],
  affected_nodes: ["fetch"],
  user_impact: "Unsafe auto-fix would proceed without a verified guard.",
  why_previous_attempt_failed: "The initial execution path lacked an explicit validation branch.",
  recommended_fix: "Insert a generated validator stage into the execution plan."
};

export const mockCollaboration: CollaborationStep[] = [
  {
    id: "col_1",
    run_id: "run_demo_001",
    agent: "planner",
    started_at: now,
    completed_at: now,
    tools_used: ["analyze_python_code", "normalize_workflow"],
    handoff_summary: "Planner grounded the graph and identified validator gaps.",
    risk_level: "medium",
    confidence: 0.84,
    dependencies: []
  },
  {
    id: "col_2",
    run_id: "run_demo_001",
    agent: "reflection",
    started_at: now,
    completed_at: now,
    tools_used: ["retrieve_memory", "rank_repair_strategies"],
    handoff_summary: "Reflection proposed validator injection with safe replay.",
    risk_level: "high",
    confidence: 0.71,
    dependencies: ["validator"]
  }
];

export const mockDetail: QARunDetail = {
  ...mockRuns[0],
  findings: [
    {
      id: "finding_1",
      category: "validation",
      severity: "high",
      title: "Missing validation layer",
      description: "The workflow has no explicit validation node or rule after execution steps.",
      evidence: ["No downstream edge from the API node was found."],
      affected_nodes: ["fetch"],
      recommendation: "Insert a validator node or schema validation rule before success."
    }
  ],
  playback: mockEvents,
  snapshots: mockSnapshots,
  failure_explanation: mockFailure,
  repair_strategies: [],
  collaboration: mockCollaboration,
  report_markdown: "# Demo report",
  report_pdf_path: null
};

export const mockMetrics: MetricsOverview = {
  total_runs: 12,
  success_rate: 66.7,
  average_retries: 1.4,
  approval_queue: 3,
  reliability_trend: [
    { runId: "run_001", reliability: 72, overall: 69 },
    { runId: "run_002", reliability: 88, overall: 86 },
    { runId: "run_003", reliability: 61, overall: 59 }
  ],
  risk_breakdown: [
    { name: "low", value: 4 },
    { name: "medium", value: 5 },
    { name: "high", value: 3 }
  ],
  agent_contribution: [
    { agent: "planner", share: 18 },
    { agent: "executor", share: 24 },
    { agent: "validator", share: 20 },
    { agent: "reflection", share: 16 },
    { agent: "memory", share: 10 },
    { agent: "notifier", share: 12 }
  ]
};

export const mockNotifications: NotificationLog[] = [
  {
    id: "notif_1",
    run_id: "run_demo_001",
    channel: "whatsapp",
    recipient: "unconfigured",
    message: "QA run run_demo_001 is now approval_required with score 69/100.",
    status: "simulated",
    provider_sid: "WA_demo",
    created_at: now
  }
];
