import type { ReactNode } from "react";
import { BackgroundFX } from "@/components/kisan/BackgroundFX";
import { Sidebar } from "@/components/kisan/Sidebar";
import { TopBar } from "@/components/kisan/TopBar";
import { MobileNav } from "@/components/kisan/MobileNav";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="relative min-h-dvh text-white">
      <BackgroundFX />
      <Sidebar />
      <div className="relative z-10 lg:pl-64">
        <TopBar />
        <main className="mx-auto max-w-[1600px] space-y-6 p-4 pb-28 sm:p-6 lg:pb-8">
          {children}
          <footer className="pt-6 text-center text-[11px] text-white/40">
            <span className="text-mono">KISAN·MITRA·AI</span> · Agriculture Operations OS · v4.2 ·
            <span className="text-[var(--lime-glow)]"> All systems nominal</span>
          </footer>
        </main>
      </div>
      <MobileNav />
    </div>
  );
}
