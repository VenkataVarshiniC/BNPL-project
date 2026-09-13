import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL,
  timeout: 15000,
});

export async function checkHealth() {
  const { data } = await api.get("/health");
  return data;
}

// Endpoint 1 — Segmentation
export async function getSegmentation() {
  const { data } = await api.get("/api/segmentation/customers");
  return data;
}

// Endpoint 2 — Merchant/category profitability
export async function getProfitability() {
  const { data } = await api.get("/api/profitability/merchants");
  return data;
}

// Endpoint 3 — Default risk scoring
export async function postRiskScore(payload) {
  const { data } = await api.post("/api/risk/score", payload);
  return data;
}

// Endpoint 4 — Portfolio-level profitability
export async function getPortfolio() {
  const { data } = await api.get("/api/portfolio/profitability");
  return data;
}

// Endpoint 5 — Risk-adjusted strategy simulation
//
// Assumptions are passed through as query params so the whole simulation —
// baselines, strategy ladder and recommendation — recomputes server-side.
// Undefined values are omitted so the backend applies its configured default.
export async function getOptimization(assumptions = {}) {
  const { lgd, minApprovalRatePct, creditScoreCutoff } = assumptions;
  const params = {};
  if (lgd !== undefined && lgd !== null) params.lgd = lgd;
  if (minApprovalRatePct !== undefined && minApprovalRatePct !== null)
    params.min_approval_rate_pct = minApprovalRatePct;
  if (creditScoreCutoff !== undefined && creditScoreCutoff !== null)
    params.credit_score_cutoff = creditScoreCutoff;

  const { data } = await api.get("/api/optimization/thresholds", { params });
  return data;
}

// Endpoint 6 — Explainability
export async function getExplainability(customerId, params = {}) {
  const { data } = await api.get(`/api/explainability/${customerId}`, {
    params,
  });
  return data;
}
