import { useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from "recharts";
import { getExplainability } from "../api/client.js";
import Loader from "../components/Loader.jsx";
import ErrorState from "../components/ErrorState.jsx";
import { formatPercent } from "../utils/format.js";

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="card px-3 py-2 text-xs">
      <div className="num text-paper font-medium mb-1">{d.feature}</div>
      <div className="num text-paper-dim">Value: {d.value}</div>
      <div className={`num ${d.shap_contribution >= 0 ? "text-coral" : "text-teal"}`}>
        SHAP: {d.shap_contribution > 0 ? "+" : ""}{d.shap_contribution}
      </div>
    </div>
  );
}

export default function Explainability() {
  const [customerId, setCustomerId] = useState("CUST100000");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await getExplainability(customerId);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  }

  const chartData = result?.top_contributions
    ? [...result.top_contributions].sort((a, b) => a.shap_contribution - b.shap_contribution)
    : [];

  return (
    <div className="max-w-4xl">
      <form onSubmit={handleSubmit} className="flex gap-3 mb-6">
        <input
          className="flex-1 bg-ink-surface2 border border-ink-border rounded-md px-3 py-2 text-sm num text-paper focus-ring"
          value={customerId}
          onChange={(e) => setCustomerId(e.target.value)}
          placeholder="CUST100000"
        />
        <button
          type="submit"
          disabled={loading}
          className="focus-ring px-5 py-2 rounded-md bg-gold text-ink font-medium text-sm hover:bg-gold-soft transition-colors disabled:opacity-50"
        >
          {loading ? "Explaining…" : "Explain"}
        </button>
      </form>

      {loading && <Loader label="Computing SHAP values" />}
      {error && <ErrorState message={error} />}

      {result && (
        <>
          <div className="card p-5 mb-6 flex items-center gap-8">
            <div>
              <div className="text-xs text-paper-dim mb-1">Default probability</div>
              <div className="num text-2xl font-semibold text-paper">
                {formatPercent(result.default_probability)}
              </div>
            </div>
            <div>
              <div className="text-xs text-paper-dim mb-1">Base rate (model average)</div>
              <div className="num text-2xl font-semibold text-paper-dim">
                {result.base_value}
              </div>
            </div>
          </div>

          <div className="card p-5">
            <h2 className="font-display font-medium text-paper mb-1 text-sm">
              Feature contributions
            </h2>
            <p className="text-xs text-paper-dim mb-4">
              Red pushes risk up, teal pushes it down. Sorted by SHAP contribution.
            </p>
            <ResponsiveContainer width="100%" height={Math.max(240, chartData.length * 36)}>
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 4, right: 24, left: 8, bottom: 4 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#2A3350" horizontal={false} />
                <XAxis type="number" tick={{ fill: "#8B92AB", fontSize: 11 }} />
                <YAxis
                  type="category"
                  dataKey="feature"
                  tick={{ fill: "#8B92AB", fontSize: 11 }}
                  width={140}
                />
                <Tooltip content={<ChartTooltip />} cursor={{ fill: "#1C2339" }} />
                <Bar dataKey="shap_contribution" radius={[0, 4, 4, 0]}>
                  {chartData.map((entry, i) => (
                    <Cell key={i} fill={entry.shap_contribution >= 0 ? "#E2604F" : "#4FB8A8"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      {!loading && !error && !result && (
        <div className="card p-5 text-sm text-paper-dim">
          Enter a customer ID to see which features drove their default-risk prediction, using their historical average transaction as the example.
        </div>
      )}
    </div>
  );
}
