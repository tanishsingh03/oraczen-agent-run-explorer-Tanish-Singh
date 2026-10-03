"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/runs", label: "Runs", icon: "▶" },
  { href: "/dashboard", label: "Dashboard", icon: "◈" },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <>
      <style>{`
        .nav-link { display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:8px;margin-bottom:4px;font-size:13px;text-decoration:none;transition:all 0.15s; }
        .nav-link:not(.active):hover { background:var(--bg-hover);color:var(--text-primary)!important; }
      `}</style>
      <aside style={{
        width: "220px", minHeight: "100vh",
        background: "var(--bg-surface)",
        borderRight: "1px solid var(--border)",
        display: "flex", flexDirection: "column", flexShrink: 0,
        position: "sticky", top: 0, height: "100vh",
      }}>
        {/* Logo */}
        <div style={{ padding: "24px 20px 20px", borderBottom: "1px solid var(--border)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{
              width: "32px", height: "32px",
              background: "linear-gradient(135deg, #3b82f6, #8b5cf6)",
              borderRadius: "8px",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: "14px",
            }}>⚡</div>
            <div>
              <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)" }}>
                Run Explorer
              </div>
              <div style={{ fontSize: "10px", color: "var(--text-muted)", letterSpacing: "0.05em" }}>
                AGENT TRACES
              </div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav style={{ padding: "16px 12px", flex: 1 }}>
          {navItems.map(({ href, label, icon }) => {
            const active = pathname === href || pathname.startsWith(href + "/");
            return (
              <Link
                key={href}
                href={href}
                className={`nav-link${active ? " active" : ""}`}
                style={{
                  fontWeight: active ? 600 : 400,
                  color: active ? "var(--text-primary)" : "var(--text-secondary)",
                  background: active ? "var(--bg-hover)" : "transparent",
                  borderLeft: active ? "2px solid var(--accent)" : "2px solid transparent",
                }}
              >
                <span style={{ fontSize: "14px" }}>{icon}</span>
                {label}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div style={{ padding: "16px 20px", borderTop: "1px solid var(--border)" }}>
          <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
            Backend: <span style={{ color: "var(--green)" }}>●</span> localhost:8000
          </div>
        </div>
      </aside>
    </>
  );
}
