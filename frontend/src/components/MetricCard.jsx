import { motion } from "framer-motion";
import AnimatedNumber from "./AnimatedNumber.jsx";

export default function MetricCard({ label, rawValue, format, value, sublabel, tone = "default" }) {
  const toneClass =
    tone === "positive"
      ? "text-teal"
      : tone === "negative"
      ? "text-coral"
      : "text-paper";

  return (
    <motion.div
      whileHover={{ y: -2, borderColor: "#D4A94E" }}
      transition={{ duration: 0.15 }}
      className="card p-5"
    >
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
    </motion.div>
  );
}
