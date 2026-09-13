import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Cell,
} from "recharts";
import { getPortfolio, getProfitability } from "../api/client.js";
import { useOptimization, recommendedStrategy } from "../hooks/useOptimization.js";
import MetricCard from "../components/MetricCard.jsx";
import { SkeletonGrid, SkeletonChart } from "../components/Skeleton.jsx";
import ErrorState from "../components/ErrorState.jsx";
import { Flag } from "../components/Caveats.jsx";
import {
  formatCurrency,
  formatPercent,
  formatNumber,
  signGlyph,
} from "../utils/format.js";

function CategoryTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="card px-3 py-2 text-xs">
      <div className="text-paper font-medium mb-1">{d.merchant_category}</div>
      <div className="num text-paper-dim">
        Net profit: {formatCurrency(d.net_profit)}
      </div>
      <div className="num text-paper-dim">
        Default rate: {formatPercent(d.default_rate)}
      </div>
      <div className="num text-paper-dim">
        Volume: {formatCurrency(d.total_volume, { compact: true })}
      </div>
    </div>
  );
}

export default function Overview() {
  const [portfolio, setPortfolio] = useState(null);
  const [categories, setCategories] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const { data: opt, error: optError } = useOptimization();

  function load() {
    setLoading(true);
    setError(null);
    Promise.all([getPortfolio(), getProfitability()])
      .then(([p, c]) => {
        setPortfolio(p);
        setCategories(c.categories);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  if (loading)
    return (
      <div className="max-w-5xl">
        <SkeletonGrid count={4} cols="sm:grid-cols-2 lg:grid-cols-4" />
        <div className="mt-6">
          <SkeletonChart />
        </div>
      </div>
    );
  if (error) return <ErrorState message={error} onRetry={load} />;

  const legacy = opt?.legacy_baseline;
  const rec = recommendedStrategy(opt);

  // Loss concentration — computed here rather than assumed, so it stays true
  // if the assumptions change underneath it.
  const losers = categories.filter((c) => c.net_profit < 0);
  const totalLoss = losers.reduce((s, c) => s + c.net_profit, 0);
  const worst = [...losers].sort((a, b) => a.net_profit - b.net_profit);
  const worstShare = worst.length ? worst[0].net_profit / totalLoss : 0;
  const top4Share = worst
    .slice(0, 4)
    .reduce((s, c) => s + c.net_profit, 0) / (totalLoss || 1);

  const chartData = [...categories].sort((a, b) => a.net_profit - b.net_profit);

  return (
    <div className="max-w-5xl space-y-6">
      {/* The problem, in four numbers */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Current policy — net"
          rawValue={legacy?.projected_net_profit}
          format={(v) => `${signGlyph(v)} ${formatCurrency(v)}`}
          tone={legacy && legacy.projected_net_profit >= 0 ? "positive" : "negative"}
          sublabel={
            legacy
              ? `Credit score ≥ ${legacy.credit_score_cutoff} · ${legacy.approval_rate_pct}% approved`
              : "Loading baseline…"
          }
        />
        <MetricCard
          label="Fee revenue"
          rawValue={portfolio.total_fee_revenue}
          format={(v) => formatCurrency(v)}
          sublabel={`${formatNumber(portfolio.total_transactions)} transactions`}
        />
        <MetricCard
          label="Default losses"
          rawValue={portfolio.total_default_losses}
          format={(v) => formatCurrency(v)}
          tone="negative"
          sublabel={`${formatPercent(portfolio.overall_default_rate)} default rate · ${formatPercent(portfolio.loss_given_default)} LGD`}
        />
        <MetricCard
          label="Recommended change"
          rawValue={rec?.profit_vs_legacy}
          format={(v) => `${signGlyph(v)} ${formatCurrency(v)}`}
          tone={rec ? "positive" : "default"}
          value={rec ? undefined : "None shippable"}
          sublabel={
            rec
              ? `${rec.approval_rate_change_pp}pp approval · to ${formatCurrency(rec.projected_net_profit)}`
              : "No strategy clears the volume floor profitably"
          }
        />
      </div>

      {/* What is causing it */}
      <div className="card p-5">
        <div className="flex items-baseline justify-between mb-1">
          <h2 className="font-display font-medium text-paper text-sm">
            Where the money goes
          </h2>
          <Link
            to="/app/risk"
            className="focus-ring text-xs text-gold hover:text-gold-soft transition-colors"
          >
            Full risk analysis →
          </Link>
        </div>
        <p className="text-sm text-paper-dim mb-4 leading-relaxed">
          Net profit by merchant category, before any approval policy is
          applied. {losers.length} of {categories.length} categories lose money.{" "}
          <span className="text-paper">{worst[0]?.merchant_category}</span> alone
          accounts for {formatPercent(worstShare)} of the total loss, and the
          worst four for {formatPercent(top4Share)}.
        </p>

        <ResponsiveContainer width="100%" height={300}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 4, right: 16, left: 96, bottom: 4 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#2A3350" horizontal={false} />
            <XAxis
              type="number"
              tick={{ fill: "#8B92AB", fontSize: 11 }}
              tickFormatter={(v) => formatCurrency(v, { compact: true })}
            />
            <YAxis
              type="category"
              dataKey="merchant_category"
              tick={{ fill: "#8B92AB", fontSize: 11 }}
              width={92}
            />
            <Tooltip content={<CategoryTooltip />} cursor={{ fill: "#1C2339" }} />
            <ReferenceLine x={0} stroke="#2A3350" />
            <Bar dataKey="net_profit" radius={[0, 3, 3, 0]}>
              {chartData.map((d) => (
                <Cell
                  key={d.merchant_category}
                  fill={d.net_profit >= 0 ? "#4FB8A8" : "#E2604F"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* The finding, stated plainly */}
      <div className="card p-6">
        <h2 className="font-display font-medium text-paper mb-3">
          The risk-adjustment gap
        </h2>
        <div className="space-y-3 text-sm text-paper-dim leading-relaxed">
          <p>
            The current policy approves on credit score alone. Credit score is
            one general-purpose signal — it ignores installment count, merchant
            category and employment status, each of which carries independent
            default signal in this book.
          </p>
          <p>
            The result is concentrated: the loss-making categories are
            consistently large-ticket and high-default, priced at fee rates that
            do not compensate for the risk they carry. The two profitable
            categories are both small-ticket and low-risk.
          </p>
          {rec ? (
            <p>
              Scoring on all available signals instead recovers{" "}
              <span className="text-teal num">
                {formatCurrency(rec.profit_vs_legacy)}
              </span>{" "}
              — but it costs{" "}
              <span className="text-paper num">
                {Math.abs(rec.approval_rate_change_pp)}pp
              </span>{" "}
              of approval volume.{" "}
              <Link
                to="/app/decision"
                className="focus-ring text-gold hover:text-gold-soft transition-colors"
              >
                See the recommendation and its trade-off →
              </Link>
            </p>
          ) : (
            <p>
              Under the current assumptions, no approval threshold both clears
              the volume floor and returns the book to profit.{" "}
              <Link
                to="/app/simulator"
                className="focus-ring text-gold hover:text-gold-soft transition-colors"
              >
                Explore the trade-off →
              </Link>
            </p>
          )}
        </div>
      </div>

      {opt?.volume_floor_feasible === false && (
        <Flag tone="warn">
          <strong>The volume floor cannot be met profitably.</strong> No
          threshold both keeps {opt.min_approval_rate_pct}% of transactions
          approved and returns a profit. This is the central finding, not an
          error — declining transactions alone cannot fix this book without
          giving up more volume than the floor allows.
        </Flag>
      )}

      {optError && (
        <Flag tone="bad">
          Strategy simulation unavailable: {optError}. The portfolio figures
          above are unaffected.
        </Flag>
      )}

      <p className="text-xs text-paper-dim">
        Synthetic portfolio · {formatNumber(portfolio.total_customers)} customers
        · {formatNumber(portfolio.total_transactions)} transactions ·{" "}
        {formatCurrency(portfolio.total_volume, { compact: true })} gross volume.
        All figures are projections under stated assumptions, not realised
        results.
      </p>
    </div>
  );
}
