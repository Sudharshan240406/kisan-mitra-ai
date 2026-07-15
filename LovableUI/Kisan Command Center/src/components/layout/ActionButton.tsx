import type { ReactNode } from "react";

type Variant = "primary" | "ghost";

export function ActionButton({
  children,
  icon: Icon,
  onClick,
  variant = "ghost",
}: {
  children: ReactNode;
  icon?: React.ComponentType<{ className?: string }>;
  onClick?: () => void;
  variant?: Variant;
}) {
  const base =
    "inline-flex items-center gap-2 rounded-full px-3.5 py-2 text-xs font-semibold transition active:scale-[0.97]";
  const styles =
    variant === "primary"
      ? "bg-gradient-to-r from-[var(--lime-glow)] to-emerald-300 text-[var(--forest-950)] shadow-[0_0_20px_-6px_var(--lime-glow)] hover:brightness-110"
      : "bg-white/5 text-white/80 ring-1 ring-inset ring-white/10 hover:bg-white/10 hover:text-white";
  return (
    <button onClick={onClick} className={`${base} ${styles}`}>
      {Icon && <Icon className="size-3.5" />}
      {children}
    </button>
  );
}
