import { useEffect, useState } from "react";
import { checkHealth } from "../api/client.js";

export default function TopBar({ title, subtitle }) {
  const [status, setStatus] = useState("checking");

  useEffect(() => {
    let cancelled = false;
    checkHealth()
      .then(() => !cancelled && setStatus("online"))
      .catch(() => !cancelled && setStatus("offline"));
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <header className="flex items-center justify-between px-8 py-5 border-b border-ink-border">
      <div>
        <h1 className="font-display font-semibold text-xl text-paper tracking-tight">
          {title}
        </h1>
        {subtitle && <p className="text-sm text-paper-dim mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-2 text-xs font-mono">
        <span
          className={`h-1.5 w-1.5 rounded-full ${
            status === "online"
              ? "bg-teal"
              : status === "offline"
              ? "bg-coral"
              : "bg-paper-dim animate-pulse"
          }`}
        />
        <span className="text-paper-dim">
          {status === "online" && "API connected"}
          {status === "offline" && "API unreachable"}
          {status === "checking" && "Checking API…"}
        </span>
      </div>
    </header>
  );
}
