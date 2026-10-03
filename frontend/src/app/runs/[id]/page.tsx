import { getRun } from "@/lib/api";
import { notFound } from "next/navigation";
import Link from "next/link";
import ExplainButton from "./ExplainButton";
import type { Step } from "@/types";
import StepsList from "./StepsList";

interface PageProps {
  params: Promise<{ id: string }>;
}

function StatusBadge({ status }: { status: string }) {
  return <span className={`badge badge-${status}`}>{status}</span>;
}

function formatDuration(ms: number | null): string {
  if (ms === null) return "—";
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-US", {
    month: "short", day: "numeric", year: "numeric",
    hour: "2-digit", minute: "2-digit", second: "2-digit"
  });
}

function MetaRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div style={{ display: "flex", gap: "12px", padding: "10px 0", borderBottom: "1px solid var(--border)" }}>
      <span style={{ width: "140px", flexShrink: 0, fontSize: "12px", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", lineHeight: "1.6" }}>
        {label}
      </span>
      <span style={{ fontSize: "13px", color: "var(--text-primary)", flex: 1 }}>{value}</span>
    </div>
  );
}

export default async function RunDetailPage({ params }: PageProps) {
  const { id } = await params;
  let run;
  try {
    run = await getRun(id);
  } catch (e) {
    if (e instanceof Error && e.message === "not_found") notFound();
    throw e;
  }

  const totalTokens = run.input_tokens + run.output_tokens;

  return (
    <div style={{ maxWidth: "900px" }}>
      {/* Back link */}
      <Link href="/runs" style={{
        display: "inline-flex", alignItems: "center", gap: "6px",
        color: "var(--text-muted)", fontSize: "13px", marginBottom: "20px",
        textDecoration: "none", transition: "color 0.15s",
      }}
  
      >
        ← Back to runs
      </Link>

      {/* Run header */}
      <div style={{ marginBottom: "24px", display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
            <h1 style={{ fontSize: "20px", fontWeight: 700, margin: 0, fontFamily: "monospace" }}>{run.id}</h1>
            <StatusBadge status={run.status} />
          </div>
          <p style={{ margin: 0, color: "var(--text-secondary)", fontSize: "14px", maxWidth: "600px", lineHeight: "1.5" }}>
            {run.prompt}
          </p>
        </div>
        <ExplainButton runId={run.id} />
      </div>

      {/* Error block */}
      {run.error && (
        <div style={{
          background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.3)",
          borderRadius: "12px", padding: "16px 20px", marginBottom: "24px",
        }}>
          <div style={{ display: "flex", gap: "10px", alignItems: "flex-start" }}>
            <span style={{ fontSize: "16px" }}>🚨</span>
            <div>
              <div style={{ fontWeight: 600, color: "#ef4444", marginBottom: "4px", fontSize: "14px" }}>
                {run.error.type}
                <span style={{ marginLeft: "8px", fontSize: "12px", color: "var(--text-muted)", fontWeight: 400 }}>
                  at step {run.error.step_index}
                </span>
              </div>
              <div style={{ color: "#fca5a5", fontSize: "13px" }}>{run.error.message}</div>
            </div>
          </div>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px", marginBottom: "24px" }}>
        {/* Metadata card */}
        <div className="card" style={{ padding: "20px" }}>
          <div style={{ fontSize: "12px", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: "12px" }}>
            Run Metadata
          </div>
          <MetaRow label="Agent" value={<span style={{ color: "#3b82f6" }}>{run.agent}</span>} />
          <MetaRow label="Model" value={run.model} />
          <MetaRow label="Tenant" value={<span style={{ fontFamily: "monospace", fontSize: "12px" }}>{run.tenant_id}</span>} />
          <MetaRow label="Started" value={formatDate(run.started_at)} />
          <MetaRow label="Ended" value={formatDate(run.ended_at)} />
        </div>

        {/* Performance card */}
        <div className="card" style={{ padding: "20px" }}>
          <div style={{ fontSize: "12px", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: "12px" }}>
            Performance
          </div>
          <MetaRow label="Duration" value={
            <span style={{ fontFamily: "monospace", fontWeight: 600, color: run.duration_ms ? "var(--text-primary)" : "var(--text-muted)" }}>
              {formatDuration(run.duration_ms)}
            </span>
          } />
          <MetaRow label="Cost" value={
            <span style={{ fontFamily: "monospace", fontWeight: 600 }}>
              {run.cost_usd !== null ? `$${run.cost_usd.toFixed(6)}` : <span style={{ color: "var(--text-muted)" }}>unknown</span>}
            </span>
          } />
          <MetaRow label="Input tokens" value={
            <span style={{ fontFamily: "monospace" }}>{run.input_tokens.toLocaleString()}</span>
          } />
          <MetaRow label="Output tokens" value={
            <span style={{ fontFamily: "monospace" }}>{run.output_tokens.toLocaleString()}</span>
          } />
          <MetaRow label="Total tokens" value={
            <span style={{ fontFamily: "monospace", fontWeight: 600 }}>{totalTokens.toLocaleString()}</span>
          } />
        </div>
      </div>

      {/* Steps */}
      <div className="card" style={{ padding: "20px" }}>
        <div style={{ fontSize: "12px", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: "16px" }}>
          Steps ({run.steps.length})
        </div>
        {run.steps.length === 0 ? (
          <div style={{ color: "var(--text-muted)", fontSize: "13px", textAlign: "center", padding: "24px 0" }}>
            No steps recorded for this run
          </div>
        ) : (
          <StepsList steps={run.steps} />
        )}
      </div>
    </div>
  );
}
