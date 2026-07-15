import { Link, useRouterState } from "@tanstack/react-router";
import { LayoutDashboard, Bot, MapPin, Bell, Settings } from "lucide-react";

const items = [
  { icon: LayoutDashboard, label: "Home", to: "/" },
  { icon: Bot, label: "Agents", to: "/ai-agents" },
  { icon: MapPin, label: "Map", to: "/gis-map" },
  { icon: Bell, label: "Alerts", to: "/alerts" },
  { icon: Settings, label: "Settings", to: "/settings" },
];

export function MobileNav() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  return (
    <nav className="glass-panel-strong fixed bottom-3 left-3 right-3 z-30 flex items-center justify-around rounded-2xl px-2 py-2 lg:hidden">
      {items.map((it) => {
        const Icon = it.icon;
        const active = it.to === pathname;
        return (
          <Link
            key={it.label}
            to={it.to}
            className={[
              "flex min-h-11 min-w-11 flex-col items-center justify-center gap-0.5 rounded-xl px-3 py-1 transition",
              active ? "text-[var(--lime-glow)]" : "text-white/50 hover:text-white",
            ].join(" ")}
          >
            <Icon className="size-5" />
            <span className="text-[10px] font-semibold">{it.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
