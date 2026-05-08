export type QARunStatus =
  | "queued"
  | "running"
  | "approval_required"
  | "success"
  | "failed";

export interface QualityScores {
  reliability: number;
  validation: number;
  hallucination_risk: number;
  retry_health: number;
  overall: number;
}

export interface WorkflowFinding {
  id: string;
  category: string;
  severity: string;
  title: string;
  description: string;
  evidence: string[];
  affected_nodes: string[];
  recommendation: string;
}

export interface PlaybackEvent {
  id: string;
  run_id: string;
  event_type: string;
  agent: string;
  step: string;
  status: string;
  tool?: string | null;
  payload: Record<string, unknown>;
  sequence: number;
  timestamp: string;
}

export interface PlaybackSnapshot {
  id: string;
  run_id: string;
  current_node: string;
  status_map: Record<string, string>;
  created_at: string;
}

export interface CollaborationStep {
  id: string;
  run_id: string;
  agent: string;
  started_at: string;
  completed_at?: string | null;
  tools_used: string[];
  handoff_summary: string;
  risk_level: string;
  confidence: number;
  dependencies: string[];
}

export interface FailureExplanation {
  root_cause: string;
  evidence: string[];
  affected_nodes: string[];
  user_impact: string;
  why_previous_attempt_failed: string;
  recommended_fix: string;
}

export interface RepairStrategy {
  id: string;
  title: string;
  strategy_type: string;
  rationale: string;
  steps: string[];
  memory_similarity: number;
  prior_success_rate: number;
  safety_score: number;
  selected: boolean;
  fixed_code?: string;
  explanation?: string;
  evidence: string[];
}

export interface RunArtifact {
  name: string;
  file_type: string;
  path: string;
}

export interface QARunRecord {
  id: string;
  task: string;
  validation_mode: string;
  status: QARunStatus;
  approval_status: string;
  retry_enabled: boolean;
  notifications_enabled: boolean;
  max_retries: number;
  retries_used: number;
  current_agent: string;
  risk_level: "low" | "medium" | "high";
  created_by: string;
  created_at: string;
  updated_at: string;
  project_file_name: string;
  workflow_file_name: string;
  attachments: RunArtifact[];
  scores: QualityScores;
  latest_state: Record<string, unknown>;
}

export interface QARunDetail extends QARunRecord {
  findings: WorkflowFinding[];
  playback: PlaybackEvent[];
  snapshots: PlaybackSnapshot[];
  failure_explanation?: FailureExplanation | null;
  repair_strategies: RepairStrategy[];
  collaboration: CollaborationStep[];
  report_markdown?: string | null;
  report_pdf_path?: string | null;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  config?: Record<string, unknown>;
  status?: string | null;
}

export interface GraphEdge {
  source: string;
  target: string;
  label?: string | null;
}

export interface MetricsOverview {
  total_runs: number;
  success_rate: number;
  average_retries: number;
  approval_queue: number;
  reliability_trend: Array<Record<string, number | string>>;
  risk_breakdown: Array<{ name: string; value: number }>;
  agent_contribution: Array<{ agent: string; share: number }>;
}

export interface NotificationLog {
  id: string;
  run_id: string;
  channel: "whatsapp" | "sms";
  recipient: string;
  message: string;
  status: string;
  provider_sid?: string | null;
  created_at: string;
}
