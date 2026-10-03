import { getRuns } from "@/lib/api";
import type { RunSummary } from "@/types";
import Link from "next/link";
import RunsFilters from "./RunsFilters";
import Pagination from "./Pagination";
import RunRow from "./RunRow";

interface PageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

function getParam(v: string | string[] | undefined): string {
  if (!v) return "";
  return Array.isArray(v) ? v[0] : v;
}

function getArray(v: string | string[] | undefined): string[] {
  if (!v) return [];
  return Array.isArray(v) ? v : [v];
}

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`badge badge-${status}`}>
      {status === "running" && <span style={{ animation: "pulse 1s infinite" }}>●</span>}
      {status}
    </span>
  );
}

function formatDuration(ms: number | null): string {
  if (ms === null) return "—";
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatCost(usd: number | null): string {
  if (usd === null) return "—";
  return `$${usd.toFixed(4)}`;
}

function timeAgo(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diff = Math.floor((now.getTime() - d.getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function agentColor(agent: string): string {
  const colors: Record<string, string> = {
    "email-drafter": "#3b82f6",
    "support-router": "#10b981",
    "kpi-analyst": "#8b5cf6",
    "contract-reviewer": "#f59e0b",
    "invoice-extractor": "#06b6d4",
  };
  return colors[agent] ?? "#94a3b8";
}

export default async function RunsPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const page = parseInt(getParam(params.page) || "1");
  const page_size = parseInt(getParam(params.page_size) || "25");
  const q = getParam(params.q);
  const sort_by = getParam(params.sort_by) || "started_at";
  const sort_dir = getParam(params.sort_dir) || "desc";
  const started_after = getParam(params.started_after);
  const started_before = getParam(params.started_before);
  const status = getArray(params.status);
  const agent = getArray(params.agent);
  const tool = getArray(params.tool);

  let data;
  let error: string | null = null;

  try {
    data = await getRuns({
      page, page_size, q: q || undefined,
      sort_by, sort_dir,
      started_after: started_after || undefined,
      started_before: started_before || undefined,
      status: status.length ? status : undefined,
      agent: agent.length ? agent : undefined,
      tool: tool.length ? tool : undefined,
    });
  } catch (e) {
    error = e instanceof Error ? e.message : "Unknown error";
  }

  const from = data ? (page - 1) * page_size + 1 : 0;
  const to = data ? Math.min(page * page_size, data.total) : 0;

  return (
    <div style={{ maxWidth: "1200px" }}>
      {/* Header */}
      <div style={{ marginBottom: "24px" }}>
        <h1 style={{ fontSize: "24px", fontWeight: 700, marginBottom: "4px", color: "var(--text-primary)" }}>
          Agent Runs
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "14px", margin: 0 }}>
          Browse and filter execution traces across all agents
        </p>
      </div>

      {/* Filters — client component */}
      <RunsFilters
        defaultQ={q}
        defaultStatus={status}
        defaultAgent={agent}
        defaultSortBy={sort_by}
        defaultSortDir={sort_dir}
        defaultStartedAfter={started_after}
        defaultStartedBefore={started_before}
      />

      {/* Results bar */}
      {data && (
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between",
          marginBottom: "16px", color: "var(--text-secondary)", fontSize: "13px"
        }}>
          <span>
            {data.total === 0
              ? "No runs match your filters"
              : `Showing ${from}–${to} of ${data.total} run${data.total !== 1 ? "s" : ""}`}
          </span>
          <span style={{ color: "var(--text-muted)" }}>
            Page {page} of {Math.ceil(data.total / page_size) || 1}
          </span>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="card" style={{
          padding: "24px", textAlign: "center",
          borderColor: "rgba(239,68,68,0.3)", marginBottom: "16px"
        }}>
          <div style={{ fontSize: "20px", marginBottom: "8px" }}>⚠️</div>
          <div style={{ color: "var(--red)", fontWeight: 600, marginBottom: "4px" }}>
            Could not load runs
          </div>
          <div style={{ color: "var(--text-secondary)", fontSize: "13px" }}>{error}</div>
          <div style={{ color: "var(--text-muted)", fontSize: "12px", marginTop: "8px" }}>
            Make sure the backend is running on localhost:8000
          </div>
        </div>
      )}

      {/* Empty state */}
      {data && data.items.length === 0 && !error && (
        <div className="card" style={{ padding: "48px", textAlign: "center" }}>
          <div style={{ fontSize: "32px", marginBottom: "12px" }}>🔍</div>
          <div style={{ fontWeight: 600, marginBottom: "4px" }}>No runs found</div>
          <div style={{ color: "var(--text-secondary)", fontSize: "13px" }}>
            Try adjusting your filters or search query
          </div>
        </div>
      )}

      {/* Table */}
      {data && data.items.length > 0 && (
        <div className="card" style={{ overflow: "hidden", marginBottom: "20px" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)" }}>
                {["Run ID", "Agent", "Status", "Prompt", "Duration", "Cost", "Started"].map(h => (
                  <th key={h} style={{
                    padding: "12px 16px", textAlign: "left",
                    fontSize: "11px", fontWeight: 600, letterSpacing: "0.08em",
                    color: "var(--text-muted)", textTransform: "uppercase",
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.items.map((run: RunSummary, i: number) => (
                <RunRow key={run.id} run={run} isLast={i === data.items.length - 1} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {data && data.total > page_size && (
        <Pagination
          page={page}
          pageSize={page_size}
          total={data.total}
        />
      )}
    </div>
  );
}
