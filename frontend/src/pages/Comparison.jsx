import { useState, useEffect } from "react";
import { useOptimization, orderedStrategies } from "../hooks/useOptimization.js";
import AssumptionControls from "../components/AssumptionControls.jsx";
import Caveats from "../components/Caveats.jsx";
import { SkeletonChart } from "../components/Skeleton.jsx";
import ErrorState from "../components/ErrorState.jsx";
import { formatCurrency, formatPercent } from "../utils/format.js";

const METRICS = [
  { key: "approval_rate_pct", label: "Approval rate", fmt: (v) => `${v}%` },
  { key: "volume_retained_pct", label: "Volume retained", fmt: (v) => (v == null ? "—" : `${v}%`) },
  { key: "approved_default_rate", label: "Approved default rate", fmt: (v) => formatPercent(v, { digits: 2 }) },
  { key: "projected_fee_revenue", label: "Fee revenue", fmt: (v) => formatCurrency(v) },
  { key: "projected_default_losses", label: "Expected loss", fmt: (v) => formatCurrency(v) },
  { key: "projected_net_profit", label: "Net profit", fmt: (v) => formatCurrency(v), signed: true, emphasis: true },
];

export default function Comparison() {
  const { data, error, loading, reload } = useOptimization();
  const [enabled, setEnabled] = useState(null);

  useEffect(() => {
    if (!data?.strategies) return;
    setEnabled(Object.keys(data.strategies));
  }, [data]);

  if (loading && !data)
    return <div className="max-w-6xl"><SkeletonChart height={420} /></div>;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data || !enabled) return null;

  const strategies = orderedStrategies(data).filter((s) =>
    enabled.includes(s.strategy_key)
  );

  // Baselines are always shown. A comparison that lets you hide the thing you
  // are comparing against is not a comparison.
  const columns = [
    {
      key: "__approve_all",
      label: "Approve all",
      sublabel: "Reference only",
      data: data.approve_all_baseline,
      isBaseline: true,
      muted: true,
    },
    {
      key: "__legacy",
      label: "Current policy",
      sublabel: `Credit score ≥ ${data.legacy_baseline.credit_score_cutoff}`,
      data: data.legacy_baseline,
      isBaseline: true,
    },
    ...strategies.map((s) => ({
      key: s.strategy_key,
      label: s.strategy_label,
      sublabel: `Threshold ${s.approval_threshold}`,
      data: s,
      isRecommended: s.strategy_key === data.recommended_strategy,
      meetsFloor: s.meets_volume_floor,
    })),
  ];

  // The highlighted column is the RECOMMENDED strategy, not the one with the
  // largest number in some filtered subset.
  //
  // An earlier version highlighted "most profitable among those meeting the
  // volume floor", which on this portfolio selects a strategy that still loses
  // $41,115 — and then labelled it "best" on the same screen where the
  // recommendation star sat on a different, profitable column. Two conflicting
  // answers to "which one?" is worse than none.
  const recommended = data.recommended_strategy
    ? data.strategies[data.recommended_strategy]
    : null;

  // Kept separately because the gap between these two is the finding worth
  // stating: the best strategy that satisfies the volume floor, which may
  // still be loss-making.
  const bestWithinFloor = strategies
    .filter((s) => s.meets_volume_floor)
    .reduce((a, b) => (!a || b.projected_net_profit > a.projected_net_profit ? b : a), null);

  function toggle(key) {
    setEnabled((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    );
  }

  return (
    <div className="max-w-6xl space-y-6">
      <AssumptionControls />

      {loading && (
        <p className="text-xs text-gold">Recomputing under new assumptions…</p>
      )}

      {/* Strategy selection */}
      <div className="card p-5">
        <h2 className="font-display font-medium text-paper text-sm mb-1">
          Strategies to compare
        </h2>
        <p className="text-xs text-paper-dim mb-3">
          Both baselines are always shown. Toggle strategies to narrow the
          comparison.
        </p>
        <div className="flex flex-wrap gap-2">
          {orderedStrategies(data).map((s) => (
            <button
              key={s.strategy_key}
              onClick={() => toggle(s.strategy_key)}
              className={`focus-ring text-xs px-3 py-1.5 rounded-md border transition-colors ${
                enabled.includes(s.strategy_key)
                  ? "border-gold text-gold bg-gold/10"
                  : "border-ink-border text-paper-dim hover:text-paper"
              }`}
            >
              {s.strategy_label}
            </button>
          ))}
        </div>
      </div>

      {/* Comparison table */}
      <div className="card overflow-x-auto">
        <table className="w-full text-sm min-w-[840px]">
          <thead>
            <tr className="border-b border-ink-border">
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wide text-paper-dim font-medium">
                Metric
              </th>
              {columns.map((col) => (
                <th key={col.key} className="px-4 py-3 text-right font-medium">
                  <div
                    className={`text-xs ${
                      col.isRecommended
                        ? "text-gold"
                        : col.muted
                        ? "text-paper-dim/60"
                        : "text-paper"
                    }`}
                  >
                    {col.label}
                    {col.isRecommended && " ★"}
                  </div>
                  <div className="text-[10px] text-paper-dim font-normal mt-0.5">
                    {col.sublabel}
                  </div>
                  {!col.isBaseline && !col.meetsFloor && (
                    <div className="text-[10px] text-gold font-normal mt-0.5">
                      below volume floor
                    </div>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {METRICS.map((m) => (
              <tr
                key={m.key}
                className={`border-b border-ink-border/50 ${
                  m.emphasis ? "bg-ink-surface2/30" : ""
                }`}
              >
                <td
                  className={`px-4 py-3 ${
                    m.emphasis ? "text-paper font-medium" : "text-paper-dim"
                  }`}
                >
                  {m.label}
                </td>
                {columns.map((col) => {
                  const v = col.data?.[m.key];
                  const isBest =
                    m.key === "projected_net_profit" &&
                    recommended &&
                    col.key === recommended.strategy_key;
                  const colorClass = m.signed
                    ? v >= 0
                      ? "text-teal"
                      : "text-coral"
                    : col.muted
                    ? "text-paper-dim/60"
                    : "text-paper-dim";
                  return (
                    <td
                      key={col.key}
                      className={`px-4 py-3 text-right num ${colorClass} ${
                        m.emphasis ? "font-semibold" : ""
                      } ${isBest ? "bg-gold/10" : ""}`}
                    >
                      {v == null ? "—" : m.fmt(v)}
                    </td>
                  );
                })}
              </tr>
            ))}

            {/* Improvement row — only meaningful against the legacy baseline */}
            <tr className="border-b border-ink-border/50">
              <td className="px-4 py-3 text-paper font-medium">
                vs current policy
              </td>
              {columns.map((col) => {
                if (col.key === "__legacy")
                  return (
                    <td key={col.key} className="px-4 py-3 text-right text-paper-dim num">
                      —
                    </td>
                  );
                const v =
                  col.data.projected_net_profit -
                  data.legacy_baseline.projected_net_profit;
                return (
                  <td
                    key={col.key}
                    className={`px-4 py-3 text-right num font-semibold ${
                      v >= 0 ? "text-teal" : "text-coral"
                    } ${col.muted ? "opacity-60" : ""}`}
                  >
                    {v >= 0 ? "+" : ""}
                    {formatCurrency(v)}
                  </td>
                );
              })}
            </tr>

            <tr>
              <td className="px-4 py-3 text-paper-dim">Approval change</td>
              {columns.map((col) => {
                if (col.isBaseline)
                  return (
                    <td key={col.key} className="px-4 py-3 text-right text-paper-dim num">
                      {col.key === "__legacy" ? "—" : `+${(100 - data.legacy_baseline.approval_rate_pct).toFixed(2)}pp`}
                    </td>
                  );
                return (
                  <td key={col.key} className="px-4 py-3 text-right num text-paper-dim">
                    {col.data.approval_rate_change_pp >= 0 ? "+" : ""}
                    {col.data.approval_rate_change_pp}pp
                  </td>
                );
              })}
            </tr>
          </tbody>
        </table>
      </div>

      {/* How to read this */}
      <div className="card p-5">
        <h2 className="font-display font-medium text-paper text-sm mb-3">
          How to read this
        </h2>
        <div className="space-y-3 text-sm text-paper-dim leading-relaxed">
          <p>
            <span className="text-paper">Approve all</span> is shown only to
            isolate the book's gross economics. It is not a lending policy anyone
            operates, and it should never be the comparator for an improvement
            claim — doing so inflates every number by the cost of a straw man.
          </p>
          <p>
            <span className="text-paper">Current policy</span> is the honest
            baseline: a credit-score cutoff that ignores installment count,
            merchant category and employment status. Every improvement figure on
            this page is measured against it.
          </p>
          <p>
            <span className="text-paper">Risk-adjusted at current volume</span>{" "}
            holds approval rate roughly constant, so its entire gain is
            attributable to better selection rather than to lending less. It is
            the cleanest measure of what risk adjustment is actually worth.
          </p>
          <p>
            <span className="text-paper">Maximum profit</span> is an upper bound,
            not a candidate. It is reported for completeness and excluded from
            the best-performer highlight, because a strategy that declines most
            of the book is not one a lender would ship.
          </p>
          {recommended && (
            <p className="pt-2 border-t border-ink-border">
              <span className="text-gold">★ Recommended:</span>{" "}
              <span className="text-paper">{recommended.strategy_label}</span> at{" "}
              <span className={`num ${recommended.projected_net_profit >= 0 ? "text-teal" : "text-coral"}`}>
                {formatCurrency(recommended.projected_net_profit)}
              </span>
              , approving{" "}
              <span className="num">{recommended.approval_rate_pct}%</span> of
              transactions —{" "}
              <span className="num">
                {recommended.profit_vs_legacy >= 0 ? "+" : ""}
                {formatCurrency(recommended.profit_vs_legacy)}
              </span>{" "}
              against current policy.
            </p>
          )}
          {bestWithinFloor && bestWithinFloor.projected_net_profit < 0 && (
            <p>
              Note the tension this table exposes: the most profitable strategy
              that actually satisfies the{" "}
              {data.min_approval_rate_pct}% volume floor is{" "}
              <span className="text-paper">{bestWithinFloor.strategy_label}</span>
              , and it still loses{" "}
              <span className="num text-coral">
                {formatCurrency(Math.abs(bestWithinFloor.projected_net_profit))}
              </span>
              . The recommendation deliberately goes below the floor, because
              holding the floor means accepting a loss. That is a business
              decision, not an analytical one — which is why both columns are
              shown rather than one.
            </p>
          )}
        </div>
      </div>

      <Caveats caveats={data.caveats} />
    </div>
  );
}
