import type { ReactNode } from "react";
import { Link, useRouterState } from "@tanstack/react-router";
import { ChevronRight, Home } from "lucide-react";
import { findNav } from "./nav-config";

type Props = {
  eyebrow?: string;
  title: string;
  description?: string;
  icon?: React.ComponentType<{ className?: string }>;
  actions?: ReactNode;
};

export function PageHeader({ eyebrow, title, description, icon: Icon, actions }: Props) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const current = findNav(pathname);

  return (
    <header className="space-y-4">
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-[11px] text-mono text-white/40">
        <Link to="/" className="flex items-center gap-1 hover:text-[var(--lime-glow)]">
          <Home className="size-3" /> Home
        </Link>
        {current && current.to !== "/" && (
          <>
            <ChevronRight className="size-3" />
            <span className="text-white/70">{current.label}</span>
          </>
        )}
      </nav>

      <div className="glass-panel-strong overflow-hidden rounded-3xl border border-white/5 p-5 sm:p-6">
        <div className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4 sm:flex sm:flex-wrap sm:justify-between">
          <div className="flex min-w-0 items-center gap-4">
            {Icon && (
              <div className="grid size-12 shrink-0 place-items-center rounded-2xl bg-gradient-to-br from-[var(--lime-glow)]/25 to-[var(--forest-800)]/40 ring-1 ring-inset ring-[var(--lime-glow)]/30 shadow-[0_0_20px_-6px_var(--lime-glow)]">
                <Icon className="size-6 text-[var(--lime-glow)]" />
              </div>
            )}
            <div className="min-w-0">
              {eyebrow && (
                <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--lime-glow)]">
                  {eyebrow}
                </div>
              )}
              <h1 className="mt-0.5 truncate font-display text-xl font-bold sm:text-2xl">{title}</h1>
              {description && (
                <p className="mt-1 text-xs text-white/60 sm:text-sm">{description}</p>
              )}
            </div>
          </div>
          {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
        </div>
      </div>
    </header>
  );
}
