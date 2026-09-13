import { useMemo, useState, useEffect } from "react";
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
import { getProfitability } from "../api/client.js";
import { SkeletonChart } from "../components/Skeleton.jsx";
import ErrorState from "../components/ErrorState.jsx";
import { formatCurrency, formatPercent } from "../utils/format.js";

const SORTS = [
  { key: "net_profit", label: "Net profit" },
  { key: "total_volume", label: "Volume" },
  { key: "default_rate", label: "Default rate" },
];

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="card px-3 py-2 text-xs">
      <div className="text-paper font-medium mb-1">{label}</div>
      <div className="num text-paper-dim">Net profit: {formatCurrency(d.net_profit)}</div>
      <div className="num text-paper-dim">Default rate: {formatPercent(d.default_rate)}</div>
    </div>
  );
}

export default function Profitability() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState("net_profit");
  const [onlyLosses, setOnlyLosses] = useState(false);
  const [highlighted, setHighlighted] = useState(null);

  function load() {
    setLoading(true);
    setError(null);
    getProfitability()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  const chartData = useMemo(() => {
    if (!data) return [];
    let rows = [...data.categories];
    if (onlyLosses) rows = rows.filter((r) => r.net_profit < 0);
    rows.sort((a, b) => b[sortKey] - a[sortKey]);
    return rows;
  }, [data, sortKey, onlyLosses]);

  if (loading) return <div className="max-w-5xl"><SkeletonChart height={280} /></div>;
  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="max-w-5xl">
      <div className="card p-5 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h2 className="font-display font-medium text-paper text-sm">
            Net profit by merchant category
          </h2>
          <div className="flex items-center gap-2">
            <div className="flex rounded-md border border-ink-border overflow-hidden text-xs">
              {SORTS.map((s) => (
                <button
                  key={s.key}
                  onClick={() => setSortKey(s.key)}
                  className={`focus-ring px-3 py-1.5 transition-colors ${
                    sortKey === s.key
                      ? "bg-gold text-ink font-medium"
                      : "bg-ink-surface2 text-paper-dim hover:text-paper"
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
            <button
              onClick={() => setOnlyLosses((v) => !v)}
              className={`focus-ring text-xs px-3 py-1.5 rounded-md border transition-colors ${
                onlyLosses
                  ? "border-coral text-coral bg-coral/10"
                  : "border-ink-border text-paper-dim hover:text-paper"
              }`}
            >
              Losses only
            </button>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} margin={{ top: 4, right: 8, left: 8, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2A3350" vertical={false} />
            <XAxis
              dataKey="merchant_category"
              tick={{ fill: "#8B92AB", fontSize: 11 }}
              angle={-35}
              textAnchor="end"
              interval={0}
              height={70}
            />
            <YAxis
              tick={{ fill: "#8B92AB", fontSize: 11 }}
              tickFormatter={(v) => formatCurrency(v, { compact: true })}
            />
            <Tooltip content={<ChartTooltip />} cursor={{ fill: "#1C2339" }} />
            <Bar
              dataKey="net_profit"
              radius={[4, 4, 0, 0]}
              onClick={(entry) => setHighlighted(entry.merchant_category)}
              cursor="pointer"
            >
              {chartData.map((entry, i) => {
                const isDim = highlighted && highlighted !== entry.merchant_category;
                return (
                  <Cell
                    key={i}
                    fill={entry.net_profit >= 0 ? "#4FB8A8" : "#E2604F"}
                    opacity={isDim ? 0.35 : 1}
                  />
                );
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        {highlighted && (
          <button
            onClick={() => setHighlighted(null)}
            className="focus-ring text-xs text-gold hover:text-gold-soft transition-colors mt-2"
          >
            Clear highlight
          </button>
        )}
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-ink-border text-left text-xs text-paper-dim uppercase tracking-wide">
              <th className="px-5 py-3 font-medium">Category</th>
              <th className="px-5 py-3 font-medium text-right">Volume</th>
              <th className="px-5 py-3 font-medium text-right">Fee revenue</th>
              <th className="px-5 py-3 font-medium text-right">Default losses</th>
              <th className="px-5 py-3 font-medium text-right">Net profit</th>
              <th className="px-5 py-3 font-medium text-right">Default rate</th>
            </tr>
          </thead>
          <tbody>
            {chartData.map((row) => (
              <tr
                key={row.merchant_category}
                onClick={() =>
                  setHighlighted(
                    highlighted === row.merchant_category ? null : row.merchant_category
                  )
                }
                className={`border-b border-ink-border last:border-0 cursor-pointer transition-colors ${
                  highlighted === row.merchant_category
                    ? "bg-ink-surface2"
                    : "hover:bg-ink-surface2/50"
                }`}
              >
                <td className="px-5 py-3 text-paper">{row.merchant_category}</td>
                <td className="px-5 py-3 text-right num text-paper-dim">
                  {formatCurrency(row.total_volume)}
                </td>
                <td className="px-5 py-3 text-right num text-paper-dim">
                  {formatCurrency(row.total_fee_revenue)}
                </td>
                <td className="px-5 py-3 text-right num text-coral">
                  {formatCurrency(row.total_default_losses)}
                </td>
                <td
                  className={`px-5 py-3 text-right num font-medium ${
                    row.net_profit >= 0 ? "text-teal" : "text-coral"
                  }`}
                >
                  {formatCurrency(row.net_profit)}
                </td>
                <td className="px-5 py-3 text-right num text-paper-dim">
                  {formatPercent(row.default_rate)}
                </td>
              </tr>
            ))}
            {chartData.length === 0 && (
              <tr>
                <td colSpan={6} className="px-5 py-8 text-center text-paper-dim text-sm">
                  No categories match this filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
