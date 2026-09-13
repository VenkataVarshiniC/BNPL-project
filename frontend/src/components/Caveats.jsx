/**
 * Standing caveats, rendered inline rather than linked.
 *
 * These come from the API, not the frontend — the backend refuses to return a
 * projection without them, so a figure cannot be separated from its
 * qualifications in transit.
 */
export default function Caveats({ caveats, className = "" }) {
  if (!caveats?.length) return null;

  return (
    <div className={`card p-5 border-gold/30 ${className}`}>
      <h3 className="text-xs uppercase tracking-wide text-gold mb-3">
        What these figures do and don't mean
      </h3>
      <ul className="space-y-2">
        {caveats.map((c, i) => (
          <li
            key={i}
            className="text-sm text-paper-dim leading-relaxed flex gap-2.5"
          >
            <span className="text-gold shrink-0 mt-0.5" aria-hidden="true">
              —
            </span>
            <span>{c}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Inline flag for a condition the reader must not miss. */
export function Flag({ tone = "warn", children }) {
  const toneClass =
    tone === "warn"
      ? "border-gold/40 text-gold"
      : tone === "bad"
      ? "border-coral/40 text-coral"
      : "border-teal/40 text-teal";

  return (
    <div className={`rounded-md border px-4 py-3 text-sm leading-relaxed ${toneClass}`}>
      {children}
    </div>
  );
}
