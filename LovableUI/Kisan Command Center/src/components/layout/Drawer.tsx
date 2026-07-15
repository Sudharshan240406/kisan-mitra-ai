import type { ReactNode } from "react";
import { useEffect } from "react";
import { X } from "lucide-react";

type Props = {
  open: boolean;
  onClose: () => void;
  title?: string;
  eyebrow?: string;
  children: ReactNode;
  widthClass?: string;
};

export function Drawer({ open, onClose, title, eyebrow, children, widthClass = "sm:max-w-md" }: Props) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[100]" role="dialog" aria-modal="true">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200"
        onClick={onClose}
      />
      <aside
        className={`glass-panel-strong absolute inset-y-0 right-0 flex w-full ${widthClass} flex-col border-l border-white/10 shadow-[0_0_60px_-10px_rgba(0,0,0,0.6)] animate-in slide-in-from-right duration-300`}
      >
        <header className="flex items-start justify-between gap-3 border-b border-white/5 px-5 py-4">
          <div className="min-w-0">
            {eyebrow && (
              <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--lime-glow)]">{eyebrow}</div>
            )}
            {title && <h2 className="mt-0.5 truncate font-display text-lg font-bold">{title}</h2>}
          </div>
          <button onClick={onClose} className="rounded-full bg-white/5 p-1.5 text-white/60 hover:bg-white/10 hover:text-white">
            <X className="size-4" />
          </button>
        </header>
        <div className="flex-1 overflow-y-auto p-5">{children}</div>
      </aside>
    </div>
  );
}
