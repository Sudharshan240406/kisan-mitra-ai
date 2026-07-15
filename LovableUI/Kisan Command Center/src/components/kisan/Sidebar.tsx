import { useState } from "react";
import { Link, useRouterState } from "@tanstack/react-router";
import { Leaf, X, Menu } from "lucide-react";
import { navGroups } from "@/components/layout/nav-config";

function NavList({ activePath, onNavigate }: { activePath: string; onNavigate?: () => void }) {
  return (
    <nav className="space-y-6">
      {navGroups.map((g) => (
        <div key={g.title}>
          <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/35">
            {g.title}
          </div>
          <div className="space-y-0.5">
            {g.items.map((item) => {
              const active = item.to === activePath;
              const Icon = item.icon;
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  onClick={onNavigate}
                  className={[
                    "group relative flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm transition-all",
                    active
                      ? "bg-gradient-to-r from-[var(--lime-glow)]/15 via-[var(--forest-800)]/25 to-transparent text-[var(--lime-glow)] ring-1 ring-inset ring-[var(--lime-glow)]/20"
                      : "text-white/60 hover:bg-white/5 hover:text-white",
                  ].join(" ")}
                >
                  {active && (
                    <span className="absolute left-0 top-1/2 h-6 w-[3px] -translate-y-1/2 rounded-r-full bg-[var(--lime-glow)] shadow-[0_0_12px_var(--lime-glow)]" />
                  )}
                  <Icon className="size-4 shrink-0" />
                  <span className="flex-1 truncate font-medium">{item.label}</span>
                  {item.badge && (
                    <span
                      className={[
                        "rounded-md px-1.5 py-0.5 text-[10px] font-bold text-mono",
                        active
                          ? "bg-[var(--lime-glow)]/20 text-[var(--lime-glow)]"
                          : "bg-white/5 text-white/60",
                      ].join(" ")}
                    >
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        </div>
      ))}
    </nav>
  );
}

function Brand() {
  return (
    <Link to="/" className="flex items-center gap-3 px-2">
      <div className="relative grid size-10 place-items-center rounded-xl bg-gradient-to-br from-[var(--lime-glow)] to-[var(--forest-800)] shadow-[0_0_20px_-4px_var(--lime-glow)]">
        <Leaf className="size-5 text-[var(--forest-950)]" strokeWidth={2.5} />
      </div>
      <div className="flex flex-col leading-tight">
        <span className="text-[15px] font-bold tracking-tight">Kisan Mitra</span>
        <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--lime-glow)]">
          AI · Ops
        </span>
      </div>
    </Link>
  );
}

function SatelliteStatus() {
  return (
    <div className="glass-panel rounded-2xl p-4">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-white/40">
          Satellite Link
        </span>
        <span className="text-[10px] text-mono text-[var(--lime-glow)]">GS-4</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="relative flex size-2">
          <span className="absolute inset-0 animate-ping rounded-full bg-[var(--lime-glow)] opacity-60" />
          <span className="relative rounded-full bg-[var(--lime-glow)] size-2" />
        </span>
        <span className="text-xs font-medium text-white/80">Uplink stable</span>
      </div>
      <div className="mt-3 h-1 overflow-hidden rounded-full bg-white/5">
        <div className="h-full w-[82%] rounded-full bg-gradient-to-r from-[var(--lime-glow)] to-[var(--sky-agri)]" />
      </div>
      <div className="mt-1.5 flex justify-between text-[10px] text-mono text-white/40">
        <span>82% BW</span>
        <span>12ms</span>
      </div>
    </div>
  );
}

export function Sidebar() {
  const [open, setOpen] = useState(false);
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <>
      <button
        aria-label="Open navigation"
        onClick={() => setOpen(true)}
        className="glass-panel fixed left-4 top-4 z-50 grid size-11 place-items-center rounded-xl lg:hidden"
      >
        <Menu className="size-5" />
      </button>

      <aside className="glass-panel-strong fixed left-0 top-0 z-40 hidden h-screen w-64 flex-col border-r border-white/5 lg:flex">
        <div className="p-6">
          <Brand />
        </div>
        <div className="flex-1 overflow-y-auto px-3 pb-4">
          <NavList activePath={pathname} />
        </div>
        <div className="p-4">
          <SatelliteStatus />
        </div>
      </aside>

      {open && (
        <div className="fixed inset-0 z-[60] lg:hidden">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-in fade-in"
            onClick={() => setOpen(false)}
          />
          <aside className="glass-panel-strong absolute inset-y-0 left-0 flex w-[85%] max-w-[320px] flex-col border-r border-white/10 animate-in slide-in-from-left duration-300">
            <div className="flex items-center justify-between p-6">
              <Brand />
              <button
                aria-label="Close navigation"
                onClick={() => setOpen(false)}
                className="grid size-9 place-items-center rounded-lg bg-white/5"
              >
                <X className="size-4" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto px-3 pb-4">
              <NavList activePath={pathname} onNavigate={() => setOpen(false)} />
            </div>
            <div className="p-4">
              <SatelliteStatus />
            </div>
          </aside>
        </div>
      )}
    </>
  );
}
