import { Search } from "lucide-react";

type Props = {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  className?: string;
};

export function SearchInput({ value, onChange, placeholder = "Search…", className = "" }: Props) {
  return (
    <div className={`glass-panel flex items-center gap-2 rounded-full px-3 py-1.5 ring-1 ring-inset ring-white/5 ${className}`}>
      <Search className="size-3.5 text-white/40" />
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-transparent text-xs outline-none placeholder:text-white/40"
      />
    </div>
  );
}
