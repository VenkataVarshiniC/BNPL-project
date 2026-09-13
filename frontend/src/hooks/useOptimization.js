import { useCallback, useEffect, useState } from "react";
import { getOptimization } from "../api/client.js";
import { useAssumptions } from "../state/assumptions.jsx";

/**
 * Fetches the strategy simulation under the current shared assumptions.
 *
 * Every screen that reports a projection uses this, so the simulator,
 * comparison and decision summary can never disagree about what was assumed.
 */
export function useOptimization() {
  const { assumptions } = useAssumptions();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    getOptimization(assumptions)
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message || "Request failed");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [assumptions]);

  useEffect(() => load(), [load]);

  return { data, error, loading, reload: load };
}

/** The strategy the backend recommends, or null if none is shippable. */
export function recommendedStrategy(data) {
  if (!data?.recommended_strategy) return null;
  return data.strategies?.[data.recommended_strategy] ?? null;
}

/** Strategy ladder in a stable, meaningful order — least to most disruptive. */
export const STRATEGY_ORDER = [
  "volume_matched",
  "breakeven",
  "constrained_max",
  "unconstrained_max",
];

export function orderedStrategies(data) {
  if (!data?.strategies) return [];
  return STRATEGY_ORDER.map((key) => data.strategies[key]).filter(Boolean);
}
