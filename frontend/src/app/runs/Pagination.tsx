"use client";
import { useRouter, useSearchParams } from "next/navigation";

interface Props {
  page: number;
  pageSize: number;
  total: number;
}

export default function Pagination({ page, pageSize, total }: Props) {
  const router = useRouter();
  const sp = useSearchParams();
  const totalPages = Math.ceil(total / pageSize);

  const go = (p: number) => {
    const params = new URLSearchParams(sp.toString());
    params.set("page", String(p));
    router.push(`/runs?${params.toString()}`);
  };

  const pages: (number | "...")[] = [];
  if (totalPages <= 7) {
    for (let i = 1; i <= totalPages; i++) pages.push(i);
  } else {
    pages.push(1);
    if (page > 3) pages.push("...");
    for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) pages.push(i);
    if (page < totalPages - 2) pages.push("...");
    pages.push(totalPages);
  }

  const btnStyle = (active: boolean, disabled?: boolean) => ({
    padding: "6px 10px",
    minWidth: "34px",
    borderRadius: "6px",
    border: "1px solid",
    borderColor: active ? "var(--accent)" : "var(--border)",
    background: active ? "var(--accent)" : "transparent",
    color: active ? "white" : disabled ? "var(--text-muted)" : "var(--text-secondary)",
    cursor: disabled ? "not-allowed" : "pointer",
    fontSize: "13px",
    transition: "all 0.15s",
  });

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "6px", justifyContent: "center", paddingTop: "8px" }}>
      <button style={btnStyle(false, page === 1)} disabled={page === 1} onClick={() => go(page - 1)}>
        ← Prev
      </button>
      {pages.map((p, i) =>
        p === "..." ? (
          <span key={`dot-${i}`} style={{ color: "var(--text-muted)", padding: "0 4px" }}>…</span>
        ) : (
          <button key={p} style={btnStyle(p === page)} onClick={() => go(p as number)}>
            {p}
          </button>
        )
      )}
      <button style={btnStyle(false, page === totalPages)} disabled={page === totalPages} onClick={() => go(page + 1)}>
        Next →
      </button>
    </div>
  );
}
