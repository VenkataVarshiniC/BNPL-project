import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { postRiskScore } from "../api/client.js";
import Loader from "../components/Loader.jsx";
import ErrorState from "../components/ErrorState.jsx";
import { formatPercent } from "../utils/format.js";

const CATEGORIES = [
  "Electronics", "Fashion & Apparel", "Home & Furniture", "Beauty & Wellness",
  "Travel", "Groceries", "Sporting Goods", "Jewelry & Accessories",
  "Health & Fitness", "Education",
];

const TIER_TONE = {
  Low: "text-teal border-teal/40 bg-teal/10",
  Medium: "text-gold border-gold/40 bg-gold/10",
  High: "text-coral-soft border-coral/40 bg-coral/10",
  "Very high": "text-coral border-coral/50 bg-coral/15",
};

export default function RiskScore() {
  const [form, setForm] = useState({
    customer_id: "CUST100000",
    transaction_amount: 300,
    num_installments: 4,
    merchant_category: "Electronics",
  });
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await postRiskScore({
        ...form,
        transaction_amount: Number(form.transaction_amount),
        num_installments: Number(form.num_installments),
      });
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl grid grid-cols-1 md:grid-cols-2 gap-6">
      <form onSubmit={handleSubmit} className="card p-5 space-y-4">
        <div>
          <label className="block text-xs text-paper-dim mb-1.5">Customer ID</label>
          <input
            className="w-full bg-ink-surface2 border border-ink-border rounded-md px-3 py-2 text-sm num text-paper focus-ring"
            value={form.customer_id}
            onChange={(e) => update("customer_id", e.target.value)}
            placeholder="CUST100000"
            required
          />
        </div>

        <div>
          <label className="block text-xs text-paper-dim mb-1.5">Transaction amount ($)</label>
          <input
            type="number"
            min="1"
            step="0.01"
            className="w-full bg-ink-surface2 border border-ink-border rounded-md px-3 py-2 text-sm num text-paper focus-ring"
            value={form.transaction_amount}
            onChange={(e) => update("transaction_amount", e.target.value)}
            required
          />
        </div>

        <div>
          <label className="block text-xs text-paper-dim mb-1.5">Installments</label>
          <select
            className="w-full bg-ink-surface2 border border-ink-border rounded-md px-3 py-2 text-sm num text-paper focus-ring"
            value={form.num_installments}
            onChange={(e) => update("num_installments", e.target.value)}
          >
            {[2, 3, 4, 6, 12].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs text-paper-dim mb-1.5">Merchant category</label>
          <select
            className="w-full bg-ink-surface2 border border-ink-border rounded-md px-3 py-2 text-sm text-paper focus-ring"
            value={form.merchant_category}
            onChange={(e) => update("merchant_category", e.target.value)}
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="focus-ring w-full py-2.5 rounded-md bg-gold text-ink font-medium text-sm hover:bg-gold-soft transition-colors disabled:opacity-50"
        >
          {loading ? "Scoring…" : "Score transaction"}
        </button>
      </form>

      <div>
        {loading && <Loader label="Scoring transaction" />}
        {error && <ErrorState message={error} />}
        {result && (
          <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.25 }}
            className="card p-5"
          >
            <div className="text-xs text-paper-dim mb-1">{result.customer_id}</div>
            <div className="num text-3xl font-semibold text-paper mb-3">
              {formatPercent(result.default_probability)}
            </div>
            <div className="text-xs text-paper-dim mb-4">Default probability</div>

            <span
              className={`inline-block text-xs px-2.5 py-1 rounded-full border font-medium mb-4 ${TIER_TONE[result.risk_tier]}`}
            >
              {result.risk_tier} risk
            </span>

            <div className="pt-4 border-t border-ink-border">
              <div className="text-xs text-paper-dim mb-1">Recommended action</div>
              <div className="text-sm text-paper">{result.recommended_action}</div>
            </div>
          </motion.div>
        )}
        {!loading && !error && !result && (
          <div className="card p-5 text-sm text-paper-dim">
            Fill in the form and score a transaction to see the model's default probability, risk tier, and recommended action.
          </div>
        )}
      </div>
    </div>
  );
}
