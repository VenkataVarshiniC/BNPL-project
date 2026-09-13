import { useEffect, useMemo, useState } from "react";
import { getProfitability, getPortfolio } from "../api/client.js";
import { SkeletonChart } from "../components/Skeleton.jsx";
import ErrorState from "../components/ErrorState.jsx";
import {
  formatCurrency,
  formatPercent,
  formatNumber,
} from "../utils/format.js";

const COLUMNS = [
  { key: "merchant_category", label: "Category", numeric: false },
  { key: "transaction_count", label: "Txns", numeric: true, fmt: (v) => formatNumber(v) },
  { key: "total_volume", label: "Volume", numeric: true, fmt: (v) => formatCurrency(v, { compact: true }) },
  { key: "total_fee_revenue", label: "Fee revenue", numeric: true, fmt: (v) => formatCurrency(v) },
  { key: "total_default_losses", label: "Losses", numeric: true, fmt: (v) => formatCurrency(v) },
  { key: "net_profit", label: "Net profit", numeric: true, fmt: (v) => formatCurrency(v), signed: true },
  { key: "profit_margin_pct", label: "Margin", numeric: true, fmt: (v) => formatPercent(v, { fromFraction: false, digits: 2 }), signed: true },
  { key: "default_rate", label: "Default rate", numeric: true, fmt: (v) => formatPercent(v, { digits: 2 }) },
];

const FILTERS = [
  { key: "all", label: "All categories" },
  { key: "loss", label: "Loss-making only" },
  { key: "profit", label: "Profitable only" },
  { key: "highrisk", label: "Default rate > 10%" },
];

function SortIcon({ dir }) {
  return (
    <span className="text-gold ml-1 text-[10px]" aria-hidden="true">
      {dir === "asc" ? "▲" : "▼"}
    </span>
  );
}

function CategoryDetail({ row, totalLoss, portfolioProfit, onClose }) {
  const shareOfLoss = row.net_profit < 0 ? row.net_profit / totalLoss : 0;
  const avgTicket = row.total_volume / row.transaction_count;
  const effectiveFeeRate = row.total_fee_revenue / row.total_volume;

  return (
    <div className="card p-5 border-gold/40">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="font-display font-medium text-paper">
            {row.merchant_category}
          </h3>
          <p className="text-xs text-paper-dim mt-0.5">
            {formatNumber(row.transaction_count)} transactions ·{" "}
            {formatCurrency(row.total_volume)} volume
          </p>
        </div>
        <button
          onClick={onClose}
          className="focus-ring text-xs text-paper-dim hover:text-paper transition-colors"
        >
          Close ✕
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
        <div>
          <div className="text-xs text-paper-dim mb-1">Net profit</div>
          <div className={`num text-lg font-semibold ${row.net_profit >= 0 ? "text-teal" : "text-coral"}`}>
            {formatCurrency(row.net_profit)}
          </div>
        </div>
        <div>
          <div className="text-xs text-paper-dim mb-1">Average ticket</div>
          <div className="num text-lg text-paper">{formatCurrency(avgTicket)}</div>
        </div>
        <div>
          <div className="text-xs text-paper-dim mb-1">Effective fee rate</div>
          <div className="num text-lg text-paper">
            {formatPercent(effectiveFeeRate, { digits: 2 })}
          </div>
        </div>
        <div>
          <div className="text-xs text-paper-dim mb-1">Default rate</div>
          <div className="num text-lg text-paper">
            {formatPercent(row.default_rate, { digits: 2 })}
          </div>
        </div>
      </div>

      <div className="text-sm text-paper-dim leading-relaxed border-t border-ink-border pt-4">
        {row.net_profit < 0 ? (
          <>
            This category contributes{" "}
            <span className="text-coral num">{formatPercent(shareOfLoss)}</span>{" "}
            of the portfolio's total category loss. It earns{" "}
            <span className="num">{formatCurrency(row.total_fee_revenue)}</span>{" "}
            in fees against{" "}
            <span className="num">{formatCurrency(row.total_default_losses)}</span>{" "}
            in projected default losses — an effective fee rate of{" "}
            <span className="num">{formatPercent(effectiveFeeRate, { digits: 2 })}</span>{" "}
            on an average ticket of{" "}
            <span className="num">{formatCurrency(avgTicket)}</span>, at a{" "}
            <span className="num">{formatPercent(row.default_rate, { digits: 2 })}</span>{" "}
            default rate. The fee does not compensate for the risk carried.
          </>
        ) : (
          <>
            This category is profitable: {formatCurrency(row.total_fee_revenue)} in
            fees against {formatCurrency(row.total_default_losses)} in projected
            losses. Its average ticket of {formatCurrency(avgTicket)} and{" "}
            {formatPercent(row.default_rate, { digits: 2 })} default rate keep
            exposure per transaction low enough for the{" "}
            {formatPercent(effectiveFeeRate, { digits: 2 })} fee rate to cover it.
          </>
        )}
      </div>
    </div>
  );
}

export default function RiskAnalysis() {
  const [categories, setCategories] = useState(null);
  const [portfolio, setPortfolio] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const [sortKey, setSortKey] = useState("net_profit");
  const [sortDir, setSortDir] = useState("asc");
  const [filter, setFilter] = useState("all");
  const [selected, setSelected] = useState(null);

  function load() {
    setLoading(true);
    setError(null);
    Promise.all([getProfitability(), getPortfolio()])
      .then(([c, p]) => {
        setCategories(c.categories);
        setPortfolio(p);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  const filtered = useMemo(() => {
    if (!categories) return [];
    let rows = [...categories];
    if (filter === "loss") rows = rows.filter((r) => r.net_profit < 0);
    if (filter === "profit") rows = rows.filter((r) => r.net_profit >= 0);
    if (filter === "highrisk") rows = rows.filter((r) => r.default_rate > 0.1);

    rows.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      const cmp =
        typeof av === "string" ? av.localeCompare(bv) : av - bv;
      return sortDir === "asc" ? cmp : -cmp;
    });
    return rows;
  }, [categories, filter, sortKey, sortDir]);

  if (loading) return <div className="max-w-6xl"><SkeletonChart height={360} /></div>;
  if (error) return <ErrorState message={error} onRetry={load} />;

  const losers = categories.filter((c) => c.net_profit < 0);
  const totalLoss = losers.reduce((s, c) => s + c.net_profit, 0);

  function toggleSort(key) {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(key === "merchant_category" ? "asc" : "desc");
    }
  }

  return (
    <div className="max-w-6xl space-y-6">
      {/* What is driving the loss */}
      <div className="card p-5">
        <h2 className="font-display font-medium text-paper text-sm mb-2">
          What is driving the current loss?
        </h2>
        <p className="text-sm text-paper-dim leading-relaxed">
          {losers.length} of {categories.length} merchant categories lose money,
          together accounting for{" "}
          <span className="num text-coral">{formatCurrency(totalLoss)}</span>. The
          pattern is consistent: the loss-making categories carry large average
          tickets and elevated default rates, at fee rates too low to cover the
          exposure. Portfolio-wide the book defaults at{" "}
          <span className="num text-paper">
            {formatPercent(portfolio.overall_default_rate)}
          </span>
          , and at a{" "}
          <span className="num text-paper">
            {formatPercent(portfolio.loss_given_default)}
          </span>{" "}
          loss-given-default assumption that produces{" "}
          <span className="num text-coral">
            {formatCurrency(portfolio.total_default_losses)}
          </span>{" "}
          in projected losses against{" "}
          <span className="num text-paper">
            {formatCurrency(portfolio.total_fee_revenue)}
          </span>{" "}
          of fee revenue.
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`focus-ring text-xs px-3 py-1.5 rounded-md border transition-colors ${
              filter === f.key
                ? "border-gold text-gold bg-gold/10"
                : "border-ink-border text-paper-dim hover:text-paper hover:border-paper-dim"
            }`}
          >
            {f.label}
          </button>
        ))}
        {filter !== "all" && (
          <span className="text-xs text-paper-dim ml-1">
            {filtered.length} of {categories.length} shown
          </span>
        )}
      </div>

      {/* Table */}
      <div className="card overflow-x-auto">
        {filtered.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-sm text-paper-dim">
              No categories match this filter.
            </p>
            <button
              onClick={() => setFilter("all")}
              className="focus-ring text-xs text-gold hover:text-gold-soft mt-2 transition-colors"
            >
              Clear filter
            </button>
          </div>
        ) : (
          <table className="w-full text-sm min-w-[760px]">
            <thead>
              <tr className="border-b border-ink-border">
                {COLUMNS.map((col) => (
                  <th
                    key={col.key}
                    className={`px-4 py-3 font-medium text-xs uppercase tracking-wide text-paper-dim ${
                      col.numeric ? "text-right" : "text-left"
                    }`}
                  >
                    <button
                      onClick={() => toggleSort(col.key)}
                      className="focus-ring hover:text-paper transition-colors"
                    >
                      {col.label}
                      {sortKey === col.key && <SortIcon dir={sortDir} />}
                    </button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((row) => {
                const isSelected =
                  selected?.merchant_category === row.merchant_category;
                return (
                  <tr
                    key={row.merchant_category}
                    onClick={() => setSelected(isSelected ? null : row)}
                    className={`border-b border-ink-border/50 cursor-pointer transition-colors ${
                      isSelected ? "bg-ink-surface2" : "hover:bg-ink-surface2/50"
                    }`}
                  >
                    {COLUMNS.map((col) => {
                      const v = row[col.key];
                      const negative = col.signed && v < 0;
                      const positive = col.signed && v >= 0;
                      return (
                        <td
                          key={col.key}
                          className={`px-4 py-3 ${col.numeric ? "text-right num" : "text-paper"} ${
                            negative ? "text-coral" : positive ? "text-teal" : "text-paper-dim"
                          }`}
                        >
                          {col.fmt ? col.fmt(v) : v}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      <p className="text-xs text-paper-dim">
        Click any row to drill into that category. Category net profits sum to
        the portfolio net profit — asserted in the backend test suite, not by
        inspection.
      </p>

      {selected && (
        <CategoryDetail
          row={selected}
          totalLoss={totalLoss}
          portfolioProfit={portfolio.net_profit}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}
