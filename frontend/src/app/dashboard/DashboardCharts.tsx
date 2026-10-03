"use client";

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend, Cell,
} from "recharts";
import type { StatsResponse } from "@/types";

const AGENT_COLORS: Record<string, string> = {
  "email-drafter":     "#3b82f6",
  "support-router":    "#10b981",
  "kpi-analyst":       "#8b5cf6",
  "contract-reviewer": "#f59e0b",
  "invoice-extractor": "#06b6d4",
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "var(--bg-card)", border: "1px solid var(--border-bright)",
      borderRadius: "8px", padding: "10px 14px", fontSize: "13px",
    }}>
      <div style={{ fontWeight: 600, marginBottom: "4px", color: "var(--text-primary)" }}>{label}</div>
      {payload.map((p: any) => (
        <div key={p.dataKey} style={{ color: p.color || "var(--text-secondary)" }}>
          {p.name ?? p.dataKey}: <strong>{typeof p.value === "number" && p.value < 1 ? `${(p.value * 100).toFixed(1)}%` : p.value}</strong>
        </div>
      ))}
    </div>
  );
};

export default function DashboardCharts({ stats }: { stats: StatsResponse }) {
  const agentData = stats.per_agent.map(a => ({
    name: a.agent,
    runs: a.total_runs,
    success: Math.round(a.success_rate * 100),
    cost: a.total_cost_usd ?? 0,
    partial: a.cost_usd_is_partial,
  }));

  const dailyData = stats.daily_counts.map(d => ({
    date: d.date.slice(5), // "MM-DD"
    count: d.count,
  }));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Daily runs chart */}
      <div className="card" style={{ padding: "24px" }}>
        <div style={{ marginBottom: "16px" }}>
          <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--text-primary)" }}>
            Daily Run Volume
          </div>
          <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>
            Total runs per day across the dataset
          </div>
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={dailyData} margin={{ top: 4, right: 4, bottom: 4, left: -24 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis dataKey="date" tick={{ fontSize: 11, fill: "var(--text-muted)" }} tickLine={false} axisLine={false} interval={6} />
            <YAxis tick={{ fontSize: 11, fill: "var(--text-muted)" }} tickLine={false} axisLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} dot={false} name="Runs" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
        {/* Success rate per agent */}
        <div className="card" style={{ padding: "24px" }}>
          <div style={{ marginBottom: "16px" }}>
            <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--text-primary)" }}>
              Success Rate by Agent
            </div>
            <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>
              % succeeded (excludes running runs)
            </div>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={agentData} margin={{ top: 4, right: 4, bottom: 40, left: -24 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: "var(--text-muted)" }} tickLine={false} axisLine={false} angle={-25} textAnchor="end" />
              <YAxis tick={{ fontSize: 11, fill: "var(--text-muted)" }} tickLine={false} axisLine={false} domain={[0, 100]} tickFormatter={v => `${v}%`} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="success" name="Success %" radius={[4, 4, 0, 0]}>
                {agentData.map((entry) => (
                  <Cell key={entry.name} fill={AGENT_COLORS[entry.name] ?? "#94a3b8"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Cost per agent */}
        <div className="card" style={{ padding: "24px" }}>
          <div style={{ marginBottom: "16px" }}>
            <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--text-primary)" }}>
              Total Cost by Agent
            </div>
            <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>
              USD — ✱ = partial (some runs unpriced)
            </div>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={agentData} margin={{ top: 4, right: 4, bottom: 40, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: "var(--text-muted)" }} tickLine={false} axisLine={false} angle={-25} textAnchor="end" />
              <YAxis tick={{ fontSize: 11, fill: "var(--text-muted)" }} tickLine={false} axisLine={false} tickFormatter={v => `$${v.toFixed(0)}`} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="cost" name="Cost (USD)" radius={[4, 4, 0, 0]}>
                {agentData.map((entry) => (
                  <Cell key={entry.name} fill={entry.partial ? "#f59e0b" : (AGENT_COLORS[entry.name] ?? "#94a3b8")} fillOpacity={entry.partial ? 0.7 : 1} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div style={{ fontSize: "11px", color: "var(--yellow)", marginTop: "8px" }}>
            ✱ Yellow bars = partial cost (not all runs priced)
          </div>
        </div>
      </div>
    </div>
  );
}
