import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { getSegmentation } from "../api/client.js";
import { SkeletonGrid } from "../components/Skeleton.jsx";
import ErrorState from "../components/ErrorState.jsx";
import { formatCurrency, formatPercent, formatNumber } from "../utils/format.js";

export default function Segmentation() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);

  function load() {
    setLoading(true);
    setError(null);
    getSegmentation()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  if (loading) return <div className="max-w-5xl"><SkeletonGrid count={4} cols="md:grid-cols-2" /></div>;
  if (error) return <ErrorState message={error} onRetry={load} />;

  const portfolioAvgSpend =
    data.segments.reduce((sum, s) => sum + s.avg_total_spend * s.customer_count, 0) /
    data.total_customers;

  const activeSeg = data.segments.find((s) => s.segment_name === selected);

  return (
    <div className="max-w-5xl">
      <p className="text-sm text-paper-dim mb-5">
        {formatNumber(data.total_customers)} customers grouped by spend, transaction frequency, and credit quality.
        Click a segment to compare it against the portfolio average.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data.segments.map((seg) => {
          const isActive = selected === seg.segment_name;
          return (
            <motion.button
              key={seg.segment_name}
              onClick={() => setSelected(isActive ? null : seg.segment_name)}
              whileHover={{ y: -2 }}
              className={`card p-5 text-left transition-colors focus-ring ${
                isActive ? "border-gold" : "hover:border-paper-dim/40"
              }`}
            >
              <div className="flex items-baseline justify-between mb-4">
                <h3 className="font-display font-medium text-paper">{seg.segment_name}</h3>
                <span className="num text-xs text-paper-dim">
                  {formatNumber(seg.customer_count)} customers
                </span>
              </div>

              <dl className="grid grid-cols-2 gap-y-3 gap-x-4 text-sm">
                <div>
                  <dt className="text-paper-dim text-xs mb-0.5">Avg. income</dt>
                  <dd className="num text-paper">{formatCurrency(seg.avg_income)}</dd>
                </div>
                <div>
                  <dt className="text-paper-dim text-xs mb-0.5">Avg. credit score</dt>
                  <dd className="num text-paper">{formatNumber(seg.avg_credit_score, 0)}</dd>
                </div>
                <div>
                  <dt className="text-paper-dim text-xs mb-0.5">Avg. transactions</dt>
                  <dd className="num text-paper">{formatNumber(seg.avg_transaction_count, 1)}</dd>
                </div>
                <div>
                  <dt className="text-paper-dim text-xs mb-0.5">Avg. total spend</dt>
                  <dd className="num text-paper">{formatCurrency(seg.avg_total_spend)}</dd>
                </div>
                <div className="col-span-2 pt-2 border-t border-ink-border">
                  <dt className="text-paper-dim text-xs mb-0.5">Default rate</dt>
                  <dd className={`num ${seg.default_rate > 0.1 ? "text-coral" : "text-teal"}`}>
                    {formatPercent(seg.default_rate)}
                  </dd>
                </div>
              </dl>
            </motion.button>
          );
        })}
      </div>

      {activeSeg && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="card p-5 mt-4 overflow-hidden"
        >
          <h3 className="font-display font-medium text-paper mb-3 text-sm">
            {activeSeg.segment_name} vs. portfolio average
          </h3>
          <div className="text-sm text-paper-dim leading-relaxed">
            This segment spends{" "}
            <span className={activeSeg.avg_total_spend >= portfolioAvgSpend ? "text-teal" : "text-coral"}>
              {formatCurrency(Math.abs(activeSeg.avg_total_spend - portfolioAvgSpend))}{" "}
              {activeSeg.avg_total_spend >= portfolioAvgSpend ? "more" : "less"}
            </span>{" "}
            on average than the portfolio-wide mean of {formatCurrency(portfolioAvgSpend)}, with a{" "}
            <span className={activeSeg.default_rate <= 0.1 ? "text-teal" : "text-coral"}>
              {formatPercent(activeSeg.default_rate)} default rate
            </span>
            .
          </div>
        </motion.div>
      )}
    </div>
  );
}
