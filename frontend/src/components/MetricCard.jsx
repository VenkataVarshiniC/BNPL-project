import AnimatedNumber from "./AnimatedNumber.jsx";

export default function MetricCard({ label, rawValue, format, value, sublabel, tone = "default" }) {
  const toneClass =
    tone === "positive"
      ? "text-teal"
      : tone === "negative"
      ? "text-coral"
      : "text-paper";

  return (
    <div className="card p-5 transition-transform hover:-translate-y-0.5 hover:border-gold">
      <div className="text-xs uppercase tracking-wide text-paper-dim mb-2">
        {label}
      </div>
      <div className={`num text-2xl font-semibold ${toneClass}`}>
        {typeof rawValue === "number" && format ? (
          <AnimatedNumber value={rawValue} format={format} />
        ) : (
          value
        )}
      </div>
      {sublabel && <div className="text-xs text-paper-dim mt-1.5">{sublabel}</div>}
    </div>
  );
}
