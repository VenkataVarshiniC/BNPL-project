import { NavLink, Link } from "react-router-dom";

// Grouped by the question each screen answers, in the order a reader would
// work through them: what is happening → why → what should we do about it.
const NAV_GROUPS = [
  {
    heading: "Position",
    items: [{ to: "/app", label: "Executive summary", glyph: "01" }],
  },
  {
    heading: "Analysis",
    items: [
      { to: "/app/risk", label: "Risk analysis", glyph: "02" },
      { to: "/app/profitability", label: "Merchant detail", glyph: "03" },
      { to: "/app/segmentation", label: "Segmentation", glyph: "04" },
    ],
  },
  {
    heading: "Decision",
    items: [
      { to: "/app/simulator", label: "Strategy simulator", glyph: "05" },
      { to: "/app/comparison", label: "Scenario comparison", glyph: "06" },
      { to: "/app/decision", label: "Decision summary", glyph: "07" },
    ],
  },
  {
    heading: "Model",
    items: [
      { to: "/app/risk-score", label: "Risk score", glyph: "08" },
      { to: "/app/explainability", label: "Explainability", glyph: "09" },
    ],
  },
];

export default function Sidebar() {
  return (
    <aside className="w-60 shrink-0 border-r border-ink-border bg-ink-surface flex flex-col">
      <Link
        to="/"
        className="focus-ring px-5 py-6 border-b border-ink-border block hover:bg-ink-surface2/40 transition-colors"
      >
        <div className="font-display font-semibold text-lg tracking-tight text-paper">
          Ledger
        </div>
        <div className="text-xs text-paper-dim font-mono mt-0.5">
          BNPL risk &amp; profitability
        </div>
      </Link>

      <nav className="flex-1 py-3 overflow-y-auto">
        {NAV_GROUPS.map((group) => (
          <div key={group.heading} className="mb-2">
            <div className="px-5 py-1.5 text-[10px] uppercase tracking-wider text-paper-dim/60">
              {group.heading}
            </div>
            {group.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/app"}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-5 py-2 text-sm transition-colors focus-ring ${
                    isActive
                      ? "text-paper bg-ink-surface2 border-r-2 border-gold"
                      : "text-paper-dim hover:text-paper hover:bg-ink-surface2/50"
                  }`
                }
              >
                <span className="font-mono text-xs text-paper-dim">
                  {item.glyph}
                </span>
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className="px-5 py-4 border-t border-ink-border text-xs text-paper-dim leading-relaxed">
        Synthetic dataset · 5,000 customers
        <div className="text-paper-dim/60 mt-1">
          Decision support only. No lending decisions are made here.
        </div>
      </div>
    </aside>
  );
}
