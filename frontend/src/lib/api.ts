import type { RunsParams, RunsResponse, RunDetail, StatsResponse } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function buildQuery(params: Record<string, unknown>): string {
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value)) {
      value.forEach((v) => qs.append(key, String(v)));
    } else {
      qs.set(key, String(value));
    }
  }
  return qs.toString();
}

export async function getRuns(params: RunsParams = {}): Promise<RunsResponse> {
  const qs = buildQuery(params as Record<string, unknown>);
  const res = await fetch(`${API_URL}/api/runs${qs ? `?${qs}` : ""}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to fetch runs: ${res.status}`);
  return res.json();
}

export async function getRun(id: string): Promise<RunDetail> {
  const res = await fetch(`${API_URL}/api/runs/${id}`, { cache: "no-store" });
  if (res.status === 404) throw new Error("not_found");
  if (!res.ok) throw new Error(`Failed to fetch run: ${res.status}`);
  return res.json();
}

export async function getStats(): Promise<StatsResponse> {
  const res = await fetch(`${API_URL}/api/stats`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch stats: ${res.status}`);
  return res.json();
}

export function getExplainUrl(id: string): string {
  return `${API_URL}/api/runs/${id}/explain`;
}
