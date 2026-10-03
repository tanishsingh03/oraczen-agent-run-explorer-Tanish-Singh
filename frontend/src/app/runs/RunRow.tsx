"use client";
import Link from "next/link";
import type { RunSummary } from "@/types";

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

export default function RunRow({ run, isLast }: { run: RunSummary; isLast: boolean }) {
  return (
    <tr style={{
      borderBottom: isLast ? "none" : "1px solid var(--border)",
      cursor: "pointer", transition: "background 0.1s",
    }}
      onMouseEnter={e => (e.currentTarget.style.background = "var(--bg-hover)")}
      onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
    >
      <td style={{ padding: "14px 16px" }}>
        <Link href={`/runs/${run.id}`} style={{
          fontFamily: "monospace", fontSize: "12px",
          color: "var(--accent)", textDecoration: "none", fontWeight: 600,
        }}>
          {run.id}
        </Link>
      </td>
      <td style={{ padding: "14px 16px" }}>
        <span style={{
          fontSize: "12px", fontWeight: 500,
          color: agentColor(run.agent),
          background: `${agentColor(run.agent)}18`,
          padding: "3px 8px", borderRadius: "4px",
        }}>{run.agent}</span>
      </td>
      <td style={{ padding: "14px 16px" }}>
        <span className={`badge badge-${run.status}`}>{run.status}</span>
      </td>
      <td style={{ padding: "14px 16px", maxWidth: "280px" }}>
        <span style={{
          fontSize: "13px", color: "var(--text-secondary)",
          display: "block", overflow: "hidden",
          whiteSpace: "nowrap", textOverflow: "ellipsis",
        }} title={run.prompt}>{run.prompt}</span>
      </td>
      <td style={{ padding: "14px 16px" }}>
        <span style={{ fontSize: "13px", color: "var(--text-secondary)", fontVariantNumeric: "tabular-nums" }}>
          {formatDuration(run.duration_ms)}
        </span>
      </td>
      <td style={{ padding: "14px 16px" }}>
        <span style={{ fontSize: "13px", color: run.cost_usd === null ? "var(--text-muted)" : "var(--text-secondary)", fontVariantNumeric: "tabular-nums" }}>
          {formatCost(run.cost_usd)}
        </span>
      </td>
      <td style={{ padding: "14px 16px" }}>
        <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
          {timeAgo(run.started_at)}
        </span>
      </td>
    </tr>
  );
}
