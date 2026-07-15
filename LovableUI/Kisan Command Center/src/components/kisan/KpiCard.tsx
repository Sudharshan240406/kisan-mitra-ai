import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { Area, AreaChart, ResponsiveContainer } from "recharts";
import type { LucideIcon } from "lucide-react";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";

export type Kpi = {
  label: string;
  value: number;
  suffix?: string;
  prefix?: string;
  delta: number;
  icon: LucideIcon;
  tone: "lime" | "wheat" | "sky" | "leaf";
  data: number[];
};

const tones = {
  lime: { fg: "var(--lime-glow)", from: "oklch(0.88 0.22 125 / 40%)", to: "oklch(0.88 0.22 125 / 0%)" },
  wheat: { fg: "var(--wheat)", from: "oklch(0.78 0.14 78 / 40%)", to: "oklch(0.78 0.14 78 / 0%)" },
  sky: { fg: "var(--sky-agri)", from: "oklch(0.78 0.13 235 / 40%)", to: "oklch(0.78 0.13 235 / 0%)" },
  leaf: { fg: "var(--leaf)", from: "oklch(0.72 0.19 135 / 40%)", to: "oklch(0.72 0.19 135 / 0%)" },
};

function useCountUp(target: number, duration = 1200) {
  const [n, setN] = useState(0);
  useEffect(() => {
    let raf = 0;
    const start = performance.now();
    const tick = (t: number) => {
      const p = Math.min(1, (t - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      setN(target * eased);
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return n;
}

function fmt(n: number) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "k";
  return Math.round(n).toLocaleString("en-IN");
}

export function KpiCard({ kpi, index }: { kpi: Kpi; index: number }) {
  const tone = tones[kpi.tone];
  const value = useCountUp(kpi.value);
  const Icon = kpi.icon;
  const positive = kpi.delta >= 0;
  const chartData = kpi.data.map((v, i) => ({ i, v }));
  const uid = `kpi-grad-${kpi.tone}-${index}`;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.05 * index, ease: [0.16, 1, 0.3, 1] }}
      whileHover={{ y: -3 }}
      className="glass-panel group relative overflow-hidden rounded-2xl p-5 transition-shadow hover:shadow-[0_20px_60px_-20px_oklch(0_0_0/50%)]"
    >
      <div
        className="absolute inset-x-0 -top-px h-px opacity-70"
        style={{ background: `linear-gradient(90deg, transparent, ${tone.fg}, transparent)` }}
      />
      <div className="mb-4 flex items-start justify-between">
        <div
          className="grid size-10 place-items-center rounded-xl"
          style={{ background: `color-mix(in oklab, ${tone.fg} 15%, transparent)`, color: tone.fg }}
        >
          <Icon className="size-5" />
        </div>
        <div
          className={[
            "flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-bold",
            positive ? "bg-[var(--lime-glow)]/10 text-[var(--lime-glow)]" : "bg-red-500/10 text-red-400",
          ].join(" ")}
        >
          {positive ? <ArrowUpRight className="size-3" /> : <ArrowDownRight className="size-3" />}
          {Math.abs(kpi.delta)}%
        </div>
      </div>
      <div className="text-[11px] font-medium uppercase tracking-wider text-white/50">{kpi.label}</div>
      <div className="mt-1 flex items-baseline gap-1 font-display text-3xl font-bold tabular-nums text-white">
        {kpi.prefix}
        <span>{fmt(value)}</span>
        {kpi.suffix && <span className="text-base font-medium text-white/50">{kpi.suffix}</span>}
      </div>
      <div className="pointer-events-none mt-3 h-12">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id={uid} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={tone.from} />
                <stop offset="100%" stopColor={tone.to} />
              </linearGradient>
            </defs>
            <Area
              type="monotone"
              dataKey="v"
              stroke={tone.fg}
              strokeWidth={1.75}
              fill={`url(#${uid})`}
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
