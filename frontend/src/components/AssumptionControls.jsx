import { useAssumptions, DEFAULT_ASSUMPTIONS } from "../state/assumptions.jsx";
import { formatPercent } from "../utils/format.js";

function Control({ label, help, children, value }) {
  return (
    <div>
      <div className="flex items-baseline justify-between mb-1.5">
        <label className="text-xs uppercase tracking-wide text-paper-dim">
          {label}
        </label>
        <span className="num text-sm text-paper">{value}</span>
      </div>
      {children}
      <p className="text-xs text-paper-dim mt-1.5 leading-relaxed">{help}</p>
    </div>
  );
}

/**
 * The assumptions panel.
 *
 * Deliberately not hidden behind a settings menu. Every profit figure in this
 * product is conditional on these three numbers, so they sit beside the
 * results rather than somewhere a reader could fail to find them.
 */
export default function AssumptionControls() {
  const { assumptions, setAssumption, resetAssumptions, isDefault } =
    useAssumptions();

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="font-display font-medium text-paper text-sm">
            Modelling assumptions
          </h2>
          <p className="text-xs text-paper-dim mt-0.5">
            Every figure on this page is conditional on these.
          </p>
        </div>
        {!isDefault && (
          <button
            onClick={resetAssumptions}
            className="focus-ring text-xs text-gold hover:text-gold-soft transition-colors shrink-0 ml-4"
          >
            Reset to defaults
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <Control
          label="Loss given default"
          value={formatPercent(assumptions.lgd)}
          help="Share of principal unrecovered when a customer defaults. An assumption, not a measurement — and the single largest source of uncertainty here."
        >
          <input
            type="range"
            min={0.35}
            max={0.95}
            step={0.05}
            value={assumptions.lgd}
            onChange={(e) => setAssumption("lgd", Number(e.target.value))}
            className="w-full accent-gold cursor-pointer focus-ring"
            aria-label="Loss given default"
          />
        </Control>

        <Control
          label="Approval-volume floor"
          value={`${assumptions.minApprovalRatePct}%`}
          help="Minimum share of transactions the business is willing to keep approving. Below this, a strategy is not commercially shippable however profitable it looks."
        >
          <input
            type="range"
            min={30}
            max={95}
            step={5}
            value={assumptions.minApprovalRatePct}
            onChange={(e) =>
              setAssumption("minApprovalRatePct", Number(e.target.value))
            }
            className="w-full accent-gold cursor-pointer focus-ring"
            aria-label="Approval volume floor"
          />
        </Control>

        <Control
          label="Baseline credit cutoff"
          value={assumptions.creditScoreCutoff}
          help="The current-state policy this is measured against: approve if credit score is at or above this, ignoring every other signal."
        >
          <input
            type="range"
            min={500}
            max={720}
            step={20}
            value={assumptions.creditScoreCutoff}
            onChange={(e) =>
              setAssumption("creditScoreCutoff", Number(e.target.value))
            }
            className="w-full accent-gold cursor-pointer focus-ring"
            aria-label="Baseline credit score cutoff"
          />
        </Control>
      </div>

      {!isDefault && (
        <p className="text-xs text-gold mt-4 pt-4 border-t border-ink-border">
          Assumptions changed from the documented base case (LGD{" "}
          {formatPercent(DEFAULT_ASSUMPTIONS.lgd)}, floor{" "}
          {DEFAULT_ASSUMPTIONS.minApprovalRatePct}%, cutoff{" "}
          {DEFAULT_ASSUMPTIONS.creditScoreCutoff}). Figures on this page no
          longer match the published number set.
        </p>
      )}
    </div>
  );
}
