export default function MetricCard({ label, value, hint, tone = "teal" }) {
  const toneStyles = {
    teal: "border-teal-200 bg-teal-50",
    orange: "border-orange-200 bg-orange-50",
    slate: "border-slate-200 bg-slate-50"
  };

  return (
    <article className={`rounded-2xl border p-4 ${toneStyles[tone] ?? toneStyles.slate}`}>
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="mt-2 font-display text-4xl font-extrabold text-ink">{value}</p>
      <p className="mt-1 text-sm text-slate-600">{hint}</p>
    </article>
  );
}
