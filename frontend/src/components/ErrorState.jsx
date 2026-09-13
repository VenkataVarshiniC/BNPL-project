export default function ErrorState({ message, onRetry }) {
  return (
    <div className="card p-8 text-center">
      <div className="text-coral font-display font-medium mb-1">
        Couldn't load this data
      </div>
      <p className="text-sm text-paper-dim mb-4">
        {message || "The backend didn't respond as expected. Make sure it's running on the configured API URL."}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="focus-ring text-sm px-4 py-2 rounded-md bg-ink-surface2 border border-ink-border text-paper hover:border-gold transition-colors"
        >
          Retry
        </button>
      )}
    </div>
  );
}
