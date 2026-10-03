import Link from "next/link";

export default function NotFound() {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "60vh", textAlign: "center" }}>
      <div style={{ fontSize: "72px", marginBottom: "16px", lineHeight: 1 }}>404</div>
      <h2 style={{ fontSize: "20px", fontWeight: 700, marginBottom: "8px" }}>Run not found</h2>
      <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginBottom: "24px" }}>
        That run ID doesn&apos;t exist in the dataset.
      </p>
      <Link href="/runs" className="btn btn-primary">← Back to runs</Link>
    </div>
  );
}
