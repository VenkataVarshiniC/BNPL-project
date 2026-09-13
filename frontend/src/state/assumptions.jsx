import { createContext, useContext, useMemo, useState } from "react";

/**
 * Shared modelling assumptions.
 *
 * These live above the page tree deliberately. Loss-given-default, the
 * approval-volume floor and the baseline credit cutoff are not properties of
 * one screen — they condition every figure the product reports. If the
 * simulator let you set LGD to 0.75 and the decision summary quietly kept
 * reporting 0.65, the product would be contradicting itself between tabs.
 *
 * Defaults mirror backend/app/config.py. They are sent explicitly rather than
 * omitted so the UI always states what it is assuming.
 */

export const DEFAULT_ASSUMPTIONS = {
  lgd: 0.65,
  minApprovalRatePct: 75,
  creditScoreCutoff: 600,
};

const AssumptionsContext = createContext(null);

export function AssumptionsProvider({ children }) {
  const [assumptions, setAssumptions] = useState(DEFAULT_ASSUMPTIONS);

  const value = useMemo(() => {
    const isDefault =
      assumptions.lgd === DEFAULT_ASSUMPTIONS.lgd &&
      assumptions.minApprovalRatePct === DEFAULT_ASSUMPTIONS.minApprovalRatePct &&
      assumptions.creditScoreCutoff === DEFAULT_ASSUMPTIONS.creditScoreCutoff;

    return {
      assumptions,
      isDefault,
      setAssumption: (key, val) =>
        setAssumptions((prev) => ({ ...prev, [key]: val })),
      resetAssumptions: () => setAssumptions(DEFAULT_ASSUMPTIONS),
    };
  }, [assumptions]);

  return (
    <AssumptionsContext.Provider value={value}>
      {children}
    </AssumptionsContext.Provider>
  );
}

export function useAssumptions() {
  const ctx = useContext(AssumptionsContext);
  if (!ctx) {
    throw new Error("useAssumptions must be used inside an AssumptionsProvider");
  }
  return ctx;
}
