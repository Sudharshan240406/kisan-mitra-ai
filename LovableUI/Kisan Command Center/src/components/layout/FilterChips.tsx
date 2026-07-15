type Option = { value: string; label: string };

type Props = {
  options: Option[];
  value: string | null;
  onChange: (v: string | null) => void;
  allLabel?: string;
};

export function FilterChips({ options, value, onChange, allLabel = "All" }: Props) {
  const items: Option[] = [{ value: "", label: allLabel }, ...options];
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((o) => {
        const active = (value ?? "") === o.value;
        return (
          <button
            key={o.value || "__all"}
            onClick={() => onChange(o.value || null)}
            className={[
              "rounded-full px-3 py-1 text-[11px] font-semibold transition ring-1 ring-inset",
              active
                ? "bg-[var(--lime-glow)]/15 text-[var(--lime-glow)] ring-[var(--lime-glow)]/30"
                : "bg-white/[0.03] text-white/60 ring-white/10 hover:text-white/85",
            ].join(" ")}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
