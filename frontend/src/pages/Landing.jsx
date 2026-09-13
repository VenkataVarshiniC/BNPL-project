import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { getPortfolio, getOptimization } from "../api/client.js";
import { formatCurrency, formatPercent } from "../utils/format.js";

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.5, ease: "easeOut" },
  }),
};

const PILLARS = [
  {
    tag: "01",
    title: "Attribute the loss",
    body: "Net profit by merchant category, reconciled to the portfolio total in the test suite. The loss turns out to be concentrated rather than spread — and the pattern is large tickets at fee rates that don't cover the risk they carry.",
  },
  {
    tag: "02",
    title: "Measure against a real baseline",
    body: "Not against “approve everyone”, which no lender does. Against a credit-score cutoff — the policy that actually exists, and the one that ignores installment count, merchant category and employment status.",
  },
  {
    tag: "03",
    title: "Simulate honestly",
    body: "Every transaction is scored by a model fold that never trained on it. In-sample scoring flatters the approved book and inflates projected profit; out-of-fold scoring is the only version that means anything.",
  },
  {
    tag: "04",
    title: "Report the trade-off, not an optimum",
    body: "The profit-maximising threshold declines most of the book — an answer no lender would ship. Four strategies are reported instead, each with the approval volume it costs stated in full.",
  },
];

export default function Landing() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [opt, setOpt] = useState(null);

  useEffect(() => {
    getPortfolio().then(setStats).catch(() => {});
    getOptimization().then(setOpt).catch(() => {});
  }, []);

  const legacy = opt?.legacy_baseline;
  const rec = opt?.recommended_strategy
    ? opt.strategies?.[opt.recommended_strategy]
    : null;

  return (
    <div className="min-h-screen bg-ink text-paper overflow-y-auto">
      {/* Hero */}
      <section className="max-w-5xl mx-auto px-6 pt-24 pb-16">
        <motion.div
          initial="hidden"
          animate="show"
          variants={fadeUp}
          className="font-mono text-xs text-gold tracking-widest uppercase mb-5"
        >
          Ledger — BNPL Risk &amp; Profitability
        </motion.div>

        <motion.h1
          custom={1}
          initial="hidden"
          animate="show"
          variants={fadeUp}
          className="font-display font-semibold text-4xl sm:text-5xl leading-[1.1] tracking-tight max-w-3xl"
        >
          The book is losing money.
          <br />
          <span className="text-paper-dim">
            Lending less is the easy answer, not the right one.
          </span>
        </motion.h1>

        <motion.p
          custom={2}
          initial="hidden"
          animate="show"
          variants={fadeUp}
          className="text-paper-dim text-base leading-relaxed max-w-2xl mt-6"
        >
          A BNPL lender earns a fee on every approved transaction and absorbs
          the principal when a customer defaults, so the approval policy decides
          whether the business makes money. On a synthetic book of 5,000
          customers and 42,000 transactions, a credit-score-only policy loses{" "}
          {legacy ? (
            <span className="text-coral num">
              {formatCurrency(Math.abs(legacy.projected_net_profit))}
            </span>
          ) : (
            "money"
          )}
          . This is a decision-support platform for working out what to do about
          it — and for being honest about what each option costs.
        </motion.p>

        <motion.div
          custom={3}
          initial="hidden"
          animate="show"
          variants={fadeUp}
          className="flex flex-wrap items-center gap-4 mt-9"
        >
          <button
            onClick={() => navigate("/app")}
            className="focus-ring px-6 py-3 rounded-md bg-gold text-ink font-medium text-sm hover:bg-gold-soft transition-colors"
          >
            Enter the dashboard →
          </button>
          <button
            onClick={() => navigate("/app/decision")}
            className="focus-ring px-6 py-3 rounded-md border border-ink-border text-paper font-medium text-sm hover:border-gold transition-colors"
          >
            Read the recommendation
          </button>
        </motion.div>
      </section>

      {/* Live stats strip */}
      <section className="border-y border-ink-border bg-ink-surface/50">
        <div className="max-w-5xl mx-auto px-6 py-8 grid grid-cols-2 sm:grid-cols-4 gap-6">
          {[
            {
              label: legacy
                ? `Current policy (credit ≥ ${legacy.credit_score_cutoff})`
                : "Current policy",
              value: legacy ? formatCurrency(legacy.projected_net_profit) : "—",
              tone:
                legacy && legacy.projected_net_profit >= 0
                  ? "text-teal"
                  : "text-coral",
            },
            {
              label: rec ? "Recommended change" : "Recommendation",
              value: rec ? `+${formatCurrency(rec.profit_vs_legacy)}` : "—",
              tone: "text-teal",
            },
            {
              label: "Approval volume cost",
              value: rec ? `${rec.approval_rate_change_pp}pp` : "—",
              tone: "text-paper",
            },
            {
              label: "Default rate",
              value: stats ? formatPercent(stats.overall_default_rate) : "—",
              tone: "text-paper",
            },
          ].map((s, i) => (
            <motion.div
              key={s.label}
              custom={i}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true }}
              variants={fadeUp}
            >
              <div className={`num text-2xl font-semibold ${s.tone}`}>
                {s.value}
              </div>
              <div className="text-xs text-paper-dim mt-1">{s.label}</div>
            </motion.div>
          ))}
        </div>
        <div className="max-w-5xl mx-auto px-6 pb-6 -mt-2">
          <p className="text-xs text-paper-dim">
            Projected under stated assumptions on a synthetic portfolio — not a
            realised result.
          </p>
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-5xl mx-auto px-6 py-20">
        <motion.h2
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          variants={fadeUp}
          className="font-display font-medium text-xl text-paper mb-3"
        >
          How this analysis tries not to fool itself
        </motion.h2>
        <motion.p
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          variants={fadeUp}
          className="text-sm text-paper-dim max-w-2xl mb-10 leading-relaxed"
        >
          The naive version of this project reports one optimal threshold and a
          large improvement number. That version is wrong in three specific ways,
          and each one is corrected here.
        </motion.p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-px bg-ink-border rounded-lg overflow-hidden">
          {PILLARS.map((p, i) => (
            <motion.div
              key={p.tag}
              custom={i}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true }}
              variants={fadeUp}
              className="bg-ink-surface p-6 hover:bg-ink-surface2 transition-colors"
            >
              <div className="font-mono text-xs text-gold mb-3">{p.tag}</div>
              <h3 className="font-display font-medium text-paper mb-2">
                {p.title}
              </h3>
              <p className="text-sm text-paper-dim leading-relaxed">{p.body}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <footer className="max-w-5xl mx-auto px-6 pb-16 text-xs text-paper-dim font-mono leading-relaxed">
        Synthetic dataset — no real customer data. Decision support only: this
        system makes no lending decisions and has no connection to any approval
        system.
      </footer>
    </div>
  );
}
