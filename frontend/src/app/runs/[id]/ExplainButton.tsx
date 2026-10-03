"use client";
import { useState } from "react";
import { getExplainUrl } from "@/lib/api";

interface Props { runId: string; }

export default function ExplainButton({ runId }: Props) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  const explain = async () => {
    setText("");
    setError(null);
    setDone(false);
    setLoading(true);
    setOpen(true);
    try {
      const res = await fetch(getExplainUrl(runId), { method: "POST" });
      if (!res.ok) throw new Error(`${res.status}`);
      const reader = res.body?.getReader();
      if (!reader) throw new Error("No response body");
      const decoder = new TextDecoder();
      while (true) {
        const { done: d, value } = await reader.read();
        if (d) break;
        setText(prev => prev + decoder.decode(value));
      }
      setDone(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to explain");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ flexShrink: 0 }}>
      <button
        className="btn btn-primary"
        onClick={explain}
        disabled={loading}
        id="explain-button"
        style={{ whiteSpace: "nowrap", opacity: loading ? 0.7 : 1 }}
      >
        {loading ? (
          <><span style={{ display: "inline-block", animation: "spin 1s linear infinite" }}>◌</span> Explaining…</>
        ) : "✦ Explain this run"}
      </button>

      {open && (
        <div style={{
          marginTop: "12px",
          background: "linear-gradient(135deg, rgba(59,130,246,0.06) 0%, rgba(139,92,246,0.06) 100%)",
          border: "1px solid rgba(59,130,246,0.2)",
          borderRadius: "12px",
          padding: "16px 20px",
          width: "340px",
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
            <span style={{ fontSize: "12px", fontWeight: 600, letterSpacing: "0.06em", textTransform: "uppercase", color: "var(--accent)" }}>
              ✦ AI Explanation
            </span>
            <button
              onClick={() => { setOpen(false); setDone(false); setText(""); }}
              style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "16px", lineHeight: 1 }}
            >✕</button>
          </div>

          {error && <div style={{ color: "var(--red)", fontSize: "13px" }}>Error: {error}</div>}

          {!text && loading && (
            <div style={{ color: "var(--text-muted)", fontSize: "13px" }}>Generating explanation…</div>
          )}

          {text && (
            <p style={{ margin: 0, fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.7", whiteSpace: "pre-wrap" }}>
              {text}
              {loading && (
                <span style={{
                  display: "inline-block", width: "6px", height: "13px",
                  background: "var(--accent)", marginLeft: "2px",
                  animation: "blink 0.8s infinite", verticalAlign: "text-bottom",
                }} />
              )}
            </p>
          )}

          {done && (
            <div style={{ marginTop: "10px", fontSize: "11px", color: "var(--text-muted)", borderTop: "1px solid var(--border)", paddingTop: "8px" }}>
              Mock LLM provider · deterministic output
            </div>
          )}
        </div>
      )}

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }
      `}</style>
    </div>
  );
}
