const baseURL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

async function request(path, { method = "GET", params, body } = {}) {
  const url = new URL(`${baseURL}${path}`);
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null) url.searchParams.set(key, value);
  });
  const response = await fetch(url, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();
  if (!response.ok) {
    const detail = typeof payload === "object" ? payload?.detail || payload?.error : payload;
    const error = new Error(detail || `Request failed with status ${response.status}`);
    error.status = response.status;
    error.data = payload;
    throw error;
  }
  return payload;
}

export const checkHealth = () => request("/health");
export const getSegmentation = () => request("/api/segmentation/customers");
export const getProfitability = () => request("/api/profitability/merchants");
export const postRiskScore = (body) => request("/api/risk/score", { method: "POST", body });
export const getPortfolio = () => request("/api/portfolio/profitability");

export function getOptimization(assumptions = {}) {
  const { lgd, minApprovalRatePct, creditScoreCutoff } = assumptions;
  return request("/api/optimization/thresholds", {
    params: {
      lgd,
      min_approval_rate_pct: minApprovalRatePct,
      credit_score_cutoff: creditScoreCutoff,
    },
  });
}

export const getExplainability = (customerId, params = {}) =>
  request(`/api/explainability/${encodeURIComponent(customerId)}`, { params });
export const getFpnaOverview = () => request("/api/fpna/overview");
export const getFpnaSqlReporting = () => request("/api/fpna/sql-reporting");
