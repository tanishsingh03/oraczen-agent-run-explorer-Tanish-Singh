"use client";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useTransition } from "react";

const AGENTS = ["email-drafter", "support-router", "kpi-analyst", "contract-reviewer", "invoice-extractor"];
const STATUSES = ["succeeded", "failed", "running", "cancelled"];

interface Props {
  defaultQ: string;
  defaultStatus: string[];
  defaultAgent: string[];
  defaultSortBy: string;
  defaultSortDir: string;
  defaultStartedAfter: string;
  defaultStartedBefore: string;
}

export default function RunsFilters({
  defaultQ, defaultStatus, defaultAgent,
  defaultSortBy, defaultSortDir,
  defaultStartedAfter, defaultStartedBefore
}: Props) {
  const router = useRouter();
  const sp = useSearchParams();
  const [isPending, startTransition] = useTransition();

  const push = useCallback((updates: Record<string, string | string[] | null>) => {
    const params = new URLSearchParams(sp.toString());
    params.set("page", "1"); // reset page on any filter change
    for (const [key, val] of Object.entries(updates)) {
      params.delete(key);
      if (val === null || val === "" || (Array.isArray(val) && val.length === 0)) continue;
      if (Array.isArray(val)) val.forEach(v => params.append(key, v));
      else params.set(key, val);
    }
    startTransition(() => router.push(`/runs?${params.toString()}`));
  }, [router, sp]);

  const toggleMulti = (key: string, current: string[], value: string) => {
    const next = current.includes(value)
      ? current.filter(v => v !== value)
      : [...current, value];
    push({ [key]: next });
  };

  return (
    <div className="card" style={{ padding: "16px 20px", marginBottom: "20px" }}>
      <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", alignItems: "flex-end" }}>
        {/* Search */}
        <div style={{ flex: "1 1 200px", minWidth: "180px" }}>
          <label style={{ display: "block", fontSize: "11px", fontWeight: 600, color: "var(--text-muted)", marginBottom: "6px", letterSpacing: "0.06em", textTransform: "uppercase" }}>
            Search prompt
          </label>
          <div style={{ position: "relative" }}>
            <span style={{ position: "absolute", left: "10px", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)", fontSize: "12px" }}>🔍</span>
            <input
              className="input"
              style={{ paddingLeft: "28px" }}
              placeholder="e.g. renewal, billing..."
              defaultValue={defaultQ}
              onChange={e => {
                const val = e.target.value;
                const t = setTimeout(() => push({ q: val }), 400);
                return () => clearTimeout(t);
              }}
              id="search-input"
            />
          </div>
        </div>

        {/* Status filter */}
        <div style={{ flex: "0 0 auto" }}>
          <label style={{ display: "block", fontSize: "11px", fontWeight: 600, color: "var(--text-muted)", marginBottom: "6px", letterSpacing: "0.06em", textTransform: "uppercase" }}>
            Status
          </label>
          <div style={{ display: "flex", gap: "6px" }}>
            {STATUSES.map(s => (
              <button key={s} onClick={() => toggleMulti("status", defaultStatus, s)}
                className={`badge ${defaultStatus.includes(s) ? `badge-${s}` : ""}`}
                style={{
                  cursor: "pointer", border: "1px solid",
                  borderColor: defaultStatus.includes(s) ? "currentColor" : "var(--border)",
                  background: defaultStatus.includes(s) ? undefined : "transparent",
                  color: defaultStatus.includes(s) ? undefined : "var(--text-muted)",
                  transition: "all 0.15s",
                }}
              >{s}</button>
            ))}
          </div>
        </div>

        {/* Agent filter */}
        <div style={{ flex: "0 0 auto" }}>
          <label style={{ display: "block", fontSize: "11px", fontWeight: 600, color: "var(--text-muted)", marginBottom: "6px", letterSpacing: "0.06em", textTransform: "uppercase" }}>
            Agent
          </label>
          <select className="select" multiple
            value={defaultAgent}
            onChange={e => {
              const vals = Array.from(e.target.selectedOptions).map(o => o.value);
              push({ agent: vals });
            }}
            style={{ height: "36px", minWidth: "160px" }}
          >
            {AGENTS.map(a => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
        </div>

        {/* Date range */}
        <div>
          <label style={{ display: "block", fontSize: "11px", fontWeight: 600, color: "var(--text-muted)", marginBottom: "6px", letterSpacing: "0.06em", textTransform: "uppercase" }}>
            From
          </label>
          <input type="date" className="input" style={{ width: "140px" }}
            defaultValue={defaultStartedAfter}
            onChange={e => push({ started_after: e.target.value })}
          />
        </div>
        <div>
          <label style={{ display: "block", fontSize: "11px", fontWeight: 600, color: "var(--text-muted)", marginBottom: "6px", letterSpacing: "0.06em", textTransform: "uppercase" }}>
            To
          </label>
          <input type="date" className="input" style={{ width: "140px" }}
            defaultValue={defaultStartedBefore}
            onChange={e => push({ started_before: e.target.value })}
          />
        </div>

        {/* Sort */}
        <div>
          <label style={{ display: "block", fontSize: "11px", fontWeight: 600, color: "var(--text-muted)", marginBottom: "6px", letterSpacing: "0.06em", textTransform: "uppercase" }}>
            Sort by
          </label>
          <div style={{ display: "flex", gap: "6px" }}>
            <select className="select" value={defaultSortBy}
              onChange={e => push({ sort_by: e.target.value })}
            >
              <option value="started_at">Date</option>
              <option value="duration_ms">Duration</option>
              <option value="cost_usd">Cost</option>
            </select>
            <button className="btn btn-ghost" style={{ padding: "8px 10px" }}
              onClick={() => push({ sort_dir: defaultSortDir === "desc" ? "asc" : "desc" })}
              title={defaultSortDir === "desc" ? "Descending" : "Ascending"}
            >
              {defaultSortDir === "desc" ? "↓" : "↑"}
            </button>
          </div>
        </div>

        {/* Clear */}
        {(defaultQ || defaultStatus.length || defaultAgent.length || defaultStartedAfter || defaultStartedBefore) && (
          <div style={{ alignSelf: "flex-end" }}>
            <button className="btn btn-ghost" style={{ color: "var(--red)", borderColor: "rgba(239,68,68,0.3)" }}
              onClick={() => {
                startTransition(() => router.push("/runs"));
              }}
            >
              ✕ Clear
            </button>
          </div>
        )}

        {isPending && (
          <div style={{ alignSelf: "flex-end", fontSize: "12px", color: "var(--text-muted)", paddingBottom: "10px" }}>
            Loading…
          </div>
        )}
      </div>
    </div>
  );
}
