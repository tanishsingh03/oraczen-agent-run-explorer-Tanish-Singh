export default function Loading() {
  return (
    <div style={{ maxWidth: "1200px" }}>
      <div style={{ marginBottom: "24px" }}>
        <div style={{ height: "28px", width: "160px", background: "var(--bg-hover)", borderRadius: "6px", marginBottom: "8px" }} />
        <div style={{ height: "16px", width: "320px", background: "var(--bg-hover)", borderRadius: "4px", opacity: 0.5 }} />
      </div>
      {/* Filter skeleton */}
      <div className="card" style={{ padding: "16px 20px", marginBottom: "20px", height: "70px" }} />
      {/* Table skeleton */}
      <div className="card" style={{ overflow: "hidden" }}>
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} style={{
            display: "flex", gap: "20px", padding: "14px 16px",
            borderBottom: i < 7 ? "1px solid var(--border)" : "none",
            alignItems: "center",
          }}>
            <div style={{ width: "80px", height: "14px", background: "var(--bg-hover)", borderRadius: "4px" }} />
            <div style={{ width: "120px", height: "20px", background: "var(--bg-hover)", borderRadius: "4px" }} />
            <div style={{ width: "70px", height: "20px", background: "var(--bg-hover)", borderRadius: "10px" }} />
            <div style={{ flex: 1, height: "14px", background: "var(--bg-hover)", borderRadius: "4px", opacity: 0.5 }} />
            <div style={{ width: "50px", height: "14px", background: "var(--bg-hover)", borderRadius: "4px", opacity: 0.4 }} />
          </div>
        ))}
      </div>
      <style>{`
        @keyframes shimmer {
          0% { opacity: 0.4; }
          50% { opacity: 0.8; }
          100% { opacity: 0.4; }
        }
        .card > div { animation: shimmer 1.4s ease-in-out infinite; }
      `}</style>
    </div>
  );
}
