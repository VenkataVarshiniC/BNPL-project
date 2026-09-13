import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getPortfolio, getProfitability } from "../api/client.js";
import { useOptimization, recommendedStrategy, orderedStrategies } from "../hooks/useOptimization.js";
import Caveats, { Flag } from "../components/Caveats.jsx";
import { SkeletonChart } from "../components/Skeleton.jsx";
import ErrorState from "../components/ErrorState.jsx";
import { formatCurrency, formatPercent, formatNumber } from "../utils/format.js";

function Section({ n, title, children }) {
  return (
    <section className="card p-6">
      <div className="flex items-baseline gap-3 mb-3">
        <span className="num text-xs text-gold">{n}</span>
        <h2 className="font-display font-medium text-paper">{title}</h2>
      </div>
      <div className="text-sm text-paper-dim leading-relaxed space-y-3">
        {children}
      </div>
    </section>
  );
}

export default function Decision() {
  const { data, error, loading, reload } = useOptimization();
  const [portfolio, setPortfolio] = useState(null);
  const [categories, setCategories] = useState(null);
  const [auxError, setAuxError] = useState(null);

  useEffect(() => {
    Promise.all([getPortfolio(), getProfitability()])
      .then(([p, c]) => {
        setPortfolio(p);
        setCategories(c.categories);
      })
      .catch((e) => setAuxError(e.message));
  }, []);

  if (loading && !data)
    return <div className="max-w-4xl"><SkeletonChart height={420} /></div>;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data || !portfolio || !categories) {
    if (auxError) return <ErrorState message={auxError} onRetry={reload} />;
    return <div className="max-w-4xl"><SkeletonChart height={420} /></div>;
  }

  const legacy = data.legacy_baseline;
  const rec = recommendedStrategy(data);
  const strategies = orderedStrategies(data);
  const maxProfit = data.strategies?.unconstrained_max;
  const matched = data.strategies?.volume_matched;

  const losers = categories.filter((c) => c.net_profit < 0);
  const totalLoss = losers.reduce((s, c) => s + c.net_profit, 0);
  const worst = [...losers].sort((a, b) => a.net_profit - b.net_profit);
  const top4 = worst.slice(0, 4);
  const top4Share = top4.reduce((s, c) => s + c.net_profit, 0) / (totalLoss || 1);

  return (
    <div className="max-w-4xl space-y-5">
      {/* Headline */}
      <div className="card p-6 border-gold/40">
        <div className="text-xs uppercase tracking-wide text-gold mb-2">
          Recommendation
        </div>
        {rec ? (
          <>
            <div className="font-display text-2xl text-paper mb-2">
              {rec.strategy_label}
            </div>
            <div className="flex flex-wrap gap-x-8 gap-y-3 mt-4">
              <div>
                <div className="text-xs text-paper-dim mb-1">Projected improvement</div>
                <div className="num text-2xl font-semibold text-teal">
                  +{formatCurrency(rec.profit_vs_legacy)}
                </div>
              </div>
              <div>
                <div className="text-xs text-paper-dim mb-1">Net position</div>
                <div className="num text-2xl font-semibold text-paper">
                  {formatCurrency(legacy.projected_net_profit)} →{" "}
                  <span className={rec.projected_net_profit >= 0 ? "text-teal" : "text-coral"}>
                    {formatCurrency(rec.projected_net_profit)}
                  </span>
                </div>
              </div>
              <div>
                <div className="text-xs text-paper-dim mb-1">Cost</div>
                <div className="num text-2xl font-semibold text-coral">
                  {rec.approval_rate_change_pp}pp
                </div>
                <div className="text-xs text-paper-dim">approval volume</div>
              </div>
            </div>
          </>
        ) : (
          <div className="font-display text-xl text-coral">
            No shippable recommendation under current assumptions
          </div>
        )}
      </div>

      <Section n="01" title="What is the problem?">
        <p>
          The current underwriting policy — approve if credit score is at or
          above {legacy.credit_score_cutoff} — approves{" "}
          <span className="num text-paper">{legacy.approval_rate_pct}%</span> of
          applications ({formatNumber(legacy.approved_count)} of{" "}
          {formatNumber(portfolio.total_transactions)}) and produces a projected
          net loss of{" "}
          <span className="num text-coral">
            {formatCurrency(Math.abs(legacy.projected_net_profit))}
          </span>
          , against{" "}
          <span className="num">{formatCurrency(legacy.projected_fee_revenue)}</span>{" "}
          of fee revenue.
        </p>
      </Section>

      <Section n="02" title="What is causing it?">
        <p>
          A <span className="text-paper">risk-adjustment gap</span>. Credit score
          is a single general-purpose signal. It ignores installment count,
          merchant category and employment status — each of which carries
          independent default signal in this portfolio.
        </p>
        <p>
          The loss is concentrated rather than spread: {losers.length} of{" "}
          {categories.length} merchant categories lose money, and the worst four
          — {top4.map((c) => c.merchant_category).join(", ")} — account for{" "}
          <span className="num text-coral">{formatPercent(top4Share)}</span> of
          the total. All four share the same profile: large average ticket, high
          default rate, fee rate too low to compensate.{" "}
          <Link to="/app/risk" className="focus-ring text-gold hover:text-gold-soft">
            See the full attribution →
          </Link>
        </p>
      </Section>

      <Section n="03" title="What options exist?">
        <p>
          Four approval strategies were simulated across{" "}
          {data.simulated_points.length} thresholds using out-of-fold model
          scores, and measured against the current policy:
        </p>
        <ul className="space-y-2 mt-2">
          {strategies.map((s) => (
            <li key={s.strategy_key} className="flex gap-3">
              <span className="text-gold shrink-0" aria-hidden="true">—</span>
              <span>
                <span className="text-paper">{s.strategy_label}</span> —{" "}
                {s.approval_rate_pct}% approved,{" "}
                <span className={s.projected_net_profit >= 0 ? "text-teal num" : "text-coral num"}>
                  {formatCurrency(s.projected_net_profit)}
                </span>{" "}
                ({s.profit_vs_legacy >= 0 ? "+" : ""}
                {formatCurrency(s.profit_vs_legacy)} vs current)
                {!s.meets_volume_floor && (
                  <span className="text-gold"> · below the volume floor</span>
                )}
              </span>
            </li>
          ))}
        </ul>
        <p className="pt-1">
          <Link to="/app/comparison" className="focus-ring text-gold hover:text-gold-soft">
            Compare them side by side →
          </Link>
        </p>
      </Section>

      <Section n="04" title="What is recommended?">
        <p>{data.recommended_reason}</p>
        {rec && (
          <p>
            The selection rule is stated rather than implied: maximise approved
            volume subject to not losing money. That rule is a business
            judgement, not a mathematical result — a different appetite for
            volume would select a different strategy, which is why all four are
            reported.
          </p>
        )}
      </Section>

      <Section n="05" title="What is the projected impact?">
        {rec ? (
          <>
            <p>
              Net position moves from{" "}
              <span className="num text-coral">
                {formatCurrency(legacy.projected_net_profit)}
              </span>{" "}
              to{" "}
              <span className={`num ${rec.projected_net_profit >= 0 ? "text-teal" : "text-coral"}`}>
                {formatCurrency(rec.projected_net_profit)}
              </span>{" "}
              — a projected improvement of{" "}
              <span className="num text-teal">
                {formatCurrency(rec.profit_vs_legacy)}
              </span>{" "}
              under the stated assumptions.
            </p>
            <p>
              Approval rate moves from {legacy.approval_rate_pct}% to{" "}
              {rec.approval_rate_pct}% ({rec.approval_rate_change_pp}pp), and the
              default rate among approved transactions falls from{" "}
              {formatPercent(legacy.approved_default_rate, { digits: 2 })} to{" "}
              {formatPercent(rec.approved_default_rate, { digits: 2 })}.
            </p>
            {matched && (
              <p>
                Of that improvement,{" "}
                <span className="num text-paper">
                  {formatCurrency(matched.profit_vs_legacy)}
                </span>{" "}
                is available at{" "}
                <span className="text-paper">no reduction in volume at all</span>{" "}
                — that is the portion attributable purely to better selection.
                The remainder is bought by lending less.
              </p>
            )}
          </>
        ) : (
          <p>
            No strategy on the simulated grid both clears the volume floor and
            returns the book to profit, so no impact can be projected.
          </p>
        )}
      </Section>

      <Section n="06" title="What are the risks?">
        <ul className="space-y-2">
          <li className="flex gap-3">
            <span className="text-coral shrink-0" aria-hidden="true">—</span>
            <span>
              <span className="text-paper">Assumption risk.</span> Every loss
              figure is conditional on a{" "}
              {formatPercent(portfolio.loss_given_default)} loss-given-default
              assumption that has not been measured. At a materially lower LGD
              the problem substantially dissolves; at a higher one it deepens.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="text-coral shrink-0" aria-hidden="true">—</span>
            <span>
              <span className="text-paper">Volume risk.</span> Declining{" "}
              {Math.abs(rec?.approval_rate_change_pp ?? 0)}pp more of the book
              affects merchant conversion and customer growth. Those costs are
              real and are not modelled here.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="text-coral shrink-0" aria-hidden="true">—</span>
            <span>
              <span className="text-paper">Model risk.</span> The projection is a
              backtest on out-of-fold scores, not a forward forecast. Live
              performance would differ, and the model has not been validated by
              an independent function.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="text-coral shrink-0" aria-hidden="true">—</span>
            <span>
              <span className="text-paper">Data risk.</span> The portfolio is
              synthetic. Whether the risk-adjustment gap holds on real BNPL data
              is untested and cannot be tested here.
            </span>
          </li>
          {data.volume_floor_feasible === false && (
            <li className="flex gap-3">
              <span className="text-coral shrink-0" aria-hidden="true">—</span>
              <span>
                <span className="text-paper">Structural risk.</span> Declining
                alone cannot make this book profitable while holding{" "}
                {data.min_approval_rate_pct}% approval. The recommendation
                accepts a volume reduction below that floor.
              </span>
            </li>
          )}
        </ul>
      </Section>

      <Section n="07" title="What are the assumptions?">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-2">
          <div>
            <div className="text-xs text-paper-dim mb-1">Loss given default</div>
            <div className="num text-paper">
              {formatPercent(data.assumptions.loss_given_default)}
            </div>
          </div>
          <div>
            <div className="text-xs text-paper-dim mb-1">Approval-volume floor</div>
            <div className="num text-paper">
              {data.assumptions.min_approval_rate_pct}%
            </div>
          </div>
          <div>
            <div className="text-xs text-paper-dim mb-1">Baseline cutoff</div>
            <div className="num text-paper">
              Credit score ≥ {data.assumptions.legacy_credit_score_cutoff}
            </div>
          </div>
        </div>
        <p>
          Scoring is {data.assumptions.scoring} over{" "}
          {data.assumptions.cv_folds} folds, on a {data.assumptions.dataset}{" "}
          dataset. Fee revenue is assumed earned at transaction time and not
          clawed back on a later default; declining is assumed to forgo the fee
          entirely, with no substitution to a different term or product.
        </p>
      </Section>

      <Section n="08" title="What should happen next?">
        <ol className="space-y-2 list-none">
          <li className="flex gap-3">
            <span className="num text-gold shrink-0">1</span>
            <span>
              <span className="text-paper">Measure LGD.</span> It is the single
              largest source of uncertainty and the only assumption that can
              change the conclusion outright. Recovery data would settle it.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="num text-gold shrink-0">2</span>
            <span>
              <span className="text-paper">Agree the volume floor with
              commercial owners.</span> It is currently set at{" "}
              {data.assumptions.min_approval_rate_pct}% by assumption. The
              recommendation is sensitive to it, and it is a negotiation rather
              than an analytical output.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="num text-gold shrink-0">3</span>
            <span>
              <span className="text-paper">Simulate risk-based pricing.</span>{" "}
              Declining cannot hold both volume and margin. Charging a fee rate
              that compensates for segment risk is the untested lever, and the
              analysis points directly at it.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="num text-gold shrink-0">4</span>
            <span>
              <span className="text-paper">Pilot before rollout.</span> Apply the
              recommended threshold to a limited segment and compare realised
              losses against projection before changing policy book-wide.
            </span>
          </li>
        </ol>
      </Section>

      {data.volume_floor_feasible === false && (
        <Flag tone="warn">
          <strong>The volume floor and profitability are incompatible here.</strong>{" "}
          No simulated threshold satisfies both. The recommendation accepts
          falling below the floor; the alternative is accepting the loss.
        </Flag>
      )}

      <Caveats caveats={data.caveats} />

      <p className="text-xs text-paper-dim">
        This is a decision-support output. It makes no lending decision and has
        no connection to any approval system. Every figure is a projection on a
        synthetic portfolio under the assumptions stated above.
      </p>
    </div>
  );
}
