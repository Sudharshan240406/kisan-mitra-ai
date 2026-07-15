import { useEffect, useState } from "react";
import { Bell, Search, Sun, Globe, Cloud } from "lucide-react";

export function TopBar() {
  const [now, setNow] = useState<Date | null>(null);
  useEffect(() => {
    setNow(new Date());
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const time = now ? now.toLocaleTimeString("en-IN", { hour12: false }) : "--:--:--";
  const date = now ? now.toLocaleDateString("en-IN", { weekday: "short", day: "2-digit", month: "short" }) : "";

  return (
    <header className="sticky top-4 z-30 mx-4 lg:mx-6">
      <div className="glass-panel-strong flex h-16 items-center justify-between gap-3 rounded-2xl px-4 lg:rounded-full lg:px-6">
        {/* Left cluster */}
        <div className="flex min-w-0 items-center gap-3 pl-11 lg:pl-0">
          <div className="hidden items-center gap-2 rounded-full bg-white/5 px-3 py-1.5 md:flex">
            <span className="relative flex size-2">
              <span className="absolute inset-0 animate-ping rounded-full bg-[var(--lime-glow)] opacity-60" />
              <span className="relative size-2 rounded-full bg-[var(--lime-glow)]" />
            </span>
            <span className="text-[11px] font-semibold text-[var(--lime-glow)]">All systems nominal</span>
          </div>
          <div className="hidden items-center gap-2 text-mono text-[11px] text-white/50 xl:flex">
            <Cloud className="size-3.5" />
            <span>28°C · Nagpur, MH</span>
          </div>
        </div>

        {/* Search */}
        <div className="glass-panel hidden max-w-md flex-1 items-center gap-2 rounded-full px-4 py-2 md:flex">
          <Search className="size-4 text-white/40" />
          <input
            aria-label="Search"
            placeholder="Search farmers, mandis, schemes…"
            className="flex-1 bg-transparent text-sm text-white placeholder:text-white/40 outline-none"
          />
          <kbd className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] text-mono text-white/50">⌘K</kbd>
        </div>

        {/* Right cluster */}
        <div className="flex items-center gap-2">
          <div className="hidden flex-col items-end pr-2 text-right leading-tight sm:flex">
            <span className="text-[11px] text-mono text-white/70">{time}</span>
            <span className="text-[10px] text-white/40">{date}</span>
          </div>
          <button
            aria-label="Change language"
            className="hidden size-9 place-items-center rounded-full bg-white/5 hover:bg-white/10 md:grid"
          >
            <Globe className="size-4 text-white/70" />
          </button>
          <button
            aria-label="Theme"
            className="hidden size-9 place-items-center rounded-full bg-white/5 hover:bg-white/10 md:grid"
          >
            <Sun className="size-4 text-white/70" />
          </button>
          <button
            aria-label="Notifications"
            className="relative grid size-9 place-items-center rounded-full bg-white/5 hover:bg-white/10"
          >
            <Bell className="size-4 text-white/70" />
            <span className="absolute right-1.5 top-1.5 size-1.5 rounded-full bg-[var(--wheat)] shadow-[0_0_8px_var(--wheat)]" />
          </button>
          <div className="grid size-9 place-items-center rounded-full bg-gradient-to-br from-[var(--wheat)] to-[var(--earth)] text-[11px] font-bold text-[var(--forest-950)] ring-1 ring-white/20">
            AD
          </div>
        </div>
      </div>
    </header>
  );
}
