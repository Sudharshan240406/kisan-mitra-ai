import type { ReactNode } from "react";

type Props = {
  title?: string;
  eyebrow?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  strong?: boolean;
};

export function GlassCard({ title, eyebrow, actions, children, className = "", strong }: Props) {
  return (
    <section
      className={[
        strong ? "glass-panel-strong" : "glass-panel",
        "rounded-2xl border border-white/5 p-4 sm:p-5",
        className,
      ].join(" ")}
    >
      {(title || eyebrow || actions) && (
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="min-w-0">
            {eyebrow && (
              <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--lime-glow)]">
                {eyebrow}
              </div>
            )}
            {title && <h3 className="mt-0.5 truncate font-display text-sm font-bold sm:text-base">{title}</h3>}
          </div>
          {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
        </div>
      )}
      {children}
    </section>
  );
}
