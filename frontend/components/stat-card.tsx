interface StatCardProps {
  label: string;
  value: string;
  meta: string;
  tone?: "positive" | "warning";
}

export function StatCard({ label, value, meta, tone = "positive" }: StatCardProps) {
  return (
    <article className="card kpi">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
      <div className={tone === "positive" ? "trend-positive" : "trend-warning"}>{meta}</div>
    </article>
  );
}
