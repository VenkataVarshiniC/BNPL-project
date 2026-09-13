export function formatCurrency(value, opts = {}) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const { compact = false } = opts;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: compact ? 1 : 0,
    notation: compact ? "compact" : "standard",
  }).format(value);
}

export function formatPercent(value, opts = {}) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const { fromFraction = true, digits = 1 } = opts;
  const pct = fromFraction ? value * 100 : value;
  return `${pct.toFixed(digits)}%`;
}

export function formatNumber(value, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: digits,
  }).format(value);
}

export function signColor(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "text-paper-dim";
  return value >= 0 ? "text-teal" : "text-coral";
}

export function signGlyph(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "";
  return value >= 0 ? "▲" : "▼";
}
