import { useEffect, useRef, useState } from "react";

/**
 * Audio-driven waveform.
 *
 * The component NEVER fabricates amplitudes. It renders bars from the
 * `amplitudes` prop (values in [0..1]) — expected to come from a real audio
 * frame stream (Web Audio `AnalyserNode`, backend RMS packets, etc.).
 *
 * When `amplitudes` is empty or `active` is false, all bars sit at a flat
 * idle baseline so the row is still visible but visually silent.
 */
export function VoiceWaveform({
  amplitudes,
  active = false,
  tone = "lime",
  bars = 28,
  className = "",
}: {
  /** Real audio frame amplitudes in [0..1]. When absent the waveform is idle. */
  amplitudes?: number[];
  active?: boolean;
  tone?: "lime" | "sky" | "wheat";
  bars?: number;
  className?: string;
}) {
  const IDLE_LEVEL = 0.08;
  const [values, setValues] = useState<number[]>(() => Array.from({ length: bars }, () => IDLE_LEVEL));
  const raf = useRef<number | null>(null);

  useEffect(() => {
    // Cancel any pending frame from a previous render.
    if (raf.current != null) cancelAnimationFrame(raf.current);

    if (!active || !amplitudes || amplitudes.length === 0) {
      setValues(Array.from({ length: bars }, () => IDLE_LEVEL));
      return;
    }

    // Map incoming frames to the fixed bar count without inventing data.
    // If the source produced fewer than `bars` samples, remaining bars stay
    // at the idle baseline rather than being filled with random values.
    raf.current = requestAnimationFrame(() => {
      setValues(
        Array.from({ length: bars }, (_, i) => {
          const idx = Math.floor((i / bars) * amplitudes.length);
          const v = amplitudes[idx];
          return typeof v === "number" ? Math.max(0, Math.min(1, v)) : IDLE_LEVEL;
        }),
      );
    });

    return () => {
      if (raf.current != null) cancelAnimationFrame(raf.current);
    };
  }, [amplitudes, active, bars]);

  const color =
    tone === "sky" ? "var(--sky-agri)" : tone === "wheat" ? "var(--wheat)" : "var(--lime-glow)";
  const live = active && !!amplitudes && amplitudes.length > 0;

  return (
    <div className={`flex h-12 items-center gap-[3px] ${className}`} aria-hidden>
      {values.map((v, i) => (
        <span
          key={i}
          className="w-[3px] rounded-full transition-all duration-150 ease-out"
          style={{
            height: `${Math.max(6, v * 100)}%`,
            background: `linear-gradient(180deg, ${color}, color-mix(in oklab, ${color} 30%, transparent))`,
            boxShadow: live ? `0 0 8px -1px ${color}` : "none",
            opacity: live ? 0.9 : 0.3,
          }}
        />
      ))}
    </div>
  );
}
