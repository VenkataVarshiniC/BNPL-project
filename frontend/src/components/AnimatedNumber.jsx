import { useEffect, useState } from "react";

export default function AnimatedNumber({ value, format = (v) => v, duration = 1 }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (typeof value !== "number" || Number.isNaN(value)) return undefined;
    const started = performance.now();
    let frame;
    const tick = (now) => {
      const progress = Math.min((now - started) / (duration * 1000), 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(value * eased);
      if (progress < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value, duration]);

  if (typeof value !== "number" || Number.isNaN(value)) {
    return <span>{format(value)}</span>;
  }

  return <span>{format(display)}</span>;
}
