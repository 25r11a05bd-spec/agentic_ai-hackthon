import "server-only";

import { buildBackendHeaders } from "@/lib/session";
import type {
  CollaborationStep,
  FailureExplanation,
  MetricsOverview,
  NotificationLog,
  PlaybackEvent,
  PlaybackSnapshot,
  QARunDetail,
  QARunRecord
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    cache: "no-store",
    headers: await buildBackendHeaders()
  });
  
  if (!response.ok) {
    const errText = await response.text();
    console.error(`[API Error] ${response.status} - ${path}: ${errText}`);
    throw new Error(`API Request Failed: ${response.status} ${response.statusText}`);
  }
  
  const payload = (await response.json()) as { data: T };
  return payload.data;
}

export async function getRuns(): Promise<QARunRecord[]> {
  return request<QARunRecord[]>("/api/v1/qa-runs");
}

export async function getRun(runId: string): Promise<QARunDetail> {
  return request<QARunDetail>(`/api/v1/qa-runs/${runId}`);
}

export async function getGraph(runId: string): Promise<{ nodes: any[]; edges: any[] }> {
  return request<{ nodes: any[]; edges: any[] }>(`/api/v1/qa-runs/${runId}/graph`);
}

export async function getPlayback(
  runId: string
): Promise<{ events: PlaybackEvent[]; snapshots: PlaybackSnapshot[] }> {
  return request<{ events: PlaybackEvent[]; snapshots: PlaybackSnapshot[] }>(`/api/v1/qa-runs/${runId}/playback`);
}

export async function getFailureExplainer(
  runId: string
): Promise<FailureExplanation | null> {
  return request<FailureExplanation | null>(`/api/v1/qa-runs/${runId}/failure-explainer`);
}

export async function getCollaboration(runId: string): Promise<CollaborationStep[]> {
  return request<CollaborationStep[]>(`/api/v1/qa-runs/${runId}/collaboration`);
}

export async function getMetrics(): Promise<MetricsOverview> {
  return request<MetricsOverview>("/api/v1/metrics/overview");
}

export async function getNotificationLogs(): Promise<NotificationLog[]> {
  return request<NotificationLog[]>("/api/v1/notifications/logs");
}
