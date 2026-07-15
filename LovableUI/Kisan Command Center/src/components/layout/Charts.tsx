import { LineChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid, AreaChart, Area, BarChart, Bar } from "recharts";

type Point = { x: string | number; y: number };

const tooltip = {
  contentStyle: { background: "rgba(10,20,15,0.95)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 12, fontSize: 11 },
  cursor: { stroke: "rgba(255,255,255,0.08)" },
};

export function MiniLine({ data, color = "var(--lime-glow)", height = 160 }: { data: Point[]; color?: string; height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 4, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
        <XAxis dataKey="x" tick={{ fontSize: 10, fill: "rgba(255,255,255,0.4)" }} axisLine={false} tickLine={false} />
        <YAxis hide />
        <Tooltip {...tooltip} />
        <Line type="monotone" dataKey="y" stroke={color} strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function AreaSpark({ data, color = "var(--sky-agri)", height = 160 }: { data: Point[]; color?: string; height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 8, right: 4, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="areaSpark" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.5} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
        <XAxis dataKey="x" tick={{ fontSize: 10, fill: "rgba(255,255,255,0.4)" }} axisLine={false} tickLine={false} />
        <YAxis hide />
        <Tooltip {...tooltip} />
        <Area type="monotone" dataKey="y" stroke={color} strokeWidth={2} fill="url(#areaSpark)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function MiniBars({ data, color = "var(--wheat)", height = 160 }: { data: Point[]; color?: string; height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 4, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
        <XAxis dataKey="x" tick={{ fontSize: 10, fill: "rgba(255,255,255,0.4)" }} axisLine={false} tickLine={false} />
        <YAxis hide />
        <Tooltip {...tooltip} />
        <Bar dataKey="y" fill={color} radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
