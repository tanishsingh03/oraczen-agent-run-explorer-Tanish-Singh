"use client";
import { useState, useEffect } from "react";
import type { Step } from "@/types";

function toolColor(tool: string): string {
  const colors: Record<string, string> = {
    llm: "#8b5cf6", sql: "#06b6d4", http: "#f59e0b",
    vector_search: "#10b981", none: "#4a5568",
  };
  return colors[tool] ?? "#94a3b8";
}

function formatDuration(ms: number | null): string {
  if (ms === null) return "—";
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

function StepRow({ step, isLast, defaultOpen }: { step: Step; isLast: boolean; defaultOpen: boolean }) {
  const [expanded, setExpanded] = useState(defaultOpen);
  const hasContent = step.input || step.output;

  return (
    <div id={`step-${step.index}`} style={{ display: "flex", gap: "0" }}>
      {/* Timeline connector */}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: "32px", flexShrink: 0 }}>
        <div style={{
          width: "10px", height: "10px", borderRadius: "50%",
          background: step.status === "succeeded" ? "var(--green)"
            : step.status === "failed" ? "var(--red)"
            : step.status === "running" ? "var(--accent)"
            : "var(--text-muted)",
          border: "2px solid var(--bg-card)",
          zIndex: 1, flexShrink: 0, marginTop: "6px",
          boxShadow: step.status === "failed" ? "0 0 8px rgba(239,68,68,0.4)" : undefined,
        }} />
        {!isLast && <div style={{ width: "1px", flex: 1, background: "var(--border)", marginTop: "4px" }} />}
      </div>

      {/* Step content */}
      <div style={{ flex: 1, paddingLeft: "12px", paddingBottom: isLast ? 0 : "16px" }}>
        <div
          style={{ display: "flex", alignItems: "center", gap: "10px", cursor: hasContent ? "pointer" : "default", padding: "4px 0" }}
          onClick={() => hasContent && setExpanded(e => !e)}
        >
          <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-primary)" }}>
            {step.index}. {step.name}
          </span>
          <span style={{
            fontSize: "10px", fontWeight: 600, letterSpacing: "0.06em",
            padding: "2px 6px", borderRadius: "4px",
            background: `${toolColor(step.tool)}20`, color: toolColor(step.tool),
          }}>
            {step.tool}
          </span>
          <span className={`badge badge-${step.status}`} style={{ fontSize: "10px", padding: "1px 6px" }}>
            {step.status}
          </span>
          <span style={{ fontSize: "12px", color: "var(--text-muted)", marginLeft: "auto" }}>
            {formatDuration(step.duration_ms)}
          </span>
          {(step.tokens.input > 0 || step.tokens.output > 0) && (
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
              {step.tokens.input.toLocaleString()}↑ {step.tokens.output.toLocaleString()}↓
            </span>
          )}
          {hasContent && (
            <span style={{ fontSize: "11px", color: "var(--text-muted)", marginLeft: "4px" }}>
              {expanded ? "▲" : "▼"}
            </span>
          )}
        </div>

        {expanded && (
          <div style={{ marginTop: "8px", display: "flex", flexDirection: "column", gap: "8px" }}>
            {step.input && (
              <div>
                <div style={{ fontSize: "10px", fontWeight: 600, color: "var(--text-muted)", letterSpacing: "0.06em", marginBottom: "4px", textTransform: "uppercase" }}>
                  Input
                </div>
                <pre style={{
                  background: "var(--bg-surface)", border: "1px solid var(--border)",
                  borderRadius: "6px", padding: "10px 12px",
                  fontSize: "12px", color: "var(--text-secondary)",
                  margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-word",
                  fontFamily: "monospace", maxHeight: "200px", overflow: "auto",
                }}>{step.input}</pre>
              </div>
            )}
            {step.output && (
              <div>
                <div style={{ fontSize: "10px", fontWeight: 600, color: "var(--text-muted)", letterSpacing: "0.06em", marginBottom: "4px", textTransform: "uppercase" }}>
                  Output
                </div>
                <pre style={{
                  background: "var(--bg-surface)", border: "1px solid var(--border)",
                  borderRadius: "6px", padding: "10px 12px",
                  fontSize: "12px", color: "var(--text-secondary)",
                  margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-word",
                  fontFamily: "monospace", maxHeight: "200px", overflow: "auto",
                }}>{step.output}</pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function StepsList({ steps }: { steps: Step[] }) {
  // Deep-link support: /runs/run_0042#step-3 opens that step expanded
  const [deepLinkedStep, setDeepLinkedStep] = useState<number | null>(null);

  useEffect(() => {
    const hash = window.location.hash; // e.g. "#step-3"
    if (hash.startsWith("#step-")) {
      const idx = parseInt(hash.replace("#step-", ""));
      if (!isNaN(idx)) {
        setDeepLinkedStep(idx);
        // Scroll to element after render
        setTimeout(() => {
          document.getElementById(`step-${idx}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
        }, 100);
      }
    }
  }, []);

  return (
    <div>
      {steps.map((step, i) => (
        <StepRow
          key={step.index}
          step={step}
          isLast={i === steps.length - 1}
          defaultOpen={step.index === deepLinkedStep}
        />
      ))}
    </div>
  );
}
