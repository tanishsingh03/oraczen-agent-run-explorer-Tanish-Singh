import { getStats } from "@/lib/api";
import DashboardCharts from "./DashboardCharts";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dashboard — Agent Run Explorer",
};

function StatCard({
  label, value, sub, color,
}: {
  label: string; value: string; sub?: string; color?: string;
}) {
  return (
    <div className="stat-card">
      <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "12px" }}>
        {label}
      </div>
      <div style={{ fontSize: "32px", fontWeight: 800, color: color ?? "var(--text-primary)", lineHeight: 1, marginBottom: "6px", fontVariantNumeric: "tabular-nums" }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>{sub}</div>}
    </div>
  );
}

function formatMs(ms: number | null): string {
  if (ms === null) return "—";
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export default async function DashboardPage() {
  let stats;
  let error: string | null = null;

  try {
    stats = await getStats();
  } catch (e) {
    error = e instanceof Error ? e.message : "Unknown error";
  }

  return (
    <div style={{ maxWidth: "1100px" }}>
      <div style={{ marginBottom: "28px" }}>
        <h1 style={{ fontSize: "24px", fontWeight: 700, marginBottom: "4px" }}>Dashboard</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "14px", margin: 0 }}>
          Platform-wide agent run statistics
        </p>
      </div>

      {error && (
        <div className="card" style={{ padding: "32px", textAlign: "center", borderColor: "rgba(239,68,68,0.3)" }}>
          <div style={{ color: "var(--red)", fontWeight: 600 }}>Could not load stats</div>
          <div style={{ color: "var(--text-muted)", fontSize: "13px", marginTop: "6px" }}>{error}</div>
        </div>
      )}

      {stats && (
        <>
          {/* KPI Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px", marginBottom: "28px" }}>
            <StatCard
              label="Total Runs"
              value={stats.overall.total_runs.toLocaleString()}
              sub="all time"
              color="var(--accent)"
            />
            <StatCard
              label="Success Rate"
              value={`${(stats.overall.success_rate * 100).toFixed(1)}%`}
              sub="succeeded / finished"
              color={stats.overall.success_rate > 0.8 ? "var(--green)" : "var(--yellow)"}
            />
            <StatCard
              label="Median Duration"
              value={formatMs(stats.overall.median_duration_ms)}
              sub="completed runs only"
            />
            <StatCard
              label="p95 Duration"
              value={formatMs(stats.overall.p95_duration_ms)}
              sub="95th percentile"
              color="var(--purple)"
            />
          </div>

          {/* Per-agent table */}
          <div className="card" style={{ marginBottom: "24px", overflow: "hidden" }}>
            <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)" }}>
              <div style={{ fontSize: "14px", fontWeight: 700 }}>Per-Agent Breakdown</div>
            </div>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)" }}>
                  {["Agent", "Runs", "Success Rate", "Total Cost"].map(h => (
                    <th key={h} style={{ padding: "10px 20px", textAlign: "left", fontSize: "11px", fontWeight: 600, letterSpacing: "0.07em", color: "var(--text-muted)", textTransform: "uppercase" }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {stats.per_agent.map((a, i) => (
                  <tr key={a.agent} style={{ borderBottom: i < stats.per_agent.length - 1 ? "1px solid var(--border)" : "none" }}>
                    <td style={{ padding: "14px 20px" }}>
                      <span style={{
                        fontSize: "13px", fontWeight: 500,
                        color: {
                          "email-drafter": "#3b82f6", "support-router": "#10b981",
                          "kpi-analyst": "#8b5cf6", "contract-reviewer": "#f59e0b",
                          "invoice-extractor": "#06b6d4"
                        }[a.agent] ?? "#94a3b8",
                      }}>{a.agent}</span>
                    </td>
                    <td style={{ padding: "14px 20px", fontSize: "13px", fontVariantNumeric: "tabular-nums" }}>
                      {a.total_runs}
                    </td>
                    <td style={{ padding: "14px 20px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <div style={{ width: "80px", height: "6px", background: "var(--border)", borderRadius: "3px", overflow: "hidden" }}>
                          <div style={{ width: `${a.success_rate * 100}%`, height: "100%", background: a.success_rate > 0.8 ? "var(--green)" : "var(--yellow)", borderRadius: "3px" }} />
                        </div>
                        <span style={{ fontSize: "13px", fontVariantNumeric: "tabular-nums" }}>
                          {(a.success_rate * 100).toFixed(1)}%
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: "14px 20px", fontSize: "13px", fontVariantNumeric: "tabular-nums" }}>
                      {a.total_cost_usd !== null
                        ? <span>${a.total_cost_usd.toFixed(4)}{a.cost_usd_is_partial && <sup style={{ color: "var(--yellow)", marginLeft: "2px" }}>✱</sup>}</span>
                        : <span style={{ color: "var(--text-muted)" }}>—</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div style={{ padding: "10px 20px", fontSize: "11px", color: "var(--text-muted)", borderTop: "1px solid var(--border)" }}>
              ✱ Partial cost — some runs for this agent have no price data
            </div>
          </div>

          {/* Charts */}
          <DashboardCharts stats={stats} />
        </>
      )}
    </div>
  );
}
