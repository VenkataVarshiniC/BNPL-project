import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getFpnaOverview, getFpnaSqlReporting } from "../api/client.js";
import ErrorState from "../components/ErrorState.jsx";
import Loader from "../components/Loader.jsx";
import MetricCard from "../components/MetricCard.jsx";
import { formatCurrency, formatNumber, formatPercent, signColor } from "../utils/format.js";

const money = (v) => formatCurrency(v, { compact: true });
const monthLabel = (value) =>
  new Intl.DateTimeFormat("en-US", { month: "short", year: "2-digit", timeZone: "UTC" }).format(
    new Date(value)
  );
const driverLabel = (value) => value.replaceAll("_", " ");

function Section({ title, subtitle, children }) {
  return (
    <section className="card p-5">
      <div className="mb-4">
        <h2 className="font-display font-medium text-paper text-sm">{title}</h2>
        {subtitle && <p className="text-xs text-paper-dim mt-1">{subtitle}</p>}
      </div>
      {children}
    </section>
  );
}

function FinancialTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-ink-surface border border-ink-border rounded px-3 py-2 text-xs shadow-xl">
      <div className="text-paper mb-1">{label}</div>
      {payload.map((item) => (
        <div key={item.dataKey} style={{ color: item.color }}>
          {item.name}: {money(item.value)}
        </div>
      ))}
    </div>
  );
}

export default function FpnaDashboard() {
  const [data, setData] = useState(null);
  const [sqlStatus, setSqlStatus] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    setError(null);
    Promise.all([getFpnaOverview(), getFpnaSqlReporting()])
      .then(([overview, sql]) => {
        setData(overview);
        setSqlStatus(sql.reconciliation);
      })
      .catch((e) => setError(e.message || "Request failed"))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  const monthly = useMemo(
    () =>
      (data?.forecast?.monthly || []).map((row) => ({
        ...row,
        label: monthLabel(row.month),
      })),
    [data]
  );
  const variance = data?.budget_vs_actual;
  const annual = data?.forecast?.annual;
  const scenarios = data?.scenarios?.comparison || [];
  const sensitivity = data?.sensitivity || [];
  const topDriver = sensitivity[0];

  if (loading) return <Loader label="Building management forecast" />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data || !annual) return <ErrorState message="FP&A results are unavailable" onRetry={load} />;

  return (
    <div className="space-y-5 pb-10">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="text-xs text-paper-dim max-w-3xl leading-relaxed">
          Historical values are simulated actuals from the synthetic portfolio. Forecast and operating-cost
          values are planning outputs under configurable assumptions, not realized company results.
        </div>
        <div
          className={`text-xs font-mono px-3 py-1.5 rounded border ${
            sqlStatus?.status === "PASS"
              ? "text-teal border-teal/30 bg-teal/5"
              : "text-coral border-coral/30 bg-coral/5"
          }`}
        >
          Python / DuckDB reconciliation: {sqlStatus?.status || "Unavailable"}
        </div>
      </div>

      <section>
        <h2 className="font-display font-medium text-paper mb-3">1. Financial overview</h2>
        <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-3">
          <MetricCard
            label="12-month origination forecast"
            rawValue={annual.origination_volume}
            format={money}
            sublabel={`${formatNumber(annual.transaction_count)} forecast transactions`}
          />
          <MetricCard
            label="Merchant fee revenue"
            rawValue={annual.merchant_fee_revenue}
            format={money}
            sublabel={`${formatPercent(annual.approval_rate)} approval rate`}
          />
          <MetricCard
            label="Expected credit losses"
            rawValue={annual.credit_losses}
            format={money}
            tone="negative"
            sublabel="Default rate × LGD × approved volume"
          />
          <MetricCard
            label="Operating profit"
            rawValue={annual.operating_profit}
            format={money}
            tone={annual.operating_profit >= 0 ? "positive" : "negative"}
            sublabel={`${formatPercent(annual.operating_margin)} operating margin`}
          />
        </div>
      </section>

      <Section
        title="2. Monthly management P&L"
        subtitle="Merchant fee revenue is recognized on approved volume; gross transaction volume is not revenue."
      >
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="text-paper-dim border-b border-ink-border">
              <tr>
                {["Month", "Revenue", "Credit losses", "Operating expenses", "Operating profit", "Margin"].map(
                  (label) => <th key={label} className="text-right first:text-left py-2 px-2 font-normal">{label}</th>
                )}
              </tr>
            </thead>
            <tbody>
              {monthly.map((row) => (
                <tr key={row.month} className="border-b border-ink-border/60">
                  <td className="py-2 px-2 text-paper">{row.label}</td>
                  <td className="py-2 px-2 text-right num">{formatCurrency(row.merchant_fee_revenue)}</td>
                  <td className="py-2 px-2 text-right num text-coral">{formatCurrency(row.credit_losses)}</td>
                  <td className="py-2 px-2 text-right num">{formatCurrency(row.operating_expenses)}</td>
                  <td className={`py-2 px-2 text-right num ${signColor(row.operating_profit)}`}>
                    {formatCurrency(row.operating_profit)}
                  </td>
                  <td className={`py-2 px-2 text-right num ${signColor(row.operating_margin)}`}>
                    {formatPercent(row.operating_margin)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section title="3. Revenue and expense trends" subtitle="Base forecast, monthly USD">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={monthly} margin={{ left: 8, right: 8, top: 8, bottom: 4 }}>
            <CartesianGrid stroke="#2A2D32" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: "#9B9DA3", fontSize: 11 }} />
            <YAxis tickFormatter={money} tick={{ fill: "#9B9DA3", fontSize: 11 }} width={70} />
            <Tooltip content={<FinancialTooltip />} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Line type="monotone" dataKey="merchant_fee_revenue" name="Revenue" stroke="#4DB6AC" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="credit_losses" name="Credit losses" stroke="#F07167" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="operating_expenses" name="Operating expenses" stroke="#D4A94E" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </Section>

      <Section
        title="4. Budget vs. simulated actual"
        subtitle={`${variance.method} Variance bridge differences total ${formatCurrency(
          variance.total.reconciliation_difference
        )}.`}
      >
        <div className="grid sm:grid-cols-3 gap-3 mb-5">
          <div className="bg-ink-surface2 rounded p-3">
            <div className="text-[10px] uppercase text-paper-dim">Revenue variance</div>
            <div className={`num mt-1 ${signColor(variance.total.revenue_variance)}`}>
              {formatCurrency(variance.total.revenue_variance)}
            </div>
          </div>
          <div className="bg-ink-surface2 rounded p-3">
            <div className="text-[10px] uppercase text-paper-dim">Expense variance</div>
            <div className="num mt-1 text-coral">{formatCurrency(variance.total.expense_variance)}</div>
          </div>
          <div className="bg-ink-surface2 rounded p-3">
            <div className="text-[10px] uppercase text-paper-dim">Operating profit variance</div>
            <div className={`num mt-1 ${signColor(variance.total.operating_profit_variance)}`}>
              {formatCurrency(variance.total.operating_profit_variance)} · {variance.total.favorable_unfavorable}
            </div>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={variance.monthly.map((r) => ({ ...r, label: monthLabel(r.month) }))}>
            <CartesianGrid stroke="#2A2D32" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: "#9B9DA3", fontSize: 11 }} />
            <YAxis tickFormatter={money} tick={{ fill: "#9B9DA3", fontSize: 11 }} width={70} />
            <Tooltip content={<FinancialTooltip />} />
            <Bar dataKey="budget_operating_profit" name="Budget operating profit" fill="#6E7380" />
            <Bar dataKey="actual_operating_profit" name="Simulated actual operating profit" fill="#D4A94E" />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      <Section title="5. Forecast scenarios" subtitle="Each scenario is independently evaluated through the same 12-month P&L build.">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="text-paper-dim border-b border-ink-border">
              <tr>
                {["Scenario", "Volume", "Approval", "Revenue", "Credit losses", "Operating expenses", "Operating profit", "Margin"].map(
                  (label) => <th key={label} className="text-right first:text-left py-2 px-2 font-normal">{label}</th>
                )}
              </tr>
            </thead>
            <tbody>
              {scenarios.map((row) => (
                <tr key={row.scenario} className="border-b border-ink-border/60">
                  <td className="py-2 px-2 text-paper capitalize">{row.scenario}</td>
                  <td className="py-2 px-2 text-right num">{money(row.transaction_volume)}</td>
                  <td className="py-2 px-2 text-right num">{formatPercent(row.approval_rate)}</td>
                  <td className="py-2 px-2 text-right num">{money(row.revenue)}</td>
                  <td className="py-2 px-2 text-right num">{money(row.credit_losses)}</td>
                  <td className="py-2 px-2 text-right num">{money(row.operating_expenses)}</td>
                  <td className={`py-2 px-2 text-right num ${signColor(row.operating_profit)}`}>{money(row.operating_profit)}</td>
                  <td className={`py-2 px-2 text-right num ${signColor(row.operating_margin)}`}>{formatPercent(row.operating_margin)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section title="6. Profitability drivers" subtitle="One-way ±10% sensitivity around the base case, ranked by absolute operating-profit impact.">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={sensitivity} layout="vertical" margin={{ left: 130, right: 20 }}>
            <CartesianGrid stroke="#2A2D32" horizontal={false} />
            <XAxis type="number" tickFormatter={money} tick={{ fill: "#9B9DA3", fontSize: 11 }} />
            <YAxis type="category" dataKey="driver" tickFormatter={driverLabel} tick={{ fill: "#C8C9CC", fontSize: 11 }} width={125} />
            <Tooltip content={<FinancialTooltip />} />
            <Bar dataKey="low_impact" name="Low assumption impact" fill="#F07167" />
            <Bar dataKey="high_impact" name="High assumption impact" fill="#4DB6AC" />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      <Section title="7. Executive decision summary">
        <div className="grid lg:grid-cols-2 gap-5 text-sm leading-relaxed">
          <div>
            <div className="text-paper font-medium mb-2">Decision signal</div>
            <p className="text-paper-dim">
              All three planning scenarios remain operating-loss cases after modeled operating costs. The base case forecasts {formatCurrency(
                annual.operating_profit
              )} of operating profit at a {formatPercent(annual.operating_margin)} margin. Approval tightening alone is not an operating model;
              pricing, loss performance, and cost structure must move together.
            </p>
          </div>
          <div>
            <div className="text-paper font-medium mb-2">Priority action</div>
            <p className="text-paper-dim">
              {topDriver ? `${driverLabel(topDriver.driver)} is the largest tested driver, moving annual operating profit by up to ${formatCurrency(
                topDriver.max_absolute_impact
              )}. ` : ""}
              Validate fee economics and measured recovery rates before treating any scenario as decision-ready. Held-out synthetic volume accuracy is {formatPercent(
                data.validation.volume_accuracy
              )}; this measures stability of the simulated series, not real-world forecast performance.
            </p>
          </div>
        </div>
      </Section>

      <div className="text-xs text-paper-dim leading-relaxed">
        <span className="text-paper">Accounting scope:</span> {data.accounting_simplifications.join(" ")}
      </div>
    </div>
  );
}
