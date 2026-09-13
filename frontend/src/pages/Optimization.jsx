import { useMemo, useState, useEffect } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ReferenceDot,
} from "recharts";
import {
  useOptimization,
  orderedStrategies,
} from "../hooks/useOptimization.js";
import AssumptionControls from "../components/AssumptionControls.jsx";
import Caveats, { Flag } from "../components/Caveats.jsx";
import MetricCard from "../components/MetricCard.jsx";
import { SkeletonGrid, SkeletonChart } from "../components/Skeleton.jsx";
import ErrorState from "../components/ErrorState.jsx";
import { formatCurrency, formatPercent } from "../utils/format.js";

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="card px-3 py-2 text-xs space-y-0.5">
      <div className="num text-paper font-medium">
        Threshold {d.approval_threshold}
      </div>
      <div className="num text-paper-dim">
        Approval rate: {d.approval_rate_pct}%
      </div>
      <div className="num text-paper-dim">
        Volume retained: {d.volume_retained_pct}%
      </div>
      <div className="num text-paper-dim">
        Approved default rate: {formatPercent(d.approved_default_rate)}
      </div>
      <div className={`num ${d.projected_net_profit >= 0 ? "text-teal" : "text-coral"}`}>
        Net profit: {formatCurrency(d.projected_net_profit)}
      </div>
    </div>
  );
}

export default function Optimization() {
  const { data, error, loading, reload } = useOptimization();
  const [sliderIndex, setSliderIndex] = useState(null);

  // Snap to the recommended point whenever a new simulation arrives.
  useEffect(() => {
    if (!data?.simulated_points?.length) return;
    const target = data.recommended_threshold;
    const idx = data.simulated_points.findIndex(
      (p) => p.approval_threshold === target
    );
    setSliderIndex(idx >= 0 ? idx : data.simulated_points.length - 1);
  }, [data]);

  const selected = useMemo(() => {
    if (!data?.simulated_points || sliderIndex === null) return null;
    return data.simulated_points[sliderIndex];
  }, [data, sliderIndex]);

  if (loading && !data)
    return (
      <div className="max-w-5xl space-y-6">
        <SkeletonGrid count={3} cols="sm:grid-cols-3" />
        <SkeletonChart />
      </div>
    );
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data) return null;

  const legacy = data.legacy_baseline;
  const strategies = orderedStrategies(data);
  const isRecommended =
    selected?.approval_threshold === data.recommended_threshold;
  const deltaVsLegacy = selected
    ? selected.projected_net_profit - legacy.projected_net_profit
    : 0;

  function jumpToStrategy(threshold) {
    const idx = data.simulated_points.findIndex(
      (p) => p.approval_threshold === threshold
    );
    if (idx >= 0) setSliderIndex(idx);
  }

  return (
    <div className="max-w-5xl space-y-6">
      <AssumptionControls />

      {loading && (
        <p className="text-xs text-gold">Recomputing under new assumptions…</p>
      )}

      {/* Selected point */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          label={isRecommended ? "Threshold (recommended)" : "Threshold (custom)"}
          value={selected?.approval_threshold?.toFixed(4)}
          tone={isRecommended ? "default" : "positive"}
          sublabel={
            isRecommended
              ? "The strategy this product recommends"
              : "Exploring — not the recommendation"
          }
        />
        <MetricCard
          label="Projected net profit"
          rawValue={selected?.projected_net_profit}
          format={(v) => formatCurrency(v)}
          tone={selected?.projected_net_profit >= 0 ? "positive" : "negative"}
          sublabel={`${deltaVsLegacy >= 0 ? "+" : ""}${formatCurrency(deltaVsLegacy)} vs current policy`}
        />
        <MetricCard
          label="Approval rate"
          value={`${selected?.approval_rate_pct}%`}
          sublabel={`${selected ? (selected.approval_rate_pct - legacy.approval_rate_pct).toFixed(2) : "—"}pp vs current · ${selected?.volume_retained_pct}% of volume`}
        />
      </div>

      {/* Profit curve */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-display font-medium text-paper text-sm">
            Net profit vs approval threshold
          </h2>
          {!isRecommended && data.recommended_threshold != null && (
            <button
              onClick={() => jumpToStrategy(data.recommended_threshold)}
              className="focus-ring text-xs text-gold hover:text-gold-soft transition-colors"
            >
              Back to recommended
            </button>
          )}
        </div>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart
            data={data.simulated_points}
            margin={{ top: 4, right: 16, left: 8, bottom: 4 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#2A3350" vertical={false} />
            <XAxis
              dataKey="approval_threshold"
              tick={{ fill: "#8B92AB", fontSize: 11 }}
            />
            <YAxis
              tick={{ fill: "#8B92AB", fontSize: 11 }}
              tickFormatter={(v) => formatCurrency(v, { compact: true })}
            />
            <Tooltip content={<ChartTooltip />} />
            <ReferenceLine y={0} stroke="#2A3350" />
            <ReferenceLine
              y={legacy.projected_net_profit}
              stroke="#8B92AB"
              strokeDasharray="2 4"
              label={{
                value: "Current policy",
                fill: "#8B92AB",
                fontSize: 10,
                position: "insideBottomRight",
              }}
            />
            {data.recommended_threshold != null && (
              <ReferenceLine
                x={data.recommended_threshold}
                stroke="#D4A94E"
                strokeDasharray="4 4"
                label={{
                  value: "Recommended",
                  fill: "#D4A94E",
                  fontSize: 11,
                  position: "top",
                }}
              />
            )}
            {selected && (
              <ReferenceDot
                x={selected.approval_threshold}
                y={selected.projected_net_profit}
                r={6}
                fill="#4FB8A8"
                stroke="#0B0F1A"
                strokeWidth={2}
              />
            )}
            <Line
              type="monotone"
              dataKey="projected_net_profit"
              stroke="#4FB8A8"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>

        <div className="mt-5 pt-5 border-t border-ink-border">
          <div className="flex items-center justify-between text-xs text-paper-dim mb-2">
            <span>
              Drag to explore any of the {data.simulated_points.length} simulated
              thresholds
            </span>
            <span className="num text-paper">
              {selected?.approval_threshold?.toFixed(4)}
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={data.simulated_points.length - 1}
            step={1}
            value={sliderIndex ?? 0}
            onChange={(e) => setSliderIndex(Number(e.target.value))}
            className="w-full accent-gold cursor-pointer focus-ring"
            aria-label="Approval threshold"
          />
        </div>
      </div>

      {/* Jump to a named strategy */}
      <div className="card p-5">
        <h2 className="font-display font-medium text-paper text-sm mb-3">
          Named strategies
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {strategies.map((s) => {
            const active = selected?.approval_threshold === s.approval_threshold;
            return (
              <button
                key={s.strategy_key}
                onClick={() => jumpToStrategy(s.approval_threshold)}
                className={`focus-ring text-left p-3 rounded-md border transition-colors ${
                  active
                    ? "border-gold bg-gold/10"
                    : "border-ink-border hover:border-paper-dim"
                }`}
              >
                <div className="flex items-baseline justify-between gap-2">
                  <span className="text-sm text-paper">{s.strategy_label}</span>
                  <span
                    className={`num text-sm ${s.projected_net_profit >= 0 ? "text-teal" : "text-coral"}`}
                  >
                    {formatCurrency(s.projected_net_profit)}
                  </span>
                </div>
                <div className="text-xs text-paper-dim mt-1 num">
                  {s.approval_rate_pct}% approved ·{" "}
                  {s.approval_rate_change_pp >= 0 ? "+" : ""}
                  {s.approval_rate_change_pp}pp
                  {!s.meets_volume_floor && (
                    <span className="text-gold"> · below volume floor</span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Recommendation */}
      <div className="card p-5">
        <h2 className="font-display font-medium text-paper text-sm mb-2">
          Recommendation
        </h2>
        <p className="text-sm text-paper-dim leading-relaxed">
          {data.recommended_reason}
        </p>
      </div>

      {data.boundary_optimum && (
        <Flag tone="warn">
          <strong>Boundary optimum.</strong> The profit maximum sits on the edge
          of the search grid, so profit may still be improving beyond it. Treat
          it as a grid artifact rather than a located optimum.
        </Flag>
      )}

      {data.volume_floor_feasible === false && (
        <Flag tone="warn">
          <strong>Volume floor infeasible.</strong> No threshold both keeps{" "}
          {data.min_approval_rate_pct}% of transactions approved and clears the
          profit floor. Lower the floor, or accept that declining alone cannot
          fix the book.
        </Flag>
      )}

      <Caveats caveats={data.caveats} />
    </div>
  );
}
