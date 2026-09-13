export function SkeletonCard() {
  return (
    <div className="card p-5">
      <div className="h-3 w-20 rounded bg-ink-surface2 animate-pulse mb-3" />
      <div className="h-7 w-28 rounded bg-ink-surface2 animate-pulse mb-2" />
      <div className="h-2.5 w-24 rounded bg-ink-surface2 animate-pulse" />
    </div>
  );
}

export function SkeletonGrid({ count = 3, cols = "sm:grid-cols-2 lg:grid-cols-3" }) {
  return (
    <div className={`grid grid-cols-1 ${cols} gap-4`}>
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}

export function SkeletonChart({ height = 280 }) {
  return (
    <div className="card p-5">
      <div className="h-3 w-40 rounded bg-ink-surface2 animate-pulse mb-4" />
      <div
        className="rounded bg-ink-surface2 animate-pulse"
        style={{ height }}
      />
    </div>
  );
}
