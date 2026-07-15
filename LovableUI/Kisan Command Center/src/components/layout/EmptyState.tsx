import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="glass-panel flex flex-col items-center justify-center rounded-2xl border border-dashed border-white/10 p-10 text-center">
      <div className="grid size-14 place-items-center rounded-2xl bg-white/5 text-white/60">
        <Icon className="size-6" />
      </div>
      <h4 className="mt-4 font-display text-base font-bold">{title}</h4>
      {description && <p className="mt-1 max-w-sm text-xs text-white/50">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
