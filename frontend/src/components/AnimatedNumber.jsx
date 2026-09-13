import { useEffect, useRef } from "react";
import { useMotionValue, useSpring, useInView } from "framer-motion";

export default function AnimatedNumber({ value, format = (v) => v, duration = 1 }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });
  const motionVal = useMotionValue(0);
  const spring = useSpring(motionVal, { duration: duration * 1000, bounce: 0 });

  useEffect(() => {
    if (inView && typeof value === "number" && !Number.isNaN(value)) {
      motionVal.set(value);
    }
  }, [inView, value]);

  useEffect(() => {
    const unsub = spring.on("change", (latest) => {
      if (ref.current) ref.current.textContent = format(latest);
    });
    return unsub;
  }, [spring, format]);

  if (typeof value !== "number" || Number.isNaN(value)) {
    return <span>{format(value)}</span>;
  }

  return <span ref={ref}>{format(0)}</span>;
}
