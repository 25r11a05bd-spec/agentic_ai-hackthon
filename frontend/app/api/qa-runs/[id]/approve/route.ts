import { NextRequest, NextResponse } from "next/server";

import { buildBackendHeaders } from "@/lib/session";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const payload = await request.json();
  const response = await fetch(`${API_BASE}/api/v1/qa-runs/${id}/approve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(await buildBackendHeaders(["admin"]))
    },
    body: JSON.stringify(payload)
  });

  const body = await response.json();
  return NextResponse.json(body, { status: response.status });
}
