import "server-only";

import {
  mockCollaboration,
  mockDetail,
  mockFailure,
  mockGraph,
  mockMetrics,
  mockNotifications,
  mockRuns
} from "@/lib/mock-data";
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

async function request<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      cache: "no-store",
      headers: await buildBackendHeaders()
    });
    if (!response.ok) {
      return fallback;
    }
    const payload = (await response.json()) as { data: T };
    return payload.data ?? fallback;
  } catch {
    return fallback;
  }
}

export async function getRuns(): Promise<QARunRecord[]> {
  return request("/api/v1/qa-runs", mockRuns);
}

export async function getRun(runId: string): Promise<QARunDetail> {
  return request(`/api/v1/qa-runs/${runId}`, { ...mockDetail, id: runId });
}

export async function getGraph(runId: string): Promise<typeof mockGraph> {
  return request(`/api/v1/qa-runs/${runId}/graph`, mockGraph);
}

export async function getPlayback(
  runId: string
): Promise<{ events: PlaybackEvent[]; snapshots: PlaybackSnapshot[] }> {
  return request(`/api/v1/qa-runs/${runId}/playback`, {
    events: mockDetail.playback,
    snapshots: mockDetail.snapshots
  });
}

export async function getFailureExplainer(
  runId: string
): Promise<FailureExplanation | null> {
  return request(`/api/v1/qa-runs/${runId}/failure-explainer`, mockFailure);
}

export async function getCollaboration(runId: string): Promise<CollaborationStep[]> {
  return request(`/api/v1/qa-runs/${runId}/collaboration`, mockCollaboration);
}

export async function getMetrics(): Promise<MetricsOverview> {
  return request("/api/v1/metrics/overview", mockMetrics);
}

export async function getNotificationLogs(): Promise<NotificationLog[]> {
  return request("/api/v1/notifications/logs", mockNotifications);
}
