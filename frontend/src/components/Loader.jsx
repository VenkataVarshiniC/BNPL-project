export default function Loader({ label = "Loading" }) {
  return (
    <div className="flex items-center gap-2 text-paper-dim text-sm font-mono py-12 justify-center">
      <span className="h-1.5 w-1.5 rounded-full bg-gold animate-pulse" />
      <span>{label}…</span>
    </div>
  );
}
